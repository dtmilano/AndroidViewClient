#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Sep 8, 2012

@author: diego

@see: http://code.google.com/p/android/issues/detail?id=36544
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


device, serialno = ViewClient.connectToDeviceOrExit()

FLAG_ACTIVITY_NEW_TASK = 0x10000000
# We are not using Settings as the bug describes because there's no WiFi dialog in emulator
#componentName = 'com.android.settings/.Settings'
componentName = 'com.dtmilano.android.sampleui/.MainActivity'
device.startActivity(component=componentName, flags=FLAG_ACTIVITY_NEW_TASK)
ViewClient.sleep(3)

# Set it to True or False to decide if AndroidViewClient or plain monkeyrunner is used
USE_AVC = True

if USE_AVC:
    # AndroidViewClient
    vc = ViewClient(device=device, serialno=serialno)
    showDialogButton = vc.findViewById('id/show_dialog_button')
    if showDialogButton:
        showDialogButton.touch()
        vc.dump()
        vc.findViewById('id/0x123456').type('Donald')
        ok = vc.findViewWithText('OK')
        if ok:
            # 09-08 20:17:47.860: D/MonkeyStub(2033): translateCommand: tap 265 518
            ok.touch()
        vc.dump()
        hello = vc.findViewById('id/hello')
        if hello:
            if hello.getText() == "Hello Donald":
                print "OK"
            else:
                print "FAIL"
        else:
            print >> sys.stderr, "'hello' not found"
    else:
        print >> sys.stderr, "'Show Dialog' button not found"
else:
    # MonkeyRunner
    from com.android.monkeyrunner.easy import EasyMonkeyDevice
    from com.android.monkeyrunner.easy import By
    easyDevice = EasyMonkeyDevice(device)
    showDialogButton = By.id('id/show_dialog_button')
    if showDialogButton:
        easyDevice.touch(showDialogButton, MonkeyDevice.DOWN_AND_UP)
        ViewClient.sleep(3)
        editText = By.id('id/0x123456')
        print editText
        easyDevice.type(editText, 'Donald')
        ViewClient.sleep(3)
        ok = By.id('id/button1')
        if ok:
            # 09-08 20:16:41.119: D/MonkeyStub(1992): translateCommand: tap 348 268
            easyDevice.touch(ok, MonkeyDevice.DOWN_AND_UP)
        hello = By.id('id/hello')
        if hello:
            if easyDevice.getText(hello) == "Hello Donald":
                print "OK"
            else:
                print "FAIL"
        else:
            print >> sys.stderr, "'hello' not found"

