#! /usr/bin/env python3
"""
Copyright (C) 2022  Diego Torres Milano
Created on Jun 24, 2022

@author: diego
"""

import sys

from com.dtmilano.android.viewclient import ViewClient

if len(sys.argv) != 2:
    sys.exit("usage: %s filename.png" % sys.argv[0])

filename = sys.argv.pop(1)
helper = ViewClient(*ViewClient.connectToDeviceOrExit(), useuiautomatorhelper=True).uiAutomatorHelper
helper.ui_device.take_screenshot(filename=filename)
