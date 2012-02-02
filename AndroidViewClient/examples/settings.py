#! /usr/bin/env monkeyrunner
'''
Created on Feb 1, 2012

@author: diego
'''


import re
import sys

# this must be imported before MonkeyRunner and MonkeyDevice,
# otherwise the import fails
sys.path.append('/Users/diego/Work/workspace/AndroidViewClient/src')
from com.dtmilano.android.viewclient import ViewClient

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

package='com.android.settings'                                          
activity='.Settings'                           
component_name=package + "/" + activity                        
device = MonkeyRunner.waitForConnection(60)
if True:
    device.startActivity(component=component_name)
    MonkeyRunner.sleep(3)
    device.press('KEYCODE_DPAD_DOWN') # extra VMT setting WARNING!
    MonkeyRunner.sleep(1)
    device.press('KEYCODE_DPAD_CENTER', "DOWN_AND_UP")
    device.press('KEYCODE_DPAD_DOWN', MonkeyDevice.DOWN_AND_UP)
    #device.press('KEYCODE_DPAD_DOWN', MonkeyDevice.DOWN_AND_UP)
    #device.press('KEYCODE_DPAD_DOWN', MonkeyDevice.DOWN_AND_UP)
    #device.press('KEYCODE_DPAD_CENTER', "DOWN_AND_UP")
    #device.press('KEYCODE_DPAD_CENTER', "DOWN_AND_UP")


vc = ViewClient(device)
regex = "id/checkbox.*"
p = re.compile(regex)
vc.dump()
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