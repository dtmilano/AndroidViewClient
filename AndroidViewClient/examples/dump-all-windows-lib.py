#!/usr/bin/env python
#! /usr/bin/env shebang monkeyrunner -plugin $ANDROID_VIEW_CLIENT_HOME/bin/androidviewclient-$ANDROID_VIEW_CLIENT_VERSION.jar @!
#
# Linux:
#! /usr/local/bin/shebang monkeyrunner -plugin $AVC_HOME/bin/androidviewclient-$AVC_VERSION.jar @!
#
# Other:
#! /path/to/monkeyrunner -plugin /path/to/androidviewclient/bin/androidviewclient-2.3.14.jar
#
# No shebang:
# c:>path\to\monkeyrunner -plugin \path\to\androidviewclient-2.3.13.jar dump-all-windows-lib.py

'''
Copyright (C) 2012  Diego Torres Milano
Created on Apr 30, 2013

@author: diego
'''

from com.dtmilano.android.viewclient import ViewClient

kwargs2 = {'autodump': False, 'forceviewserveruse': True}
vc = ViewClient(*ViewClient.connectToDeviceOrExit(), **kwargs2)
windows = vc.list()
for wId in windows.keys():
    print ">>> window=", wId, windows[wId]
    vc.dump(window=wId)
    vc.traverse(transform=ViewClient.TRAVERSE_CIT, indent="    ")
