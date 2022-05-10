#! /usr/bin/env python
# -*- coding: utf-8 -*-
import io
import os
import random
import sys

from culebratester_client import ObjectRef

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
            print("@@@ UiAutomatorHelperTests.setUp", file=sys.stderr)
        (self.device, self.serialno) = ViewClient.connectToDeviceOrExit(serialno='.*')
        self.assertIsNotNone(self.device)
        self.uiAutomatorHelper = UiAutomatorHelper(self.device)
        self.uiAutomatorHelper.ui_device.press_home()

    def tearDown(self):
        if DEBUG:
            print("@@@ UiAutomatorHelperTests.tearDown", file=sys.stderr)
        self.uiAutomatorHelper.quit()

    def testDumpWindowHierarchy(self):
        dump = self.uiAutomatorHelper.ui_device.dump_window_hierarchy()
        self.assertIsNotNone(dump)

    def testDumpWindowHierarchy_repeat(self):
        for _ in range(10):
            dump = self.uiAutomatorHelper.ui_device.dump_window_hierarchy()
            self.assertIsNotNone(dump)

    def testPressKeyCode(self):
        response = self.uiAutomatorHelper.ui_device.press_key_code(4)
        '''4 is KEYCODE_BACK'''
        if DEBUG:
            print("response=", response, file=sys.stderr)
        self.assertEqual(response.status, 'OK')

    def testTakeScreenshot(self):
        received = self.uiAutomatorHelper.ui_device.take_screenshot()
        self.assertIsNotNone(received)
        stream = io.BytesIO(received.read())
        self.assertIsNotNone(stream)
        from PIL import Image
        image = Image.open(stream)
        self.assertIsNotNone(image)
        self.assertEqual(image.format, 'PNG')
        filename = f'/tmp/uiautomatorhelpertests-{os.getpid()}.png'
        image.save(filename, 'PNG')
        print(f'Screenshot saved to file://{filename}')

    def testClick_random(self):
        x = random.randint(0, 1000)
        y = random.randint(0, 1000)
        response = self.uiAutomatorHelper.ui_device.click(x=x, y=y)
        if DEBUG:
            print("response=", response, file=sys.stderr)
        self.assertEqual(response.status, 'OK')

    def testSwipe_random(self):
        x0 = random.randint(0, 1000)
        y0 = random.randint(0, 1000)
        x1 = random.randint(0, 1000)
        y1 = random.randint(0, 1000)
        steps = random.randint(10, 100)
        response = self.uiAutomatorHelper.ui_device.swipe(start_x=x0, start_y=y0, end_x=x1, end_y=y1, steps=steps)
        if DEBUG:
            print("response=", response, file=sys.stderr)
        self.assertEqual(response.status, 'OK')

    def testSetText_UiObject2_Chinese_text(self):
        # This enters a Reminder using Calendar
        # See https://github.com/dtmilano/AndroidViewClient/issues/242
        self.uiAutomatorHelper.ui_device.press_home()

        obj_ref: ObjectRef = self.uiAutomatorHelper.until.find_object(
            by_selector='checkable@false,clazz@android.widget.FrameLayout,desc@Google Search,pkg@com.google.android.googlequicksearchbox,res@com.google.android.googlequicksearchbox:id/search_edit_frame')
        self.assertIsNotNone(obj_ref)
        self.assertGreater(obj_ref.oid, 0)
        self.assertTrue(isinstance(obj_ref, ObjectRef), f'obj_ref type is {type(obj_ref)} instead of ObjectRef')
        obj_ref: ObjectRef = self.uiAutomatorHelper.ui_device.wait(search_condition_ref=obj_ref.oid, timeout=3000)
        self.uiAutomatorHelper.ui_object2.click(obj_ref.oid)

        obj_ref: ObjectRef = self.uiAutomatorHelper.until.find_object(
            by_selector='checkable@false,clazz@android.widget.EditText,pkg@com.google.android.googlequicksearchbox,res@com.google.android.googlequicksearchbox:id/search_box,text@Search…')
        self.assertIsNotNone(obj_ref)
        self.assertGreater(obj_ref.oid, 0)
        self.assertTrue(isinstance(obj_ref, ObjectRef), f'obj_ref type is {type(obj_ref)} instead of ObjectRef')
        obj_ref: ObjectRef = self.uiAutomatorHelper.ui_device.wait(search_condition_ref=obj_ref.oid, timeout=3000)
        self.uiAutomatorHelper.ui_object2.set_text(obj_ref.oid, '提醒我包括中文支持')
        self.uiAutomatorHelper.ui_device.press_enter()


if __name__ == '__main__':
    unittest.main()
