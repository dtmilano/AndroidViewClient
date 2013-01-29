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

VERBOSE = 'verbose'
UNIQUE_ID = 'uniqueId'
POSITION = 'position'
CONTENT_DESCRIPTION = 'content-description'
CENTER = 'center'
MAP = {'u':ViewClient.TRAVERSE_CITUI, UNIQUE_ID:ViewClient.TRAVERSE_CITUI,
       'x':ViewClient.TRAVERSE_CITPS, POSITION:ViewClient.TRAVERSE_CITPS,
       'd':ViewClient.TRAVERSE_CITCD, CONTENT_DESCRIPTION:ViewClient.TRAVERSE_CITCD,
       'c':ViewClient.TRAVERSE_CITC, CENTER:ViewClient.TRAVERSE_CITC,
       }

def usage():
    print >> sys.stderr, 'usage: dump.py [-V|--%s] [-u|--%s] [-x|--%s] [-d|--%s] [-c|--%s] [serialno]' % \
        (VERBOSE, UNIQUE_ID, POSITION, CONTENT_DESCRIPTION, CENTER)
    sys.exit(1)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'Vuxdc',
                        [VERBOSE, UNIQUE_ID, POSITION, CONTENT_DESCRIPTION, CENTER])
except getopt.GetoptError, e:
    print >>sys.stderr, 'ERROR:', str(e)
    usage()

verbose = True
transform = ViewClient.TRAVERSE_CIT
for o, a in opts:
    o = o.strip('-')
    if o in ['V', VERBOSE]:
        verbose = True
        continue
    transform = MAP[o]

ViewClient(*ViewClient.connectToDeviceOrExit(verbose=verbose)).traverse(transform=transform)
