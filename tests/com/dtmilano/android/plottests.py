from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import time
import unittest

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

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

    def __plot_dumpsys_meminfo(self, pkg, activity, method=None):
        self.device.shell("am force-stop %s" % pkg)
        for n in range(20):
            if n % 5 == 0:
                self.device.shell(
                    "run-as %s pgrep -L 10 %s" % (pkg, pkg))
            self.device.startActivity("%s/%s" % (pkg, activity))
            time.sleep(2)
            if method:
                method()
            self.plot.append(Dumpsys(self.device, Dumpsys.MEMINFO, pkg))
            self.device.press('BACK')
            time.sleep(0.5)
            self.device.press('BACK')
            time.sleep(0.5)
            self.device.press('HOME')
            time.sleep(0.5)
        self.plot.plot()

    def test_plot_dumpsys_meminfo_sampleapplication_mainactivity(self):
        self.__plot_dumpsys_meminfo("com.dtmilano.android.sampleapplication", ".MainActivity")

    def test_plot_dumpsys_gfxinfo_sampleapplication(self):
        self.__plot_dumpsys_gfxinfo("com.dtmilano.android.sampleapplication")

    def test_plot_dumpsys_gfxinfo_systemui(self):
        self.__plot_dumpsys_gfxinfo("com.android.systemui")

    def test_plot_dumpsys_gfxinfo_perftesting(self):
        self.__plot_dumpsys_gfxinfo("com.google.android.perftesting")

    def test_plot_dumpsys_meminfo_sampleapplication_leakingactivity(self):
        def click_button():
            # we have to press the button to start the AsyncTask
            self.device.press("ENTER")
        self.__plot_dumpsys_meminfo("com.dtmilano.android.sampleapplication", ".LeakingActivity", click_button)

    def __plot_dumpsys_gfxinfo(self, pkg):
        print('plot dumpsys gfxinfo: {}'.format(pkg), file=sys.stderr)
        dumpsys = Dumpsys(self.device, Dumpsys.GFXINFO, pkg, Dumpsys.FRAMESTATS)
        self.plot.append(dumpsys) \
            .plot(_type=Dumpsys.FRAMESTATS)


if __name__ == '__main__':
    unittest.main()
