#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Sep 5, 2012

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

device, serialno = ViewClient.connectToDeviceOrExit()

FLAG_ACTIVITY_NEW_TASK = 0x10000000
#09-06 01:01:34.964: I/ActivityManager(873): START {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10200000 cmp=com.example.android.apis/.ApiDemos bnds=[784,346][880,442]} from pid 991
componentName = 'com.example.android.apis/.ApiDemos'
device.startActivity(component=componentName, flags=FLAG_ACTIVITY_NEW_TASK)

ViewClient.sleep(3)
vc = ViewClient(device=device, serialno=serialno)
app = vc.findViewWithText('App')
if app:
   app.touch()
   ViewClient.sleep(3)
   # windows changed, request a new dump
   vc.dump()
   ad = vc.findViewWithText('Alert Dialogs')
   if ad:
      ad.touch()
      ViewClient.sleep(3)
      # windows changed, request a new dump
      vc.dump()
      ld = vc.findViewWithText('List dialog')
      if ld:
         ld.touch()
         ViewClient.sleep(3)
         # windows changed, request a new dump
         vc.dump()
         c3 = vc.findViewWithText('Command three')
         if c3:
            c3.touch()
            ViewClient.sleep(10)
            device.press('KEYCODE_BACK')
         else:
            print >> sys.stderr, "Cannot find 'Command three'"
      else:
         print >> sys.stderr, "Cannot find 'List dialog'"
   else:
      print >> sys.stderr, "Cannot find 'Alert Dialogs'"
else:
   print >> sys.stderr, "Cannot find 'App'"

