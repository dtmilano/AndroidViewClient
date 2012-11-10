#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Mar 13, 2012

@author: diego
'''


import re
import sys
import os
import string

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

from com.dtmilano.android.viewclient import ViewClient
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

# Starting: Intent { act=android.intent.action.MAIN flg=0x10000000 cmp=com.android.browser/.BrowserActivity }
package = 'com.android.browser'                                          
activity = '.BrowserActivity'                           
component = package + "/" + activity
uri = 'http://dtmilano.blogspot.com'

device, serialno = ViewClient.connectToDeviceOrExit()
device.startActivity(component=component, uri=uri)
MonkeyRunner.sleep(3)

vc = ViewClient(device, serialno)
url = vc.findViewByIdOrRaise("id/url").getText()
if string.find(url, uri) != -1:
    print "%s successfully loaded" % uri
else:
    print "%s was not loaded, url=%s" % (uri, url)
