#! /usr/bin/env python2.7

'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''

import os
import sys
import unittest

# PyDev sets PYTHONPATH, use it
if 'PYTHONPATH' in os.environ:
    for p in os.environ['PYTHONPATH'].split(':'):
        if not p in sys.path:
            sys.path.append(p)
try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient


class ViewClientTest(unittest.TestCase):
    CONNECT_EMULATORS = False
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
        if ViewClientTest.CONNECT_EMULATORS:
            sys.argv = ['testViewClient_localPort_remotePort', cls.serialno1]
            cls.device1, cls.serialno1 = ViewClient.connectToDeviceOrExit(timeout=30)

            sys.argv = ['testViewClient_localPort_remotePort', cls.serialno2]
            cls.device2, cls.serialno2 = ViewClient.connectToDeviceOrExit(timeout=30)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testConnectToDeviceOrExit_none(self):
        sys.argv = ['VIEWCLIENT']
        device, serialno = ViewClient.connectToDeviceOrExit()
        self.assertNotEquals(None, device)
        self.assertNotEquals(None, serialno)

    def testConnectToDeviceOrExit_emulator_5556(self):
        if ViewClientTest.CONNECT_EMULATORS:
            sys.argv = ['VIEWCLIENT', 'emulator-5556']
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
        if ViewClientTest.CONNECT_EMULATORS:
            localPort1 = 9005
            remotePort1 = 9006
            print "Conencting to", remotePort1
            vc1 = ViewClient(device=ViewClientTest.device1, serialno=ViewClientTest.serialno1,
                             localport=localPort1, remoteport=remotePort1, autodump=True)
            self.assertTrue(vc1.getRoot() is not None)
            vc1.traverse()

            localPort2 = 9007
            remotePort2 = 9008
            print "Conencting to", remotePort2
            vc2 = ViewClient(device=ViewClientTest.device2, serialno=ViewClientTest.serialno2,
                             localport=localPort2, remoteport=remotePort2, autodump=True)
            self.assertTrue(vc2.getRoot() is not None)
            vc2.traverse()

    def testViewClient_device_disconnected(self):
        # Script gets stuck on ViewClient(device, serial) #243
        # This cannot run on emulator because we have to disconnect the USB or network
        d, s = ViewClient.connectToDeviceOrExit()
        self.assertIsNotNone(d)
        self.assertIsNotNone(s)
        raw_input('\n** Disconnect the device now and press <ENTER>')
        device = ViewClient(d, s)
        self.assertIsNotNone(device)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
