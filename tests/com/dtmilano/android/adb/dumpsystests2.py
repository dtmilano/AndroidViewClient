from __future__ import absolute_import

import unittest

from com.dtmilano.android.adb import adbclient
from com.dtmilano.android.adb.dumpsys import Dumpsys

SAMPLE_PROCESS_NAME = 'com.android.systemui'

SERIALNO = '.*'


class DumpsysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.device = adbclient.AdbClient(SERIALNO, ignoreversioncheck=False, timeout=60)

    def setUp(self):
        super(DumpsysTests, self).setUp()
        self.dumpsysMeminfo = Dumpsys.meminfo(self.device, SAMPLE_PROCESS_NAME)
        self.dumpsysGfxinfo = Dumpsys.gfxinfo(self.device, SAMPLE_PROCESS_NAME, Dumpsys.FRAMESTATS)

    def __check_meminfo_values(self, dumpsys):
        self.assertGreater(dumpsys.total, 0)
        self.assertGreater(dumpsys.nativeHeap, 0)
        self.assertGreater(dumpsys.dalvikHeap, 0)
        self.assertGreaterEqual(dumpsys.views, 0)
        self.assertGreaterEqual(dumpsys.activities, 0)
        self.assertGreaterEqual(dumpsys.appContexts, 0)
        self.assertGreaterEqual(dumpsys.viewRootImpl, 0)

    def test_meminfo_1(self):
        self.__check_meminfo_values(self.dumpsysMeminfo)

    def test_meminfo_2(self):
        self.__check_meminfo_values(self.dumpsysMeminfo)

    def test_listSubCommands(self):
        self.assertIsNotNone(Dumpsys.listSubCommands(self.device))

    def test_get_total(self):
        self.assertGreater(self.dumpsysMeminfo.get(Dumpsys.TOTAL), 0)

    def test_get_activities(self):
        self.assertGreaterEqual(self.dumpsysMeminfo.get(Dumpsys.ACTIVITIES), 0)

    def test_gfxinfo_1(self):
        self.assertGreater(len(self.dumpsysGfxinfo.gfxProfileData), 0)

    def test_gfxinfo_2(self):
        self.assertGreater(len(self.dumpsysGfxinfo.gfxProfileDataDiff), 0)


if __name__ == '__main__':
    unittest.main()
