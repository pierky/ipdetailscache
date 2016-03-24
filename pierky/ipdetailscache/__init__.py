# Copyright (c) 2016 Pier Carlo Chiodi - http://www.pierky.com
# Licensed under The MIT License (MIT) - http://opensource.org/licenses/MIT
#
# The MIT License (MIT)
# =====================
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Part of this work is based on Google Python IP address manipulation library
# (https://code.google.com/p/ipaddr-py/) and Jeff Ferland IPy library
# (https://github.com/autocracy/python-ipy).

"""A Python library to gather IP address details (ASN, prefix, resource holder,
reverse DNS) using the RIPEStat API, with a basic cache to avoid flood of
requests and to enhance performance."""


import os.path
import time
import json
import socket

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

try:
    import ipaddr  # http://code.google.com/p/ipaddr-py/ - pip install ipaddr
    ip_library = 'ipaddr'
except ImportError:
    import IPy     # https://github.com/autocracy/python-ipy/ - pip install ipy
    ip_library = 'IPy'


class IPDetailsCacheError(Exception):
    pass


class IPDetailsCacheIXPInformationError(IPDetailsCacheError):
    pass


class IPWrapper():

    def __init__(self, ip):
        if ip_library == 'ipaddr':
            self.ip_object = ipaddr.IPAddress(ip)
        else:
            self.ip_object = IPy.IP(ip)

    def get_version(self):
        if ip_library == 'ipaddr':
            return self.ip_object.version
        else:
            return self.ip_object.version()

    def is_globally_routable(self):
        if ip_library == 'ipaddr':
            if self.get_version() == 4:
                return not self.ip_object.is_private
            else:
                return not (self.ip_object.is_private or
                            self.ip_object.is_reserved or
                            self.ip_object.is_link_local or
                            self.ip_object.is_site_local or
                            self.ip_object.is_unspecified)
        else:
            return self.ip_object.iptype() not in ['RESERVED', 'UNSPECIFIED',
                                                   'LOOPBACK', 'UNASSIGNED',
                                                   'DOCUMENTATION', 'ULA',
                                                   'LINKLOCAL', 'PRIVATE']

    def exploded(self):
        if ip_library == 'ipaddr':
            return self.ip_object.exploded
        else:
            return self.ip_object.strFullsize()


class NetWrapper():

    def __init__(self, prefix):
        if ip_library == 'ipaddr':
            self.net_object = ipaddr.IPNetwork(prefix)
        else:
            self.net_object = IPy.IP(prefix)

    def contains(self, ip_obj):
        if ip_library == 'ipaddr':
            return self.net_object.Contains(ip_obj.ip_object)
        else:
            return ip_obj.ip_object in self.net_object


class IPDetailsCache():

    PEERINGDB_API_ixpfx = "https://www.peeringdb.com/api/ixpfx"
    PEERINGDB_API_ixlan = "https://www.peeringdb.com/api/ixlan"
    PEERINGDB_API_ix = "https://www.peeringdb.com/api/ix"

    URL = "https://stat.ripe.net/data/prefix-overview/data.json?resource={}"

    def _Debug(self, s):
        if self.Debug:
            print("DEBUG - IPDetailsCache - %s" % s)

    @staticmethod
    def _read_from_url(url):
        response = urlopen(url)
        return response.read().decode("utf-8")

    def FetchIPInfo(self, IP):
        self._Debug("Fetching info for {} from RIPEStat API".format(IP))
        url = IPDetailsCache.URL.format(IP)
        return json.loads(self._read_from_url(url))

    # IPPrefixesCache[<ip prefix>]["TS"]
    # IPPrefixesCache[<ip prefix>]["ASN"]
    # IPPrefixesCache[<ip prefix>]["Holder"]

    # IPAddressesCache[<ip>]["TS"]
    # IPAddressesCache[<ip>]["ASN"]
    # IPAddressesCache[<ip>]["Holder"]
    # IPAddressesCache[<ip>]["Prefix"]
    # IPAddressesCache[<ip>]["HostName"]

    def _enrich_with_ixp_info(self, IPObj, Result):
        if Result["IsIXP"] is not None:
            # cached address already enriched with IXPs info
            return

        if self.UseIXPsCache == 2 or (self.UseIXPsCache == 1 and
                                      not Result["ASN"].isdigit()):

            self._Debug("Looking for IXP info")

            Result["IsIXP"] = False

            for IPPrefix in self.IXPsCache["Data"].keys():
                if NetWrapper(IPPrefix).contains(IPObj):
                    Result["IsIXP"] = True
                    Result["IXPName"] = \
                        self.IXPsCache["Data"][IPPrefix]["name"]
                    self._Debug(
                        "IXP found: prefix {}, name {}".format(
                            IPPrefix,
                            self.IXPsCache["Data"][IPPrefix]["name"]
                        )
                    )
                    break

    def GetIPInformation(self, in_IP):
        Result = {}
        Result["TS"] = 0
        Result["ASN"] = ""
        Result["Holder"] = ""
        Result["Prefix"] = ""
        Result["HostName"] = ""
        Result["IsIXP"] = None
        Result["IXPName"] = ""

        IP = in_IP
        IPObj = IPWrapper(IP)

        if IP != IPObj.exploded():
            IP = IPObj.exploded()

        if IP not in self.IPAddressObjects:
            self.IPAddressObjects[IP] = IPObj

        if not IPObj.is_globally_routable():
            Result["ASN"] = "unknown"
            return Result

        exp_epoch = int(time.time()) - self.MAX_CACHE
        if IP in self.IPAddressesCache:
            if self.IPAddressesCache[IP]["TS"] >= exp_epoch:
                for k in self.IPAddressesCache[IP].keys():
                    Result[k] = self.IPAddressesCache[IP][k]
                self._Debug("IP address cache hit for %s" % IP)
                self._enrich_with_ixp_info(IPObj, Result)
                return Result
            else:
                self._Debug("Expired IP address cache hit for %s" % IP)

        for IPPrefix in self.IPPrefixesCache:
            if self.IPPrefixesCache[IPPrefix]["TS"] >= exp_epoch:
                if IPPrefix not in self.IPPrefixObjects:
                    self.IPPrefixObjects[IPPrefix] = NetWrapper(IPPrefix)

                if self.IPPrefixObjects[IPPrefix].contains(IPObj):
                    Result["TS"] = self.IPPrefixesCache[IPPrefix]["TS"]
                    Result["ASN"] = self.IPPrefixesCache[IPPrefix]["ASN"]
                    Result["Holder"] = \
                        self.IPPrefixesCache[IPPrefix].get("Holder", "")
                    Result["Prefix"] = IPPrefix
                    self._Debug(
                        "IP prefix cache hit for {} (prefix {})".format(
                            IP, IPPrefix
                        )
                    )
                    break

        if Result["ASN"] == "":
            self._Debug("No cache hit for %s" % IP)

            obj = self.FetchIPInfo(IP)

            if obj["status"] == "ok":
                Result["TS"] = int(time.time())

                if obj["data"]["asns"] != []:
                    try:
                        Result["ASN"] = str(obj["data"]["asns"][0]["asn"])
                        Result["Holder"] = obj["data"]["asns"][0]["holder"]
                        Result["Prefix"] = obj["data"]["resource"]

                        self._Debug(
                            "Got data for {}: ASN {}, prefix {}".format(
                                IP, Result["ASN"], Result["Prefix"]
                            )
                        )
                    except:
                        Result["ASN"] = "unknown"

                        self._Debug("No data for %s" % IP)
                else:
                    Result["ASN"] = "not announced"
                    Result["Holder"] = ""
                    Result["Prefix"] = obj["data"]["resource"]

            if Result["ASN"].isdigit() or Result["ASN"] == "not announced":
                HostName = socket.getfqdn(IP)
                if HostName == IP or HostName == "":
                    Result["HostName"] = "unknown"
                else:
                    Result["HostName"] = HostName

        self._enrich_with_ixp_info(IPObj, Result)

        if IP not in self.IPAddressesCache:
            self.IPAddressesCache[IP] = {}
            self._Debug("Adding %s to addresses cache" % IP)
        else:
            self._Debug("Updating addresses cache for %s" % IP)

        self.IPAddressesCache[IP]["TS"] = Result["TS"]
        self.IPAddressesCache[IP]["ASN"] = Result["ASN"]
        self.IPAddressesCache[IP]["Holder"] = Result["Holder"]
        self.IPAddressesCache[IP]["Prefix"] = Result["Prefix"]
        self.IPAddressesCache[IP]["HostName"] = Result["HostName"]
        self.IPAddressesCache[IP]["IsIXP"] = Result["IsIXP"]
        self.IPAddressesCache[IP]["IXPName"] = Result["IXPName"]

        if Result["Prefix"] != "":
            IPPrefix = Result["Prefix"]

            if IPPrefix not in self.IPPrefixesCache:
                self.IPPrefixesCache[IPPrefix] = {}
                self._Debug("Adding %s to prefixes cache" % IPPrefix)

            self.IPPrefixesCache[IPPrefix]["TS"] = Result["TS"]
            self.IPPrefixesCache[IPPrefix]["ASN"] = Result["ASN"]
            self.IPPrefixesCache[IPPrefix]["Holder"] = Result["Holder"]

        return Result

    def SaveCache(self):
        # Save IP addresses cache

        if self.IP_ADDRESSES_CACHE_FILE:
            self._Debug(
                "Saving IP addresses cache to {}.tmp".format(
                    self.IP_ADDRESSES_CACHE_FILE
                )
            )
            with open("%s.tmp" % self.IP_ADDRESSES_CACHE_FILE, "w") as outfile:
                json.dump(self.IPAddressesCache, outfile)

            self._Debug(
                "Renaming temporary IP addresses cache file in {}".format(
                    self.IP_ADDRESSES_CACHE_FILE
                )
            )
            os.rename("%s.tmp" % self.IP_ADDRESSES_CACHE_FILE,
                      self.IP_ADDRESSES_CACHE_FILE)

        if self.IP_PREFIXES_CACHE_FILE:
            # Save IP prefixes cache
            self._Debug(
                "Saving IP prefixes cache to {}.tmp".format(
                    self.IP_PREFIXES_CACHE_FILE
                )
            )
            with open("%s.tmp" % self.IP_PREFIXES_CACHE_FILE, "w") as outfile:
                json.dump(self.IPPrefixesCache, outfile)

            self._Debug(
                "Renaming temporary IP prefixes cache file in {}".format(
                    self.IP_PREFIXES_CACHE_FILE
                )
            )
            os.rename("%s.tmp" % self.IP_PREFIXES_CACHE_FILE,
                      self.IP_PREFIXES_CACHE_FILE)

    def LoadCache(self):
        # Load IP addresses cache

        if self.IP_ADDRESSES_CACHE_FILE:
            if self._file_not_zero(self.IP_ADDRESSES_CACHE_FILE):
                self._Debug(
                    "Loading IP addresses cache from {}".format(
                        self.IP_ADDRESSES_CACHE_FILE
                    )
                )
                json_data = open(self.IP_ADDRESSES_CACHE_FILE)
                self.IPAddressesCache = json.load(json_data)
                json_data.close()
            else:
                self._Debug(
                    "No IP addresses cache file found: {}".format(
                        self.IP_ADDRESSES_CACHE_FILE
                    )
                )

        # Load IP prefixes cache

        if self.IP_PREFIXES_CACHE_FILE:
            if self._file_not_zero(self.IP_PREFIXES_CACHE_FILE):
                self._Debug(
                    "Loading IP prefixes cache from {}".format(
                        self.IP_PREFIXES_CACHE_FILE
                    )
                )

                json_data = open(self.IP_PREFIXES_CACHE_FILE)
                self.IPPrefixesCache = json.load(json_data)
                json_data.close()
            else:
                self._Debug(
                    "No IP prefixes cache file found: {}".format(
                        self.IP_PREFIXES_CACHE_FILE
                    )
                )

    @staticmethod
    def _file_not_zero(path):
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return True
        else:
            return False

    def __init__(self, IP_ADDRESSES_CACHE_FILE="ip_addr.cache",
                 IP_PREFIXES_CACHE_FILE="ip_pref.cache", MAX_CACHE=604800,
                 dont_save_on_del=False, Debug=False):

        self.IPAddressesCache = {}
        self.IPPrefixesCache = {}
        self.IPAddressObjects = {}
        self.IPPrefixObjects = {}

        self.IP_ADDRESSES_CACHE_FILE = IP_ADDRESSES_CACHE_FILE
        self.IP_PREFIXES_CACHE_FILE = IP_PREFIXES_CACHE_FILE
        self.MAX_CACHE = MAX_CACHE

        self.IXPsCache = {}

        # 0 = do not use, 1 = only when no ASN found, 2 = always
        self.UseIXPsCache = 0

        self.DontSaveOnDel = dont_save_on_del
        self.Debug = Debug

        self.LoadCache()

        if self.IP_ADDRESSES_CACHE_FILE:
            # Test write access to IP addresses cache file
            self._Debug("Testing write permissions on IP addresses cache file")
            with open(self.IP_ADDRESSES_CACHE_FILE, "a") as outfile:
                outfile.close()
            self._Debug("Write permissions on IP addresses cache file OK")

        if self.IP_PREFIXES_CACHE_FILE:
            # Test write access to IP prefixes cache file
            self._Debug("Testing write permissions on IP prefixes cache file")
            with open(self.IP_PREFIXES_CACHE_FILE, "a") as outfile:
                outfile.close()
            self._Debug("Write permissions on IP prefixes cache file OK")

    def LoadIXPsCache(self, cache_file):
        if not cache_file:
            return

        if self._file_not_zero(cache_file):
            self._Debug("Loading IXPs cache from %s" % cache_file)
            json_data = open(cache_file)
            self.IXPsCache = json.load(json_data)
            json_data.close()
        else:
            self._Debug("No IXPs cache file found: %s" % cache_file)

    def FetchIXPsInfo(self):
        self._Debug("Fetching IXPs info from PeeringDB API...")

        try:
            url = IPDetailsCache.PEERINGDB_API_ixpfx
            ixpfxs = json.loads(self._read_from_url(url))

            url = IPDetailsCache.PEERINGDB_API_ixlan
            ixlans = json.loads(self._read_from_url(url))

            url = IPDetailsCache.PEERINGDB_API_ix
            ixs = json.loads(self._read_from_url(url))
        except Exception as e:
            raise IPDetailsCacheIXPInformationError(
                "Error fetching IXPs info from PeeringDB API: {}".format(
                    str(e)
                )
            )

        self._Debug("IXPs info fetched")

        return (ixpfxs, ixlans, ixs)

    def ValidateIXPInfo(self, ixpfxs, ixlans, ixs):

        try:
            for dct, dct_name, keys in [
                (ixpfxs, "ixpfxs", ["prefix", "ixlan_id"]),
                (ixlans, "ixlans", ["id", "ix_id"]),
                (ixs, "ixs", ["id", "name"])
            ]:

                if "data" not in dct:
                    raise KeyError(dct_name + " - missing key: data")
                if not isinstance(dct["data"], list):
                    raise TypeError(dct_name + " - data is not a list")
                if len(dct["data"]) == 0:
                    raise ValueError(dct_name + " - data is empty")

                dct_el = dct["data"][0]
                if not isinstance(dct_el, dict):
                    raise TypeError(dct_name + " - 1st element is not a dict")

                for k in keys:
                    if k not in dct_el.keys():
                        raise KeyError(
                            dct_name + " - missing key from elements: "
                            "{}".format(k)
                        )
        except Exception as e:
            raise IPDetailsCacheIXPInformationError(
                "Error validing PeeringDB IXPs information: {}".format(
                    str(e)
                )
            )

    def UseIXPs(self, WhenUse=1, IXP_CACHE_FILE="ixps.cache",
                MAX_CACHE=604800):

        self.UseIXPsCache = WhenUse

        if self.UseIXPsCache not in [0, 1, 2]:
            raise ValueError("UseIXPs WhenUse argument can be 0, 1 or 2.")

        if self.UseIXPsCache == 0:
            return

        self.LoadIXPsCache(IXP_CACHE_FILE)

        if "TS" in self.IXPsCache:
            if self.IXPsCache["TS"] < int(time.time()) - self.MAX_CACHE:
                self._Debug("IXPs cache expired. Updating it...")
            else:
                return

        ixpfxs, ixlans, ixs = self.FetchIXPsInfo()

        self.ValidateIXPInfo(ixpfxs, ixlans, ixs)

        ixs_dict = {}
        for ix in ixs["data"]:
            ixs_dict[str(ix["id"])] = {"name": ix["name"]}

        ixlans_dict = {}
        for ixlan in ixlans["data"]:
            ixlans_dict[str(ixlan["id"])] = {"ix_id": ixlan["ix_id"]}

        ixpfx_dict = {}
        for ixpfx in ixpfxs["data"]:
            prefix = ixpfx["prefix"]
            ixlan_id = ixpfx["ixlan_id"]
            ix_id = ixlans_dict[str(ixlan_id)]["ix_id"]
            ixpfx_dict[prefix] = {
                "name": ixs_dict[str(ix_id)]["name"]
            }
            self.IXPsCache = {
                "TS": int(time.time()),
                "Data": ixpfx_dict
            }

        if IXP_CACHE_FILE:
            with open(IXP_CACHE_FILE, "w") as outfile:
                json.dump(self.IXPsCache, outfile)

    def __del__(self):
        if not self.DontSaveOnDel:
            self.SaveCache()
