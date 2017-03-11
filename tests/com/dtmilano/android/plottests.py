from __future__ import absolute_import

import time
import unittest

from com.dtmilano.android.adb import adbclient
from com.dtmilano.android.adb.dumpsys import Dumpsys
from com.dtmilano.android.plot import Plot

SERIALNO = '.*'


class PlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.device = adbclient.AdbClient(SERIALNO, ignoreversioncheck=False, timeout=60)

    def setUp(self):
        super(PlotTests, self).setUp()
        self.plot = Plot()

    def test_plot_dumpsys_meminfo(self):
        for n in range(100):
            self.plot.append(Dumpsys(self.device, Dumpsys.MEMINFO, 'com.android.systemui'))
            time.sleep(1)
        self.plot.plot()


if __name__ == '__main__':
    unittest.main()
