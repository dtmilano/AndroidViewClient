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

UNIQUE_IDS = 'uniqueIds'
POSITIONS = 'positions'

def usage():
    print >> sys.stderr, 'usage: dump.py [-u|--%s] [-x|--%s] [serialno]' % (UNIQUE_IDS, POSITIONS)
    sys.exit(1)

try:
    opts, args = getopt.getopt(sys.argv[1:], 'ux', [UNIQUE_IDS, POSITIONS])
except getopt.GetoptError, e:
    print >>sys.stderr, 'ERROR:', str(e)
    usage()

transform = ViewClient.TRAVERSE_CIT
for o, a in opts:
    o = o.strip('-')
    if o in ['u', UNIQUE_IDS]:
        transform = ViewClient.TRAVERSE_CITUI
    elif o in ['x', POSITIONS]:
        transform = ViewClient.TRAVERSE_CITPS

ViewClient(*ViewClient.connectToDeviceOrExit()).traverse(transform=transform)
