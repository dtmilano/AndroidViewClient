#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 3, 2012

@author: diego
'''


import sys
import os
import re
import time

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

from com.dtmilano.android.viewclient import *

package = 'com.android.gallery'
activity = 'com.android.camera.GalleryPicker'
component = package + "/" + activity

device, serialno = ViewClient.connectToDeviceOrExit()
device.startActivity(component=component)
time.sleep(3)
vc = ViewClient(device, serialno)
if vc.build[VERSION_SDK_PROPERTY] != 15:
    print 'This script is intended to run on API-15'
    sys.exit(1)
ALL_PICTURES = 'All pictures'
vc.findViewWithTextOrRaise(re.compile('%s \(\d+\)' % ALL_PICTURES)).touch()
vc.dump()
vc.findViewWithTextOrRaise(ALL_PICTURES)
print "'%s' found" % ALL_PICTURES
