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
from com.dtmilano.android.viewclient import ViewClient, View


vc = ViewClient(*ViewClient.connectToDeviceOrExit())

button = vc.findViewWithTextOrRaise('Show Dialog')
print "button: ", button.getClass(), button.getId(), button.getCoords()

