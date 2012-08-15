#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Aug 15, 2012

@author: diego
'''


import re
import sys
import os

# this must be imported before MonkeyRunner and MonkeyDevice,
# otherwise the import fails
try:
    ANDROID_VIEW_CLIENT_HOME = os.environ['ANDROID_VIEW_CLIENT_HOME']
except KeyError:
    print >>sys.stderr, "%s: ERROR: ANDROID_VIEW_CLIENT_HOME not set in environment" % __file__
    sys.exit(1)
sys.path.append(ANDROID_VIEW_CLIENT_HOME + '/src')
from com.dtmilano.android.viewclient import ViewClient

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

START_ACTIVITY = True
FLAG_ACTIVITY_NEW_TASK = 0x10000000

package='com.android.settings'                                          
activity='.Settings'                           
componentName=package + "/" + activity                        

device = MonkeyRunner.waitForConnection(60)
if not device:
	raise Exception('Cannot connect to device')

if START_ACTIVITY:
    device.startActivity(component=componentName, flags=FLAG_ACTIVITY_NEW_TASK)
    MonkeyRunner.sleep(3)

vc = ViewClient(device)
vc.dump()
# this may help you find the attributes for specific Views
#vc.traverse(vc.getRoot())
text = 'Display'
view = vc.findViewWithText(text)
if view:
	print view.__smallStr__()
	print view.getCoords()
	print view['layout:mLeft'], ',', view['layout:mTop']
else:
	print "Not found"
