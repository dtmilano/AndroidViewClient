#! /usr/bin/env python3
#
# Dumps the window hierarchy in JSON format
#

import json

from com.dtmilano.android.viewclient import ViewClient

device, serialno = ViewClient.connectToDeviceOrExit()

vc = ViewClient(device, serialno, useuiautomatorhelper=True)
print(json.dumps(vc.uiAutomatorHelper.ui_device.dump_window_hierarchy().to_dict()))
