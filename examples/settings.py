#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 1, 2012

@author: diego
'''


import re
import sys
import os

# This must be imported before MonkeyRunner and MonkeyDevice,
# otherwise the import fails.
# PyDev sets PYTHONPATH, use it
try:
    for p in os.environ['PYTHONPATH'].split(':'):
        if not p in sys.path:
            sys.path.append(p)
except:
    pass

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient

package='com.android.settings'
activity='.Settings'
component=package + "/" + activity
device, serialno = ViewClient.connectToDeviceOrExit()

if True:
    device.startActivity(component=component)
    ViewClient.sleep(3)
    device.press('KEYCODE_DPAD_DOWN') # extra VMT setting WARNING!
    ViewClient.sleep(1)
    device.press('KEYCODE_DPAD_CENTER', MonkeyDevice.DOWN_AND_UP)
    device.press('KEYCODE_DPAD_DOWN', MonkeyDevice.DOWN_AND_UP)
    #device.press('KEYCODE_DPAD_DOWN', MonkeyDevice.DOWN_AND_UP)
    #device.press('KEYCODE_DPAD_DOWN', MonkeyDevice.DOWN_AND_UP)
    #device.press('KEYCODE_DPAD_CENTER', "DOWN_AND_UP")
    #device.press('KEYCODE_DPAD_CENTER', "DOWN_AND_UP")

vc = ViewClient(device, serialno)
regex = "id/checkbox.*"
p = re.compile(regex)
found = False
for id in vc.getViewIds():
    #print id
    m = p.match(id)
    if m:
        found = True
        attrs =  vc.findViewById(id)
        if attrs['isSelected()'] == 'true':
            print "Wi-Fi is",
            if attrs['isChecked()'] != 'true':
                print "not",
            print "set"

if not found:
    print "No Views found that match " + regex
