import json
import mock
import unittest


from pierky.ipdetailscache import IPDetailsCache


class TestIPDetailsCacheBase(unittest.TestCase):
    LIVE = False

    IP = '193.0.6.1'
    ASN = '3333'
    HOLDER = 'RIPE-NCC-AS Reseaux IP Europeens Network Coordination Centre (RIPE NCC),NL'
    SAME_PREFIX_IP = '193.0.6.2'
    PREFIX = '193.0.0.0/21'
    SAME_AS_DIFFERENT_PREFIX_IP = '193.0.22.1'
    NOT_ANNOUNCED_IP = '80.81.192.1'
    IXPS_NOT_ANNOUNCED_IP = '80.81.203.4'
    IXPS_NOT_ANNOUNCED_IP_IXPNAME = 'DE-CIX Hamburg'
    IXPS_ANNOUNCED_IP = '80.249.208.1'
    IXPS_ANNOUNCED_IP_ASN = '1200'
    IXPS_ANNOUNCED_IP_IXPNAME = 'AMS-IX'
    MOCK_RESULTS = {
        IP: {"status": "ok", "server_id": "stat-app2", "cached": False, "status_code": 200, "time": "2015-10-12T15:30:00.113317", "messages": [["warning", "Given resource is not announced but result has been aligned to first-level less-specific (193.0.0.0/21)."]], "version": "1.3", "data_call_status": "supported - connecting to ursa", "see_also": [], "process_time": 561, "query_id": "196d2754-70f6-11e5-b8ba-782bcb346712", "data": {"query_time": "2015-10-12T08:00:00", "is_less_specific": True, "resource": "193.0.0.0/21", "actual_num_related": 0, "num_filtered_out": 0, "asns": [{"holder": "RIPE-NCC-AS Reseaux IP Europeens Network Coordination Centre (RIPE NCC),NL", "asn": 3333}], "announced": True, "related_prefixes": [], "type": "prefix", "block": {"resource": "193.0.0.0/8", "name": "IANA IPv4 Address Space Registry", "desc": "RIPE NCC (Status: ALLOCATED)"}}},
        SAME_AS_DIFFERENT_PREFIX_IP: {"status": "ok", "server_id": "stat-app2", "cached": False, "status_code": 200, "time": "2015-10-12T15:32:25.778643", "messages": [["warning", "Given resource is not announced but result has been aligned to first-level less-specific (193.0.22.0/23)."]], "version": "1.3", "data_call_status": "supported - connecting to ursa", "see_also": [], "process_time": 818, "query_id": "7018b6cc-70f6-11e5-8bf8-782bcb346712", "data": {"query_time": "2015-10-12T08:00:00", "is_less_specific": True, "resource": "193.0.22.0/23", "actual_num_related": 0, "num_filtered_out": 0, "asns": [{"holder": "RIPE-NCC-AS Reseaux IP Europeens Network Coordination Centre (RIPE NCC),NL", "asn": 3333}], "announced": True, "related_prefixes": [], "type": "prefix", "block": {"resource": "193.0.0.0/8", "name": "IANA IPv4 Address Space Registry", "desc": "RIPE NCC (Status: ALLOCATED)"}}},
        NOT_ANNOUNCED_IP: {"status": "ok", "server_id": "stat-app2", "cached": False, "status_code": 200, "time": "2015-10-12T15:33:58.911309", "messages": [["info", "2 routes were filtered due to low visibility (min peers:3)."]], "version": "1.3", "data_call_status": "supported - connecting to ursa", "see_also": [], "process_time": 462, "query_id": "a7d1daee-70f6-11e5-aaec-782bcb346712", "data": {"query_time": "2015-10-12T08:00:00", "is_less_specific": False, "resource": "80.81.192.1", "actual_num_related": 0, "num_filtered_out": 2, "asns": [], "announced": False, "related_prefixes": [], "type": "prefix", "block": {"resource": "80.0.0.0/8", "name": "IANA IPv4 Address Space Registry", "desc": "RIPE NCC (Status: ALLOCATED)"}}},
        IXPS_NOT_ANNOUNCED_IP: {'messages': [['info', '1 routes were filtered due to low visibility (min peers:3).']], 'version': '1.3', 'cached': False, 'see_also': [], 'build_version': '2016.1.24.32', 'time': '2016-01-25T09:39:57.495147', 'status_code': 200, 'process_time': 222, 'status': 'ok', 'data': {'announced': False, 'actual_num_related': 0, 'num_filtered_out': 1, 'type': 'prefix', 'resource': '80.81.203.4', 'is_less_specific': False, 'block': {'name': 'IANA IPv4 Address Space Registry', 'resource': '80.0.0.0/8', 'desc': 'RIPE NCC (Status: ALLOCATED)'}, 'related_prefixes': [], 'query_time': '2016-01-25T00:00:00', 'asns': []}, 'server_id': 'stat-app2', 'data_call_status': 'supported - connecting to ursa', 'query_id': '98776cdc-c347-11e5-b539-782bcb346712'}, 
        IXPS_ANNOUNCED_IP: {'messages': [['info', '2 routes were filtered due to low visibility (min peers:3).'], ['warning', 'Given resource is not announced but result has been aligned to first-level less-specific (80.249.208.0/21).']], 'version': '1.3', 'cached': False, 'see_also': [], 'build_version': '2016.1.24.32', 'time': '2016-01-25T09:41:16.190176', 'status_code': 200, 'process_time': 293, 'status': 'ok', 'data': {'announced': True, 'actual_num_related': 0, 'num_filtered_out': 2, 'type': 'prefix', 'resource': '80.249.208.0/21', 'is_less_specific': True, 'block': {'name': 'IANA IPv4 Address Space Registry', 'resource': '80.0.0.0/8', 'desc': 'RIPE NCC (Status: ALLOCATED)'}, 'related_prefixes': [], 'query_time': '2016-01-25T00:00:00', 'asns': [{'holder': 'AMS-IX1 Amsterdam Internet Exchange B.V.,NL', 'asn': 1200}]}, 'server_id': 'stat-app5', 'data_call_status': 'supported - connecting to ursa', 'query_id': 'c75468de-c347-11e5-812f-c81f66be54ce'}
    }

    def setUp(self):
        self.cache = IPDetailsCache(
            IP_ADDRESSES_CACHE_FILE=None,
            IP_PREFIXES_CACHE_FILE=None
        )

        if self.LIVE:
            self.cache.FetchIPInfo = mock.Mock(wraps=self.cache.FetchIPInfo)
        else:
            def fetchipinfo(self, ip):
                return TestIPDetailsCacheBase.MOCK_RESULTS[ip]

            self.mock_fetchipinfo = mock.patch.object(
                IPDetailsCache,
                "FetchIPInfo",
                autospec=True
            ).start()
            self.mock_fetchipinfo.side_effect = fetchipinfo

    def tearDown(self):
        mock.patch.stopall()

    def shortDescription(self):
        return self._testMethodDoc.format(" (LIVE)" if self.LIVE else "")

    def verify_fetchipinfo_calls(self, val):
        if self.LIVE:
            self.assertEquals(self.cache.FetchIPInfo.call_count, val)
        else:
            self.assertEquals(self.mock_fetchipinfo.call_count, val)

class TestIPDetailsCacheBaseTests(TestIPDetailsCacheBase):

    LIVE = False

    def test_ipv4_loopback(self):
        """IPv4, loopback address{}"""
        ip = self.cache.GetIPInformation("127.0.0.1")

        self.assertEquals(ip["ASN"], "unknown")
        self.verify_fetchipinfo_calls(0)

    def test_loopback6(self):
        """IPv6, loopback address{}"""
        ip = self.cache.GetIPInformation("::1")

        self.assertEquals(ip["ASN"], "unknown")
        self.verify_fetchipinfo_calls(0)

    def test_nocache(self):
        """No cache{}"""
        ip = self.cache.GetIPInformation(self.IP)

        self.assertEquals(ip["ASN"], self.ASN)
        self.assertEquals(ip["Prefix"], self.PREFIX)
        self.assertEquals(ip["Holder"], self.HOLDER)
        self.verify_fetchipinfo_calls(1)

    def test_fakecache_sameip(self):
        """Fake cache, same IP{}"""
        ip = self.cache.GetIPInformation(self.IP)
        ip = self.cache.GetIPInformation(self.IP)

        self.assertEquals(ip["ASN"], self.ASN)
        self.verify_fetchipinfo_calls(1)

    def test_fakecache_sameprefix(self):
        """Fake cache, same prefix{}"""
        ip1 = self.cache.GetIPInformation(self.IP)
        ip2 = self.cache.GetIPInformation(self.SAME_PREFIX_IP)

        self.assertEquals(ip1["ASN"], self.ASN)
        self.assertEquals(ip2["ASN"], ip1["ASN"])
        self.verify_fetchipinfo_calls(1)

    def test_fakecache_diffprefix(self):
        """Fake cache, same AS, different prefix{}"""
        ip1 = self.cache.GetIPInformation(self.IP)
        ip2 = self.cache.GetIPInformation(self.SAME_AS_DIFFERENT_PREFIX_IP)

        self.assertEquals(ip1["ASN"], self.ASN)
        self.assertEquals(ip2["ASN"], ip1["ASN"])
        self.verify_fetchipinfo_calls(2)

    def test_fakecache_notannounced(self):
        """Fake cache, IP not announced{}"""
        ip = self.cache.GetIPInformation(self.NOT_ANNOUNCED_IP)

        self.assertEquals(ip["ASN"], "not announced")
        self.verify_fetchipinfo_calls(1)

        ip = self.cache.GetIPInformation(self.NOT_ANNOUNCED_IP)
        self.verify_fetchipinfo_calls(1)

    def test_expiredentries(self):
        """Fake cache, expired entries{}"""
        ip = self.cache.GetIPInformation(self.IP)

        for k in self.cache.IPAddressesCache.keys():
            self.cache.IPAddressesCache[k]["TS"] = 0

        for k in self.cache.IPPrefixesCache.keys():
            self.cache.IPPrefixesCache[k]["TS"] = 0

        ip = self.cache.GetIPInformation(self.IP)

        self.assertEquals(ip["ASN"], self.ASN)
        self.verify_fetchipinfo_calls(2)

