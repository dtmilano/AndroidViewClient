from __future__ import absolute_import

import time
import unittest

from com.dtmilano.android.adb import adbclient
from com.dtmilano.android.adb.dumpsys import Dumpsys
from com.dtmilano.android.plot import Plot

SERIALNO = '.*'
SAMPLE_PROCESS_NAME = 'com.android.systemui'


class PlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.device = adbclient.AdbClient(SERIALNO, ignoreversioncheck=False, timeout=60)

    def setUp(self):
        super(PlotTests, self).setUp()
        self.plot = Plot()

    def test_plot_dumpsys_meminfo(self):
        for n in range(10):
            self.plot.append(Dumpsys(self.device, Dumpsys.MEMINFO, SAMPLE_PROCESS_NAME))
            time.sleep(1)
        self.plot.plot()

    def test_plot_dumpsys_meminfo_sampleapplication(self):
        self.device.shell("am force-stop com.dtmilano.android.sampleapplication")
        for n in range(10):
            self.device.startActivity("com.dtmilano.android.sampleapplication/.MainActivity")
            time.sleep(2)
            self.plot.append(Dumpsys(self.device, Dumpsys.MEMINFO, "com.dtmilano.android.sampleapplication"))
            self.device.press('BACK')
            time.sleep(0.5)
            self.device.press('BACK')
            time.sleep(0.5)
            self.device.press('HOME')
            time.sleep(0.5)
        self.plot.plot()


if __name__ == '__main__':
    unittest.main()
