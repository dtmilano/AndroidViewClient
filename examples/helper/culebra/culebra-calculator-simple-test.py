#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2013-2022  Diego Torres Milano
Created on 2023-09-03 by Culebra v22.6.0
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

obj_ref = helper.until.find_object(body={'checkable': False,
                                         'checked': None,
                                         'clazz': 'android.widget.ImageButton',
                                         'clickable': True,
                                         'depth': None,
                                         'desc': '3',
                                         'has_child': None,
                                         'has_descendant': None,
                                         'index': None,
                                         'instance': None,
                                         'pkg': 'com.google.android.calculator',
                                         'res': 'com.google.android.calculator:id/digit_3',
                                         'scrollable': None,
                                         'text': ''})
response = helper.ui_device.wait(oid=obj_ref.oid)
helper.ui_object2.click(oid=response['oid'])
helper.ui_device.wait_for_window_update()

obj_ref = helper.until.find_object(body={'checkable': False,
                                         'checked': None,
                                         'clazz': 'android.widget.ImageButton',
                                         'clickable': True,
                                         'depth': None,
                                         'desc': 'multiply',
                                         'has_child': None,
                                         'has_descendant': None,
                                         'index': None,
                                         'instance': None,
                                         'pkg': 'com.google.android.calculator',
                                         'res': 'com.google.android.calculator:id/op_mul',
                                         'scrollable': None,
                                         'text': ''})
response = helper.ui_device.wait(oid=obj_ref.oid)
helper.ui_object2.click(oid=response['oid'])
helper.ui_device.wait_for_window_update()

obj_ref = helper.until.find_object(body={'checkable': False,
                                         'checked': None,
                                         'clazz': 'android.widget.ImageButton',
                                         'clickable': True,
                                         'depth': None,
                                         'desc': '2',
                                         'has_child': None,
                                         'has_descendant': None,
                                         'index': None,
                                         'instance': None,
                                         'pkg': 'com.google.android.calculator',
                                         'res': 'com.google.android.calculator:id/digit_2',
                                         'scrollable': None,
                                         'text': ''})
response = helper.ui_device.wait(oid=obj_ref.oid)
helper.ui_object2.click(oid=response['oid'])
helper.ui_device.wait_for_window_update()

obj_ref = helper.until.find_object(body={'checkable': False,
                                         'checked': None,
                                         'clazz': 'android.widget.ImageButton',
                                         'clickable': True,
                                         'depth': None,
                                         'desc': 'equals',
                                         'has_child': None,
                                         'has_descendant': None,
                                         'index': None,
                                         'instance': None,
                                         'pkg': 'com.google.android.calculator',
                                         'res': 'com.google.android.calculator:id/eq',
                                         'scrollable': None,
                                         'text': ''})
response = helper.ui_device.wait(oid=obj_ref.oid)
helper.ui_object2.click(oid=response['oid'])
helper.ui_device.wait_for_window_update()

assert helper.ui_device.has_object(body={'checkable': False,
                                         'checked': None,
                                         'clazz': 'android.widget.TextView',
                                         'clickable': False,
                                         'depth': None,
                                         'desc': '',
                                         'has_child': None,
                                         'has_descendant': None,
                                         'index': None,
                                         'instance': None,
                                         'pkg': 'com.google.android.calculator',
                                         'res': 'com.google.android.calculator:id/result_final',
                                         'scrollable': None,
                                         'text': '6'})

obj_ref = helper.until.find_object(body={'checkable': False,
                                         'checked': None,
                                         'clazz': 'android.widget.ImageButton',
                                         'clickable': True,
                                         'depth': None,
                                         'desc': 'clear',
                                         'has_child': None,
                                         'has_descendant': None,
                                         'index': None,
                                         'instance': None,
                                         'pkg': 'com.google.android.calculator',
                                         'res': 'com.google.android.calculator:id/clr',
                                         'scrollable': None,
                                         'text': ''})
response = helper.ui_device.wait(oid=obj_ref.oid)
helper.ui_object2.click(oid=response['oid'])
helper.ui_device.wait_for_window_update()
