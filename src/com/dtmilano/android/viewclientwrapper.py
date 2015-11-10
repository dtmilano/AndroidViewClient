# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2015  Diego Torres Milano
Created on Nov 10, 2015

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@author: Diego Torres Milano
'''

__version__ = '10.9.1'
__author__ = 'diego'

import sys
from com.dtmilano.android.viewclient import ViewClient


"""A library to integrate *AndroidViewClient/culebra* tests with Robotframework.

This documentation is created using reStructuredText__.

__ http://docutils.sourceforge.net
"""

DEBUG = False
ROBOT_LIBRARY_DOC_FORMAT = 'reST'

class ViewClientWrapper:
    def __init__(self, serialno):
        device, serialno = ViewClient.connectToDeviceOrExit(serialno=serialno)
        self.viewClient = ViewClient(device, serialno)
        if DEBUG:
            print >> sys.stderr, "ViewClientWrapper: connected to", device, serialno

    def dump(self):
        """Dumps window hierarchy."""
        return self.viewClient.dump()

    def start_activity(self, component):
        """Starts Activity."""
        return self.viewClient.device.startActivity(component)

    def long_touch_button(self, text):
        """Long-touches the button."""
        self.viewClient.findViewWithTextOrRaise(text).longTouch()


