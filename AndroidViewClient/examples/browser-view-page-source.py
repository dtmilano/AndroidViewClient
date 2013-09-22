#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Oct 12, 2012

@author: diego
'''


import re
import sys
import os

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient


VPS = "javascript:alert(document.getElementsByTagName('html')[0].innerHTML);"
USE_BROWSER = True
if USE_BROWSER:
    package = 'com.android.browser'
    activity = '.BrowserActivity'
    _id = 'id/no_id/12'
else:
    package = 'com.android.chrome'
    activity = 'com.google.android.apps.chrome.Main'
    _id = 'id/no_id/28'
component = package + "/" + activity
uri = 'http://dtmilano.blogspot.com'
                   

device, serialno = ViewClient.connectToDeviceOrExit()

device.startActivity(component=component, uri=uri)
ViewClient.sleep(5)

vc = ViewClient(device=device, serialno=serialno)
sdkVersion = vc.getSdkVersion()

if sdkVersion > 10:
    device.drag((240, 180), (240, 420), 1, 20)
else:
    for i in range(10):
        device.press('KEYCODE_DPAD_UP')
        ViewClient.sleep(1)

vc.findViewByIdOrRaise(_id if sdkVersion >= 16 else 'id/url' if sdkVersion > 10 else 'id/title').touch()
ViewClient.sleep(1)

device.press('KEYCODE_DEL')
device.type(VPS)
ViewClient.sleep(1)
device.press('KEYCODE_ENTER')
ViewClient.sleep(3)

vc.dump()
print vc.findViewByIdOrRaise('id/no_id/11' if sdkVersion >= 16 else 'id/message').getText().replace('\\n', "\n")

device.press('KEYCODE_BACK' if sdkVersion > 10 else 'KEYCODE_ENTER')
