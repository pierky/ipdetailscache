import json
import mock
from time import time
import unittest


from base_class import TestIPDetailsCacheBase
from pierky.ipdetailscache import IPDetailsCache, \
                                  IPDetailsCacheIXPInformationError


class TestIXPInfoFail(TestIPDetailsCacheBase):
    LIVE = False

    def setup_ixps(self, whenuse):

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

    def mock_with_return_value(self, retval):
        self.mock_fetch_ixps = mock.patch.object(
            IPDetailsCache,
            "FetchIXPsInfo",
            autospec=True
        ).start()
        self.mock_fetch_ixps.return_value = retval

    def simulate_failure(self, retval, expmsg=None):
        self.mock_with_return_value(retval)

        if expmsg:
            with self.assertRaisesRegexp(IPDetailsCacheIXPInformationError,
                                        expmsg):
                self.cache.UseIXPs(IXP_CACHE_FILE=None)
        else:
            try:
                self.cache.UseIXPs(IXP_CACHE_FILE=None)
            except Exception as e:
                raise self.failureException(e)

    def test_ixps_failure1(self):
        """IXPs info failure, missing key: data"""

        self.simulate_failure(({}, {}, {}), "ixpfxs - missing key: data")

    def test_ixps_failure2(self):
        """IXPs info failure, data is empty"""

        self.simulate_failure(({"data": []}, {}, {}), "ixpfxs - data is empty")

    def test_ixps_failure3(self):
        """IXPs info failure, bad data"""

        self.simulate_failure((
            {"data": "string"},
            {},
            {}
        ), "ixpfxs - data is not a list")

    def test_ixps_failure4(self):
        """IXPs info failure, missing elements attribute, prefix"""

        self.simulate_failure((
            {"data": [{}]},
            {"data": [{}]},
            {"data": [{}]}
        ), "ixpfxs - missing key from elements: prefix")

    def test_ixps_failure5(self):
        """IXPs info failure, missing elements attribute, ixlan_id"""

        self.simulate_failure((
            {"data": [
                {"prefix": ""}]
            },
            {"data": [{}]},
            {"data": [{}]}
        ), "ixpfxs - missing key from elements: ixlan_id")

    def test_ixps_failure_ok(self):
        """IXPs info failure, everything ok"""

        self.simulate_failure((
            {"data": [
                {"prefix": "", "ixlan_id": ""}]
            },
            {"data": [
                {"id": "", "ix_id": ""}]
            },
            {"data": [
                {"id": "", "name": ""}]
            }
        ))
