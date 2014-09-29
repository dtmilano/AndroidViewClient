#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Apr 23, 2013

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

HELP = 'help'
VERBOSE = 'verbose'
IGNORE_SECURE_DEVICE = 'ignore-secure-device'
FORCE_VIEW_SERVER_USE = 'force-view-server-use'
DO_NOT_START_VIEW_SERVER = 'do-not-start-view-server'
# -u,-s,-p,-v eaten by monkeyrunner
SHORT_OPTS = 'HVIFS'
LONG_OPTS =  [HELP, VERBOSE, IGNORE_SECURE_DEVICE, FORCE_VIEW_SERVER_USE, DO_NOT_START_VIEW_SERVER]

def usage(exitVal=1):
    print >> sys.stderr, 'usage: list.py [-H|--%s] [-V|--%s] [-I|--%s] [-F|--%s] [-S|--%s] [serialno]' % \
        tuple(LONG_OPTS)
    sys.exit(exitVal)

try:
    opts, args = getopt.getopt(sys.argv[1:], SHORT_OPTS, LONG_OPTS)
except getopt.GetoptError, e:
    print >>sys.stderr, 'ERROR:', str(e)
    usage()

kwargs1 = {VERBOSE: False, 'ignoresecuredevice': False}
# We force viewserver use by default
kwargs2 = {'forceviewserveruse': True, 'startviewserver': True, 'autodump': False}
for o, a in opts:
    o = o.strip('-')
    if o in ['H', HELP]:
        usage(0)
    elif o in ['V', VERBOSE]:
        kwargs1[VERBOSE] = True
    elif o in ['I', IGNORE_SECURE_DEVICE]:
        kwargs1['ignoresecuredevice'] = True
    elif o in ['F', FORCE_VIEW_SERVER_USE]:
        kwargs2['forceviewserveruse'] = True
    elif o in ['S', DO_NOT_START_VIEW_SERVER]:
        kwargs2['startviewserver'] = False

print ViewClient(*ViewClient.connectToDeviceOrExit(**kwargs1), **kwargs2).list()
