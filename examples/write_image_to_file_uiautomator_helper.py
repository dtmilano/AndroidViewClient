#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2013-2019  Diego Torres Milano
Created on 2021-09-01 by Culebra v20.1.0b1
                      __    __    __    __
                     /  \  /  \  /  \  /  \
____________________/  __\/  __\/  __\/  __\_____________________________
___________________/  /__/  /__/  /__/  /________________________________
                   | / \   / \   / \   / \   \___
                   |/   \_/   \_/   \_/   \    o \
                                           \_____/--<
@author: Diego Torres Milano
@author: Jennifer E. Swofford (ascii art snake)
"""
import os
import sys

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import CulebraTestCase

TAG = 'CULEBRA'


class CulebraTests(CulebraTestCase):

    sleep = None

    @classmethod
    def setUpClass(cls):
        cls.kwargs1 = {'verbose': False, 'ignoresecuredevice': False, 'ignoreversioncheck': False}
        cls.kwargs2 = {'forceviewserveruse': False, 'startviewserver': False, 'autodump': False,
                       'ignoreuiautomatorkilled': True, 'compresseddump': True, 'useuiautomatorhelper': True,
                       'debug': {}}
        cls.options = {'find-views-by-id': True, 'find-views-with-text': True,
                       'find-views-with-content-description': True, 'use-regexps': False, 'verbose-comments': False,
                       'unit-test-class': True, 'unit-test-method': None, 'use-jar': False, 'use-dictionary': False,
                       'dictionary-keys-from': 'id', 'auto-regexps': None, 'start-activity': None, 'output': None,
                       'interactive': False, 'window': -1, 'prepend-to-sys-path': True, 'save-screenshot': None,
                       'save-view-screenshots': None, 'gui': True, 'do-not-verify-screen-dump': True, 'scale': 0.5,
                       'orientation-locked': None, 'multi-device': False, 'log-actions': False, 'device-art': None,
                       'drop-shadow': False, 'glare': False, 'null-back-end': False, 'concertina': False,
                       'concertina-config': None, 'install-apk': None}
        cls.sleep = 5

    def setUp(self):
        super(CulebraTests, self).setUp()

    def tearDown(self):
        super(CulebraTests, self).tearDown()

    def preconditions(self):
        if not super(CulebraTests, self).preconditions():
            return False

        if not CulebraTests.kwargs2['useuiautomatorhelper']:
            return False
        return True

    def testSomething(self):
        if not self.preconditions():
            self.fail('Preconditions failed')

        _s = CulebraTests.sleep
        _v = CulebraTests.verbose

        r = []
        for n in range(10):
            r.append(self.vc.uiAutomatorHelper.ui_device.take_screenshot(async_req=True))
        for n in range(10):
            with open(f'/tmp/{CulebraTestCase.serialno}-{n}.png', 'wb') as f:
                f.write(r[n].get().read())


if __name__ == '__main__':
    CulebraTests.main()
