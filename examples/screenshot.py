#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Aug 31, 2013

@author: diego
'''


import sys
import os

from com.dtmilano.android.viewclient import ViewClient

if len(sys.argv) < 2:
    sys.exit("usage: %s filename.png [serialno]" % sys.argv[0])

filename = sys.argv.pop(1)
device, serialno = ViewClient.connectToDeviceOrExit(verbose=False)
device.takeSnapshot().save(filename, 'PNG')
