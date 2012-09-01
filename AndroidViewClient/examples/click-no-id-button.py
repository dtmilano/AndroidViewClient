#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Aug 7, 2012
  
@author: diego
'''

import sys
import os
import time

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
                     
device = MonkeyRunner.waitForConnection(60, "emulator-5554")
if not device:
	raise Exception('Cannot connect to device')

MonkeyRunner.sleep(5)

vc = ViewClient(device)
vc.dump()

for i in range(1, 9):
    view = vc.findViewById("id/no_id/%d" % i)
    print view
#button2.touch(MonkeyDevice.DOWN_AND_UP)
print >>sys.stderr, "bye"
