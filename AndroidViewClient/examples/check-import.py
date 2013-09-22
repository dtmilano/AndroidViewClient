#! /usr/bin/env python
'''
Created on Aug 29, 2012

@author: diego
'''

import re
import sys
import os

debug = False
if '--debug' in sys.argv or '-X' in sys.argv:
    debug = True

try:
    if os.environ.has_key('ANDROID_VIEW_CLIENT_HOME'):
        avcd = os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src')
        if os.path.isdir(avcd):
            sys.path.append(avcd)
        else:
            print >>sys.stderr, "WARNING: '%s' is not a directory and is pointed by ANDROID_VIEW_CLIENT_HOME environment variable" % avcd
except:
    pass

if debug:
    print >>sys.stderr, "sys.path=", sys.path
for d in sys.path:
    if d in [ '__classpath__', '__pyclasspath__/']:
        continue
    if not os.path.exists(d):
        if re.search('/Lib$', d):
            if not os.path.exists(re.sub('/Lib$', '', d)):
                print >>sys.stderr, "WARNING: '%s' is in sys.path but doesn't exist" % d
import com
import com.dtmilano
import com.dtmilano.android
import com.dtmilano.android.viewclient
from com.dtmilano.android.viewclient import ViewClient, View
print "OK"
