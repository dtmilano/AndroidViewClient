#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient
from com.dtmilano.android.adb.dumpsys import Dumpsys
from com.dtmilano.android.plot import Plot

try:
    pkg = sys.argv.pop(1)
except:
    sys.exit('usage: %s <package> [serialno]' % sys.argv[0])

device, serialno = ViewClient.connectToDeviceOrExit()
Plot().append(Dumpsys(device, Dumpsys.GFXINFO, pkg, Dumpsys.FRAMESTATS)).plot(_type=Dumpsys.FRAMESTATS)
