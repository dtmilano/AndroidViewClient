# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2018  Diego Torres Milano
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

__version__ = '20.5.1'
__author__ = 'diego'

import sys

from com.dtmilano.android.viewclient import ViewClient

"""A library to integrate *AndroidViewClient/culebra* tests with Robotframework.

To import this wrapper you have to use::

**Settings**
...
Library     com.dtmilano.android.robotframework.viewclientwrapper.ViewClientWrapper   serialno=<your-device>


This documentation is created using reStructuredText__.

__ http://docutils.sourceforge.net
"""

DEBUG = False
ROBOT_LIBRARY_DOC_FORMAT = 'reST'

class ViewClientWrapper:
    def __init__(self, serialno):
        device, serialno = ViewClient.connectToDeviceOrExit(serialno=serialno)
        self.vc = ViewClient(device, serialno)
        self.device = device
        if DEBUG:
            print("ViewClientWrapper: connected to", device, serialno, file=sys.stderr)

    def dump(self):
        """Dumps window hierarchy."""
        return self.vc.dump()

    def touch(self, x, y):
        """Touches a point.

        :param x: x
        :param y: y
        :return:
        """
        return self.vc.touch(x, y)

    @staticmethod
    def long_touch_view(view):
        """Long-touches the view."""
        return view.longTouch()

    @staticmethod
    def touch_view(view):
        """Touches the View"""
        return view.touch()

    @staticmethod
    def get_view_position_and_size(view):
        """ Gets the View position and size
        :param view: the View
        :return: the position and size
        """
        return view.getPositionAndSize()

    def find_view_with_text(self, text):
        return self.vc.findViewWithText(text)

    def find_view_by_id(self, id):
        return self.vc.findViewById(id)

    def start_activity(self, component):
        """Starts Activity."""
        return self.vc.device.startActivity(component)

    def get_top_activity_name(self):
        return self.device.getTopActivityName()

    def force_stop_package(self, package):
        self.device.shell('am force-stop %s' % package)

    def get_windows(self):
        return self.device.getWindows()

    def is_keyboard_show(self):
        return self.device.isKeyboardShown()

