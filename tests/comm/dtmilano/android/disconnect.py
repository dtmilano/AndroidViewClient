#! /usr/bin/env python2.7

'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''

import sys
import os
import unittest

# PyDev sets PYTHONPATH, use it
if 'PYTHONPATH' in os.environ:
    for p in os.environ['PYTHONPATH'].split(':'):
        if not p in sys.path:
            sys.path.append(p)
try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import View, TextView, EditText, ViewClient


# Script gets stuck on ViewClient(device, serial) #243
d, s = ViewClient.connectToDeviceOrExit()
raw_input('\n** Disconnect the device now and press <ENTER>')
device = ViewClient(d, s)
