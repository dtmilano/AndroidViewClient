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

DEBUG = True
FLAG_ACTIVITY_NEW_TASK = 0x10000000
# We are not using Settings as the bug describes because there's no WiFi dialog in emulator
componentName = 'com.android.settings/.Settings'
device.startActivity(component=componentName, flags=FLAG_ACTIVITY_NEW_TASK)
ViewClient.sleep(3)

vc = ViewClient(device=device, serialno=serialno)
if DEBUG: vc.traverse(transform=ViewClient.TRAVERSE_CIT)
sound = vc.findViewWithText('Sound')
if sound:
    sound.touch()
    vc.dump()
    phoneRingtone = vc.findViewWithText('Phone ringtone')
    if phoneRingtone:
        phoneRingtone.touch()
        vc.dump()
        vespa = vc.findViewWithText('Vespa')
        if vespa:
            vespa.touch()
        ViewClient.sleep(1)
        ok = vc.findViewById('id/button1')
        if ok:
            ok.touch()
            vc.dump()
            vespa = vc.findViewWithText('Vespa')
            # If for some reason the dialog is still there we will have Vespa and OK
            ok = vc.findViewById('id/button1')
            if vespa and not ok:
                print "OK"
            else:
                print "FAIL to set ringtone Vespa"
                sys.exit(1)
        else:
            print >> sys.stderr, "'OK' not found"
    else:
        print >> sys.stderr, "'Phone ringtone' not found"
else:
    print >> sys.stderr, "'Sound' not found"
