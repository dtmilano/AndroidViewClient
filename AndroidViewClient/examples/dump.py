#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 3, 2012

@author: diego
'''


import sys
import os
import getopt

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

UNIQUE_ID = 'uniqueId'
POSITION = 'position'
CONTENT_DESCRIPTION = 'content-description'
MAP = {'u':ViewClient.TRAVERSE_CITUI, UNIQUE_ID:ViewClient.TRAVERSE_CITUI,
       'x':ViewClient.TRAVERSE_CITPS, POSITION:ViewClient.TRAVERSE_CITPS,
       'd':ViewClient.TRAVERSE_CITPS, CONTENT_DESCRIPTION:ViewClient.TRAVERSE_CITCD,
       }

def usage():
    print >> sys.stderr, 'usage: dump.py [-u|--%s] [-x|--%s] [-d|--%s] [serialno]' % \
        (UNIQUE_ID, POSITION, CONTENT_DESCRIPTION)
    sys.exit(1)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'uxd', [UNIQUE_ID, POSITION, CONTENT_DESCRIPTION])
except getopt.GetoptError, e:
    print >>sys.stderr, 'ERROR:', str(e)
    usage()

transform = ViewClient.TRAVERSE_CIT
for o, a in opts:
    transform = MAP[o.strip('-')]

ViewClient(*ViewClient.connectToDeviceOrExit()).traverse(transform=transform)
