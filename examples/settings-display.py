#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Aug 15, 2012

@author: diego
'''


import re
import sys
import os

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient, View


START_ACTIVITY = True
FLAG_ACTIVITY_NEW_TASK = 0x10000000

package='com.android.settings'
activity='.Settings'
component=package + "/" + activity

device, serialno = ViewClient.connectToDeviceOrExit()

if START_ACTIVITY:
    device.startActivity(component=component, flags=FLAG_ACTIVITY_NEW_TASK)
    ViewClient.sleep(3)

vc = ViewClient(device, serialno)

# this may help you find the attributes for specific Views
#vc.traverse(vc.getRoot())
text = 'Display'
view = vc.findViewWithText(text)
if view:
	print view.__smallStr__()
	print view.getCoords()
	print view.getX(), ',', view.getY()
else:
	print "View with text='%s' was not found" % text
