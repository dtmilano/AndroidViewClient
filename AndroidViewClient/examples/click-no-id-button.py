#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Aug 7, 2012

@author: diego
'''

import sys
import os

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient


vc = ViewClient(*ViewClient.connectToDeviceOrExit())

for i in range(1, 9):
    view = vc.findViewById("id/no_id/%d" % i)
    if view:
        print view.__tinyStr__()
        view.touch()
