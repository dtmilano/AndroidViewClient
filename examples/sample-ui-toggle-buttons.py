#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Aug 31, 2012

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
from com.dtmilano.android.viewclient import ViewClient, ViewNotFoundException

vc = ViewClient(*ViewClient.connectToDeviceOrExit())
if vc.useUiAutomator:
    print "ViewClient: using UiAutomator backend"

# Find the 3 toggle buttons, because the first 2 change their text if they are selected
# we use a regex to find them.
# Once found, we touch them changing their state
for t in [re.compile('Button 1 .*'), re.compile('Button 2 .*'), 'Button with ID']:
    try:
        vc.findViewWithTextOrRaise(t).touch()
    except ViewNotFoundException:
        print >>sys.stderr, "Couldn't find button with text=", t

