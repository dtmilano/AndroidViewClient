#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on May 5, 2012

@author: diego
'''

import sys
import os
import time

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient

vc = ViewClient(*ViewClient.connectToDeviceOrExit())

for bt in [ 'One', 'Two', 'Three', 'Four', 'Five' ]:
    b = vc.findViewWithText(bt)
    if b:
        (x, y) = b.getXY()
        print >>sys.stderr, "clicking b%s @ (%d,%d) ..." % (bt, x, y)
        b.touch()
    else:
        print >>sys.stderr, "b%s not found" % bt
    time.sleep(7)

print >>sys.stderr, "bye"
