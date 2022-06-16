#! /usr/bin/env python3

from com.dtmilano.android.viewclient import ViewClient

device, serialno = ViewClient.connectToDeviceOrExit()
helper = ViewClient(device, serialno, useuiautomatorhelper=True).uiAutomatorHelper

helper.target_context.start_activity('com.android.chrome', 'com.google.android.apps.chrome.Main',
                                     uri='https://google.com')
