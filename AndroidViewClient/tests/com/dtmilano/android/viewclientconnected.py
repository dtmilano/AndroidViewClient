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
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import *

VERBOSE = False

# NOTE:
# Because there's no way of disconnect a MonkeyDevice and there's no
# either the alternative of connecting twice from the same script
# this is the only alternative
sys.argv = ['ViewClientConnectedTest', 'emulator-5554']
device, serialno = ViewClient.connectToDeviceOrExit(verbose=True)
       
class ViewClientConnectedTest(unittest.TestCase):

    def setUp(self):
        self.device = device
        self.serialno = serialno


    def tearDown(self):
        # WARNING:
        # There's no way of disconnect the device
        pass
    
    
    def testAutodumpVsDump(self):
        vc = ViewClient(self.device, self.serialno)
        ids = vc.getViewIds()
        views = vc.dump()
        self.assertEquals(len(ids), len(views))
        
    def testNewViewClientInstancesDontDuplicateTreeConnected(self):
        vc = {}
        n = {}
        m = {}
        d = {}
        
        for i in range(10):
            vc[i] = ViewClient(self.device, self.serialno)
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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
