

import os
import unittest

import sys

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.adb import adbclient
from com.dtmilano.android.adb.dumpsys import Dumpsys

SAMPLE_PROCESS_NAMES = ['com.android.systemui', 'system:ui']

SERIALNO = '.*'


class DumpsysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.device = adbclient.AdbClient(SERIALNO, ignoreversioncheck=False, timeout=60)
        cls.sample_process_name = None
        for line in cls.device.shell('ps').splitlines():
            process = line.split()[-1]
            if process in SAMPLE_PROCESS_NAMES:
                cls.sample_process_name = process
                break
        else:
            raise RuntimeError('Cannot find suitable process from {}'.format(SAMPLE_PROCESS_NAMES))

    def setUp(self):
        super(DumpsysTests, self).setUp()
        self.dumpsysMeminfo = Dumpsys.meminfo(self.device, self.sample_process_name)
        self.dumpsysGfxinfo = Dumpsys.gfxinfo(self.device, self.sample_process_name, Dumpsys.FRAMESTATS)

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

    # def test_gfxinfo_2(self):
    #     self.assertGreater(len(self.dumpsysGfxinfo.gfxProfileDataDiff), 0)

    def test_parseGfxinfoFramestats(self):
        out = '''\
Something
Something
Something
Something

---PROFILEDATA---
Flags,IntendedVsync,Vsync,OldestInputEvent,NewestInputEvent,HandleInputStart,AnimationStart,PerformTraversalsStart,DrawStart,SyncQueued,SyncStart,IssueDrawCommandsStart,SwapBuffers,FrameCompleted,
0,1538750837982,1539034171304,9223372036854775807,0,1539047401632,1539047424965,1539047516299,1539047541049,1539047873632,1539048042382,1539048073215,1539085917465,1539087148465,
0,1808866542439,1808899875771,9223372036854775807,0,1808909338401,1808909869234,1808911205068,1808911288234,1808911729484,1808911906651,1808912287651,1808920894568,1808922659568,
---PROFILEDATA---

Something
Something
Something
Something
Something

---PROFILEDATA---
Flags,IntendedVsync,Vsync,OldestInputEvent,NewestInputEvent,HandleInputStart,AnimationStart,PerformTraversalsStart,DrawStart,SyncQueued,SyncStart,IssueDrawCommandsStart,SwapBuffers,FrameCompleted,
1,1538295812863,1538495812855,9223372036854775807,0,1538506027632,1538506079049,1538506994882,1538517724382,1538550285632,1538550403216,1538550458966,1538559445132,1538561759382,
---PROFILEDATA---




        '''
        dumpsys = Dumpsys(None, None)
        dumpsys.parseGfxinfoFramestats(out)


if __name__ == '__main__':
    unittest.main()
