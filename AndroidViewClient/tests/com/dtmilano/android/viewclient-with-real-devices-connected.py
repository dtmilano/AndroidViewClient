'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''

import sys
import os
import unittest

# PyDev sets PYTHONPATH, use it
for p in os.environ['PYTHONPATH'].split(':'):
    if not p in sys.path:
        sys.path.append(p)
try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import View, TextView, EditText, ViewClient



class ViewClientTest(unittest.TestCase):

    serialno1 = 'emulator-5554'
    device1 = None
    serialno2 = 'emulator-5556'
    device2 = None

    @classmethod
    def setUpClass(cls):
        '''
        Set ups the class.

        The preconditions to run this test is to have at least 2 emulators running:
           - emulator-5554
           - emulator-5556
        '''
        sys.argv = ['testViewClient_localPort_remotePort', serialno1]
        cls.device1, cls.serialno1 = ViewClient.connectToDeviceOrExit(timeout=30)

        sys.argv = ['testViewClient_localPort_remotePort', serialno2]
        cls.device2, cls.serialno2 = ViewClient.connectToDeviceOrExit(timeout=30)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testConnectToDeviceOrExit_none(self):
        sys.argv = [ 'VIEWCLIENT']
        device, serialno = ViewClient.connectToDeviceOrExit()
        self.assertNotEquals(None, device)
        self.assertNotEquals(None, serialno)

    def testConnectToDeviceOrExit_emulator_5556(self):
        sys.argv = [ 'VIEWCLIENT', 'emulator-5556']
        device, serialno = ViewClient.connectToDeviceOrExit()
        self.assertNotEquals(None, device)
        self.assertNotEquals(None, serialno)

#    @unittest.skip("until multiple devices could be connected")
#    def testViewClient_localPort_remotePort(self):
#        serialno = 'emulator-5554'
#        sys.argv = ['testViewClient_localPort_remotePort', serialno]
#        device, serialno = ViewClient.connectToDeviceOrExit(timeout=30)
#        localPort = 9005
#        remotePort = 9006
#        vc = ViewClient(device=device, serialno=serialno, localport=localPort, remoteport=remotePort, autodump=True)
#        self.assertTrue(vc.getRoot() != None)

    def testViewClient_oneDevice_TwoViewClients(self):
        localPort1 = 9005
        remotePort1 = 9006
        print "Conencting to", remotePort1
        vc1 = ViewClient(device=ViewClientTest.device1, serialno=ViewClientTest.serialno1,
                         localport=localPort1, remoteport=remotePort1, autodump=True)
        self.assertTrue(vc1.getRoot() != None)
        vc1.traverse()

        localPort2 = 9007
        remotePort2 = 9008
        print "Conencting to", remotePort2
        vc2 = ViewClient(device=ViewClientTest.device2, serialno=ViewClientTest.serialno2,
                         localport=localPort2, remoteport=remotePort2, autodump=True)
        self.assertTrue(vc2.getRoot() != None)
        vc2.traverse()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
