import unittest

from com.dtmilano.android.adb import adbclient
from com.dtmilano.android.adb.dumpsys import Dumpsys

SERIALNO = '192.168.2.158:5555'

class DumpsysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
       cls.device = adbclient.AdbClient(SERIALNO, ignoreversioncheck=False, timeout=60)

    def test_meminfo(self):
        dumpsys = Dumpsys(self.device, 'meminfo', 'com.android.systemui')
        self.assertGreater(dumpsys.total, 0)


if __name__ == '__main__':
    unittest.main()
