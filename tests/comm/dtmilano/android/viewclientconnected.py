'''
Created on 2012-10-25

@author: diego
'''

import sys
import os
import unittest


# PyDev sets PYTHONPATH, use it
try:
    for p in os.environ['PYTHONPATH'].split(':'):
        if not p in sys.path:
            sys.path.append(p)
except:
    pass

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import *
from mocks import MockDevice

VERBOSE = True

# NOTE:
# Because there's no way of disconnect a MonkeyDevice and there's no
# either the alternative of connecting twice from the same script
# this is the only alternative
SERIALNO = '1.*' # 'emulator-5554'
#sys.argv = ['ViewClientConnectedTest', SERIALNO]
#device, serialno = ViewClient.connectToDeviceOrExit(verbose=VERBOSE, serialno=SERIALNO)

class ViewClientConnectedTest(unittest.TestCase):

    def setUp(self):
        device, serialno = ViewClient.connectToDeviceOrExit(serialno=SERIALNO)
        self.device = device
        self.serialno = serialno


    def tearDown(self):
        # WARNING:
        # There's no way of disconnect the device
        pass

    @unittest.skip("icannot connect adb to mock device")
    def testInit_adbNone(self):
        device = MockDevice()
        vc = ViewClient(device, serialno=device.serialno, adb=None, autodump=False)
        self.assertNotEqual(None, vc)

    def testAutodumpVsDump(self):
        vc = ViewClient(self.device, self.serialno, forceviewserveruse=True)
        ids = vc.getViewIds()
        views = vc.dump()
        self.assertEquals(len(ids), len(views))

    def testNewViewClientInstancesDontDuplicateTreeConnected(self):
        vc = {}
        n = {}
        m = {}
        d = {}

        for i in range(10):
            vc[i] = ViewClient(self.device, self.serialno, forceviewserveruse=True)
            n[i] = len(vc[i].getViewIds())
            m[i] = len(vc[i].dump())
            d[i] = len(vc[i].getViewIds())
            if VERBOSE:
                print "Pass %d: Found %d views and %d after dump with %d view Ids" % \
                    (i, n[i], m[i], d[i])

        for i in range(1, 10):
            self.assertEquals(n[0], n[i])
            self.assertEquals(n[0], m[i])
            self.assertEquals(n[0], d[i])
            
    def testViewClientBackendsConsistency(self):
        kwargs1 = {'verbose': True, 'ignoresecuredevice': False, 'ignoreversioncheck': False}
        
        kwargs2 = {'forceviewserveruse': False, 'startviewserver': True, 'autodump': False, 'ignoreuiautomatorkilled': True}
        device1, serialno1 = ViewClient.connectToDeviceOrExit(serialno=SERIALNO, **kwargs1)
        vc1 = ViewClient(device1, serialno1, **kwargs2)
        self.assertTrue(vc1.useUiAutomator)

        kwargs2['forceviewserveruse'] = True
        device2, serialno2 = ViewClient.connectToDeviceOrExit(serialno=SERIALNO, **kwargs1)
        vc2 = ViewClient(device1, serialno1, **kwargs2)
        self.assertFalse(vc2.useUiAutomator)

        # UiAutomator
        dump1 = vc1.dump(-1)
        # ViewServer
        dump2 = vc2.dump(-1)

        # Can't do this, v2 usually has much more views than v1
        #self.assertEqual(len(dump1), len(dump2), "Different number of views (%d != %d)" % (len(dump1), len(dump2)))
        
        found = False
        for v2 in dump2:
            for v1 in dump1:
                # At least, let's verify that all unique Ids from dump2 (smaller) are in dump1 (bigger)
                if v2.getUniqueId() == v1.getUniqueId():
                    found = True
                    break
        self.assertTrue(found) 

        missing = ''
        # The smallest
        for v2 in dump2:
            coords = v2.getCoords()
            found = False
            for v1 in dump1:
                msg = "Comparing %s{%s} and %s{%s}" % (v1.getClass(), v1.getId(), v2.getClass(), v2.getId())
                if coords == v1.getCoords():
                    found = True
                    break
            if not found:
                missing += "Couldn't find view with coords=%s in dump1\n" % (str(v2.getCoords()))
        self.assertEqual('', missing, missing)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
