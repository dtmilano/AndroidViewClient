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

from com.dtmilano.android.adb.adbclienttests import AdbClientTests
from com.dtmilano.android.viewclienttests import ViewTests, ViewClientTests

if __name__ == "__main__":
    #sys.argv = ['', 'ViewTest.testName']
    #sys,argv = ['allTests', 'AdbClientTests', 'ViewTests', 'ViewClientTests']
#     adbClientTestsSuite = unittest.TestLoader().loadTestsFromTestCase(AdbClientTests)
#     viewTestsSuite = unittest.TestLoader().loadTestsFromTestCase(ViewTests)
#     viewClientTestsSuite = unittest.TestLoader().loadTestsFromTestCase(ViewClientTests)
#     suite = unittest.TestSuite()
#     suite.addTest(adbClientTestsSuite)
#     suite.addTest(viewTestsSuite)
#     suite.addTest(viewClientTestsSuite)
#     unittest.TextTestRunner(verbosity=2).run(suite)
    pass
