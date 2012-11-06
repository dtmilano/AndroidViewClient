#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Oct 1, 2012

@author: diego
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

from com.dtmilano.android.viewclient import ViewClient, TextView, EditText
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

device, serialno = ViewClient.connectToDeviceOrExit()
vc = ViewClient(device=device, serialno=serialno)
#send = vc.findViewWithTextOrRaise('Send')
send = vc.findViewByIdOrRaise('id/send')
#to = EditText(vc.findViewByIdOrRaise('id/to'))
to = vc.findViewByIdOrRaise('id/to')
subject = vc.findViewByIdOrRaise('id/subject')
subject.touch()
subject.type('AVCSample')
MonkeyRunner.sleep(10)
to.touch()
#to.type('androidviewclient@gmail.com')
device.type('androidviewclient@gmail.com')
MonkeyRunner.sleep(10)
send.touch()
