'''
Created on Aug 29, 2012

@author: diego
'''

import re
import sys
import os

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

print >>sys.stderr, "sys.path=", sys.path
import com
import com.dtmilano
import com.dtmilano.android
import com.dtmilano.android.viewclient
from com.dtmilano.android.viewclient import ViewClient, View
print "OK"

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice