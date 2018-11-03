#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''
import unittest
import sys
import os


try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from comm.dtmilano.android.adb.adbclienttests import AdbClientTest
from comm.dtmilano.android.viewclienttests import ViewTest, ViewClientTest


if __name__ == "__main__":
    adbClientTestsSuite = unittest.TestLoader().loadTestsFromTestCase(AdbClientTest)
    viewTestsSuite = unittest.TestLoader().loadTestsFromTestCase(ViewTest)
    viewClientTestsSuite = unittest.TestLoader().loadTestsFromTestCase(ViewClientTest)
    suite = unittest.TestSuite()
    suite.addTest(adbClientTestsSuite)
    suite.addTest(viewTestsSuite)
    suite.addTest(viewClientTestsSuite)

    unittest.TextTestRunner(verbosity=3).run(suite)
