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
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
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

"""A Python library to gather IP address details (ASN, prefix, resource holder, reverse DNS) using the 
RIPEStat API, with a basic cache to avoid flood of requests and to enhance performance."""

__version__ = "v0.3.0"

import os.path
import time
import json
import socket
import urllib2

try:
  import ipaddr	# http://code.google.com/p/ipaddr-py/ - pip install ipaddr
  ip_library = 'ipaddr'
except ImportError:
  import IPy			# https://github.com/autocracy/python-ipy/ - pip install ipy
  ip_library = 'IPy'

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
                                             'LINKLOCAL']

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

        PEERINGDB_API_ixpfx = "https://beta.peeringdb.com/api/ixpfx"
        PEERINGDB_API_ixlan = "https://beta.peeringdb.com/api/ixlan"
        PEERINGDB_API_ix = "https://beta.peeringdb.com/api/ix"

	def _Debug(self, s):
		if self.Debug:
			print("DEBUG - IPDetailsCache - %s" % s)

        def FetchIPInfo(self, IP):
                URL = "https://stat.ripe.net/data/prefix-overview/data.json?resource=%s" % IP

                return json.loads( urllib2.urlopen(URL).read() )

	# IPPrefixesCache[<ip prefix>]["TS"]
	# IPPrefixesCache[<ip prefix>]["ASN"]
	# IPPrefixesCache[<ip prefix>]["Holder"]

	# IPAddressesCache[<ip>]["TS"]
	# IPAddressesCache[<ip>]["ASN"]
	# IPAddressesCache[<ip>]["Holder"]
	# IPAddressesCache[<ip>]["Prefix"]
	# IPAddressesCache[<ip>]["HostName"]

	def GetIPInformation( self, in_IP ):
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

		if not IP in self.IPAddressObjects:
			self.IPAddressObjects[IP] = IPObj

		if not IPObj.is_globally_routable():
			Result["ASN"] = "unknown"
			return Result

		if IP in self.IPAddressesCache:
			if self.IPAddressesCache[IP]["TS"] >= int(time.time()) - self.MAX_CACHE:
                                for k in self.IPAddressesCache[IP].keys():
                                    Result[k] = self.IPAddressesCache[IP][k]
				self._Debug("IP address cache hit for %s" % IP)
                                return Result
			else:
				self._Debug("Expired IP address cache hit for %s" % IP)

		for IPPrefix in self.IPPrefixesCache:
			if self.IPPrefixesCache[IPPrefix]["TS"] >= int(time.time()) - self.MAX_CACHE:
				if not IPPrefix in self.IPPrefixObjects:
					self.IPPrefixObjects[IPPrefix] = NetWrapper(IPPrefix)

				if self.IPPrefixObjects[IPPrefix].contains(IPObj):
					Result["TS"] = self.IPPrefixesCache[IPPrefix]["TS"]
					Result["ASN"] = self.IPPrefixesCache[IPPrefix]["ASN"]
					Result["Holder"] = self.IPPrefixesCache[IPPrefix].get("Holder","")
					Result["Prefix"] = IPPrefix
					self._Debug("IP prefix cache hit for %s (prefix %s)" % ( IP, IPPrefix ) )
					break

		if Result["ASN"] == "":
			self._Debug("No cache hit for %s" % IP )

                        obj = self.FetchIPInfo(IP)

			if obj["status"] == "ok":
				Result["TS"] = int(time.time())

				if obj["data"]["asns"] != []:
					try:
						Result["ASN"] = str(obj["data"]["asns"][0]["asn"])
						Result["Holder"] = obj["data"]["asns"][0]["holder"]
						Result["Prefix"] = obj["data"]["resource"]

						self._Debug("Got data for %s: ASN %s, prefix %s" % ( IP, Result["ASN"], Result["Prefix"] ) )
					except:
						Result["ASN"] = "unknown"

						self._Debug("No data for %s" % IP )
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

                        if self.UseIXPsCache == 2 or ( self.UseIXPsCache == 1 and not Result["ASN"].isdigit() ):
                            self._Debug("Looking for IXP info")

                            Result["IsIXP"] = False

                            for IPPrefix in self.IXPsCache["Data"].keys():
                                if NetWrapper(IPPrefix).contains(IPObj):
                                    Result["IsIXP"] = True
                                    Result["IXPName"] = self.IXPsCache["Data"][IPPrefix]["name"]
                                    self._Debug("IXP found: prefix %s, name %s" % (IPPrefix, self.IXPsCache["Data"][IPPrefix]["name"]))
                                    break

		if not IP in self.IPAddressesCache:
			self.IPAddressesCache[IP] = {}
			self._Debug("Adding %s to addresses cache" % IP)

		self.IPAddressesCache[IP]["TS"] = Result["TS"]
		self.IPAddressesCache[IP]["ASN"] = Result["ASN"]
		self.IPAddressesCache[IP]["Holder"] = Result["Holder"]
		self.IPAddressesCache[IP]["Prefix"] = Result["Prefix"]
		self.IPAddressesCache[IP]["HostName"] = Result["HostName"]
                self.IPAddressesCache[IP]["IsIXP"] = Result["IsIXP"]
                self.IPAddressesCache[IP]["IXPName"] = Result["IXPName"]

		if Result["Prefix"] != "":
			IPPrefix = Result["Prefix"]

			if not IPPrefix in self.IPPrefixesCache:
				self.IPPrefixesCache[IPPrefix] = {}
				self._Debug("Adding %s to prefixes cache" % IPPrefix)

			self.IPPrefixesCache[IPPrefix]["TS"] = Result["TS"]
			self.IPPrefixesCache[IPPrefix]["ASN"] = Result["ASN"]
			self.IPPrefixesCache[IPPrefix]["Holder"] = Result["Holder"]


		return Result

	def SaveCache( self ):
		# Save IP addresses cache
		self._Debug("Saving IP addresses cache to %s" % self.IP_ADDRESSES_CACHE_FILE)
		with open( self.IP_ADDRESSES_CACHE_FILE, "w" ) as outfile:
			json.dump( self.IPAddressesCache, outfile )

		# Save IP prefixes cache
		self._Debug("Saving IP prefixes cache to %s" % self.IP_PREFIXES_CACHE_FILE)
		with open( self.IP_PREFIXES_CACHE_FILE, "w" ) as outfile:
			json.dump( self.IPPrefixesCache, outfile )

        def LoadCache( self ):
		# Load IP addresses cache
		if self._file_not_zero(self.IP_ADDRESSES_CACHE_FILE):
			self._Debug("Loading IP addresses cache from %s" % self.IP_ADDRESSES_CACHE_FILE)
			json_data = open( self.IP_ADDRESSES_CACHE_FILE )
			self.IPAddressesCache = json.load( json_data )
			json_data.close()
		else:
			self._Debug("No IP addresses cache file found: %s" % self.IP_ADDRESSES_CACHE_FILE)

		# Load IP prefixes cache
		if self._file_not_zero(self.IP_PREFIXES_CACHE_FILE):
			self._Debug("Loading IP prefixes cache from %s" % self.IP_PREFIXES_CACHE_FILE)

			json_data = open( self.IP_PREFIXES_CACHE_FILE )
			self.IPPrefixesCache = json.load( json_data )
			json_data.close()
		else:
			self._Debug("No IP prefixes cache file found: %s" % self.IP_PREFIXES_CACHE_FILE)

	@staticmethod
	def _file_not_zero(path):
		return True if os.path.exists(path) and os.path.getsize(path) > 0 else False

	def __init__(self, IP_ADDRESSES_CACHE_FILE="ip_addr.cache",
                     IP_PREFIXES_CACHE_FILE="ip_pref.cache", MAX_CACHE=604800,
                     dont_save_on_exit=False, Debug=False):
		self.IPAddressesCache = {}
		self.IPPrefixesCache = {}
		self.IPAddressObjects = {}
		self.IPPrefixObjects = {}

		self.IP_ADDRESSES_CACHE_FILE = IP_ADDRESSES_CACHE_FILE
		self.IP_PREFIXES_CACHE_FILE = IP_PREFIXES_CACHE_FILE
		self.MAX_CACHE = MAX_CACHE

                self.IXPsCache = {}
                self.UseIXPsCache = 0   # 0 = do not use
                                        # 1 = only when no ASN found
                                        # 2 = always

                self.DontSaveOnExit = dont_save_on_exit
		self.Debug = Debug

                self.LoadCache()

		# Test write access to IP addresses cache file
		self._Debug("Testing write permissions on IP addresses cache file")
		with open( self.IP_ADDRESSES_CACHE_FILE, "a" ) as outfile:
			outfile.close()
		self._Debug("Write permissions on IP addresses cache file OK")

		# Test write access to IP prefixes cache file
		self._Debug("Testing write permissions on IP prefixes cache file")
		with open( self.IP_PREFIXES_CACHE_FILE, "a" ) as outfile:
			outfile.close()
		self._Debug("Write permissions on IP prefixes cache file OK")

        def LoadIXPsCache(self, cache_file):
            if self._file_not_zero(cache_file):
                self._Debug("Loading IXPs cache from %s" % cache_file)
                json_data = open( cache_file )
                self.IXPsCache = json.load( json_data )
                json_data.close()
            else:
                self._Debug("No IXPs cache file found: %s" % cache_file)

        def FetchIXPsInfo(self):
            self._Debug("Fetching IXPs info from PeeringDB API...")

            ixpfxs = json.loads( urllib2.urlopen(IPDetailsCache.PEERINGDB_API_ixpfx).read() )
            ixlans = json.loads( urllib2.urlopen(IPDetailsCache.PEERINGDB_API_ixlan).read() )
            ixs = json.loads( urllib2.urlopen(IPDetailsCache.PEERINGDB_API_ix).read() )

            self._Debug("IXPs info fetched")

            return (ixpfxs, ixlans, ixs)

        def UseIXPs(self, WhenUse=1, IXP_CACHE_FILE="ixps.cache", MAX_CACHE=604800):

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

            ixs_dict = {}
            for ix in ixs["data"]:
                ixs_dict[str(ix["id"])] = { "name": ix["name"] }

            ixlans_dict = {}
            for ixlan in ixlans["data"]:
                ixlans_dict[str(ixlan["id"])] = { "ix_id": ixlan["ix_id"] }

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

            with open( IXP_CACHE_FILE, "w" ) as outfile:
                json.dump( self.IXPsCache, outfile )

	def __del__( self ):
            if not self.DontSaveOnExit:
		self.SaveCache()
