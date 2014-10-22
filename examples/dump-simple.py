#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Apr 30, 2013

@author: diego
'''


import sys
import os

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

from com.dtmilano.android.viewclient import ViewClient

ViewClient(*ViewClient.connectToDeviceOrExit(verbose=True)).traverse(transform=ViewClient.TRAVERSE_CIT)
