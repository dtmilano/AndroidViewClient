#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Sep 5, 2012

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
from com.dtmilano.android.viewclient import ViewClient, View

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice


device = MonkeyRunner.waitForConnection(60, "emulator-5554")
if not device:
    raise Exception('Cannot connect to device')

FLAG_ACTIVITY_NEW_TASK = 0x10000000
#09-06 01:01:34.964: I/ActivityManager(873): START {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10200000 cmp=com.example.android.apis/.ApiDemos bnds=[784,346][880,442]} from pid 991
componentName = 'com.example.android.apis/.ApiDemos'
device.startActivity(component=componentName, flags=FLAG_ACTIVITY_NEW_TASK)

MonkeyRunner.sleep(3)
vc = ViewClient(device)
app = vc.findViewWithText('App')
if app:
   app.touch()
   MonkeyRunner.sleep(3)
   # windows changed, request a new dump
   vc.dump()
   ad = vc.findViewWithText('Alert Dialogs')
   if ad:
      ad.touch()
      MonkeyRunner.sleep(3)
      # windows changed, request a new dump
      vc.dump()
      ld = vc.findViewWithText('List dialog')
      if ld:
         ld.touch()
         MonkeyRunner.sleep(3)
         # windows changed, request a new dump
         vc.dump()
         c3 = vc.findViewWithText('Command three')
         if c3:
            c3.touch()
            MonkeyRunner.sleep(10)
            device.press('KEYCODE_BACK', MonkeyDevice.DOWN_AND_UP)
         else:
            print >> sys.stderr, "Cannot find 'Command three'"
      else:
         print >> sys.stderr, "Cannot find 'List dialog'"
   else:
      print >> sys.stderr, "Cannot find 'Alert Dialogs'"
else:
   print >> sys.stderr, "Cannot find 'App'"

