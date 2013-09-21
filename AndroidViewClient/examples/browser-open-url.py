#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Mar 13, 2012

@author: diego
'''


import re
import sys
import os
import string

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient

USE_BROWSER = True
# Starting: Intent { act=android.intent.action.MAIN flg=0x10000000 cmp=com.android.browser/.BrowserActivity }
if USE_BROWSER:
    package = 'com.android.browser'
    activity = '.BrowserActivity'
else:
    package = 'com.android.chrome'
    activity = 'com.google.android.apps.chrome.Main'
component = package + "/" + activity
uri = 'http://dtmilano.blogspot.com'

device, serialno = ViewClient.connectToDeviceOrExit()
device.startActivity(component=component, uri=uri)
ViewClient.sleep(5)

vc = ViewClient(device, serialno)
if vc.getSdkVersion() >= 16:
    if USE_BROWSER:
        url = vc.findViewByIdOrRaise("id/no_id/12").getText()
    else:
        url = vc.findViewWithContentDescription("Search or type url").getText()
else:
    url = vc.findViewByIdOrRaise("id/url").getText()
if string.find(uri, url) != -1:
    print "%s successfully loaded" % uri
else:
    print "%s was not loaded, url=%s" % (uri, url)
