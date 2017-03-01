import unittest

from com.dtmilano.android.adb import adbclient
from com.dtmilano.android.adb.dumpsys import Dumpsys

SERIALNO = '.*'

class DumpsysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
       cls.device = adbclient.AdbClient(SERIALNO, ignoreversioncheck=False, timeout=60)

    def test_meminfo(self):
        dumpsys = Dumpsys(self.device, 'meminfo', 'com.android.systemui')
        self.assertGreater(dumpsys.total, 0)
        self.assertGreater(dumpsys.nativeHeap, 0)
        self.assertGreater(dumpsys.dalvikHeap, 0)
        self.assertGreaterEqual(dumpsys.views, 0)
        self.assertGreaterEqual(dumpsys.activities, 0)
        self.assertGreaterEqual(dumpsys.appContexts, 0)
        self.assertGreaterEqual(dumpsys.viewRootImpl, 0)


if __name__ == '__main__':
    unittest.main()
