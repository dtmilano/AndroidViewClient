#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2013-2023  Diego Torres Milano
Created on 2023-09-17 by Culebra v22.7.2
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
# set enabled to False if you don't want kato to find the closet selectors if one is not found
helper.kato.enabled = True

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.TextView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': 'Pattern:[012]?\\d:[0-5]\\d([ \\u200a][AP]M)*',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/clock',
                                             'scrollable': False,
                                             'text': 'Pattern:[012]?\\d:[0-5]\\d([ \\u200a][AP]M)*'})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': 'Android Setup notification: Finish setting up your sdk_gphone_x86',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': 'Settings notification: Virtual SD card',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/notificationIcons',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/notification_icon_area_inner',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/notification_icon_area',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/status_bar_left_side',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/wifi_signal',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/wifi_combo',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/wifi_group',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': 'Wifi signal full.',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/wifi_combo',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/mobile_signal',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/mobile_group',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': 'Phone three bars.',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/mobile_combo',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/statusIcons',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': 'Battery 100 percent.',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/battery',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/system_icons',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/system_icon_area',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/status_bar_contents',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/status_bar',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/status_bar_container',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.TextView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': 'Alarm'})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'rk',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'Alarm',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.TextView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': 'Clock'})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'rk',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'Clock',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.TextView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': 'Timer'})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'rk',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'Timer',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.TextView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': 'Stopwatch'})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'rk',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'Stopwatch',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.HorizontalScrollView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/tabs',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'More options',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.support.v7.widget.LinearLayoutCompat',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.view.ViewGroup',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/toolbar',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/app_bar_layout',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.TextView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': 'Pattern:[012]?\\d:[0-5]\\d([ \\u200a][AP]M)*',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/digital_clock',
                                             'scrollable': False,
                                             'text': 'Pattern:[012]?\\d:[0-5]\\d([ \\u200a][AP]M)*'})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.view.ViewGroup',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.TextView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': 'Pattern:(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), '
                                                     '(January|February|March|April|May|June|July|August|September|October|November|December) '
                                                     '[0123]?\\d',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/date',
                                             'scrollable': False,
                                             'text': 'Pattern:(Mon|Tue|Wed|Thu|Fri|Sat|Sun), '
                                                     '(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0123]?\\d'})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.support.v7.widget.RecyclerView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/cities',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/fab_container',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.view.ViewGroup',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/desk_clock_pager',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageButton',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'Cities',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/fab',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.view.ViewGroup',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/content',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'android:id/content',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': 'com.google.android.deskclock:id/action_bar_root',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.google.android.deskclock',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.RelativeLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'Back',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/back',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.RelativeLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'Overview',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/recent_apps',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.RelativeLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.RelativeLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/ends_group',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': 'Home',
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/home_button',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.RelativeLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/white_cutout',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.ImageView',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/white',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': True,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/home',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.LinearLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/center_group',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/nav_buttons',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/horizontal',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/navigation_inflater',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': None,
                                             'scrollable': False,
                                             'text': None})
assert obj_ref

obj_ref = helper.ui_device.find_object(body={'checkable': False,
                                             'checked': False,
                                             'clazz': 'android.widget.FrameLayout',
                                             'clickable': False,
                                             'depth': None,
                                             'desc': None,
                                             'has_child': None,
                                             'has_descendant': None,
                                             'index': None,
                                             'instance': None,
                                             'pkg': 'com.android.systemui',
                                             'res': 'com.android.systemui:id/navigation_bar_frame',
                                             'scrollable': False,
                                             'text': None})
assert obj_ref


