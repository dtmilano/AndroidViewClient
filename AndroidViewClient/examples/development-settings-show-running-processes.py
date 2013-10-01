#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 3, 2012

@author: diego
'''


import re
import sys
import os


try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient

# 01-04 18:23:42.000: I/ActivityManager(4288): Displayed com.android.development/.DevelopmentSettings: +379ms
package = 'com.android.development'
activity = '.DevelopmentSettings'
component = package + "/" + activity
device, serialno = ViewClient.connectToDeviceOrExit()
device.startActivity(component=component)
ViewClient.sleep(5)

vc = ViewClient(device, serialno)

showCpu = vc.findViewWithTextOrRaise("Show CPU usage")
showLoad = vc.findViewWithTextOrRaise("Show running processes")
alwaysFinish = vc.findViewWithTextOrRaise("Immediately destroy activities")

if not showLoad.isChecked():
    print "touching @", showLoad.getCenter()
    showLoad.touch()

if not alwaysFinish.isChecked():
    print "touching @", alwaysFinish.getCenter()
    alwaysFinish.touch()

if not showCpu.isChecked():
    # WARNING: Show CPU usage is de-activated as soon as it's activated, that's why it seems it
    # is never set
    print "touching @", showCpu.getCenter()
    showCpu.touch()
