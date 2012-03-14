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

# this must be imported before MonkeyRunner and MonkeyDevice,
# otherwise the import fails
try:
    ANDROID_VIEW_CLIENT_HOME = os.environ['ANDROID_VIEW_CLIENT_HOME']
except KeyError:
    print >>sys.stderr, "%s: ERROR: ANDROID_VIEW_CLIENT_HOME not set in environment" % __file__
    sys.exit(1)
sys.path.append(ANDROID_VIEW_CLIENT_HOME + '/src')
from com.dtmilano.android.viewclient import ViewClient

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

# Starting: Intent { act=android.intent.action.MAIN flg=0x10000000 cmp=com.android.browser/.BrowserActivity }
package = 'com.android.browser'                                          
activity = '.BrowserActivity'                           
component = package + "/" + activity
uri = 'http://dtmilano.blogspot.com'
                   
device = MonkeyRunner.waitForConnection(60)
if not device:
	raise Exception('Cannot connect to device')

device.startActivity(component=component, uri=uri)
MonkeyRunner.sleep(3)

vc = ViewClient(device)
vc.dump()
title = vc.findViewById("id/title")['mText']
if string.find(title, uri) != -1:
    print "%s successfully loaded" % uri
else:
    print "%s was not loaded, title=%s" % (uri, title)
