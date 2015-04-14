#! /usr/bin/env python

'''
Copyright (C) 2014  Diego Torres Milano
Created on Apr 24, 2014

@author: diego
'''

import sys
import os

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient

kwargs1 = {'verbose': True, 'ignoresecuredevice': True}
kwargs2 = {'startviewserver': True, 'forceviewserveruse': True, 'autodump': False, 'ignoreuiautomatorkilled': True}
vc = ViewClient(*ViewClient.connectToDeviceOrExit(**kwargs1), **kwargs2)
windows = vc.list()
for wId in windows.keys():
    print ">>> window=", wId, windows[wId]
    vc.dump(window=wId)
    vc.traverse(transform=ViewClient.TRAVERSE_CITCD, indent="    ")
