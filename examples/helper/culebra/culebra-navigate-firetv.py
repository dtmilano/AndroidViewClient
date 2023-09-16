#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2013-2023  Diego Torres Milano
Created on 2023-09-05 by Culebra v22.6.1
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
import re
import sys
import time

from com.dtmilano.android.viewclient import ViewClient, KEY_EVENT


TAG = 'CULEBRA'
_s = 5
_v = '--verbose' in sys.argv
pid = os.getpid()


kwargs1 = {'verbose': False, 'ignoresecuredevice': False, 'ignoreversioncheck': False}
device, serialno = ViewClient.connectToDeviceOrExit(**kwargs1)

kwargs2 = {'forceviewserveruse': False, 'startviewserver': True, 'autodump': False, 'ignoreuiautomatorkilled': True, 'compresseddump': True, 'useuiautomatorhelper': True, 'debug': {}}
vc = ViewClient(device, serialno, **kwargs2)

helper = vc.uiAutomatorHelper

helper.ui_device.press_key_code(KEY_EVENT['KEYCODE_DPAD_RIGHT'])
helper.ui_device.wait_for_window_update()

helper.ui_device.press_key_code(KEY_EVENT['KEYCODE_DPAD_RIGHT'])
helper.ui_device.wait_for_window_update()

helper.ui_device.press_key_code(KEY_EVENT['KEYCODE_DPAD_RIGHT'])
helper.ui_device.wait_for_window_update()

helper.ui_device.press_key_code(KEY_EVENT['KEYCODE_DPAD_RIGHT'])
helper.ui_device.wait_for_window_update()

helper.ui_device.press_key_code(KEY_EVENT['KEYCODE_DPAD_CENTER'])
helper.ui_device.wait_for_window_update()

helper.ui_device.press_key_code(KEY_EVENT['KEYCODE_HOME'])
helper.ui_device.wait_for_window_update()
