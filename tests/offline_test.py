import json
import mock
from time import time
import unittest


from base_class import TestIPDetailsCacheBase
from pierky.ipdetailscache import IPDetailsCache


class TestIPDetailsCache(TestIPDetailsCacheBase):
    LIVE = False

    def setup_ixps(self, whenuse):

        def fetch_ixps_info(self):
            return None

        self.mock_fetch_ixps = mock.patch.object(
            IPDetailsCache,
            "FetchIXPsInfo",
            autospec=True
        ).start()
        self.mock_fetch_ixps.side_effect = fetch_ixps_info

        def load_ixps(self, cache_file):
            with open("tests/data/ixps.json", "r") as f:
                data = json.loads(f.read())
                data["TS"] = int(time())
                self.IXPsCache = data

        self.mock_load_ixps = mock.patch.object(
            IPDetailsCache,
            "LoadIXPsCache",
            autospec=True
        ).start()
        self.mock_load_ixps.side_effect = load_ixps

        self.cache.UseIXPs(
            WhenUse=whenuse,
            IXP_CACHE_FILE=None
        )

    def test_ixps_whenuse1_notannounced(self):
        """IXPs info, WhenUse = 1, IP not announced"""
        self.setup_ixps(1)
        ip = self.cache.GetIPInformation(self.IXPS_NOT_ANNOUNCED_IP)

        self.assertEquals(ip["ASN"], "not announced")
        self.verify_fetchipinfo_calls(1)
        self.assertEquals(ip["IsIXP"], True)
        self.assertEquals(ip["IXPName"], self.IXPS_NOT_ANNOUNCED_IP_IXPNAME)

        ip = self.cache.GetIPInformation(self.IXPS_NOT_ANNOUNCED_IP)
        self.verify_fetchipinfo_calls(1)

    def test_ixps_whenuse1_announced(self):
        """IXPs info, WhenUse = 1, announced IP"""
        self.setup_ixps(1)
        ip = self.cache.GetIPInformation(self.IXPS_ANNOUNCED_IP)

        self.assertEquals(ip["ASN"], self.IXPS_ANNOUNCED_IP_ASN)
        self.verify_fetchipinfo_calls(1)
        self.assertIsNone(ip["IsIXP"])

    def test_ixps_whenuse2_notannounced(self):
        """IXPs info, WhenUse = 2, IP not announced"""
        self.setup_ixps(2)
        ip = self.cache.GetIPInformation(self.IXPS_NOT_ANNOUNCED_IP)

        self.assertEquals(ip["ASN"], "not announced")
        self.verify_fetchipinfo_calls(1)
        self.assertEquals(ip["IsIXP"], True)
        self.assertEquals(ip["IXPName"], self.IXPS_NOT_ANNOUNCED_IP_IXPNAME)

        ip = self.cache.GetIPInformation(self.IXPS_NOT_ANNOUNCED_IP)
        self.verify_fetchipinfo_calls(1)
    
    def test_ixps_whenuse2_announced(self):
        """IXPs info, WhenUse = 2, announced IP"""
        self.setup_ixps(2)
        ip = self.cache.GetIPInformation(self.IXPS_ANNOUNCED_IP)

        self.assertEquals(ip["ASN"], self.IXPS_ANNOUNCED_IP_ASN)
        self.verify_fetchipinfo_calls(1)
        self.assertEquals(ip["IsIXP"], True)
        self.assertEquals(ip["IXPName"], self.IXPS_ANNOUNCED_IP_IXPNAME)

    def test_ixps_whenuse2_announced_not_ixp(self):
        """IXPs info, WhenUse = 2, announced IP, not an IXP"""
        self.setup_ixps(2)
        ip = self.cache.GetIPInformation(self.IP)

        self.assertEquals(ip["ASN"], self.ASN)
        self.assertEquals(ip["Prefix"], self.PREFIX)
        self.assertEquals(ip["Holder"], self.HOLDER)
        self.assertEquals(ip["IsIXP"], False)
        self.verify_fetchipinfo_calls(1)

