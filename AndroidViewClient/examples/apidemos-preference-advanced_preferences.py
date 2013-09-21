#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Sep 18, 2012

@author: diego
'''


import re
import sys
import os

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

import com.dtmilano.android.viewclient as viewclient
if viewclient.__version__ < '1.0':
    print >> sys.stderr, "%s: This script requires viewclient 1.0 or greater." % os.path.basename(sys.argv[0])
    sys.exit(1)

device, serialno = viewclient.ViewClient.connectToDeviceOrExit()

FLAG_ACTIVITY_NEW_TASK = 0x10000000
#09-06 01:01:34.964: I/ActivityManager(873): START {act=android.intent.action.MAIN cat=[android.intent.category.LAUNCHER] flg=0x10200000 cmp=com.example.android.apis/.ApiDemos bnds=[784,346][880,442]} from pid 991
componentName = 'com.example.android.apis/.ApiDemos'
device.startActivity(component=componentName, flags=FLAG_ACTIVITY_NEW_TASK)

viewclient.ViewClient.sleep(3)
vc = viewclient.ViewClient(device=device, serialno=serialno)
vc.findViewWithTextOrRaise('Preference').touch()
vc.dump()
vc.findViewWithTextOrRaise(re.compile('.*Advanced preferences')).touch()
vc.dump()
myPreference = vc.findViewWithTextOrRaise('My preference')
if vc.getSdkVersion() >= 16:
    _id = 'id/no_id/22'
else:
    _id = 'id/mypreference_widget'
value0 = vc.findViewByIdOrRaise(_id).getText()
for i in range(10):
    myPreference.touch()
vc.dump()
value1 = vc.findViewByIdOrRaise(_id).getText()
print "My preference started with value %s and is now %s" % (value0, value1)
