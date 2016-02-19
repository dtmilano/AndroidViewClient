#! /usr/bin/env python
from PIL import Image
import random
import sys
import os
import time
import cStringIO

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass


from com.dtmilano.android.viewclient import ViewClient
from com.dtmilano.android.uiautomator.uiautomatorhelper import UiAutomatorHelper

__author__ = 'diego'

import unittest


DEBUG = False

class UiAutomatorHelperTests(unittest.TestCase):
    def setUp(self):
        if DEBUG:
            print >> sys.stderr, "@@@ UiAutomatorHelperTests.setUp"
        (self.device, self.serialno) = ViewClient.connectToDeviceOrExit(serialno='.*')
        self.assertIsNotNone(self.device)
        self.uiAutomatorHelper = UiAutomatorHelper(self.device)

    def tearDown(self):
        if DEBUG:
            print >> sys.stderr, "@@@ UiAutomatorHelperTests.tearDown"
        self.uiAutomatorHelper.quit()

    def testDumpWindowHierarchy(self):
        dump = self.uiAutomatorHelper.dumpWindowHierarchy()
        self.assertIsNotNone(dump)

    def testDumpWindowHierarchy_repeat(self):
        for _ in range(10):
            dump = self.uiAutomatorHelper.dumpWindowHierarchy()
            self.assertIsNotNone(dump)

    def testPressKeyCode(self):
        response = self.uiAutomatorHelper.pressKeyCode(4)
        '''4 is KEYCODE_BACK'''
        if DEBUG:
            print >> sys.stderr, "response=", response

    def testTakeScreenshot(self):
        buf = self.uiAutomatorHelper.takeScreenshot()
        self.assertIsNotNone(buf)
        self.assertTrue(len(buf) > 0)
        image = Image.open(cStringIO.StringIO(buf))
        self.assertIsNotNone(image)
        self.assertEqual(image.format, 'PNG')

    def testClick_random(self):
        x = random.randint(0, 1000)
        y = random.randint(0, 1000)
        response = self.uiAutomatorHelper.click(x=x, y=y)
        if DEBUG:
            print >> sys.stderr, "response=", response

    def testSwipe_random(self):
        x0 = random.randint(0, 1000)
        y0 = random.randint(0, 1000)
        x1 = random.randint(0, 1000)
        y1 = random.randint(0, 1000)
        steps = random.randint(10, 100)
        response = self.uiAutomatorHelper.swipe(startX=x0, startY=y0, endX=x1, endY=y1, steps=steps)
        if DEBUG:
            print >> sys.stderr, "response=", response



if __name__ == '__main__':
    unittest.main()
