#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 3, 2012

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


# 01-04 18:23:42.000: I/ActivityManager(4288): Displayed com.android.development/.DevelopmentSettings: +379ms
package = 'com.android.development'                                          
activity = '.DevelopmentSettings'                           
componentName = package + "/" + activity                        
device = MonkeyRunner.waitForConnection(60, "emulator-5554")
if not device:
	raise Exception('Cannot connect to device')

device.startActivity(component=componentName)
MonkeyRunner.sleep(5)

vc = ViewClient(device)
vc.dump()

showCpu = vc.findViewById("id/show_cpu")
showLoad = vc.findViewById("id/show_load")
alwaysFinish = vc.findViewById("id/always_finish")

if not showLoad.isChecked():
    showLoad.touch()

if not alwaysFinish.isChecked():
    alwaysFinish.touch()

if not showCpu.isChecked():
    # WARNING: Show CPU usage is de-activated as soon as it's activated, that's why it seems it
    # is never set
    showCpu.touch()
