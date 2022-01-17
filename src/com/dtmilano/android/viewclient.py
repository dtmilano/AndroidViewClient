# -*- coding: utf-8 -*-
"""
Copyright (C) 2012-2022  Diego Torres Milano
Created on Feb 2, 2012

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
"""

from __future__ import print_function

import json

from culebratester_client import WindowHierarchyChild, WindowHierarchy

__version__ = '20.5.1'

import sys
import warnings

from com.dtmilano.android.adb.adbclient import AdbClient

if sys.executable:
    if 'monkeyrunner' in sys.executable:
        warnings.warn(
            '''
        
            You should use a 'python' interpreter, not 'monkeyrunner' for this module
        
            ''', RuntimeWarning)
import subprocess
import re
import socket
import os
import time
import signal
import copy
import pickle
import platform
import xml.parsers.expat
import unittest
import io
from com.dtmilano.android.common import _nd, _nh, _ns, obtainPxPy, obtainVxVy, \
    obtainVwVh, obtainAdbPath, substituteDeviceTemplate
from com.dtmilano.android.window import Window
from com.dtmilano.android.adb import adbclient
from com.dtmilano.android.uiautomator.uiautomatorhelper import UiAutomatorHelper
import pprint

DEBUG = False
DEBUG_DEVICE = DEBUG and False
DEBUG_RECEIVED = DEBUG and False
DEBUG_TREE = DEBUG and False
DEBUG_GETATTR = DEBUG and False
DEBUG_CALL = DEBUG and False
DEBUG_COORDS = DEBUG and False
DEBUG_TOUCH = DEBUG and False
DEBUG_STATUSBAR = DEBUG and False
DEBUG_WINDOWS = DEBUG and False
DEBUG_BOUNDS = DEBUG and False
DEBUG_DISTANCE = DEBUG and False
DEBUG_MULTI = DEBUG and False
DEBUG_VIEW = DEBUG and False
DEBUG_VIEW_FACTORY = DEBUG and False
DEBUG_CHANGE_LANGUAGE = DEBUG and False
DEBUG_UI_AUTOMATOR = DEBUG and False
DEBUG_UI_AUTOMATOR_HELPER = DEBUG and False
DEBUG_NAV_BUTTONS = DEBUG and False

WARNINGS = False

VIEW_SERVER_HOST = 'localhost'
VIEW_SERVER_PORT = 4939

ADB_DEFAULT_PORT = 5555

OFFSET = 25
''' This assumes the smallest touchable view on the screen is approximately 50px x 50px
    and touches it at M{(x+OFFSET, y+OFFSET)} '''

USE_ADB_CLIENT_TO_GET_BUILD_PROPERTIES = True
''' Use C{AdbClient} to obtain the needed properties. If this is
    C{False} then C{adb shell getprop} is used '''

USE_PHYSICAL_DISPLAY_INFO = True
''' Use C{dumpsys display} to obtain display properties. If this is
    C{False} then C{USE_ADB_CLIENT_TO_GET_BUILD_PROPERTIES} is used '''

SKIP_CERTAIN_CLASSES_IN_GET_XY_ENABLED = False
''' Skips some classes related with the Action Bar and the PhoneWindow$DecorView in the
    coordinates calculation
    @see: L{View.getXY()} '''

VIEW_CLIENT_TOUCH_WORKAROUND_ENABLED = False
''' Under some conditions the touch event should be longer [t(DOWN) << t(UP)]. C{True} enables a
    workaround to delay the events.'''

# some device properties
VERSION_SDK_PROPERTY = 'ro.build.version.sdk'
VERSION_RELEASE_PROPERTY = 'ro.build.version.release'

# some constants for the attributes
ID_PROPERTY = 'mID'
ID_PROPERTY_UI_AUTOMATOR = 'uniqueId'
TEXT_PROPERTY = 'text:mText'
TEXT_PROPERTY_API_10 = 'mText'
TEXT_PROPERTY_UI_AUTOMATOR = 'text'
WS = "\xfe"  # the whitespace replacement char for TEXT_PROPERTY
TAG_PROPERTY = 'getTag()'
LEFT_PROPERTY = 'layout:mLeft'
LEFT_PROPERTY_API_8 = 'mLeft'
TOP_PROPERTY = 'layout:mTop'
TOP_PROPERTY_API_8 = 'mTop'
WIDTH_PROPERTY = 'layout:getWidth()'
WIDTH_PROPERTY_API_8 = 'getWidth()'
HEIGHT_PROPERTY = 'layout:getHeight()'
HEIGHT_PROPERTY_API_8 = 'getHeight()'
GET_VISIBILITY_PROPERTY = 'getVisibility()'
LAYOUT_TOP_MARGIN_PROPERTY = 'layout:layout_topMargin'
IS_FOCUSED_PROPERTY_UI_AUTOMATOR = 'focused'
IS_FOCUSED_PROPERTY = 'focus:isFocused()'

# visibility
VISIBLE = 0x0
INVISIBLE = 0x4
GONE = 0x8

RegexType = type(re.compile(''))
IP_RE = re.compile('^(\d{1,3}\.){3}\d{1,3}$')
ID_RE = re.compile('id/([^/]*)(/(\d+))?')
IP_DOMAIN_NAME_PORT_REGEX = r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' \
                            r'localhost|' \
                            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' \
                            r'(?::\d+)?' \
                            r'(?:/?|[/?]\S+)$'
IPV6_RE = re.compile('^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$', re.IGNORECASE)
IPV6_PORT_RE = re.compile(r'^\[(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}\]:\d+$', re.IGNORECASE)


class ViewNotFoundException(Exception):
    '''
    ViewNotFoundException is raised when a View is not found.
    '''

    def __init__(self, attr, value, root):
        if isinstance(value, RegexType):
            msg = "Couldn't find View with %s that matches '%s' in tree with root=%s" % (attr, value.pattern, root)
        else:
            msg = "Couldn't find View with %s='%s' in tree with root=%s" % (attr, value, root)
        super(Exception, self).__init__(msg)


class View:
    '''
    View class
    '''

    @staticmethod
    def factory(arg1, arg2, version=-1, forceviewserveruse=False, windowId=None, uiAutomatorHelper=None):
        '''
        View factory

        @type arg1: ClassType or dict
        @type arg2: View instance or AdbClient
        '''

        if DEBUG_VIEW_FACTORY:
            print("View.factory(%s, %s, %s, %s, %s, %s)" % (
                arg1, arg2, version, forceviewserveruse, windowId, uiAutomatorHelper), file=sys.stderr)
        if type(arg1) == type:
            cls = arg1
            attrs = None
        else:
            cls = None
            attrs = arg1
        if isinstance(arg2, View):
            view = arg2
            device = None
        else:
            device = arg2
            view = None

        if attrs and 'class' in attrs:
            clazz = attrs['class']
            if DEBUG_VIEW_FACTORY:
                print("    View.factory: creating View with specific class: %s" % clazz, file=sys.stderr)
            if clazz == 'android.widget.TextView':
                return TextView(attrs, device, version, forceviewserveruse, windowId, uiAutomatorHelper)
            elif clazz == 'android.widget.EditText':
                return EditText(attrs, device, version, forceviewserveruse, windowId, uiAutomatorHelper)
            elif clazz == 'android.widget.ListView':
                return ListView(attrs, device, version, forceviewserveruse, windowId, uiAutomatorHelper)
            else:
                return View(attrs, device, version, forceviewserveruse, windowId, uiAutomatorHelper)
        elif cls:
            if view:
                return cls.__copy(view)
            else:
                return cls(attrs, device, version, forceviewserveruse, windowId, uiAutomatorHelper)
        elif view:
            return copy.copy(view)
        else:
            if DEBUG_VIEW_FACTORY:
                print("    View.factory: creating generic View", file=sys.stderr)
            return View(attrs, device, version, forceviewserveruse, windowId, uiAutomatorHelper)

    @classmethod
    def __copy(cls, view):
        '''
        Copy constructor
        '''

        return cls(view.map, view.device, view.version, view.forceviewserveruse, view.windowId, view.uiAutomatorHelper)

    @classmethod
    def clone(cls, view):
        _map = view.map.copy()
        # enforce the correct class in the map
        _map['class'] = cls.getAndroidClassName()
        return cls(_map, view.device, view.version, view.forceviewserveruse, view.windowId, view.uiAutomatorHelper)

    @classmethod
    def getAndroidClassName(cls):
        return 'android.widget.View'

    def __init__(self, _map, device, version=-1, forceviewserveruse=False, windowId=None, uiAutomatorHelper=None):
        '''
        Constructor

        @type _map: map
        @param _map: the map containing the (attribute, value) pairs
        @type device: AdbClient
        @param device: the device containing this View
        @type version: int
        @param version: the Android SDK version number of the platform where this View belongs. If
                        this is C{-1} then the Android SDK version will be obtained in this
                        constructor.
        @type forceviewserveruse: boolean
        @param forceviewserveruse: Force the use of C{ViewServer} even if the conditions were given
                        to use C{UiAutomator}.
        @type uiAutomatorHelper: UiAutomatorHelper
        @:param uiAutomatorHelper: The UiAutomatorHelper if available
        '''

        if DEBUG_VIEW:
            print("☣️ View.__init__(%s, %s, %s, %s)" % (
                "map" if _map is not None else None, device, version, forceviewserveruse), file=sys.stderr)
            if _map:
                print("    map:", type(_map), file=sys.stderr)
                for attr, val in _map.items():
                    try:
                        if val and len(val) > 50:
                            val = val[:50] + "..."
                    except TypeError:
                        pass
                    print("        %s=%s" % (attr, val), file=sys.stderr)
        self.map = _map
        ''' The map that contains the C{attr},C{value} pairs '''
        self.device = device
        ''' The AdbClient '''
        self.children = []
        ''' The children of this View '''
        self.parent = None
        ''' The parent of this View '''
        self.windows = {}
        self.currentFocus = None
        ''' The current focus '''
        self.windowId = windowId
        ''' The window this view resides '''
        self.build = {}
        ''' Build properties '''
        self.version = version
        ''' API version number '''
        self.forceviewserveruse = forceviewserveruse
        ''' Force ViewServer use '''
        self.uiScrollable = None
        ''' If this is a scrollable View this keeps the L{UiScrollable} object '''
        self.target = False
        ''' Is this a touch target zone '''
        self.uiAutomatorHelper = uiAutomatorHelper
        ''' The UiAutomatorHelper '''

        if version != -1:
            self.build[VERSION_SDK_PROPERTY] = version
        else:
            try:
                if USE_ADB_CLIENT_TO_GET_BUILD_PROPERTIES:
                    self.build[VERSION_SDK_PROPERTY] = int(device.getProperty(VERSION_SDK_PROPERTY))
                else:
                    self.build[VERSION_SDK_PROPERTY] = int(device.shell('getprop ' + VERSION_SDK_PROPERTY)[:-2])
            except:
                self.build[VERSION_SDK_PROPERTY] = -1

        version = self.build[VERSION_SDK_PROPERTY]
        self.useUiAutomator = (version >= 16) and not forceviewserveruse
        ''' Whether to use UIAutomator or ViewServer '''
        self.idProperty = None
        ''' The id property depending on the View attribute format '''
        self.textProperty = None
        ''' The text property depending on the View attribute format '''
        self.tagProperty = None
        ''' The tag property depending on the View attribute format '''
        self.leftProperty = None
        ''' The left property depending on the View attribute format '''
        self.topProperty = None
        ''' The top property depending on the View attribute format '''
        self.widthProperty = None
        ''' The width property depending on the View attribute format '''
        self.heightProperty = None
        ''' The height property depending on the View attribute format '''
        self.isFocusedProperty = None
        ''' The focused property depending on the View attribute format '''

        if version >= 16 and self.useUiAutomator:
            self.idProperty = ID_PROPERTY_UI_AUTOMATOR
            self.textProperty = TEXT_PROPERTY_UI_AUTOMATOR
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
            self.isFocusedProperty = IS_FOCUSED_PROPERTY_UI_AUTOMATOR
        elif version > 10 and (version < 16 or self.useUiAutomator):
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
            self.tagProperty = TAG_PROPERTY
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
            self.isFocusedProperty = IS_FOCUSED_PROPERTY
        elif version == 10:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY_API_10
            self.tagProperty = TAG_PROPERTY
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
            self.isFocusedProperty = IS_FOCUSED_PROPERTY
        elif version >= 7 and version < 10:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY_API_10
            self.tagProperty = TAG_PROPERTY
            self.leftProperty = LEFT_PROPERTY_API_8
            self.topProperty = TOP_PROPERTY_API_8
            self.widthProperty = WIDTH_PROPERTY_API_8
            self.heightProperty = HEIGHT_PROPERTY_API_8
            self.isFocusedProperty = IS_FOCUSED_PROPERTY
        elif version > 0 and version < 7:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY_API_10
            self.tagProperty = TAG_PROPERTY
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
            self.isFocusedProperty = IS_FOCUSED_PROPERTY
        elif version == -1:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
            self.tagProperty = TAG_PROPERTY
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
            self.isFocusedProperty = IS_FOCUSED_PROPERTY
        else:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
            self.tagProperty = TAG_PROPERTY
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
            self.isFocusedProperty = IS_FOCUSED_PROPERTY

        try:
            if self.isScrollable():
                self.uiScrollable = UiScrollable(self)
        except AttributeError:
            pass

    def __getitem__(self, key):
        return self.map[key]

    def __getattr__(self, name):
        if DEBUG_GETATTR:
            print("__getattr__(%s)    version: %d" % (name, self.build[VERSION_SDK_PROPERTY]), file=sys.stderr)
            print("__getattr__: map = %s" % self.map, file=sys.stderr)

        # NOTE:
        # I should try to see if 'name' is a defined method
        # but it seems that if I call locals() here an infinite loop is entered

        if name in self.map:
            r = self.map[name]
        elif name + '()' in self.map:
            # the method names are stored in the map with their trailing '()'
            r = self.map[name + '()']
        elif name in ['getResourceId', 'resource_id', 'id']:
            if DEBUG_GETATTR:
                print("    __getattr__: getResourceId", file=sys.stderr)
            if 'resource-id' in self.map:
                r = self.map['resource-id']
            else:
                # Default behavior
                raise AttributeError(name)
        elif name == 'unique_id':
            if 'uniqueId' in self.map:
                r = self.map['uniqueId']
            elif 'unique-id' in self.map:
                r = self.map['unique_id']
            elif 'unique_id' in self.map:
                r = self.map['unique_id']
            else:
                # Default behavior
                raise AttributeError(name)
        elif name == 'content_description':
            if 'content_description' in self.map:
                r = self.map['content_description']
            elif 'content-desc' in self.map:
                r = self.map['content-desc']
            else:
                # Default behavior
                raise AttributeError(name)
        elif name.count("_") > 0:
            mangledList = self.allPossibleNamesWithColon(name)
            mangledName = self.intersection(mangledList, list(self.map.keys()))
            if len(mangledName) > 0 and mangledName[0] in self.map:
                r = self.map[mangledName[0]]
            else:
                # Default behavior
                raise AttributeError(name)
        elif name.startswith('is'):
            # try removing 'is' prefix
            if DEBUG_GETATTR:
                print("    __getattr__: trying without 'is' prefix", file=sys.stderr)
            suffix = name[2:].lower()
            if suffix in self.map:
                r = self.map[suffix]
            else:
                # Default behavior
                raise AttributeError(name)
        elif name.startswith('get'):
            # try removing 'get' prefix
            if DEBUG_GETATTR:
                print("    __getattr__: trying without 'get' prefix", file=sys.stderr)
            suffix = name[3:].lower()
            if suffix in self.map:
                r = self.map[suffix]
            else:
                # Default behavior
                raise AttributeError(name)
        else:
            # Default behavior
            raise AttributeError(name)

        # if the method name starts with 'is' let's assume its return value is boolean
        #         if name[:2] == 'is':
        #             r = True if r == 'true' else False
        if r == 'true':
            r = True
        elif r == 'false':
            r = False

        # this should not cached in some way
        def innerMethod():
            if DEBUG_GETATTR:
                print("innerMethod: %s returning %s" % (innerMethod.__name__, r), file=sys.stderr)
            return r

        innerMethod.__name__ = name

        # this should work, but then there's problems with the arguments of innerMethod
        # even if innerMethod(self) is added
        # setattr(View, innerMethod.__name__, innerMethod)
        # setattr(self, innerMethod.__name__, innerMethod)

        return innerMethod

    def __call__(self, *args, **kwargs):
        if DEBUG_CALL:
            print("__call__(%s)" % (args if args else None), file=sys.stderr)

    def getClass(self):
        '''
        Gets the L{View} class

        @return:  the L{View} class or C{None} if not defined
        '''

        try:
            return self.map['class']
        except:
            return None

    def getId(self):
        '''
        Gets the L{View} Id

        @return: the L{View} C{Id} or C{None} if not defined
        @see: L{getUniqueId()}
        '''

        try:
            return self.map['resource-id']
        except:
            pass

        try:
            return self.map[self.idProperty]
        except:
            return None

    def getContentDescription(self):
        '''
        Gets the content description.
        '''

        try:
            return self.map['content-desc']
        except:
            return None

    def getTag(self):
        '''
        Gets the tag.
        '''

        try:
            return self.map[self.tagProperty]
        except:
            return None

    def getParent(self):
        '''
        Gets the parent.
        '''

        return self.parent

    def getChildren(self):
        '''
        Gets the children of this L{View}.
        '''

        return self.children

    def getText(self):
        '''
        Gets the text attribute.

        @return: the text attribute or C{None} if not defined
        '''

        try:
            return self.map[self.textProperty]
        except Exception:
            return None

    def getHeight(self):
        '''
        Gets the height.
        '''

        if self.useUiAutomator:
            return self.map['bounds'][1][1] - self.map['bounds'][0][1]
        else:
            try:
                return int(self.map[self.heightProperty])
            except:
                return 0

    def getWidth(self):
        '''
        Gets the width.
        '''

        if self.useUiAutomator:
            return self.map['bounds'][1][0] - self.map['bounds'][0][0]
        else:
            try:
                return int(self.map[self.widthProperty])
            except:
                return 0

    def getUniqueId(self):
        '''
        Gets the unique Id of this View.

        @see: L{ViewClient.__splitAttrs()} for a discussion on B{Unique Ids}
        '''

        try:
            return self.map['uniqueId']
        except:
            return None

    def getVisibility(self):
        '''
        Gets the View visibility
        '''

        try:
            if self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
                return VISIBLE
            elif self.map[GET_VISIBILITY_PROPERTY] == 'INVISIBLE':
                return INVISIBLE
            elif self.map[GET_VISIBILITY_PROPERTY] == 'GONE':
                return GONE
            else:
                return -2
        except:
            return -1

    def getX(self):
        '''
        Gets the View X coordinate
        '''

        return self.getXY()[0]

    def __getX(self):
        '''
        Gets the View X coordinate
        '''

        if DEBUG_COORDS:
            print("getX(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId()), file=sys.stderr)
        x = 0

        if self.useUiAutomator:
            x = self.map['bounds'][0][0]
        else:
            try:
                if GET_VISIBILITY_PROPERTY in self.map and self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
                    _x = int(self.map[self.leftProperty])
                    if DEBUG_COORDS: print("   getX: VISIBLE adding %d" % _x, file=sys.stderr)
                    x += _x
            except:
                warnings.warn("View %s has no '%s' property" % (self.getId(), self.leftProperty))

        if DEBUG_COORDS: print("   getX: returning %d" % (x), file=sys.stderr)
        return x

    def getY(self):
        '''
        Gets the View Y coordinate
        '''

        return self.getXY()[1]

    def __getY(self):
        '''
        Gets the View Y coordinate
        '''

        if DEBUG_COORDS:
            print("getY(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId()), file=sys.stderr)
        y = 0

        if self.useUiAutomator:
            y = self.map['bounds'][0][1]
        else:
            try:
                if GET_VISIBILITY_PROPERTY in self.map and self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
                    _y = int(self.map[self.topProperty])
                    if DEBUG_COORDS: print("   getY: VISIBLE adding %d" % _y, file=sys.stderr)
                    y += _y
            except:
                warnings.warn("View %s has no '%s' property" % (self.getId(), self.topProperty))

        if DEBUG_COORDS: print("   getY: returning %d" % (y), file=sys.stderr)
        return y

    def getXY(self, debug=False):
        '''
        Returns the I{screen} coordinates of this C{View}.

        WARNING: Don't call self.getX() or self.getY() inside this method
        or it will enter an infinite loop

        @return: The I{screen} coordinates of this C{View}
        '''

        if DEBUG_COORDS or debug:
            try:
                _id = self.getId()
            except:
                _id = "NO_ID"
            print("getXY(%s %s ## %s)" % (self.getClass(), _id, self.getUniqueId()), file=sys.stderr)

        x = self.__getX()
        y = self.__getY()
        if self.useUiAutomator:
            return (x, y)

        parent = self.parent
        if DEBUG_COORDS: print("   getXY: x=%s y=%s parent=%s" % (x, y, parent.getUniqueId() if parent else "None"),
                               file=sys.stderr)
        hx = 0
        ''' Hierarchy accumulated X '''
        hy = 0
        ''' Hierarchy accumulated Y '''

        if DEBUG_COORDS: print("   getXY: not using UiAutomator, calculating parent coordinates", file=sys.stderr)
        while parent != None:
            if DEBUG_COORDS: print("      getXY: parent: %s %s <<<<" % (parent.getClass(), parent.getId()),
                                   file=sys.stderr)
            if SKIP_CERTAIN_CLASSES_IN_GET_XY_ENABLED:
                if parent.getClass() in ['com.android.internal.widget.ActionBarView',
                                         'com.android.internal.widget.ActionBarContextView',
                                         'com.android.internal.view.menu.ActionMenuView',
                                         'com.android.internal.policy.impl.PhoneWindow$DecorView']:
                    if DEBUG_COORDS: print("   getXY: skipping %s %s (%d,%d)" % (
                        parent.getClass(), parent.getId(), parent.__getX(), parent.__getY()), file=sys.stderr)
                    parent = parent.parent
                    continue
            if DEBUG_COORDS: print("   getXY: parent=%s x=%d hx=%d y=%d hy=%d" % (parent.getId(), x, hx, y, hy),
                                   file=sys.stderr)
            hx += parent.__getX()
            hy += parent.__getY()
            parent = parent.parent

        (wvx, wvy) = self.__dumpWindowsInformation(debug=debug)
        if DEBUG_COORDS or debug:
            print("   getXY: wv=(%d, %d) (windows information)" % (wvx, wvy), file=sys.stderr)
        try:
            if self.windowId:
                fw = self.windows[self.windowId]
            else:
                fw = self.windows[self.currentFocus]
            if DEBUG_STATUSBAR:
                print("    getXY: focused window=", fw, file=sys.stderr)
                print("    getXY: deciding whether to consider statusbar offset because current focused windows is at",
                      (fw.wvx, fw.wvy), "parent", (fw.px, fw.py), file=sys.stderr)
        except KeyError:
            fw = None
        (sbw, sbh) = self.__obtainStatusBarDimensionsIfVisible()
        if DEBUG_COORDS or debug:
            print("   getXY: sb=(%d, %d) (statusbar dimensions)" % (sbw, sbh), file=sys.stderr)
        statusBarOffset = 0
        pwx = 0
        pwy = 0

        if fw:
            if DEBUG_COORDS:
                print("    getXY: focused window=", fw, "sb=", (sbw, sbh), file=sys.stderr)
            if fw.wvy <= sbh:  # it's very unlikely that fw.wvy < sbh, that is a window over the statusbar
                if DEBUG_STATUSBAR: print("        getXY: yes, considering offset=", sbh, file=sys.stderr)
                statusBarOffset = sbh
            else:
                if DEBUG_STATUSBAR: print("        getXY: no, ignoring statusbar offset fw.wvy=", fw.wvy, ">", sbh,
                                          file=sys.stderr)

            if fw.py == fw.wvy:
                if DEBUG_STATUSBAR: print("        getXY: but wait, fw.py == fw.wvy so we are adjusting by ",
                                          (fw.px, fw.py), file=sys.stderr)
                pwx = fw.px
                pwy = fw.py
            else:
                if DEBUG_STATUSBAR: print("    getXY: fw.py=%d <= fw.wvy=%d, no adjustment" % (fw.py, fw.wvy),
                                          file=sys.stderr)

        if DEBUG_COORDS or DEBUG_STATUSBAR or debug:
            print("   getXY: returning (%d, %d) ***" % (x + hx + wvx + pwx, y + hy + wvy - statusBarOffset + pwy),
                  file=sys.stderr)
            print("                     x=%d+%d+%d+%d" % (x, hx, wvx, pwx), file=sys.stderr)
            print("                     y=%d+%d+%d-%d+%d" % (y, hy, wvy, statusBarOffset, pwy), file=sys.stderr)
        return (x + hx + wvx + pwx, y + hy + wvy - statusBarOffset + pwy)

    def getCoords(self):
        '''
        Gets the coords of the View

        @return: A tuple containing the View's coordinates ((L, T), (R, B))
        '''

        if DEBUG_COORDS:
            print("getCoords(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId()), file=sys.stderr)

        (x, y) = self.getXY()
        w = self.getWidth()
        h = self.getHeight()
        return ((x, y), (x + w, y + h))

    def getPositionAndSize(self):
        '''
        Gets the position and size (X,Y, W, H)

        @return: A tuple containing the View's coordinates (X, Y, W, H)
        '''

        (x, y) = self.getXY()
        w = self.getWidth()
        h = self.getHeight()
        return (x, y, w, h)

    def getBounds(self):
        '''
        Gets the View bounds
        '''

        if isinstance(self, WindowHierarchyChild):
            return self.bounds
        if 'bounds' in self.map:
            return self.map['bounds']
        else:
            return self.getCoords()

    def getCenter(self):
        '''
        Gets the center coords of the View

        @author: U{Dean Morin <https://github.com/deanmorin>}
        '''

        (left, top), (right, bottom) = self.getCoords()
        x = left + (right - left) / 2
        y = top + (bottom - top) / 2
        return (x, y)

    def __obtainStatusBarDimensionsIfVisible(self):
        sbw = 0
        sbh = 0
        for winId in self.windows:
            w = self.windows[winId]
            if DEBUG_COORDS: print("      __obtainStatusBarDimensionsIfVisible: w=", w, "   w.activity=", w.activity,
                                   "%%%", file=sys.stderr)
            if w.activity == 'StatusBar':
                if w.wvy == 0 and w.visibility == 0:
                    if DEBUG_COORDS: print("      __obtainStatusBarDimensionsIfVisible: statusBar=", (w.wvw, w.wvh),
                                           file=sys.stderr)
                    sbw = w.wvw
                    sbh = w.wvh
                break

        return (sbw, sbh)

    def __obtainVxVy(self, m):
        return obtainVxVy(m)

    def __obtainVwVh(self, m):
        return obtainVwVh(m)

    def __obtainPxPy(self, m):
        return obtainPxPy(m)

    def __dumpWindowsInformation(self, debug=False):
        self.windows = {}
        self.currentFocus = None
        dww = self.device.shell('dumpsys window windows')
        if DEBUG_WINDOWS or debug: print(dww, file=sys.stderr)
        lines = dww.splitlines()
        widRE = re.compile('^ *Window #%s Window\{%s (u\d+ )?%s?.*\}:' %
                           (_nd('num'), _nh('winId'), _ns('activity', greedy=True)))
        currentFocusRE = re.compile('^  mCurrentFocus=Window\{%s .*' % _nh('winId'))
        viewVisibilityRE = re.compile(' mViewVisibility=0x%s ' % _nh('visibility'))
        # This is for 4.0.4 API-15
        containingFrameRE = re.compile('^   *mContainingFrame=\[%s,%s\]\[%s,%s\] mParentFrame=\[%s,%s\]\[%s,%s\]' %
                                       (_nd('cx'), _nd('cy'), _nd('cw'), _nd('ch'), _nd('px'), _nd('py'), _nd('pw'),
                                        _nd('ph')))
        contentFrameRE = re.compile('^   *mContentFrame=\[%s,%s\]\[%s,%s\] mVisibleFrame=\[%s,%s\]\[%s,%s\]' %
                                    (_nd('x'), _nd('y'), _nd('w'), _nd('h'), _nd('vx'), _nd('vy'), _nd('vx1'),
                                     _nd('vy1')))
        # This is for 4.1 API-16
        framesRE = re.compile('^   *Frames: containing=\[%s,%s\]\[%s,%s\] parent=\[%s,%s\]\[%s,%s\]' %
                              (_nd('cx'), _nd('cy'), _nd('cw'), _nd('ch'), _nd('px'), _nd('py'), _nd('pw'), _nd('ph')))
        contentRE = re.compile('^     *content=\[%s,%s\]\[%s,%s\] visible=\[%s,%s\]\[%s,%s\]' %
                               (_nd('x'), _nd('y'), _nd('w'), _nd('h'), _nd('vx'), _nd('vy'), _nd('vx1'), _nd('vy1')))
        policyVisibilityRE = re.compile('mPolicyVisibility=%s ' % _ns('policyVisibility', greedy=True))

        for l in range(len(lines)):
            m = widRE.search(lines[l])
            if m:
                num = int(m.group('num'))
                winId = m.group('winId')
                activity = m.group('activity')
                wvx = 0
                wvy = 0
                wvw = 0
                wvh = 0
                px = 0
                py = 0
                visibility = -1
                policyVisibility = 0x0

                for l2 in range(l + 1, len(lines)):
                    m = widRE.search(lines[l2])
                    if m:
                        l += (l2 - 1)
                        break
                    m = viewVisibilityRE.search(lines[l2])
                    if m:
                        visibility = int(m.group('visibility'))
                        if DEBUG_COORDS: print("__dumpWindowsInformation: visibility=", visibility, file=sys.stderr)
                    if self.build[VERSION_SDK_PROPERTY] >= 17:
                        m = framesRE.search(lines[l2])
                        if m:
                            px, py = obtainPxPy(m)
                            m = contentRE.search(lines[l2 + 2])
                            if m:
                                wvx, wvy = obtainVxVy(m)
                                wvw, wvh = obtainVwVh(m)
                    elif self.build[VERSION_SDK_PROPERTY] >= 16:
                        m = framesRE.search(lines[l2])
                        if m:
                            px, py = self.__obtainPxPy(m)
                            m = contentRE.search(lines[l2 + 1])
                            if m:
                                # FIXME: the information provided by 'dumpsys window windows' in 4.2.1 (API 16)
                                # when there's a system dialog may not be correct and causes the View coordinates
                                # be offset by this amount, see
                                # https://github.com/dtmilano/AndroidViewClient/issues/29
                                wvx, wvy = self.__obtainVxVy(m)
                                wvw, wvh = self.__obtainVwVh(m)
                    elif self.build[VERSION_SDK_PROPERTY] == 15:
                        m = containingFrameRE.search(lines[l2])
                        if m:
                            px, py = self.__obtainPxPy(m)
                            m = contentFrameRE.search(lines[l2 + 1])
                            if m:
                                wvx, wvy = self.__obtainVxVy(m)
                                wvw, wvh = self.__obtainVwVh(m)
                    elif self.build[VERSION_SDK_PROPERTY] == 10:
                        m = containingFrameRE.search(lines[l2])
                        if m:
                            px, py = self.__obtainPxPy(m)
                            m = contentFrameRE.search(lines[l2 + 1])
                            if m:
                                wvx, wvy = self.__obtainVxVy(m)
                                wvw, wvh = self.__obtainVwVh(m)
                    else:
                        warnings.warn("Unsupported Android version %d" % self.build[VERSION_SDK_PROPERTY])

                    # print >> sys.stderr, "Searching policyVisibility in", lines[l2]
                    m = policyVisibilityRE.search(lines[l2])
                    if m:
                        policyVisibility = 0x0 if m.group('policyVisibility') == 'true' else 0x8

                self.windows[winId] = Window(num, winId, activity, wvx, wvy, wvw, wvh, px, py,
                                             visibility + policyVisibility)
            else:
                m = currentFocusRE.search(lines[l])
                if m:
                    self.currentFocus = m.group('winId')

        if self.windowId and self.windowId in self.windows and self.windows[self.windowId].visibility == 0:
            w = self.windows[self.windowId]
            return (w.wvx, w.wvy)
        elif self.currentFocus in self.windows and self.windows[self.currentFocus].visibility == 0:
            if DEBUG_COORDS or debug:
                print("__dumpWindowsInformation: focus=", self.currentFocus, file=sys.stderr)
                print("__dumpWindowsInformation:", self.windows[self.currentFocus], file=sys.stderr)
            w = self.windows[self.currentFocus]
            return (w.wvx, w.wvy)
        else:
            if DEBUG_COORDS: print("__dumpWindowsInformation: (0,0)", file=sys.stderr)
            return (0, 0)

    def touch(self, eventType=adbclient.DOWN_AND_UP, deltaX=0, deltaY=0):
        '''
        Touches the center of this C{View}. The touch can be displaced from the center by
        using C{deltaX} and C{deltaY} values.

        @param eventType: The event type
        @type eventType: L{adbclient.DOWN}, L{adbclient.UP} or L{adbclient.DOWN_AND_UP}
        @param deltaX: Displacement from center (X axis)
        @type deltaX: int
        @param deltaY: Displacement from center (Y axis)
        @type deltaY: int
        '''

        (x, y) = self.getCenter()
        if deltaX:
            x += deltaX
        if deltaY:
            y += deltaY
        if DEBUG_TOUCH:
            print("should touch @ (%d, %d)" % (x, y), file=sys.stderr)
        if VIEW_CLIENT_TOUCH_WORKAROUND_ENABLED and eventType == adbclient.DOWN_AND_UP:
            if WARNINGS:
                print("ViewClient: touch workaround enabled", file=sys.stderr)
            self.device.touch(x, y, eventType=adbclient.DOWN)
            time.sleep(50 / 1000.0)
            self.device.touch(x + 10, y + 10, eventType=adbclient.UP)
        else:
            if self.uiAutomatorHelper:
                selector = self.obtainSelectorForView()
                if DEBUG_UI_AUTOMATOR_HELPER:
                    print('using selector="%s"' % selector, file=sys.stderr)
                if selector:
                    try:
                        object_ref = self.uiAutomatorHelper.findObject(by_selector=selector)
                        if DEBUG_UI_AUTOMATOR_HELPER:
                            print("id=%d" % object_ref.oid, file=sys.stderr)
                            print("ignoring click delta to click View as UiObject", file=sys.stderr)
                        self.uiAutomatorHelper.click(oid=object_ref.oid)
                    except RuntimeError as e:
                        print(e.message, file=sys.stderr)
                        print("UiObject click failed, using co-ordinates", file=sys.stderr)
                        self.uiAutomatorHelper.click(x=x, y=y)
                else:
                    # FIXME:
                    # The View has no CD, TEXT or ID so we cannot use it in a selector to findObject()
                    # We should try content description, text, and perhaps other properties before surrendering.
                    # For now, tet's fall back to click(x, y)
                    self.uiAutomatorHelper.click(x=x, y=y)
            else:
                self.device.touch(x, y, eventType=eventType)

    def escapeSelectorChars(self, selector):
        return selector.replace('@', '\\@').replace(',', '\\,')

    def obtainSelectorForView(self):
        selector = ''
        if self.getContentDescription():
            selector += 'desc@' + self.escapeSelectorChars(self.getContentDescription())
        if self.getText():
            if selector:
                selector += ','
            selector += 'text@' + self.escapeSelectorChars(self.getText())
        if self.getId():
            if selector:
                selector += ','
            selector += 'res@' + self.escapeSelectorChars(self.getId())
        return selector

    def longTouch(self, duration=2000):
        '''
        Long touches this C{View}

        @param duration: duration in ms
        '''

        if self.uiAutomatorHelper:
            # FIXME: is `selector` a `bySlector`?
            object_ref = self.uiAutomatorHelper.findObject(by_selector=self.obtainSelectorForView())
            if DEBUG_UI_AUTOMATOR_HELPER:
                print("♦️ object_ref=%s" % object_ref, file=sys.stderr)
            self.uiAutomatorHelper.longClick(oid=object_ref.oid)
        else:
            # FIXME: get orientation
            (x, y) = self.getCenter()
            self.device.longTouch(x, y, duration, orientation=-1)


    def allPossibleNamesWithColon(self, name):
        l = []
        for _ in range(name.count("_")):
            name = name.replace("_", ":", 1)
            l.append(name)
        return l

    def intersection(self, l1, l2):
        return list(set(l1) & set(l2))

    def containsPoint(self, xxx_todo_changeme):
        (x, y) = xxx_todo_changeme
        (X, Y, W, H) = self.getPositionAndSize()
        return (((x >= X) and (x <= (X + W)) and ((y >= Y) and (y <= (Y + H)))))

    def add(self, child):
        '''
        Adds a child

        @type child: View
        @param child: The child to add
        '''
        child.parent = self
        self.children.append(child)

    def isClickable(self):
        return self.__getattr__('isClickable')()

    def isFocused(self):
        '''
        Gets the focused value

        @return: the focused value. If the property cannot be found returns C{False}
        '''

        try:
            return True if self.map[self.isFocusedProperty].lower() == 'true' else False
        except Exception:
            return False

    @staticmethod
    def variableNameFromId(obj):
        var = None
        _id = obj.resource_id
        if callable(_id):
            _id = _id()
        if _id:
            var = _id.replace('.', '_').replace(':', '___').replace('/', '_')
        else:
            _id = obj.unique_id
            if callable(_id):
                _id = _id()
            m = ID_RE.match(_id)
            if m:
                var = m.group(1)
                if m.group(3):
                    var += m.group(3)
                if re.match(r'^\d', var):
                    var = 'id_' + var
        return var

    def setTarget(self, target):
        self.target = target

    def isTarget(self):
        return self.target

    def writeImageToFile(self, filename, _format="PNG"):
        '''
        Write the View image to the specified filename in the specified format.

        @type filename: str
        @param filename: Absolute path and optional filename receiving the image. If this points to
                         a directory, then the filename is determined by this View unique ID and
                         format extension.
        @type _format: str
        @param _format: Image format (default format is PNG)
        '''

        filename = self.device.substituteDeviceTemplate(filename)
        if not os.path.isabs(filename):
            raise ValueError("writeImageToFile expects an absolute path (fielname='%s')" % filename)
        if os.path.isdir(filename):
            filename = os.path.join(filename, View.variableNameFromId(self) + '.' + _format.lower())
        if DEBUG:
            print("writeImageToFile: saving image to '%s' in %s format" % (filename, _format), file=sys.stderr)
        # self.device.takeSnapshot().getSubImage(self.getPositionAndSize()).writeToFile(filename, _format)
        # crop:
        # im.crop(box) ⇒ image
        # Returns a copy of a rectangular region from the current image.
        # The box is a 4-tuple defining the left, upper, right, and lower pixel coordinate.
        ((l, t), (r, b)) = self.getCoords()
        box = (l, t, r, b)
        if DEBUG:
            print("writeImageToFile: cropping", box, "    reconnect=", self.device.reconnect, file=sys.stderr)
        if box == (0, 0, 0, 0):
            return
        if self.uiAutomatorHelper:
            if DEBUG_UI_AUTOMATOR_HELPER:
                print("Taking screenshot using UiAutomatorHelper", file=sys.stderr)
            received = self.uiAutomatorHelper.takeScreenshot()
            stream = io.StringIO(received)
            try:
                from pillow import Image
                image = Image.open(stream)
            except ImportError as ex:
                # FIXME: this method should be global
                self.pilNotInstalledWarning()
                sys.exit(1)
            except IOError as ex:
                print(ex, file=sys.stderr)
                print(repr(stream))
                sys.exit(1)
        else:
            image = self.device.takeSnapshot(reconnect=self.device.reconnect)
        image.crop(box).save(filename, _format)

    def __smallStr__(self):
        # 2to3
        # __str = str("View[", 'utf-8', 'replace')
        __str = "View["
        if "class" in self.map:
            __str += " class=" + self.map['class']
        __str += " id=%s" % self.getId()
        __str += " ]   parent="
        if self.parent and "class" in self.parent.map:
            __str += "%s" % self.parent.map["class"]
        else:
            __str += "None"

        return __str

    def __tinyStr__(self):
        # 2to3
        # __str = str("View[", 'utf-8', 'replace')
        __str = "View["
        if "class" in self.map:
            __str += " class=" + re.sub('.*\.', '', self.map['class'])
        __str += " id=%s" % self.getId()
        __str += " ]"

        return __str

    def __microStr__(self):
        # 2to3
        # __str = str('', 'utf-8', 'replace')
        __str = ''
        if "class" in self.map:
            __str += re.sub('.*\.', '', self.map['class'])
        _id = self.getId().replace('id/no_id/', '-')
        __str += _id
        ((L, T), (R, B)) = self.getCoords()
        __str += '@%04d%04d%04d%04d' % (L, T, R, B)
        __str += ''

        return __str

    def __str__(self):
        if type(self) == WindowHierarchyChild:
            raise RuntimeError('⛔️ This method should not be invoked with a WindowHierarchyChild')

        if type(self) == WindowHierarchy:
            return json.dumps(self.to_dict())

        __str = ''
        try:
            __str = "View["
            if "class" in self.map:
                __str += " class=" + self.map["class"].__str__() + " "
            for a in self.map:
                __str += a + "="
                # decode() works only on python's 8-bit strings
                if isinstance(self.map[a], str):
                    __str += self.map[a]
                else:
                    if sys.version_info[0] < 3:
                        if type(self.map[a]) == unicode:
                            __str += self.map[a].encode('utf-8', errors='replace').decode('utf-8')
                        else:
                            __str += str(self.map[a])
                    else:
                        __str += str(self.map[a]).encode('utf-8', errors='replace').decode('utf-8')
                __str += " "
            __str += "]   parent="
            if self.parent:
                if "class" in self.parent.map:
                    __str += "%s" % self.parent.map["class"]
                else:
                    __str += self.parent.getId().__str__()
            else:
                __str += "None"
        except AttributeError as ex:
            print('⛔️ self=%s: %s' % (self.__class__.__name__, ex), file=sys.stderr)

        return __str


class TextView(View):
    '''
    TextView class.
    '''

    @classmethod
    def getAndroidClassName(cls):
        return 'android.widget.TextView'


class EditText(TextView):
    '''
    EditText class.
    '''

    @classmethod
    def getAndroidClassName(cls):
        return 'android.widget.EditText'

    def type(self, text, alreadyTouched=False):
        if not text:
            return
        if not alreadyTouched:
            self.touch()
        time.sleep(0.5)
        self.device.type(text)
        time.sleep(0.5)

    def setText(self, text):
        """
        This function makes sure that any previously entered text is deleted before
        setting the value of the field.
        """
        if self.text() == text:
            return
        self.touch()
        maxSize = len(self.text()) + 1
        self.device.press('KEYCODE_DEL', adbclient.DOWN_AND_UP, repeat=maxSize)
        self.device.press('KEYCODE_FORWARD_DEL', adbclient.DOWN_AND_UP, repeat=maxSize)
        self.type(text, alreadyTouched=True)

    def backspace(self):
        self.touch()
        time.sleep(1)
        self.device.press('KEYCODE_DEL', adbclient.DOWN_AND_UP)


class UiDevice():
    '''
    Provides access to state information about the device. You can also use this class to simulate
    user actions on the device, such as pressing the d-pad or pressing the Home and Menu buttons.
    '''

    def __init__(self, vc):
        self.vc = vc
        self.device = self.vc.device

    def openNotification(self):
        '''
        Opens the notification shade.
        '''

        # the tablet has a different Notification/Quick Settings bar depending on x
        w13 = self.device.display['width'] / 3
        s = (w13, 0)
        e = (w13, self.device.display['height'] / 2)
        self.device.drag(s, e, 500, 20, -1)
        self.vc.sleep(1)
        self.vc.dump(-1)

    def openQuickSettings(self):
        '''
        Opens the Quick Settings shade.
        '''

        # the tablet has a different Notification/Quick Settings bar depending on x
        w23 = 2 * self.device.display['width'] / 3
        s = (w23, 0)
        e = (w23, self.device.display['height'] / 2)
        self.device.drag(s, e, 500, 20, -1)
        self.vc.sleep(1)
        if self.vc.getSdkVersion() >= 20:
            self.device.drag(s, e, 500, 20, -1)
            self.vc.sleep(1)
        self.vc.dump(-1)

    def openQuickSettingsSettings(self):
        '''
        Opens the Quick Settings shade and then tries to open Settings from there.
        '''

        STATUS_BAR_SETTINGS_SETTINGS_BUTTON = [
            "Settings", "Cài đặt", "Instellingen", "Կարգավորումներ", "设置", "Nastavitve", "සැකසීම්", "Ayarlar",
            "Setelan", "Настройки", "تنظیمات", "Mga Setting", "Тохиргоо", "Configuració", "Setări", "Налады",
            "Einstellungen", "პარამეტრები", "सेटिङहरू", "Կարգավորումներ", "Nustatymai", "Beállítások", "設定",
            "सेटिंग", "Настройки", "Inställningar", "設定", "ການຕັ້ງຄ່າ", "Configurações", "Tetapan", "설정",
            "ការ​កំណត់", "Ajustes", "הגדרות", "Ustawienia", "Nastavení", "Ρυθμίσεις", "Тохиргоо", "Ayarlar",
            "Indstillinger", "Налаштування", "Mipangilio", "Izilungiselelo", "設定", "Nastavenia", "Paramètres",
            "ቅንብሮች", "การตั้งค่า", "Seaded", "Iestatījumi", "Innstillinger", "Подешавања", "الإعدادات", "සැකසීම්",
            "Definições", "Configuración", "პარამეტრები", "Postavke", "Ayarlar", "Impostazioni", "Asetukset",
            "Instellings", "Seaded", "ការ​កំណត់", "सेटिङहरू", "Tetapan"
        ]

        self.openQuickSettings()

        # this works on API >= 20
        found = False
        for s in STATUS_BAR_SETTINGS_SETTINGS_BUTTON:
            if DEBUG:
                print("finding view with cd=", type(s), file=sys.stderr)
            view = self.vc.findViewWithContentDescription('''{0}'''.format(s))
            if view:
                found = True
                view.touch()
                break

        if not found:
            # for previous APIs, let's find the text
            for s in STATUS_BAR_SETTINGS_SETTINGS_BUTTON:
                if DEBUG:
                    print("s=", type(s), file=sys.stderr)
                    try:
                        print("finding view with text=", '''{0}'''.format(s), file=sys.stderr)
                    except:
                        pass
                view = self.vc.findViewWithText(s)
                if view:
                    found = True
                    view.touch()
                    break

        if not found:
            raise ViewNotFoundException("content-description", "'Settings' or text 'Settings'", "ROOT")

        self.vc.sleep(1)
        self.vc.dump(window=-1)

    def changeLanguage(self, languageTo):
        LANGUAGE_SETTINGS = {
            "en": "Language & input",
            "af": "Taal en invoer",
            "am": "ቋንቋ እና ግቤት",
            "ar": "اللغة والإدخال",
            "az": "Dil və daxiletmə",
            "az-rAZ": "Dil və daxiletmə",
            "be": "Мова і ўвод",
            "bg": "Език и въвеждане",
            "ca": "Idioma i introducció de text",
            "cs": "Jazyk a zadávání",
            "da": "Sprog og input",
            "de": "Sprache & Eingabe",
            "el": "Γλώσσα και εισαγωγή",
            "en-rGB": "Language & input",
            "en-rIN": "Language & input",
            "es": "Idioma e introducción de texto",
            "es-rUS": "Teclado e idioma",
            "et": "Keeled ja sisestamine",
            "et-rEE": "Keeled ja sisestamine",
            "fa": "زبان و ورود اطلاعات",
            "fi": "Kieli ja syöttötapa",
            "fr": "Langue et saisie",
            "fr-rCA": "Langue et saisie",
            "hi": "भाषा और अक्षर",
            "hr": "Jezik i ulaz",
            "hu": "Nyelv és bevitel",
            "hy": "Լեզվի & ներմուծում",
            "hy-rAM": "Լեզու և ներմուծում",
            "in": "Bahasa & masukan",
            "it": "Lingua e immissione",
            "iw": "שפה וקלט",
            "ja": "言語と入力",
            "ka": "ენისა და შეყვანის პარამეტრები",
            "ka-rGE": "ენისა და შეყვანის პარამეტრები",
            "km": "ភាសា & ការ​បញ្ចូល",
            "km-rKH": "ភាសា & ការ​បញ្ចូល",
            "ko": "언어 및 키보드",
            "lo": "ພາສາ & ການປ້ອນຂໍ້ມູນ",
            "lo-rLA": "ພາສາ & ການປ້ອນຂໍ້ມູນ",
            "lt": "Kalba ir įvestis",
            "lv": "Valodas ievade",
            "mn": "Хэл & оруулах",
            "mn-rMN": "Хэл & оруулах",
            "ms": "Bahasa & input",
            "ms-rMY": "Bahasa & input",
            "nb": "Språk og inndata",
            "ne": "भाषा र इनपुट",
            "ne-rNP": "भाषा र इनपुट",
            "nl": "Taal en invoer",
            "pl": "Język, klawiatura, głos",
            "pt": "Idioma e entrada",
            "pt-rPT": "Idioma e entrada",
            "ro": "Limbă și introducere de text",
            "ru": "Язык и ввод",
            "si": "භාෂාව සහ ආදානය",
            "si-rLK": "භාෂාව සහ ආදානය",
            "sk": "Jazyk & vstup",
            "sl": "Jezik in vnos",
            "sr": "Језик и унос",
            "sv": "Språk och inmatning",
            "sw": "Lugha, Kibodi na Sauti",
            "th": "ภาษาและการป้อนข้อมูล",
            "tl": "Wika at input",
            "tr": "Dil ve giriş",
            "uk": "Мова та введення",
            "vi": "Ngôn ngữ & phương thức nhập",
            "zh-rCN": "语言和输入法",
            "zh-rHK": "語言與輸入裝置",
            "zh-rTW": "語言與輸入設定",
            "zu": "Ulimi & ukufakwa",
        }

        PHONE_LANGUAGE = {
            "en": "Language",
            "af": "Taal",
            "am": "ቋንቋ",
            "ar": "اللغة",
            "az": "Dil",
            "az-rAZ": "Dil",
            "be": "Мова",
            "bg": "Език",
            "ca": "Idioma",
            "cs": "Jazyk",
            "da": "Sprog",
            "de": "Sprache",
            "el": "Γλώσσα",
            "en-rGB": "Language",
            "en-rIN": "Language",
            "es": "Idioma",
            "es-rUS": "Idioma",
            "et": "Keel",
            "et-rEE": "Keel",
            "fa": "زبان",
            "fi": "Kieli",
            "fr": "Langue",
            "fr-rCA": "Langue",
            "hi": "भाषा",
            "hr": "Jezik",
            "hu": "Nyelv",
            "hy": "Lեզուն",
            "hy-rAM": "Lեզուն",
            "in": "Bahasa",
            "it": "Lingua",
            "iw": "שפה",
            "ja": "言語",
            "ka": "ენა",
            "ka-rGE": "ენა",
            "km": "ភាសា",
            "km-rKH": "ភាសា",
            "ko": "언어",
            "lo": "ພາສາ",
            "lo-rLA": "ພາສາ",
            "lt": "Kalba",
            "lv": "Valoda",
            "mn": "Хэл",
            "mn-rMN": "Хэл",
            "ms": "Bahasa",
            "ms-rMY": "Bahasa",
            "nb": "Språk",
            "ne": "भाषा",
            "nl": "Taal",
            "pl": "Język",
            "pt": "Idioma",
            "pt-rPT": "Idioma",
            "ro": "Limba",
            "ru": "Язык",
            "si": "භාෂාව",
            "si-rLK": "භාෂාව",
            "sk": "Jazyk",
            "sl": "Jezik",
            "sr": "Језик",
            "sv": "Språk",
            "sw": "Lugha",
            "th": "ภาษา",
            "tl": "Wika",
            "tr": "Dil",
            "uk": "Мова",
            "vi": "Ngôn ngữ",
            "zh-rCN": "语言",
            "zh-rHK": "語言",
            "zh-rTW": "語言",
            "zu": "Ulimi",
        }

        LANGUAGES = {
            "en": "English (United States)",
            "es-rUS": "Español (Estados Unidos)",
            "af": "Afrikaans",  # Afrikaans
            "af-rNA": "Afrikaans (Namibië)",  # Afrikaans (Namibia)
            "af-rZA": "Afrikaans (Suid-Afrika)",  # Afrikaans (South Africa)
            "agq": "Aghem",  # Aghem
            "agq-rCM": "Aghem (Kàmàlûŋ)",  # Aghem (Cameroon)
            "ak": "Akan",  # Akan
            "ak-rGH": "Akan (Gaana)",  # Akan (Ghana)
            "am": "አማርኛ",  # Amharic
            "am-rET": "አማርኛ (ኢትዮጵያ)",  # Amharic (Ethiopia)
            "ar": "العربية",  # Arabic
            "ar_001": "العربية (العالم)",  # Arabic (World)
            "ar-rAE": "العربية (الإمارات العربية المتحدة)",  # Arabic (United Arab Emirates)
            "ar-rBH": "العربية (البحرين)",  # Arabic (Bahrain)
            "ar-rDJ": "العربية (جيبوتي)",  # Arabic (Djibouti)
            "ar-rDZ": "العربية (الجزائر)",  # Arabic (Algeria)
            "ar-rEG": "العربية (مصر)",  # Arabic (Egypt)
            "ar-rEH": "العربية (الصحراء الغربية)",  # Arabic (Western Sahara)
            "ar-rER": "العربية (أريتريا)",  # Arabic (Eritrea)
            "ar-rIL": "العربية (إسرائيل)",  # Arabic (Israel)
            "ar-rIQ": "العربية (العراق)",  # Arabic (Iraq)
            "ar-rJO": "العربية (الأردن)",  # Arabic (Jordan)
            "ar-rKM": "العربية (جزر القمر)",  # Arabic (Comoros)
            "ar-rKW": "العربية (الكويت)",  # Arabic (Kuwait)
            "ar-rLB": "العربية (لبنان)",  # Arabic (Lebanon)
            "ar-rLY": "العربية (ليبيا)",  # Arabic (Libya)
            "ar-rMA": "العربية (المغرب)",  # Arabic (Morocco)
            "ar-rMR": "العربية (موريتانيا)",  # Arabic (Mauritania)
            "ar-rOM": "العربية (عُمان)",  # Arabic (Oman)
            "ar-rPS": "العربية (فلسطين)",  # Arabic (Palestine)
            "ar-rQA": "العربية (قطر)",  # Arabic (Qatar)
            "ar-rSA": "العربية (المملكة العربية السعودية)",  # Arabic (Saudi Arabia)
            "ar-rSD": "العربية (السودان)",  # Arabic (Sudan)
            "ar-rSO": "العربية (الصومال)",  # Arabic (Somalia)
            "ar-rSY": "العربية (سوريا)",  # Arabic (Syria)
            "ar-rTD": "العربية (تشاد)",  # Arabic (Chad)
            "ar-rTN": "العربية (تونس)",  # Arabic (Tunisia)
            "ar-rYE": "العربية (اليمن)",  # Arabic (Yemen)
            "as": "অসমীয়া",  # Assamese
            "as-rIN": "অসমীয়া (ভাৰত)",  # Assamese (India)
            "asa": "Kipare",  # Asu
            "asa-rTZ": "Kipare (Tadhania)",  # Asu (Tanzania)
            "az": "Azərbaycanca",  # Azerbaijani
            "az-rCYRL": "Азәрбајҹан (CYRL)",  # Azerbaijani (CYRL)
            "az-rCYRL_AZ": "Азәрбајҹан (Азәрбајҹан,AZ)",  # Azerbaijani (Azerbaijan,AZ)
            "az-rLATN": "Azərbaycanca (LATN)",  # Azerbaijani (LATN)
            "az-rLATN_AZ": "Azərbaycanca (Azərbaycan,AZ)",  # Azerbaijani (Azerbaijan,AZ)
            "bas": "Ɓàsàa",  # Basaa
            "bas-rCM": "Ɓàsàa (Kàmɛ̀rûn)",  # Basaa (Cameroon)
            "be": "беларуская",  # Belarusian
            "be-rBY": "беларуская (Беларусь)",  # Belarusian (Belarus)
            "bem": "Ichibemba",  # Bemba
            "bem-rZM": "Ichibemba (Zambia)",  # Bemba (Zambia)
            "bez": "Hibena",  # Bena
            "bez-rTZ": "Hibena (Hutanzania)",  # Bena (Tanzania)
            "bg": "български",  # Bulgarian
            "bg-rBG": "български (България)",  # Bulgarian (Bulgaria)
            "bm": "Bamanakan",  # Bambara
            "bm-rML": "Bamanakan (Mali)",  # Bambara (Mali)
            "bn": "বাংলা",  # Bengali
            "bn-rBD": "বাংলা (বাংলাদেশ)",  # Bengali (Bangladesh)
            "bn-rIN": "বাংলা (ভারত)",  # Bengali (India)
            "bo": "པོད་སྐད་",  # Tibetan
            "bo-rCN": "པོད་སྐད་ (རྒྱ་ནག)",  # Tibetan (China)
            "bo-rIN": "པོད་སྐད་ (རྒྱ་གར་)",  # Tibetan (India)
            "br": "Brezhoneg",  # Breton
            "br-rFR": "Brezhoneg (Frañs)",  # Breton (France)
            "brx": "बड़ो",  # Bodo
            "brx-rIN": "बड़ो (भारत)",  # Bodo (India)
            "bs": "Bosanski",  # Bosnian
            "bs-rCYRL": "босански (CYRL)",  # Bosnian (CYRL)
            "bs-rCYRL_BA": "босански (Босна и Херцеговина,BA)",  # Bosnian (Bosnia and Herzegovina,BA)
            "bs-rLATN": "Bosanski (LATN)",  # Bosnian (LATN)
            "bs-rLATN_BA": "Bosanski (Bosna i Hercegovina,BA)",  # Bosnian (Bosnia and Herzegovina,BA)
            "ca": "Català",  # Catalan
            "ca-rAD": "Català (Andorra)",  # Catalan (Andorra)
            "ca-rES": "Català (Espanya)",  # Catalan (Spain)
            "cgg": "Rukiga",  # Chiga
            "cgg-rUG": "Rukiga (Uganda)",  # Chiga (Uganda)
            "chr": "ᏣᎳᎩ",  # Cherokee
            "chr-rUS": "ᏣᎳᎩ (ᎠᎹᏰᏟ)",  # Cherokee (United States)
            "cs": "čeština",  # Czech
            "cs-rCZ": "čeština (Česká republika)",  # Czech (Czech Republic)
            "cy": "Cymraeg",  # Welsh
            "cy-rGB": "Cymraeg (y Deyrnas Unedig)",  # Welsh (United Kingdom)
            "da": "Dansk",  # Danish
            "da-rDK": "Dansk (Danmark)",  # Danish (Denmark)
            "dav": "Kitaita",  # Taita
            "dav-rKE": "Kitaita (Kenya)",  # Taita (Kenya)
            "de": "Deutsch",  # German
            "de-rAT": "Deutsch (Österreich)",  # German (Austria)
            "de-rBE": "Deutsch (Belgien)",  # German (Belgium)
            "de-rCH": "Deutsch (Schweiz)",  # German (Switzerland)
            "de-rDE": "Deutsch (Deutschland)",  # German (Germany)
            "de-rLI": "Deutsch (Liechtenstein)",  # German (Liechtenstein)
            "de-rLU": "Deutsch (Luxemburg)",  # German (Luxembourg)
            "dje": "Zarmaciine",  # Zarma
            "dje-rNE": "Zarmaciine (Nižer)",  # Zarma (Niger)
            "dua": "Duálá",  # Duala
            "dua-rCM": "Duálá (Cameroun)",  # Duala (Cameroon)
            "dyo": "Joola",  # Jola-Fonyi
            "dyo-rSN": "Joola (Senegal)",  # Jola-Fonyi (Senegal)
            "dz": "རྫོང་ཁ",  # Dzongkha
            "dz-rBT": "རྫོང་ཁ (འབྲུག)",  # Dzongkha (Bhutan)
            "ebu": "Kĩembu",  # Embu
            "ebu-rKE": "Kĩembu (Kenya)",  # Embu (Kenya)
            "ee": "Eʋegbe",  # Ewe
            "ee-rGH": "Eʋegbe (Ghana nutome)",  # Ewe (Ghana)
            "ee-rTG": "Eʋegbe (Togo nutome)",  # Ewe (Togo)
            "el": "Ελληνικά",  # Greek
            "el-rCY": "Ελληνικά (Κύπρος)",  # Greek (Cyprus)
            "el-rGR": "Ελληνικά (Ελλάδα)",  # Greek (Greece)
            "en": "English",  # English
            "en_150": "English (Europe)",  # English (Europe)
            "en-rAG": "English (Antigua and Barbuda)",  # English (Antigua and Barbuda)
            "en-rAS": "English (American Samoa)",  # English (American Samoa)
            "en-rAU": "English (Australia)",  # English (Australia)
            "en-rBB": "English (Barbados)",  # English (Barbados)
            "en-rBE": "English (Belgium)",  # English (Belgium)
            "en-rBM": "English (Bermuda)",  # English (Bermuda)
            "en-rBS": "English (Bahamas)",  # English (Bahamas)
            "en-rBW": "English (Botswana)",  # English (Botswana)
            "en-rBZ": "English (Belize)",  # English (Belize)
            "en-rCA": "English (Canada)",  # English (Canada)
            "en-rCM": "English (Cameroon)",  # English (Cameroon)
            "en-rDM": "English (Dominica)",  # English (Dominica)
            "en-rFJ": "English (Fiji)",  # English (Fiji)
            "en-rFM": "English (Micronesia)",  # English (Micronesia)
            "en-rGB": "English (United Kingdom)",  # English (United Kingdom)
            "en-rGD": "English (Grenada)",  # English (Grenada)
            "en-rGG": "English (Guernsey)",  # English (Guernsey)
            "en-rGH": "English (Ghana)",  # English (Ghana)
            "en-rGI": "English (Gibraltar)",  # English (Gibraltar)
            "en-rGM": "English (Gambia)",  # English (Gambia)
            "en-rGU": "English (Guam)",  # English (Guam)
            "en-rGY": "English (Guyana)",  # English (Guyana)
            "en-rHK": "English (Hong Kong)",  # English (Hong Kong)
            "en-rIE": "English (Ireland)",  # English (Ireland)
            "en-rIM": "English (Isle of Man)",  # English (Isle of Man)
            "en-rIN": "English (India)",  # English (India)
            "en-rJE": "English (Jersey)",  # English (Jersey)
            "en-rJM": "English (Jamaica)",  # English (Jamaica)
            "en-rKE": "English (Kenya)",  # English (Kenya)
            "en-rKI": "English (Kiribati)",  # English (Kiribati)
            "en-rKN": "English (Saint Kitts and Nevis)",  # English (Saint Kitts and Nevis)
            "en-rKY": "English (Cayman Islands)",  # English (Cayman Islands)
            "en-rLC": "English (Saint Lucia)",  # English (Saint Lucia)
            "en-rLR": "English (Liberia)",  # English (Liberia)
            "en-rLS": "English (Lesotho)",  # English (Lesotho)
            "en-rMG": "English (Madagascar)",  # English (Madagascar)
            "en-rMH": "English (Marshall Islands)",  # English (Marshall Islands)
            "en-rMP": "English (Northern Mariana Islands)",  # English (Northern Mariana Islands)
            "en-rMT": "English (Malta)",  # English (Malta)
            "en-rMU": "English (Mauritius)",  # English (Mauritius)
            "en-rMW": "English (Malawi)",  # English (Malawi)
            "en-rNA": "English (Namibia)",  # English (Namibia)
            "en-rNG": "English (Nigeria)",  # English (Nigeria)
            "en-rNZ": "English (New Zealand)",  # English (New Zealand)
            "en-rPG": "English (Papua New Guinea)",  # English (Papua New Guinea)
            "en-rPH": "English (Philippines)",  # English (Philippines)
            "en-rPK": "English (Pakistan)",  # English (Pakistan)
            "en-rPR": "English (Puerto Rico)",  # English (Puerto Rico)
            "en-rPW": "English (Palau)",  # English (Palau)
            "en-rSB": "English (Solomon Islands)",  # English (Solomon Islands)
            "en-rSC": "English (Seychelles)",  # English (Seychelles)
            "en-rSG": "English (Singapore)",  # English (Singapore)
            "en-rSL": "English (Sierra Leone)",  # English (Sierra Leone)
            "en-rSS": "English (South Sudan)",  # English (South Sudan)
            "en-rSZ": "English (Swaziland)",  # English (Swaziland)
            "en-rTC": "English (Turks and Caicos Islands)",  # English (Turks and Caicos Islands)
            "en-rTO": "English (Tonga)",  # English (Tonga)
            "en-rTT": "English (Trinidad and Tobago)",  # English (Trinidad and Tobago)
            "en-rTZ": "English (Tanzania)",  # English (Tanzania)
            "en-rUG": "English (Uganda)",  # English (Uganda)
            "en-rUM": "English (U.S. Outlying Islands)",  # English (U.S. Outlying Islands)
            "en-rUS": "English (United States)",  # English (United States)
            "en-rUS_POSIX": "English (United States,Computer)",  # English (United States,Computer)
            "en-rVC": "English (Saint Vincent and the Grenadines)",  # English (Saint Vincent and the Grenadines)
            "en-rVG": "English (British Virgin Islands)",  # English (British Virgin Islands)
            "en-rVI": "English (U.S. Virgin Islands)",  # English (U.S. Virgin Islands)
            "en-rVU": "English (Vanuatu)",  # English (Vanuatu)
            "en-rWS": "English (Samoa)",  # English (Samoa)
            "en-rZA": "English (South Africa)",  # English (South Africa)
            "en-rZM": "English (Zambia)",  # English (Zambia)
            "en-rZW": "English (Zimbabwe)",  # English (Zimbabwe)
            "eo": "Esperanto",  # Esperanto
            "es": "Español",  # Spanish
            "es_419": "Español (Latinoamérica)",  # Spanish (Latin America)
            "es-rAR": "Español (Argentina)",  # Spanish (Argentina)
            "es-rBO": "Español (Bolivia)",  # Spanish (Bolivia)
            "es-rCL": "Español (Chile)",  # Spanish (Chile)
            "es-rCO": "Español (Colombia)",  # Spanish (Colombia)
            "es-rCR": "Español (Costa Rica)",  # Spanish (Costa Rica)
            "es-rCU": "Español (Cuba)",  # Spanish (Cuba)
            "es-rDO": "Español (República Dominicana)",  # Spanish (Dominican Republic)
            "es-rEA": "Español (Ceuta y Melilla)",  # Spanish (Ceuta and Melilla)
            "es-rEC": "Español (Ecuador)",  # Spanish (Ecuador)
            "es-rES": "Español (España)",  # Spanish (Spain)
            "es-rGQ": "Español (Guinea Ecuatorial)",  # Spanish (Equatorial Guinea)
            "es-rGT": "Español (Guatemala)",  # Spanish (Guatemala)
            "es-rHN": "Español (Honduras)",  # Spanish (Honduras)
            "es-rIC": "Español (Islas Canarias)",  # Spanish (Canary Islands)
            "es-rMX": "Español (México)",  # Spanish (Mexico)
            "es-rNI": "Español (Nicaragua)",  # Spanish (Nicaragua)
            "es-rPA": "Español (Panamá)",  # Spanish (Panama)
            "es-rPE": "Español (Perú)",  # Spanish (Peru)
            "es-rPH": "Español (Filipinas)",  # Spanish (Philippines)
            "es-rPR": "Español (Puerto Rico)",  # Spanish (Puerto Rico)
            "es-rPY": "Español (Paraguay)",  # Spanish (Paraguay)
            "es-rSV": "Español (El Salvador)",  # Spanish (El Salvador)
            "es-rUS": "Español (Estados Unidos)",  # Spanish (United States)
            "es-rUY": "Español (Uruguay)",  # Spanish (Uruguay)
            "es-rVE": "Español (Venezuela)",  # Spanish (Venezuela)
            "et": "Eesti",  # Estonian
            "et-rEE": "Eesti (Eesti)",  # Estonian (Estonia)
            "eu": "Euskara",  # Basque
            "eu-rES": "Euskara (Espainia)",  # Basque (Spain)
            "ewo": "Ewondo",  # Ewondo
            "ewo-rCM": "Ewondo (Kamərún)",  # Ewondo (Cameroon)
            "fa": "فارسی",  # Persian
            "fa-rAF": "دری (افغانستان)",  # Persian (Afghanistan)
            "fa-rIR": "فارسی (ایران)",  # Persian (Iran)
            "ff": "Pulaar",  # Fulah
            "ff-rSN": "Pulaar (Senegaal)",  # Fulah (Senegal)
            "fi": "Suomi",  # Finnish
            "fi-rFI": "Suomi (Suomi)",  # Finnish (Finland)
            "fil": "Filipino",  # Filipino
            "fil-rPH": "Filipino (Pilipinas)",  # Filipino (Philippines)
            "fo": "Føroyskt",  # Faroese
            "fo-rFO": "Føroyskt (Føroyar)",  # Faroese (Faroe Islands)
            "fr": "Français",  # French
            "fr-rBE": "Français (Belgique)",  # French (Belgium)
            "fr-rBF": "Français (Burkina Faso)",  # French (Burkina Faso)
            "fr-rBI": "Français (Burundi)",  # French (Burundi)
            "fr-rBJ": "Français (Bénin)",  # French (Benin)
            "fr-rBL": "Français (Saint-Barthélémy)",  # French (Saint Barthélemy)
            "fr-rCA": "Français (Canada)",  # French (Canada)
            "fr-rCD": "Français (République démocratique du Congo)",  # French (Congo [DRC])
            "fr-rCF": "Français (République centrafricaine)",  # French (Central African Republic)
            "fr-rCG": "Français (Congo-Brazzaville)",  # French (Congo [Republic])
            "fr-rCH": "Français (Suisse)",  # French (Switzerland)
            "fr-rCI": "Français (Côte d’Ivoire)",  # French (Côte d’Ivoire)
            "fr-rCM": "Français (Cameroun)",  # French (Cameroon)
            "fr-rDJ": "Français (Djibouti)",  # French (Djibouti)
            "fr-rDZ": "Français (Algérie)",  # French (Algeria)
            "fr-rFR": "Français (France)",  # French (France)
            "fr-rGA": "Français (Gabon)",  # French (Gabon)
            "fr-rGF": "Français (Guyane française)",  # French (French Guiana)
            "fr-rGN": "Français (Guinée)",  # French (Guinea)
            "fr-rGP": "Français (Guadeloupe)",  # French (Guadeloupe)
            "fr-rGQ": "Français (Guinée équatoriale)",  # French (Equatorial Guinea)
            "fr-rHT": "Français (Haïti)",  # French (Haiti)
            "fr-rKM": "Français (Comores)",  # French (Comoros)
            "fr-rLU": "Français (Luxembourg)",  # French (Luxembourg)
            "fr-rMA": "Français (Maroc)",  # French (Morocco)
            "fr-rMC": "Français (Monaco)",  # French (Monaco)
            "fr-rMF": "Français (Saint-Martin [partie française])",  # French (Saint Martin)
            "fr-rMG": "Français (Madagascar)",  # French (Madagascar)
            "fr-rML": "Français (Mali)",  # French (Mali)
            "fr-rMQ": "Français (Martinique)",  # French (Martinique)
            "fr-rMR": "Français (Mauritanie)",  # French (Mauritania)
            "fr-rMU": "Français (Maurice)",  # French (Mauritius)
            "fr-rNC": "Français (Nouvelle-Calédonie)",  # French (New Caledonia)
            "fr-rNE": "Français (Niger)",  # French (Niger)
            "fr-rPF": "Français (Polynésie française)",  # French (French Polynesia)
            "fr-rRE": "Français (Réunion)",  # French (Réunion)
            "fr-rRW": "Français (Rwanda)",  # French (Rwanda)
            "fr-rSC": "Français (Seychelles)",  # French (Seychelles)
            "fr-rSN": "Français (Sénégal)",  # French (Senegal)
            "fr-rSY": "Français (Syrie)",  # French (Syria)
            "fr-rTD": "Français (Tchad)",  # French (Chad)
            "fr-rTG": "Français (Togo)",  # French (Togo)
            "fr-rTN": "Français (Tunisie)",  # French (Tunisia)
            "fr-rVU": "Français (Vanuatu)",  # French (Vanuatu)
            "fr-rYT": "Français (Mayotte)",  # French (Mayotte)
            "ga": "Gaeilge",  # Irish
            "ga-rIE": "Gaeilge (Éire)",  # Irish (Ireland)
            "gl": "Galego",  # Galician
            "gl-rES": "Galego (España)",  # Galician (Spain)
            "gsw": "Schwiizertüütsch",  # Swiss German
            "gsw-rCH": "Schwiizertüütsch (Schwiiz)",  # Swiss German (Switzerland)
            "gu": "ગુજરાતી",  # Gujarati
            "gu-rIN": "ગુજરાતી (ભારત)",  # Gujarati (India)
            "guz": "Ekegusii",  # Gusii
            "guz-rKE": "Ekegusii (Kenya)",  # Gusii (Kenya)
            "gv": "Gaelg",  # Manx
            "gv-rGB": "Gaelg (Rywvaneth Unys)",  # Manx (United Kingdom)
            "ha": "Hausa",  # Hausa
            "ha-rLATN": "Hausa (LATN)",  # Hausa (LATN)
            "ha-rLATN_GH": "Hausa (Gana,GH)",  # Hausa (Ghana,GH)
            "ha-rLATN_NE": "Hausa (Nijar,NE)",  # Hausa (Niger,NE)
            "ha-rLATN_NG": "Hausa (Najeriya,NG)",  # Hausa (Nigeria,NG)
            "haw": "ʻŌlelo Hawaiʻi",  # Hawaiian
            "haw-rUS": "ʻŌlelo Hawaiʻi (ʻAmelika Hui Pū ʻIa)",  # Hawaiian (United States)
            "iw": "עברית",  # Hebrew
            "iw-rIL": "עברית (ישראל)",  # Hebrew (Israel)
            "hi": "हिन्दी",  # Hindi
            "hi-rIN": "हिन्दी (भारत)",  # Hindi (India)
            "hr": "Hrvatski",  # Croatian
            "hr-rBA": "Hrvatski (Bosna i Hercegovina)",  # Croatian (Bosnia and Herzegovina)
            "hr-rHR": "Hrvatski (Hrvatska)",  # Croatian (Croatia)
            "hu": "Magyar",  # Hungarian
            "hu-rHU": "Magyar (Magyarország)",  # Hungarian (Hungary)
            "hy": "հայերեն",  # Armenian
            "hy-rAM": "հայերեն (Հայաստան)",  # Armenian (Armenia)
            "in": "Bahasa Indonesia",  # Indonesian
            "in-rID": "Bahasa Indonesia (Indonesia)",  # Indonesian (Indonesia)
            "ig": "Igbo",  # Igbo
            "ig-rNG": "Igbo (Nigeria)",  # Igbo (Nigeria)
            "ii": "ꆈꌠꉙ",  # Sichuan Yi
            "ii-rCN": "ꆈꌠꉙ (ꍏꇩ)",  # Sichuan Yi (China)
            "is": "íslenska",  # Icelandic
            "is-rIS": "íslenska (Ísland)",  # Icelandic (Iceland)
            "it": "Italiano",  # Italian
            "it-rCH": "Italiano (Svizzera)",  # Italian (Switzerland)
            "it-rIT": "Italiano (Italia)",  # Italian (Italy)
            "it-rSM": "Italiano (San Marino)",  # Italian (San Marino)
            "ja": "日本語",  # Japanese
            "ja-rJP": "日本語 (日本)",  # Japanese (Japan)
            "jgo": "Ndaꞌa",  # Ngomba
            "jgo-rCM": "Ndaꞌa (Kamɛlûn)",  # Ngomba (Cameroon)
            "jmc": "Kimachame",  # Machame
            "jmc-rTZ": "Kimachame (Tanzania)",  # Machame (Tanzania)
            "ka": "ქართული",  # Georgian
            "ka-rGE": "ქართული (საქართველო)",  # Georgian (Georgia)
            "kab": "Taqbaylit",  # Kabyle
            "kab-rDZ": "Taqbaylit (Lezzayer)",  # Kabyle (Algeria)
            "kam": "Kikamba",  # Kamba
            "kam-rKE": "Kikamba (Kenya)",  # Kamba (Kenya)
            "kde": "Chimakonde",  # Makonde
            "kde-rTZ": "Chimakonde (Tanzania)",  # Makonde (Tanzania)
            "kea": "Kabuverdianu",  # Kabuverdianu
            "kea-rCV": "Kabuverdianu (Kabu Verdi)",  # Kabuverdianu (Cape Verde)
            "khq": "Koyra ciini",  # Koyra Chiini
            "khq-rML": "Koyra ciini (Maali)",  # Koyra Chiini (Mali)
            "ki": "Gikuyu",  # Kikuyu
            "ki-rKE": "Gikuyu (Kenya)",  # Kikuyu (Kenya)
            "kk": "қазақ тілі",  # Kazakh
            "kk-rCYRL": "қазақ тілі (CYRL)",  # Kazakh (CYRL)
            "kk-rCYRL_KZ": "қазақ тілі (Қазақстан,KZ)",  # Kazakh (Kazakhstan,KZ)
            "kl": "Kalaallisut",  # Kalaallisut
            "kl-rGL": "Kalaallisut (Kalaallit Nunaat)",  # Kalaallisut (Greenland)
            "kln": "Kalenjin",  # Kalenjin
            "kln-rKE": "Kalenjin (Emetab Kenya)",  # Kalenjin (Kenya)
            "km": "ខ្មែរ",  # Khmer
            "km-rKH": "ខ្មែរ (កម្ពុជា)",  # Khmer (Cambodia)
            "kn": "ಕನ್ನಡ",  # Kannada
            "kn-rIN": "ಕನ್ನಡ (ಭಾರತ)",  # Kannada (India)
            "ko": "한국어",  # Korean
            "ko-rKP": "한국어 (조선 민주주의 인민 공화국)",  # Korean (North Korea)
            "ko-rKR": "한국어 (대한민국)",  # Korean (South Korea)
            "kok": "कोंकणी",  # Konkani
            "kok-rIN": "कोंकणी (भारत)",  # Konkani (India)
            "ks": "کٲشُر",  # Kashmiri
            "ks-rARAB": "کٲشُر (ARAB)",  # Kashmiri (ARAB)
            "ks-rARAB_IN": "کٲشُر (ہِنٛدوستان,IN)",  # Kashmiri (India,IN)
            "ksb": "Kishambaa",  # Shambala
            "ksb-rTZ": "Kishambaa (Tanzania)",  # Shambala (Tanzania)
            "ksf": "Rikpa",  # Bafia
            "ksf-rCM": "Rikpa (kamɛrún)",  # Bafia (Cameroon)
            "kw": "Kernewek",  # Cornish
            "kw-rGB": "Kernewek (Rywvaneth Unys)",  # Cornish (United Kingdom)
            "lag": "Kɨlaangi",  # Langi
            "lag-rTZ": "Kɨlaangi (Taansanía)",  # Langi (Tanzania)
            "lg": "Luganda",  # Ganda
            "lg-rUG": "Luganda (Yuganda)",  # Ganda (Uganda)
            "ln": "Lingála",  # Lingala
            "ln-rAO": "Lingála (Angóla)",  # Lingala (Angola)
            "ln-rCD": "Lingála (Repibiki demokratiki ya Kongó)",  # Lingala (Congo [DRC])
            "ln-rCF": "Lingála (Repibiki ya Afríka ya Káti)",  # Lingala (Central African Republic)
            "ln-rCG": "Lingála (Kongo)",  # Lingala (Congo [Republic])
            "lo": "ລາວ",  # Lao
            "lo-rLA": "ລາວ (ສ.ປ.ປ ລາວ)",  # Lao (Laos)
            "lt": "Lietuvių",  # Lithuanian
            "lt-rLT": "Lietuvių (Lietuva)",  # Lithuanian (Lithuania)
            "lu": "Tshiluba",  # Luba-Katanga
            "lu-rCD": "Tshiluba (Ditunga wa Kongu)",  # Luba-Katanga (Congo [DRC])
            "luo": "Dholuo",  # Luo
            "luo-rKE": "Dholuo (Kenya)",  # Luo (Kenya)
            "luy": "Luluhia",  # Luyia
            "luy-rKE": "Luluhia (Kenya)",  # Luyia (Kenya)
            "lv": "Latviešu",  # Latvian
            "lv-rLV": "Latviešu (Latvija)",  # Latvian (Latvia)
            "mas": "Maa",  # Masai
            "mas-rKE": "Maa (Kenya)",  # Masai (Kenya)
            "mas-rTZ": "Maa (Tansania)",  # Masai (Tanzania)
            "mer": "Kĩmĩrũ",  # Meru
            "mer-rKE": "Kĩmĩrũ (Kenya)",  # Meru (Kenya)
            "mfe": "Kreol morisien",  # Morisyen
            "mfe-rMU": "Kreol morisien (Moris)",  # Morisyen (Mauritius)
            "mg": "Malagasy",  # Malagasy
            "mg-rMG": "Malagasy (Madagasikara)",  # Malagasy (Madagascar)
            "mgh": "Makua",  # Makhuwa-Meetto
            "mgh-rMZ": "Makua (Umozambiki)",  # Makhuwa-Meetto (Mozambique)
            "mgo": "Metaʼ",  # Meta'
            "mgo-rCM": "Metaʼ (Kamalun)",  # Meta' (Cameroon)
            "mk": "македонски",  # Macedonian
            "mk-rMK": "македонски (Македонија)",  # Macedonian (Macedonia [FYROM])
            "ml": "മലയാളം",  # Malayalam
            "ml-rIN": "മലയാളം (ഇന്ത്യ)",  # Malayalam (India)
            "mn": "монгол",  # Mongolian
            "mn-rCYRL": "монгол (CYRL)",  # Mongolian (CYRL)
            "mn-rCYRL_MN": "монгол (Монгол,MN)",  # Mongolian (Mongolia,MN)
            "mr": "मराठी",  # Marathi
            "mr-rIN": "मराठी (भारत)",  # Marathi (India)
            "ms": "Bahasa Melayu",  # Malay
            "ms-rLATN": "Bahasa Melayu (LATN)",  # Malay (LATN)
            "ms-rLATN_BN": "Bahasa Melayu (Brunei,BN)",  # Malay (Brunei,BN)
            "ms-rLATN_MY": "Bahasa Melayu (Malaysia,MY)",  # Malay (Malaysia,MY)
            "ms-rLATN_SG": "Bahasa Melayu (Singapura,SG)",  # Malay (Singapore,SG)
            "mt": "Malti",  # Maltese
            "mt-rMT": "Malti (Malta)",  # Maltese (Malta)
            "mua": "MUNDAŊ",  # Mundang
            "mua-rCM": "MUNDAŊ (kameruŋ)",  # Mundang (Cameroon)
            "my": "ဗမာ",  # Burmese
            "my-rMM": "ဗမာ (မြန်မာ)",  # Burmese (Myanmar [Burma])
            "naq": "Khoekhoegowab",  # Nama
            "naq-rNA": "Khoekhoegowab (Namibiab)",  # Nama (Namibia)
            "nb": "Norsk bokmål",  # Norwegian Bokmål
            "nb-rNO": "Norsk bokmål (Norge)",  # Norwegian Bokmål (Norway)
            "nd": "IsiNdebele",  # North Ndebele
            "nd-rZW": "IsiNdebele (Zimbabwe)",  # North Ndebele (Zimbabwe)
            "ne": "नेपाली",  # Nepali
            "ne-rIN": "नेपाली (भारत)",  # Nepali (India)
            "ne-rNP": "नेपाली (नेपाल)",  # Nepali (Nepal)
            "nl": "Nederlands",  # Dutch
            "nl-rAW": "Nederlands (Aruba)",  # Dutch (Aruba)
            "nl-rBE": "Nederlands (België)",  # Dutch (Belgium)
            "nl-rCW": "Nederlands (Curaçao)",  # Dutch (Curaçao)
            "nl-rNL": "Nederlands (Nederland)",  # Dutch (Netherlands)
            "nl-rSR": "Nederlands (Suriname)",  # Dutch (Suriname)
            "nl-rSX": "Nederlands (Sint-Maarten)",  # Dutch (Sint Maarten)
            "nmg": "Nmg",  # Kwasio
            "nmg-rCM": "Nmg (Kamerun)",  # Kwasio (Cameroon)
            "nn": "Nynorsk",  # Norwegian Nynorsk
            "nn-rNO": "Nynorsk (Noreg)",  # Norwegian Nynorsk (Norway)
            "nus": "Thok Nath",  # Nuer
            "nus-rSD": "Thok Nath (Sudan)",  # Nuer (Sudan)
            "nyn": "Runyankore",  # Nyankole
            "nyn-rUG": "Runyankore (Uganda)",  # Nyankole (Uganda)
            "om": "Oromoo",  # Oromo
            "om-rET": "Oromoo (Itoophiyaa)",  # Oromo (Ethiopia)
            "om-rKE": "Oromoo (Keeniyaa)",  # Oromo (Kenya)
            "or": "ଓଡ଼ିଆ",  # Oriya
            "or-rIN": "ଓଡ଼ିଆ (ଭାରତ)",  # Oriya (India)
            "pa": "ਪੰਜਾਬੀ",  # Punjabi
            "pa-rARAB": "پنجاب (ARAB)",  # Punjabi (ARAB)
            "pa-rARAB_PK": "پنجاب (پکستان,PK)",  # Punjabi (Pakistan,PK)
            "pa-rGURU": "ਪੰਜਾਬੀ (GURU)",  # Punjabi (GURU)
            "pa-rGURU_IN": "ਪੰਜਾਬੀ (ਭਾਰਤ,IN)",  # Punjabi (India,IN)
            "pl": "Polski",  # Polish
            "pl-rPL": "Polski (Polska)",  # Polish (Poland)
            "ps": "پښتو",  # Pashto
            "ps-rAF": "پښتو (افغانستان)",  # Pashto (Afghanistan)
            "pt": "Português",  # Portuguese
            "pt-rAO": "Português (Angola)",  # Portuguese (Angola)
            "pt-rBR": "Português (Brasil)",  # Portuguese (Brazil)
            "pt-rCV": "Português (Cabo Verde)",  # Portuguese (Cape Verde)
            "pt-rGW": "Português (Guiné Bissau)",  # Portuguese (Guinea-Bissau)
            "pt-rMO": "Português (Macau)",  # Portuguese (Macau)
            "pt-rMZ": "Português (Moçambique)",  # Portuguese (Mozambique)
            "pt-rPT": "Português (Portugal)",  # Portuguese (Portugal)
            "pt-rST": "Português (São Tomé e Príncipe)",  # Portuguese (São Tomé and Príncipe)
            "pt-rTL": "Português (Timor-Leste)",  # Portuguese (Timor-Leste)
            "rm": "Rumantsch",  # Romansh
            "rm-rCH": "Rumantsch (Svizra)",  # Romansh (Switzerland)
            "rn": "Ikirundi",  # Rundi
            "rn-rBI": "Ikirundi (Uburundi)",  # Rundi (Burundi)
            "ro": "Română",  # Romanian
            "ro-rMD": "Română (Republica Moldova)",  # Romanian (Moldova)
            "ro-rRO": "Română (România)",  # Romanian (Romania)
            "rof": "Kihorombo",  # Rombo
            "rof-rTZ": "Kihorombo (Tanzania)",  # Rombo (Tanzania)
            "ru": "русский",  # Russian
            "ru-rBY": "русский (Беларусь)",  # Russian (Belarus)
            "ru-rKG": "русский (Киргизия)",  # Russian (Kyrgyzstan)
            "ru-rKZ": "русский (Казахстан)",  # Russian (Kazakhstan)
            "ru-rMD": "русский (Молдова)",  # Russian (Moldova)
            "ru-rRU": "русский (Россия)",  # Russian (Russia)
            "ru-rUA": "русский (Украина)",  # Russian (Ukraine)
            "rw": "Kinyarwanda",  # Kinyarwanda
            "rw-rRW": "Kinyarwanda (Rwanda)",  # Kinyarwanda (Rwanda)
            "rwk": "Kiruwa",  # Rwa
            "rwk-rTZ": "Kiruwa (Tanzania)",  # Rwa (Tanzania)
            "saq": "Kisampur",  # Samburu
            "saq-rKE": "Kisampur (Kenya)",  # Samburu (Kenya)
            "sbp": "Ishisangu",  # Sangu
            "sbp-rTZ": "Ishisangu (Tansaniya)",  # Sangu (Tanzania)
            "seh": "Sena",  # Sena
            "seh-rMZ": "Sena (Moçambique)",  # Sena (Mozambique)
            "ses": "Koyraboro senni",  # Koyraboro Senni
            "ses-rML": "Koyraboro senni (Maali)",  # Koyraboro Senni (Mali)
            "sg": "Sängö",  # Sango
            "sg-rCF": "Sängö (Ködörösêse tî Bêafrîka)",  # Sango (Central African Republic)
            "shi": "ⵜⴰⵎⴰⵣⵉⵖⵜ",  # Tachelhit
            "shi-rLATN": "Tamazight (LATN)",  # Tachelhit (LATN)
            "shi-rLATN_MA": "Tamazight (lmɣrib,MA)",  # Tachelhit (Morocco,MA)
            "shi-rTFNG": "ⵜⴰⵎⴰⵣⵉⵖⵜ (TFNG)",  # Tachelhit (TFNG)
            "shi-rTFNG_MA": "ⵜⴰⵎⴰⵣⵉⵖⵜ (ⵍⵎⵖⵔⵉⴱ,MA)",  # Tachelhit (Morocco,MA)
            "si": "සිංහල",  # Sinhala
            "si-rLK": "සිංහල (ශ්‍රී ලංකාව)",  # Sinhala (Sri Lanka)
            "sk": "Slovenčina",  # Slovak
            "sk-rSK": "Slovenčina (Slovensko)",  # Slovak (Slovakia)
            "sl": "Slovenščina",  # Slovenian
            "sl-rSI": "Slovenščina (Slovenija)",  # Slovenian (Slovenia)
            "sn": "ChiShona",  # Shona
            "sn-rZW": "ChiShona (Zimbabwe)",  # Shona (Zimbabwe)
            "so": "Soomaali",  # Somali
            "so-rDJ": "Soomaali (Jabuuti)",  # Somali (Djibouti)
            "so-rET": "Soomaali (Itoobiya)",  # Somali (Ethiopia)
            "so-rKE": "Soomaali (Kiiniya)",  # Somali (Kenya)
            "so-rSO": "Soomaali (Soomaaliya)",  # Somali (Somalia)
            "sq": "Shqip",  # Albanian
            "sq-rAL": "Shqip (Shqipëria)",  # Albanian (Albania)
            "sq-rMK": "Shqip (Maqedoni)",  # Albanian (Macedonia [FYROM])
            "sr": "Српски",  # Serbian
            "sr-rCYRL": "Српски (CYRL)",  # Serbian (CYRL)
            "sr-rCYRL_BA": "Српски (Босна и Херцеговина,BA)",  # Serbian (Bosnia and Herzegovina,BA)
            "sr-rCYRL_ME": "Српски (Црна Гора,ME)",  # Serbian (Montenegro,ME)
            "sr-rCYRL_RS": "Српски (Србија,RS)",  # Serbian (Serbia,RS)
            "sr-rLATN": "Srpski (LATN)",  # Serbian (LATN)
            "sr-rLATN_BA": "Srpski (Bosna i Hercegovina,BA)",  # Serbian (Bosnia and Herzegovina,BA)
            "sr-rLATN_ME": "Srpski (Crna Gora,ME)",  # Serbian (Montenegro,ME)
            "sr-rLATN_RS": "Srpski (Srbija,RS)",  # Serbian (Serbia,RS)
            "sv": "Svenska",  # Swedish
            "sv-rAX": "Svenska (Åland)",  # Swedish (Åland Islands)
            "sv-rFI": "Svenska (Finland)",  # Swedish (Finland)
            "sv-rSE": "Svenska (Sverige)",  # Swedish (Sweden)
            "sw": "Kiswahili",  # Swahili
            "sw-rKE": "Kiswahili (Kenya)",  # Swahili (Kenya)
            "sw-rTZ": "Kiswahili (Tanzania)",  # Swahili (Tanzania)
            "sw-rUG": "Kiswahili (Uganda)",  # Swahili (Uganda)
            "swc": "Kiswahili ya Kongo",  # Congo Swahili
            "swc-rCD": "Kiswahili ya Kongo (Jamhuri ya Kidemokrasia ya Kongo)",  # Congo Swahili (Congo [DRC])
            "ta": "தமிழ்",  # Tamil
            "ta-rIN": "தமிழ் (இந்தியா)",  # Tamil (India)
            "ta-rLK": "தமிழ் (இலங்கை)",  # Tamil (Sri Lanka)
            "ta-rMY": "தமிழ் (மலேஷியா)",  # Tamil (Malaysia)
            "ta-rSG": "தமிழ் (சிங்கப்பூர்)",  # Tamil (Singapore)
            "te": "తెలుగు",  # Telugu
            "te-rIN": "తెలుగు (భారత దేశం)",  # Telugu (India)
            "teo": "Kiteso",  # Teso
            "teo-rKE": "Kiteso (Kenia)",  # Teso (Kenya)
            "teo-rUG": "Kiteso (Uganda)",  # Teso (Uganda)
            "th": "ไทย",  # Thai
            "th-rTH": "ไทย (ไทย)",  # Thai (Thailand)
            "ti": "ትግርኛ",  # Tigrinya
            "ti-rER": "ትግርኛ (ER)",  # Tigrinya (Eritrea)
            "ti-rET": "ትግርኛ (ET)",  # Tigrinya (Ethiopia)
            "to": "Lea fakatonga",  # Tongan
            "to-rTO": "Lea fakatonga (Tonga)",  # Tongan (Tonga)
            "tr": "Türkçe",  # Turkish
            "tr-rCY": "Türkçe (Güney Kıbrıs Rum Kesimi)",  # Turkish (Cyprus)
            "tr-rTR": "Türkçe (Türkiye)",  # Turkish (Turkey)
            "twq": "Tasawaq senni",  # Tasawaq
            "twq-rNE": "Tasawaq senni (Nižer)",  # Tasawaq (Niger)
            "tzm": "Tamaziɣt",  # Central Atlas Tamazight
            "tzm-rLATN": "Tamaziɣt (LATN)",  # Central Atlas Tamazight (LATN)
            "tzm-rLATN_MA": "Tamaziɣt (Meṛṛuk,MA)",  # Central Atlas Tamazight (Morocco,MA)
            "uk": "українська",  # Ukrainian
            "uk-rUA": "українська (Україна)",  # Ukrainian (Ukraine)
            "ur": "اردو",  # Urdu
            "ur-rIN": "اردو (بھارت)",  # Urdu (India)
            "ur-rPK": "اردو (پاکستان)",  # Urdu (Pakistan)
            "uz": "Ўзбек",  # Uzbek
            "uz-rARAB": "اوزبیک (ARAB)",  # Uzbek (ARAB)
            "uz-rARAB_AF": "اوزبیک (افغانستان,AF)",  # Uzbek (Afghanistan,AF)
            "uz-rCYRL": "Ўзбек (CYRL)",  # Uzbek (CYRL)
            "uz-rCYRL_UZ": "Ўзбек (Ўзбекистон,UZ)",  # Uzbek (Uzbekistan,UZ)
            "uz-rLATN": "Oʻzbekcha (LATN)",  # Uzbek (LATN)
            "uz-rLATN_UZ": "Oʻzbekcha (Oʻzbekiston,UZ)",  # Uzbek (Uzbekistan,UZ)
            "vai": "ꕙꔤ",  # Vai
            "vai-rLATN": "Vai (LATN)",  # Vai (LATN)
            "vai-rLATN_LR": "Vai (Laibhiya,LR)",  # Vai (Liberia,LR)
            "vai-rVAII": "ꕙꔤ (VAII)",  # Vai (VAII)
            "vai-rVAII_LR": "ꕙꔤ (ꕞꔤꔫꕩ,LR)",  # Vai (Liberia,LR)
            "vi": "Tiếng Việt",  # Vietnamese
            "vi-rVN": "Tiếng Việt (Việt Nam)",  # Vietnamese (Vietnam)
            "vun": "Kyivunjo",  # Vunjo
            "vun-rTZ": "Kyivunjo (Tanzania)",  # Vunjo (Tanzania)
            "xog": "Olusoga",  # Soga
            "xog-rUG": "Olusoga (Yuganda)",  # Soga (Uganda)
            "yav": "Nuasue",  # Yangben
            "yav-rCM": "Nuasue (Kemelún)",  # Yangben (Cameroon)
            "yo": "Èdè Yorùbá",  # Yoruba
            "yo-rNG": "Èdè Yorùbá (Orílẹ́ède Nàìjíríà)",  # Yoruba (Nigeria)
            # This was the obtained from Locale, but it seems it's different in Settings
            # "zh": u"中文", # Chinese
            "zh": "中文 (简体)",  # Chinese
            "zh-rHANS": "中文 (HANS)",  # Chinese (HANS)
            "zh-rHANS_CN": "中文 (中国,CN)",  # Chinese (China,CN)
            "zh-rHANS_HK": "中文 (香港,HK)",  # Chinese (Hong Kong,HK)
            "zh-rHANS_MO": "中文 (澳门,MO)",  # Chinese (Macau,MO)
            "zh-rHANS_SG": "中文 (新加坡,SG)",  # Chinese (Singapore,SG)
            "zh-rHANT": "中文 (HANT)",  # Chinese (HANT)
            "zh-rHANT_HK": "中文 (香港,HK)",  # Chinese (Hong Kong,HK)
            "zh-rHANT_MO": "中文 (澳門,MO)",  # Chinese (Macau,MO)
            "zh-rHANT_TW": "中文 (台灣,TW)",  # Chinese (Taiwan,TW)
            "zu": "IsiZulu",  # Zulu
            "zu-rZA": "IsiZulu (iNingizimu Afrika)",  # Zulu (South Africa)
        }

        if not languageTo in list(LANGUAGES.keys()):
            raise RuntimeError("%s is not a supported language by AndroidViewClient" % languageTo)
        self.openQuickSettingsSettings()
        view = None
        currentLanguage = None
        ATTEMPTS = 10
        if self.vc.getSdkVersion() >= 20:
            for _ in range(ATTEMPTS):
                com_android_settings___id_dashboard = self.vc.findViewByIdOrRaise("com.android.settings:id/dashboard")
                for k, v in LANGUAGE_SETTINGS.items():
                    if DEBUG_CHANGE_LANGUAGE:
                        print("searching for", v, file=sys.stderr)
                    view = self.vc.findViewWithText(v, root=com_android_settings___id_dashboard)
                    if view:
                        currentLanguage = k
                        if DEBUG_CHANGE_LANGUAGE:
                            print("found current language:", k, file=sys.stderr)
                        break
                if view:
                    break
                com_android_settings___id_dashboard.uiScrollable.flingForward()
                self.vc.sleep(1)
                self.vc.dump(-1)
            if view is None:
                raise ViewNotFoundException("text", "'Language & input' (any language)", "ROOT")
            view.touch()
            self.vc.sleep(1)
            self.vc.dump(-1)
            self.vc.findViewWithTextOrRaise(PHONE_LANGUAGE[currentLanguage]).touch()
            self.vc.sleep(1)
            self.vc.dump(-1)
        else:
            for _ in range(ATTEMPTS):
                android___id_list = self.vc.findViewByIdOrRaise("android:id/list")
                for k, v in LANGUAGE_SETTINGS.items():
                    view = self.vc.findViewWithText(v, root=android___id_list)
                    if view:
                        currentLanguage = k
                        break
                if view:
                    break
                android___id_list.uiScrollable.flingForward()
                self.vc.sleep(1)
                self.vc.dump(-1)
            if view is None:
                raise ViewNotFoundException("text", "'Language & input' (any language)", "ROOT")
            view.touch()
            self.vc.sleep(1)
            self.vc.dump(-1)
            self.vc.findViewWithTextOrRaise(PHONE_LANGUAGE[currentLanguage]).touch()
            self.vc.sleep(1)
            self.vc.dump(-1)

        android___id_list = self.vc.findViewByIdOrRaise("android:id/list")
        android___id_list.uiScrollable.setViewClient(self.vc)
        if DEBUG_CHANGE_LANGUAGE:
            print("scrolling to find", LANGUAGES[languageTo], file=sys.stderr)
        view = android___id_list.uiScrollable.scrollTextIntoView(LANGUAGES[languageTo])
        if view is not None:
            view.touch()
        else:
            # raise RuntimeError(u"Couldn't change language to %s (%s)" % (LANGUAGES[languageTo], languageTo))
            raise RuntimeError("Couldn't change language to %s" % languageTo)
        self.vc.device.press('BACK')
        self.vc.sleep(1)
        self.vc.device.press('BACK')


class UiCollection():
    '''
    Used to enumerate a container's user interface (UI) elements for the purpose of counting, or
    targeting a sub elements by a child's text or description.
    '''

    pass


class UiScrollable(UiCollection):
    '''
    A L{UiCollection} that supports searching for items in scrollable layout elements.

    This class can be used with horizontally or vertically scrollable controls.
    '''

    def __init__(self, view):
        self.vc = None
        self.view = view
        self.vertical = True
        self.bounds = view.getBounds()
        (self.x, self.y, self.w, self.h) = view.getPositionAndSize()
        self.steps = 10
        self.duration = 800
        self.swipeDeadZonePercentage = 0.1
        self.maxSearchSwipes = 10

    def flingBackward(self):
        if self.vertical:
            s = (self.x + self.w / 2, self.y + self.h * self.swipeDeadZonePercentage)
            e = (self.x + self.w / 2, self.y + self.h - self.h * self.swipeDeadZonePercentage)
        else:
            s = (self.x + self.w * self.swipeDeadZonePercentage, self.y + self.h / 2)
            e = (self.x + self.w * (1.0 - self.swipeDeadZonePercentage), self.y + self.h / 2)
        if DEBUG:
            print("flingBackward: view=", self.view.__smallStr__(), self.view.getPositionAndSize(), file=sys.stderr)
            print("self.view.device.drag(%s, %s, %s, %s)" % (s, e, self.duration, self.steps), file=sys.stderr)
        self.view.device.drag(s, e, self.duration, self.steps, self.view.device.display['orientation'])

    def flingForward(self):
        if self.vertical:
            s = (self.x + self.w / 2, (self.y + self.h) - self.h * self.swipeDeadZonePercentage)
            e = (self.x + self.w / 2, self.y + self.h * self.swipeDeadZonePercentage)
        else:
            s = (self.x + self.w * (1.0 - self.swipeDeadZonePercentage), self.y + self.h / 2)
            e = (self.x + self.w * self.swipeDeadZonePercentage, self.y + self.h / 2)
        if DEBUG:
            print("flingForward: view=", self.view.__smallStr__(), self.view.getPositionAndSize(), file=sys.stderr)
            print("self.view.device.drag(%s, %s, %s, %s)" % (s, e, self.duration, self.steps), file=sys.stderr)
        self.view.device.drag(s, e, self.duration, self.steps, self.view.device.display['orientation'])

    def flingToBeginning(self, maxSwipes=10):
        if self.vertical:
            for _ in range(maxSwipes):
                if DEBUG:
                    print("flinging to beginning", file=sys.stderr)
                self.flingBackward()

    def flingToEnd(self, maxSwipes=10):
        if self.vertical:
            for _ in range(maxSwipes):
                if DEBUG:
                    print("flinging to end", file=sys.stderr)
                self.flingForward()

    def scrollTextIntoView(self, text):
        '''
        Performs a forward scroll action on the scrollable layout element until the text you provided is visible,
        or until swipe attempts have been exhausted. See setMaxSearchSwipes(int)
        '''

        if self.vc is None:
            raise ValueError('vc must be set in order to use this method')
        for n in range(self.maxSearchSwipes):
            # FIXME: now I need to figure out the best way of navigating to the ViewClient asossiated
            # with this UiScrollable.
            # It's using setViewClient() now.
            if DEBUG or DEBUG_CHANGE_LANGUAGE:
                print("Searching for text='%s'" % text, file=sys.stderr)
                for v in self.vc.views:
                    try:
                        print("    scrollTextIntoView: v=", v.getId(), end=' ', file=sys.stderr)
                        print(v.getText(), file=sys.stderr)
                    except Exception as e:
                        print(e, file=sys.stderr)
                        pass
            # v = self.vc.findViewWithText(text, root=self.view)
            v = self.vc.findViewWithText(text)
            if v is not None:
                return v
            self.flingForward()
            # self.vc.sleep(1)
            self.vc.dump(-1)
            # WARNING: after this dump, the value kept in self.view is outdated, it should be refreshed
            # in some way
        return None

    def setAsHorizontalList(self):
        self.vertical = False

    def setAsVerticalList(self):
        self.vertical = True

    def setMaxSearchSwipes(self, maxSwipes):
        self.maxSearchSwipes = maxSwipes

    def setViewClient(self, vc):
        self.vc = vc


class ListView(View):
    '''
    ListView class.
    '''

    pass


class UiAutomator2AndroidViewClient():
    '''
    UiAutomator XML to AndroidViewClient
    '''

    def __init__(self, device, version, uiAutomatorHelper):
        self.device = device
        self.version = version
        self.uiAutomatorHelper = uiAutomatorHelper
        self.root = None
        self.nodeStack = []
        self.parent = None
        self.views = []
        self.idCount = 1

    def StartElement(self, name, attributes):
        '''
        Expat start element event handler
        '''
        if name == 'hierarchy':
            pass
        elif name == 'node':
            # Instantiate an Element object
            attributes['uniqueId'] = 'id/no_id/%d' % self.idCount
            bounds = re.split('[\][,]', attributes['bounds'])
            attributes['bounds'] = ((int(bounds[1]), int(bounds[2])), (int(bounds[4]), int(bounds[5])))
            if DEBUG_BOUNDS:
                print("bounds=", attributes['bounds'], file=sys.stderr)
            self.idCount += 1
            child = View.factory(attributes, self.device, version=self.version,
                                 uiAutomatorHelper=self.uiAutomatorHelper)
            self.views.append(child)
            # Push element onto the stack and make it a child of parent
            if not self.nodeStack:
                self.root = child
            else:
                self.parent = self.nodeStack[-1]
                self.parent.add(child)
            self.nodeStack.append(child)

    def EndElement(self, name):
        '''
        Expat end element event handler
        '''

        if name == 'hierarchy':
            pass
        elif name == 'node':
            self.nodeStack.pop()

    def CharacterData(self, data):
        '''
        Expat character data event handler
        '''

        if data.strip():
            data = data.encode()
            element = self.nodeStack[-1]
            element.cdata += data

    def Parse(self, uiautomatorxml):
        # Create an Expat parser
        parser = xml.parsers.expat.ParserCreate()  # @UndefinedVariable
        # Set the Expat event handlers to our methods
        parser.StartElementHandler = self.StartElement
        parser.EndElementHandler = self.EndElement
        parser.CharacterDataHandler = self.CharacterData
        # Parse the XML File
        try:
            encoded = uiautomatorxml.encode(encoding='utf-8', errors='replace')
            _ = parser.Parse(encoded, True)
        except xml.parsers.expat.ExpatError as ex:  # @UndefinedVariable
            print("ERROR: Offending XML:\n", repr(uiautomatorxml), file=sys.stderr)
            raise RuntimeError(ex)
        return self.root


class Excerpt2Code():
    ''' Excerpt XML to code '''

    def __init__(self):
        self.data = None

    def StartElement(self, name, attributes):
        '''
        Expat start element event handler
        '''
        if name == 'excerpt':
            pass
        else:
            warnings.warn("Unexpected element: '%s'" % name)

    def EndElement(self, name):
        '''
        Expat end element event handler
        '''

        if name == 'excerpt':
            pass

    def CharacterData(self, data):
        '''
        Expat character data event handler
        '''

        if data.strip():
            data = data.encode()
            if not self.data:
                self.data = data
            else:
                self.data += data

    def Parse(self, excerpt):
        # Create an Expat parser
        parser = xml.parsers.expat.ParserCreate()  # @UndefinedVariable
        # Set the Expat event handlers to our methods
        parser.StartElementHandler = self.StartElement
        parser.EndElementHandler = self.EndElement
        parser.CharacterDataHandler = self.CharacterData
        # Parse the XML
        _ = parser.Parse(excerpt, 1)
        return self.data


class ViewClientOptions:
    '''
    ViewClient options helper class
    '''

    DEBUG = 'debug'
    DEVICE = 'device'
    SERIALNO = 'serialno'
    AUTO_DUMP = 'autodump'
    FORCE_VIEW_SERVER_USE = 'forceviewserveruse'
    LOCAL_PORT = 'localport'  # ViewServer local port
    REMOTE_PORT = 'remoteport'  # ViewServer remote port
    START_VIEW_SERVER = 'startviewserver'
    IGNORE_UIAUTOMATOR_KILLED = 'ignoreuiautomatorkilled'
    COMPRESSED_DUMP = 'compresseddump'
    USE_UIAUTOMATOR_HELPER = 'useuiautomatorhelper'


class ViewClient:
    '''
    ViewClient is a I{ViewServer} client.

    ViewServer backend
    ==================
    If not running the ViewServer is started on the target device or emulator and then the port
    mapping is created.

    LocalViewServer backend
    =======================
    ViewServer is started as an application services instead of as a system service.

    UiAutomator backend
    ===================
    No service is started.

    null backend
    ============
    Allows only operations using PX or DIP as hierarchy is not dumped and thus Views not recognized.

    UiAutomatorHelper backend
    =========================
    Requires B{Culebra Tester} installed on Android device.
    '''

    osName = platform.system()
    ''' The OS name. We sometimes need specific behavior. '''
    isLinux = (osName == 'Linux')
    isDarwin = (osName == 'Darwin')

    imageDirectory = None
    ''' The directory used to store screenshot images '''

    def __init__(self, device, serialno, adb=None, autodump=True, forceviewserveruse=False, localport=VIEW_SERVER_PORT,
                 remoteport=VIEW_SERVER_PORT, startviewserver=True, ignoreuiautomatorkilled=False, compresseddump=True,
                 useuiautomatorhelper=False, debug={}):
        '''
        Constructor

        @type device: AdbClient
        @param device: The device running the C{View server} to which this client will connect
        @type serialno: str
        @param serialno: the serial number of the device or emulator to connect to
        @type adb: str
        @param adb: the path of the C{adb} executable or None and C{ViewClient} will try to find it
        @type autodump: boolean
        @param autodump: whether an automatic dump is performed at the end of this constructor
        @type forceviewserveruse: boolean
        @param forceviewserveruse: Force the use of C{ViewServer} even if the conditions to use
                            C{UiAutomator} are satisfied
        @type localport: int
        @param localport: the local port used in the redirection
        @type remoteport: int
        @param remoteport: the remote port used to start the C{ViewServer} in the device or
                           emulator
        @type startviewserver: boolean
        @param startviewserver: Whether to start the B{global} ViewServer
        @type ignoreuiautomatorkilled: boolean
        @param ignoreuiautomatorkilled: Ignores received B{Killed} message from C{uiautomator}
        @type compresseddump: boolean
        @param compresseddump: turns --compressed flag for uiautomator dump on/off
        @:type useuiautomatorhelper: boolean
        @:param useuiautomatorhelper: use UiAutomatorHelper Android app as backend
        '''

        if not device:
            raise Exception('Device is not connected')
        self.device = device
        ''' The C{AdbClient} device instance '''

        if not serialno:
            raise ValueError("Serialno cannot be None")
        self.serialno = self.__mapSerialNo(serialno)
        ''' The serial number of the device '''

        self.uiAutomatorHelper = None
        ''' The UiAutomatorHelper '''

        if useuiautomatorhelper:
            self.useUiAutomator = True
            self.uiAutomatorHelper = UiAutomatorHelper(device)
            # we might return here if all the dependencies to `adb` commands were removed when uiAutomatorHelper is used
            #return

        self.debug = debug
        if debug:
            if 'DEVICE' in debug:
                global DEBUG_DEVICE
                DEBUG_DEVICE = debug['DEVICE']
                if DEBUG_DEVICE:
                    print("ViewClient: using device with serialno", self.serialno, file=sys.stderr)
            if 'RECEIVED' in debug:
                global DEBUG_RECEIVED
                DEBUG_RECEIVED = debug['RECEIVED']
            if 'UI_AUTOMATOR' in debug:
                global DEBUG_UI_AUTOMATOR
                DEBUG_UI_AUTOMATOR = debug['UI_AUTOMATOR']
            if 'UI_AUTOMATOR_HELPER' in debug:
                global DEBUG_UI_AUTOMATOR_HELPER
                DEBUG_UI_AUTOMATOR_HELPER = debug['UI_AUTOMATOR_HELPER']

        if adb:
            if not os.access(adb, os.X_OK):
                raise Exception('adb="%s" is not executable' % adb)
        else:
            # Using adbclient we don't need adb executable yet (maybe it's needed if we want to
            # start adb if not running)
            adb = obtainAdbPath()

        self.adb = adb
        ''' The adb command '''
        self.root = None
        ''' The root node '''
        self.viewsById = {}
        ''' The map containing all the L{View}s indexed by their L{View.getUniqueId()} '''
        self.display = {}
        ''' The map containing the device's display properties: width, height and density '''

        for prop in ['width', 'height', 'density', 'orientation']:
            self.display[prop] = -1
            if USE_ADB_CLIENT_TO_GET_BUILD_PROPERTIES:
                try:
                    self.display[prop] = device.display[prop]
                except:
                    if WARNINGS:
                        warnings.warn("Couldn't determine display %s" % prop)
            else:
                # these values are usually not defined as properties, so we stick to the -1 set
                # before
                pass

        self.build = {}
        ''' The map containing the device's build properties: version.sdk, version.release '''

        for prop in [VERSION_SDK_PROPERTY, VERSION_RELEASE_PROPERTY]:
            self.build[prop] = -1
            try:
                if USE_ADB_CLIENT_TO_GET_BUILD_PROPERTIES:
                    self.build[prop] = device.getProperty(prop)
                else:
                    self.build[prop] = device.shell('getprop ro.build.' + prop)[:-2]
            except:
                if WARNINGS:
                    warnings.warn("Couldn't determine build %s" % prop)

            if prop == VERSION_SDK_PROPERTY:
                # we expect it to be an int
                self.build[prop] = int(self.build[prop] if self.build[prop] else -1)

        self.ro = {}
        ''' The map containing the device's ro properties: secure, debuggable '''
        for prop in ['secure', 'debuggable', 'product.board', 'product.brand']:
            try:
                self.ro[prop] = device.shell('getprop ro.' + prop)[:-2]
            except:
                if WARNINGS:
                    warnings.warn("Couldn't determine ro %s" % prop)
                self.ro[prop] = 'UNKNOWN'

        self.forceViewServerUse = forceviewserveruse
        ''' Force the use of ViewServer even if the conditions to use UiAutomator are satisfied '''
        self.useUiAutomator = (self.build[
                                   VERSION_SDK_PROPERTY] >= 16) and not forceviewserveruse  # jelly bean 4.1 & 4.2
        if DEBUG:
            print("    ViewClient.__init__: useUiAutomator=", self.useUiAutomator, "sdk=",
                  self.build[VERSION_SDK_PROPERTY], "forceviewserveruse=", forceviewserveruse, file=sys.stderr)
        ''' If UIAutomator is supported by the device it will be used '''
        self.ignoreUiAutomatorKilled = ignoreuiautomatorkilled
        ''' On some devices (i.e. Nexus 7 running 4.2.2) uiautomator is killed just after generating
        the dump file. In many cases the file is already complete so we can ask to ignore the 'Killed'
        message by setting L{ignoreuiautomatorkilled} to C{True}.

        Changes in v2.3.21 that uses C{/dev/tty} instead of a file may have turned this variable
        unnecessary, however it has been kept for backward compatibility.
        '''

        if self.useUiAutomator:
            self.textProperty = TEXT_PROPERTY_UI_AUTOMATOR
        else:
            if self.build[VERSION_SDK_PROPERTY] <= 10:
                self.textProperty = TEXT_PROPERTY_API_10
            else:
                self.textProperty = TEXT_PROPERTY
            if startviewserver:
                if not self.serviceResponse(device.shell('service call window 3')):
                    try:
                        self.assertServiceResponse(device.shell('service call window 1 i32 %d' %
                                                                remoteport))
                    except:
                        msg = 'Cannot start View server.\n' \
                              'This only works on emulator and devices running developer versions.\n' \
                              'Does hierarchyviewer work on your device?\n' \
                              'See https://github.com/dtmilano/AndroidViewClient/wiki/Secure-mode\n\n' \
                              'Device properties:\n' \
                              '    ro.secure=%s\n' \
                              '    ro.debuggable=%s\n' % (self.ro['secure'], self.ro['debuggable'])
                        raise Exception(msg)

            self.localPort = localport
            self.remotePort = remoteport
            # FIXME: it seems there's no way of obtaining the serialno from the MonkeyDevice
            subprocess.check_call([self.adb, '-s', self.serialno, 'forward', 'tcp:%d' % self.localPort,
                                   'tcp:%d' % self.remotePort])

        self.windows = None
        ''' The list of windows as obtained by L{ViewClient.list()} '''

        # FIXME: may not be true, one may want UiAutomator but without UiAutomatorHelper
        if self.useUiAutomator:
            if not useuiautomatorhelper:
                # culebratester Intrumentation running prevents `uiautomator dump` from working correctly, then if we are not
                # using UiAutomatorHelper let's kill it, just in case
                self.device.shell('am force-stop com.dtmilano.android.culebratester2')

        self.uiDevice = UiDevice(self)
        ''' The L{UiDevice} '''

        ''' The output of compressed dump is different than output of uncompressed one.
        If one requires uncompressed output, this option should be set to False
        '''
        self.compressedDump = compresseddump

        self.navBack = None
        self.navHome = None
        self.navRecentApps = None

        if autodump:
            self.dump()

    def __del__(self):
        # should clean up some things
        if hasattr(self, 'uiAutomatorHelper') and self.uiAutomatorHelper:
            self.uiAutomatorHelper.quit()

    @staticmethod
    def __obtainAdbPath():
        return obtainAdbPath()

    @staticmethod
    def __mapSerialNo(serialno):
        serialno = serialno.strip()
        # ipRE = re.compile('^\d+\.\d+.\d+.\d+$')
        if IP_RE.match(serialno):
            if DEBUG_DEVICE: print("ViewClient: adding default port to serialno", serialno, ADB_DEFAULT_PORT,
                                   file=sys.stderr)
            return serialno + ':%d' % ADB_DEFAULT_PORT

        ipPortRE = re.compile(IP_DOMAIN_NAME_PORT_REGEX, re.IGNORECASE)

        if ipPortRE.match(serialno):
            # nothing to map
            return serialno

        if IPV6_RE.match(serialno):
            if DEBUG_DEVICE: print("ViewClient: adding default port to serialno", serialno, ADB_DEFAULT_PORT,
                                   file=sys.stderr)
            return '[' + serialno + ']:%d' % ADB_DEFAULT_PORT

        if IPV6_PORT_RE.match(serialno):
            # nothing to map
            return serialno

        if re.search("[.*()+]", serialno):
            raise ValueError("Regular expression not supported as serialno in ViewClient. Found '%s'" % serialno)

        return serialno

    @staticmethod
    def __obtainDeviceSerialNumber(device):
        if DEBUG_DEVICE: print("ViewClient: obtaining serial number for connected device", file=sys.stderr)
        serialno = device.getProperty('ro.serialno')
        if not serialno:
            serialno = device.shell('getprop ro.serialno')
            if serialno:
                serialno = serialno[:-2]
        if not serialno:
            qemu = device.shell('getprop ro.kernel.qemu')
            if qemu:
                qemu = qemu[:-2]
                if qemu and int(qemu) == 1:
                    # FIXME !!!!!
                    # this must be calculated from somewhere, though using a fixed serialno for now
                    warnings.warn("Running on emulator but no serial number was specified then 'emulator-5554' is used")
                    serialno = 'emulator-5554'
        if not serialno:
            # If there's only one device connected get its serialno
            adb = ViewClient.__obtainAdbPath()
            if DEBUG_DEVICE: print("    using adb=%s" % adb, file=sys.stderr)
            # Remove ANDROID_SERIAL from the environment when using adb to
            # obtain the serial number of the device, because if the serial
            # number was specified as an environment variable that contains a
            # regular expression, adb will always return 'unknown'.
            env = os.environ.copy()
            env.pop("ANDROID_SERIAL", None)
            s = subprocess.Popen([adb, 'get-serialno'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 env=env).communicate()[0][:-1]
            if s != 'unknown':
                serialno = s
        if DEBUG_DEVICE: print("    serialno=%s" % serialno, file=sys.stderr)
        if not serialno:
            warnings.warn("Couldn't obtain the serialno of the connected device")
        return serialno

    @staticmethod
    def setAlarm(timeout):
        osName = platform.system()
        if osName.startswith('Windows'):  # alarm is not implemented in Windows
            return
        signal.alarm(timeout)

    @staticmethod
    def connectToDeviceOrExit(timeout=60, verbose=False, ignoresecuredevice=False, ignoreversioncheck=False,
                              serialno=None, adbhostname=adbclient.HOSTNAME, adbport=adbclient.PORT,
                              connect=adbclient.connect):
        """
        Connects to a device which serial number is obtained from the script arguments if available
        or using the default regex C{.*}.

        If the connection is not successful the script exits.

        History
        -------
        In MonkeyRunner times, this method was a way of overcoming one of its limitations.
        L{MonkeyRunner.waitForConnection()} returns a L{MonkeyDevice} even if the connection failed.
        Then, to detect this situation, C{device.wake()} is attempted and if it fails then it is
        assumed the previous connection failed.

        @type timeout: int
        @param timeout: timeout for the connection
        @type verbose: bool
        @param verbose: Verbose output
        @type ignoresecuredevice: bool
        @param ignoresecuredevice: Ignores the check for a secure device
        @type ignoreversioncheck: bool
        @param ignoreversioncheck: Ignores the check for a supported ADB version
        @type serialno: str
        @param serialno: The device or emulator serial number
        @type connect: function
        @param connect: Connect method to use to connect to ADB

        @return: the device and serialno used for the connection
        """
        progname = os.path.basename(sys.argv[0])
        if serialno is None:
            # eat all the extra options the invoking script may have added
            args = sys.argv
            while len(args) > 1 and args[1][0] == '-':
                args.pop(1)
            serialno = args[1] if len(args) > 1 else \
                os.environ['ANDROID_SERIAL'] if 'ANDROID_SERIAL' in os.environ \
                    else '.*'
        if IP_RE.match(serialno):
            # If matches an IP address format and port was not specified add the default
            serialno += ':%d' % ADB_DEFAULT_PORT
        if verbose:
            print('Connecting to a device with serialno=%s with a timeout of %d secs...' % \
                  (serialno, timeout), file=sys.stderr)
        ViewClient.setAlarm(timeout + 5)
        # NOTE: timeout is used for 2 different timeouts, the one to set the alarm to timeout the connection with
        # adb and the timeout used by adb (once connected) for the sockets
        device = adbclient.AdbClient(
            serialno,
            hostname=adbhostname,
            port=adbport,
            ignoreversioncheck=ignoreversioncheck,
            timeout=timeout,
            connect=connect)
        ViewClient.setAlarm(0)
        if verbose:
            print('Connected to device with serialno=%s' % serialno, file=sys.stderr)
        secure = device.getSystemProperty('ro.secure')
        debuggable = device.getSystemProperty('ro.debuggable')
        versionProperty = device.getProperty(VERSION_SDK_PROPERTY)
        if versionProperty:
            version = int(versionProperty)
        else:
            if verbose:
                print("Couldn't obtain device SDK version")
            version = -1

        # we are going to use UiAutomator for versions >= 16 that's why we ignore if the device
        # is secure if this is true
        if secure == '1' and debuggable == '0' and not ignoresecuredevice and version < 16:
            print("%s: ERROR: Device is secure, AndroidViewClient won't work." % progname, file=sys.stderr)
            if verbose:
                print("    secure=%s debuggable=%s version=%d ignoresecuredevice=%s" % \
                      (secure, debuggable, version, ignoresecuredevice), file=sys.stderr)
            sys.exit(2)
        if device.serialno:
            # If we know the serialno because it was set by AdbClient, use it
            serialno = device.serialno

        ipPortRE = re.compile(IP_DOMAIN_NAME_PORT_REGEX, re.IGNORECASE)

        if re.search("[.*()+]", serialno) and not ipPortRE.match(serialno):
            # if a regex was used we have to determine the serialno used
            serialno = ViewClient.__obtainDeviceSerialNumber(device)
        if verbose:
            print('Actual device serialno=%s' % serialno, file=sys.stderr)
        return device, serialno

    @staticmethod
    def traverseShowClassIdAndText(view, extraInfo=None, noExtraInfo=None, extraAction=None):
        '''
        Shows the View class, id and text if available.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @type extraInfo: method
        @param extraInfo: the View method to add extra info
        @type noExtraInfo: str
        @param noExtraInfo: Don't add extra info
        @type extraAction: method
        @param extraAction: An extra action to be invoked for every view

        @return: the string containing class, id, and text if available
        '''

        if type(view) == WindowHierarchy:
            return ''

        try:
            eis = ''
            if extraInfo:
                eis = extraInfo(view)
                if not eis and noExtraInfo:
                    eis = noExtraInfo
            if eis:
                eis = ' {0}'.format(eis)
            if extraAction:
                extraAction(view)
            try:
                _str = str(view.getClass())
                _str += ' '
                _str += '%s' % view.getId()
                _str += ' '
                _str += view.getText() if view.getText() else ''
            except AttributeError:
                _str = f'{view.clazz}'
                if view.resource_id:
                    _str += f' {view.resource_id}'
                if view.text:
                    _str += f' {view.text}'
            if eis:
                _str += eis
            return _str
        except Exception as e:
            import traceback
            small_str = ''
            try:
                small_str = view.__smallStr__()
            except AttributeError:
                small_str = str(view)
            return '⛔️ Exception in view=%s: %s:%s\n%s' % (
                small_str, sys.exc_info()[0].__name__, e, traceback.format_exc())

    @staticmethod
    def traverseShowClassIdTextAndUniqueId(view):
        '''
        Shows the View class, id, text if available and unique id.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available and unique Id
        '''

        return ViewClient.traverseShowClassIdAndText(view, View.getUniqueId)

    @staticmethod
    def traverseShowClassIdTextAndContentDescription(view):
        '''
        Shows the View class, id, text if available and content description.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available and the content description
        '''

        return ViewClient.traverseShowClassIdAndText(view, View.getContentDescription, 'NAF')

    @staticmethod
    def traverseShowClassIdTextAndTag(view):
        '''
        Shows the View class, id, text if available and tag.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available and tag
        '''

        return ViewClient.traverseShowClassIdAndText(view, View.getTag, None)

    @staticmethod
    def traverseShowClassIdTextContentDescriptionAndScreenshot(view):
        '''
        Shows the View class, id, text if available and unique id and takes the screenshot.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available and the content description
        '''

        return ViewClient.traverseShowClassIdAndText(view, View.getContentDescription, 'NAF',
                                                     extraAction=ViewClient.writeViewImageToFileInDir)

    @staticmethod
    def traverseShowClassIdTextAndCenter(view):
        '''
        Shows the View class, id and text if available and center.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available
        '''

        return ViewClient.traverseShowClassIdAndText(view, View.getCenter)

    @staticmethod
    def traverseShowClassIdTextPositionAndSize(view):
        '''
        Shows the View class, id and text if available.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available
        '''

        return ViewClient.traverseShowClassIdAndText(view, View.getPositionAndSize)

    @staticmethod
    def traverseShowClassIdTextAndBounds(view):
        '''
        Shows the View class, id and text if available.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available plus
                 View bounds
        '''

        return ViewClient.traverseShowClassIdAndText(view, View.getBounds)

    @staticmethod
    def traverseTakeScreenshot(view):
        '''
        Don't show any any, just takes the screenshot.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: None
        '''

        return ViewClient.writeViewImageToFileInDir(view)

    # methods that can be used to transform ViewClient.traverse output
    TRAVERSE_CIT = traverseShowClassIdAndText
    ''' An alias for L{traverseShowClassIdAndText(view)} '''
    TRAVERSE_CITUI = traverseShowClassIdTextAndUniqueId
    ''' An alias for L{traverseShowClassIdTextAndUniqueId(view)} '''
    TRAVERSE_CITCD = traverseShowClassIdTextAndContentDescription
    ''' An alias for L{traverseShowClassIdTextAndContentDescription(view)} '''
    TRAVERSE_CITG = traverseShowClassIdTextAndTag
    ''' An alias for L{traverseShowClassIdTextAndTag(view)} '''
    TRAVERSE_CITC = traverseShowClassIdTextAndCenter
    ''' An alias for L{traverseShowClassIdTextAndCenter(view)} '''
    TRAVERSE_CITPS = traverseShowClassIdTextPositionAndSize
    ''' An alias for L{traverseShowClassIdTextPositionAndSize(view)} '''
    TRAVERSE_CITB = traverseShowClassIdTextAndBounds
    ''' An alias for L{traverseShowClassIdTextAndBounds(view)} '''
    TRAVERSE_CITCDS = traverseShowClassIdTextContentDescriptionAndScreenshot
    ''' An alias for L{traverseShowClassIdTextContentDescriptionAndScreenshot(view)} '''
    TRAVERSE_S = traverseTakeScreenshot
    ''' An alias for L{traverseTakeScreenshot(view)} '''

    @staticmethod
    def sleep(secs=1.0):
        '''
        Sleeps for the specified number of seconds.

        @type secs: float
        @param secs: number of seconds
        '''
        time.sleep(secs)

    def assertServiceResponse(self, response):
        '''
        Checks whether the response received from the server is correct or raises and Exception.

        @type response: str
        @param response: Response received from the server

        @raise Exception: If the response received from the server is invalid
        '''

        if not self.serviceResponse(response):
            raise Exception('Invalid response received from service.')

    def serviceResponse(self, response):
        '''
        Checks the response received from the I{ViewServer}.

        @return: C{True} if the response received matches L{PARCEL_TRUE}, C{False} otherwise
        '''

        PARCEL_TRUE = "Result: Parcel(00000000 00000001   '........')\r\n"
        ''' The TRUE response parcel '''
        if DEBUG:
            print("serviceResponse: comparing '%s' vs Parcel(%s)" % (response, PARCEL_TRUE), file=sys.stderr)
        return response == PARCEL_TRUE

    def setViews(self, received, windowId=None):
        '''
        Sets L{self.views} to the received value splitting it into lines.

        @type received: str
        @param received: the string received from the I{View Server}
        '''

        if not received or received == "":
            raise ValueError("received is empty")
        self.views = []
        ''' The list of Views represented as C{str} obtained after splitting it into lines after being received from the server. Done by L{self.setViews()}. '''
        self.__parseTree(received.split("\n"), windowId)
        if DEBUG:
            print("there are %d views in this dump" % len(self.views), file=sys.stderr)

    def setViewsFromUiAutomatorDump(self, received):
        '''
        Sets L{self.views} to the received value parsing the received XML.

        @type received: str
        @param received: the string received from the I{UI Automator}
        '''

        if not received or received == "":
            raise ValueError("received is empty")
        self.views = []
        ''' The list of Views represented as C{str} obtained after splitting it into lines after being received from the server. Done by L{self.setViews()}. '''
        if self.uiAutomatorHelper:
            self.__treeFromWindowHierarchy(received)
        else:
            self.__parseTreeFromUiAutomatorDump(received)
        if DEBUG:
            print("there are %d views in this dump" % len(self.views), file=sys.stderr)

    def __splitAttrs(self, strArgs):
        '''
        Splits the C{View} attributes in C{strArgs} and optionally adds the view id to the C{viewsById} list.

        Unique Ids
        ==========
        It is very common to find C{View}s having B{NO_ID} as the Id. This turns very difficult to
        use L{self.findViewById()}. To help in this situation this method assigns B{unique Ids}.

        The B{unique Ids} are generated using the pattern C{id/no_id/<number>} with C{<number>} starting
        at 1.

        @type strArgs: str
        @param strArgs: the string containing the raw list of attributes and values

        @return: Returns the attributes map.
        '''

        if self.useUiAutomator:
            raise RuntimeError("This method is not compatible with UIAutomator")
        # replace the spaces in text:mText to preserve them in later split
        # they are translated back after the attribute matches
        textRE = re.compile('%s=%s,' % (self.textProperty, _nd('len')))
        m = textRE.search(strArgs)
        if m:
            __textStart = m.end()
            __textLen = int(m.group('len'))
            __textEnd = m.end() + __textLen
            s1 = strArgs[__textStart:__textEnd]
            s2 = s1.replace(' ', WS)
            strArgs = strArgs.replace(s1, s2, 1)

        idRE = re.compile("(?P<viewId>id/\S+)")
        attrRE = re.compile('%s(?P<parens>\(\))?=%s,(?P<val>[^ ]*)' % (_ns('attr'), _nd('len')), flags=re.DOTALL)
        hashRE = re.compile('%s@%s' % (_ns('class'), _nh('oid')))

        attrs = {}
        viewId = None
        m = idRE.search(strArgs)
        if m:
            viewId = m.group('viewId')
            if DEBUG:
                print("found view with id=%s" % viewId, file=sys.stderr)

        for attr in strArgs.split():
            m = attrRE.match(attr)
            if m:
                __attr = m.group('attr')
                __parens = '()' if m.group('parens') else ''
                __len = int(m.group('len'))
                __val = m.group('val')
                if WARNINGS and __len != len(__val):
                    warnings.warn("Invalid len: expected: %d   found: %d   s=%s   e=%s" % (
                        __len, len(__val), __val[:50], __val[-50:]))
                if __attr == self.textProperty:
                    # restore spaces that have been replaced
                    __val = __val.replace(WS, ' ')
                attrs[__attr + __parens] = __val
            else:
                m = hashRE.match(attr)
                if m:
                    attrs['class'] = m.group('class')
                    attrs['oid'] = m.group('oid')
                else:
                    if DEBUG:
                        print(attr, "doesn't match", file=sys.stderr)

        if True:  # was assignViewById
            if not viewId:
                # If the view has NO_ID we are assigning a default id here (id/no_id) which is
                # immediately incremented if another view with no id was found before to generate
                # a unique id
                viewId = "id/no_id/1"
            if viewId in self.viewsById:
                # sometimes the view ids are not unique, so let's generate a unique id here
                i = 1
                while True:
                    newId = re.sub('/\d+$', '', viewId) + '/%d' % i
                    if not newId in self.viewsById:
                        break
                    i += 1
                viewId = newId
                if DEBUG:
                    print("adding viewById %s" % viewId, file=sys.stderr)
            # We are assigning a new attribute to keep the original id preserved, which could have
            # been NO_ID repeated multiple times
            attrs['uniqueId'] = viewId

        return attrs

    def __parseTree(self, receivedLines, windowId=None):
        '''
        Parses the View tree contained in L{receivedLines}. The tree is created and the root node assigned to L{self.root}.
        This method also assigns L{self.viewsById} values using L{View.getUniqueId} as the key.

        @type receivedLines: str
        @param receivedLines: the string received from B{View Server}
        '''

        self.root = None
        self.viewsById = {}
        self.views = []
        parent = None
        parents = []
        treeLevel = -1
        newLevel = -1
        lastView = None
        for v in receivedLines:
            if v == '' or v == 'DONE' or v == 'DONE.':
                break
            attrs = self.__splitAttrs(v)
            if not self.root:
                if v[0] == ' ':
                    raise Exception("Unexpected root element starting with ' '.")
                self.root = View.factory(attrs, self.device, self.build[VERSION_SDK_PROPERTY], self.forceViewServerUse,
                                         windowId, self.uiAutomatorHelper)
                if DEBUG: self.root.raw = v
                treeLevel = 0
                newLevel = 0
                lastView = self.root
                parent = self.root
                parents.append(parent)
            else:
                newLevel = (len(v) - len(v.lstrip()))
                if newLevel == 0:
                    raise Exception("newLevel==0 treeLevel=%d but tree can have only one root, v=%s" % (treeLevel, v))
                child = View.factory(attrs, self.device, self.build[VERSION_SDK_PROPERTY], self.forceViewServerUse,
                                     windowId, self.uiAutomatorHelper)
                if DEBUG: child.raw = v
                if newLevel == treeLevel:
                    parent.add(child)
                    lastView = child
                elif newLevel > treeLevel:
                    if (newLevel - treeLevel) != 1:
                        raise Exception("newLevel jumps %d levels, v=%s" % ((newLevel - treeLevel), v))
                    parent = lastView
                    parents.append(parent)
                    parent.add(child)
                    lastView = child
                    treeLevel = newLevel
                else:  # newLevel < treeLevel
                    for _ in range(treeLevel - newLevel):
                        parents.pop()
                    parent = parents.pop()
                    parents.append(parent)
                    parent.add(child)
                    treeLevel = newLevel
                    lastView = child
            self.views.append(lastView)
            self.viewsById[lastView.getUniqueId()] = lastView

    def __updateNavButtons(self):
        """
        Updates the navigation buttons that might be on the device screen.
        """

        navButtons = None
        for v in self.views:
            if v.getId() == 'com.android.systemui:id/nav_buttons':
                navButtons = v
                break
        if navButtons:
            self.navBack = self.findViewById('com.android.systemui:id/back', navButtons)
            self.navHome = self.findViewById('com.android.systemui:id/home', navButtons)
            self.navRecentApps = self.findViewById('com.android.systemui:id/recent_apps', navButtons)
        else:
            if self.uiAutomatorHelper:
                print("WARNING: nav buttons not found. Perhaps the device has hardware buttons.", file=sys.stderr)
            self.navBack = None
            self.navHome = None
            self.navRecentApps = None

    def __treeFromWindowHierarchy(self, windowHierarchy):
        # FIXME: idCount should be a class field
        idCount = 1
        version = self.build[VERSION_SDK_PROPERTY]
        self.root = windowHierarchy
        self.__processWindowHierarchyChild(self.root, idCount, version)

    @staticmethod
    # python 3
    # def __attributesFromWindowHierarchyChild(unique_id, child: WindowHierarchyChild):
    def __attributesFromWindowHierarchyChild(child):
        bounds = ((int(child.bounds[0]), int(child.bounds[1])), (int(child.bounds[2]), int(child.bounds[3])))
        return {'index': child.index, 'text': child.text, 'resource-id': child.resource_id, 'class': child.clazz,
                'package': child.package, 'content-desc': child.content_description, 'checkable': child.checkable,
                'checked': child.checked,
                'clickable': child.clickable, 'enabled': child.enabled, 'focusable': child.focusable,
                'focused': child.focused,
                'scrollable': child.scrollable, 'long-clickable': child.long_clickable,
                'password': child.password, 'selected': child.selected, 'bounds': bounds,
                'uniqueId': child.unique_id}

    def __processWindowHierarchyChild(self, node, idCount, version):
        if node.id != 'hierarchy':
            # FIXME: as WindowHierarchyChild is generated we may need a descendant
            # NOTE: we are extending WindowHierarchyChild adding unique_id
            node.unique_id = 'id/no_id/%d' % idCount
            attributes = ViewClient.__attributesFromWindowHierarchyChild(node)
            view = View.factory(attributes, self.device, version=version, uiAutomatorHelper=self.uiAutomatorHelper)
            self.views.append(view)
            idCount += 1
        for ch in node.children:
            self.__processWindowHierarchyChild(ch, idCount, version)

    def __parseTreeFromUiAutomatorDump(self, receivedXml):
        if DEBUG:
            print("__parseTreeFromUiAutomatorDump(", receivedXml[:40], "...)", file=sys.stderr)
        parser = UiAutomator2AndroidViewClient(self.device, self.build[VERSION_SDK_PROPERTY], self.uiAutomatorHelper)
        try:
            start_xml_index = receivedXml.index("<?xml")
            end_xml_index = receivedXml.rindex(">")
        except ValueError:
            raise ValueError("received does not contain valid XML: " + receivedXml)
        self.root = parser.Parse(receivedXml[start_xml_index:end_xml_index + 1])
        self.views = parser.views
        self.viewsById = {}
        for v in self.views:
            self.viewsById[v.getUniqueId()] = v
        self.__updateNavButtons()
        if DEBUG_NAV_BUTTONS:
            if not self.navBack:
                print("WARNING: navBack not found", file=sys.stderr)
            if not self.navHome:
                print("WARNING: navHome not found", file=sys.stderr)
            if not self.navRecentApps:
                print("WARNING: navRecentApps not found", file=sys.stderr)

    def getRoot(self):
        '''
        Gets the root node of the C{View} tree

        @return: the root node of the C{View} tree
        '''
        return self.root

    def traverse(self, root="ROOT", indent="", transform=None, stream=sys.stdout):
        '''
        Traverses the C{View} tree and prints its nodes.

        The nodes are printed converting them to string but other transformations can be specified
        by providing a method name as the C{transform} parameter.

        @type root: L{View}
        @param root: the root node from where the traverse starts
        @type indent: str
        @param indent: the indentation string to use to print the nodes
        @type transform: method
        @param transform: a method to use to transform the node before is printed
        @param stream: the output stream
        '''

        if transform is None:
            # this cannot be a default value, otherwise
            # TypeError: 'staticmethod' object is not callable
            # is raised
            transform = ViewClient.TRAVERSE_CIT

        if root == "ROOT":
            root = self.root

        return ViewClient.__traverse(root, indent, transform, stream)

    @staticmethod
    def __traverse(root, indent="", transform=View.__str__, stream=sys.stdout):
        if not root:
            return

        s = transform(root)
        if stream and s:
            if type(root) == WindowHierarchy:
                if transform == View.__str__:
                    print(s, file=stream)
                    return
            else:
                if sys.version_info[0] < 3:
                    ius = "%s%s" % (indent, s if isinstance(s, unicode) else unicode(s, 'utf-8', 'replace'))
                else:
                    ius = "%s%s" % (indent, s if isinstance(s, str) else str(s, 'utf-8', 'replace'))
                print(ius.encode('utf-8', 'replace').decode('utf-8'), file=stream)

        for ch in root.children:
            ViewClient.__traverse(ch, indent=indent + "   ", transform=transform, stream=stream)

    def dump(self, window=-1, sleep=1):
        '''
        Dumps the window content.

        Sleep is useful to wait some time before obtaining the new content when something in the
        window has changed.

        @type window: int or str
        @param window: the window id or name of the window to dump.
                    The B{name} is the package name or the window name (i.e. StatusBar) for
                    system windows.
                    The window id can be provided as C{int} or C{str}. The C{str} should represent
                    and C{int} in either base 10 or 16.
                    Use -1 to dump all windows.
                    This parameter only is used when the backend is B{ViewServer} and it's
                    ignored for B{UiAutomator}.
        @type sleep: int
        @param sleep: sleep in seconds before proceeding to dump the content

        @return: the list of Views as C{str} received from the server after being split into lines
        '''
        if sleep > 0:
            time.sleep(sleep)

        if self.useUiAutomator:
            if self.uiAutomatorHelper:
                received = self.uiAutomatorHelper.dumpWindowHierarchy()
            else:
                api = self.getSdkVersion()
                if api >= 24:
                    # In API 23 the process' stdout,in and err are connected to the socket not to the pts as in
                    # previous versions, so we can't redirect to /dev/tty
                    # Also, if we want to write to /sdcard/something it fails event though /sdcard is a symlink
                    # Also, 'primary' storage was added.
                    if self.serialno.startswith('emulator'):
                        pathname = '/storage/self/primary'
                    else:
                        pathname = '/sdcard'
                    filename = 'window_dump.xml'
                    cmd = 'cp /dev/null {pathname}/{filename} && uiautomator dump {compressed} {pathname}/{filename} >/dev/null && cat {pathname}/{filename}'.format(
                        pathname=pathname, filename=filename,
                        compressed='--compressed' if self.compressedDump else '')
                elif api == 23:
                    # In API 23 the process' stdout,in and err are connected to the socket not to the pts as in
                    # previous versions, so we can't redirect to /dev/tty
                    # Also, if we want to write to /sdcard/something it fails event though /sdcard is a symlink
                    if self.serialno.startswith('emulator'):
                        pathname = '/storage/self'
                        filename = 'window_dump.xml'
                        cmd = 'uiautomator dump %s %s/%s >/dev/null && cat %s/%s' % (
                            '--compressed' if self.compressedDump else '', pathname, filename, pathname, filename)
                    elif self.ro['product.board'] in ['msd838', 'msd938_STB', 'msd938', 'msm8916']:
                        cmd = 'uiautomator dump %s /dev/tty >/dev/null' % (
                            '--compressed' if self.compressedDump else '')
                    else:
                        pathname = '/sdcard'
                        filename = 'window_dump.xml'
                        cmd = 'uiautomator dump %s %s/%s >/dev/null && cat %s/%s' % (
                            '--compressed' if self.compressedDump else '', pathname, filename, pathname, filename)
                else:
                    # NOTICE:
                    # Using /dev/tty this works even on devices with no sdcard
                    cmd = 'uiautomator dump %s /dev/tty >/dev/null' % (
                        '--compressed' if api >= 18 and self.compressedDump else '')
                if DEBUG_UI_AUTOMATOR:
                    print("executing '%s'" % cmd, file=sys.stderr)
                received = self.device.shell(cmd)

            if not received:
                raise RuntimeError('ERROR: Empty UiAutomator dump was received')
            if DEBUG:
                self.received = received
            if DEBUG_RECEIVED:
                try:
                    pprint.pprint(received)
                except:
                    pass
                try:
                    print("received %d chars" % len(received), file=sys.stderr)
                    print(file=sys.stderr)
                except:
                    pass
                try:
                    print(repr(received), file=sys.stderr)
                    print(file=sys.stderr)
                except:
                    pass
            if not self.uiAutomatorHelper:
                onlyKilledRE = re.compile('Killed$')
                try:
                    if onlyKilledRE.search(received):
                        MONKEY = 'com.android.commands.monkey'
                        extraInfo = ''
                        if self.device.shell('ps | grep "%s"' % MONKEY):
                            extraInfo = "\nIt is know that '%s' conflicts with 'uiautomator'. Please kill it and try again." % MONKEY
                        raise RuntimeError(
                            '''ERROR: UiAutomator output contains no valid information. UiAutomator was killed, no reason given.''' + extraInfo)
                except:
                    pass
                if self.ignoreUiAutomatorKilled:
                    if DEBUG_RECEIVED:
                        print("ignoring UiAutomator Killed", file=sys.stderr)
                    killedRE = re.compile('</hierarchy>[\n\S]*Killed', re.MULTILINE)
                    if killedRE.search(received):
                        received = re.sub(killedRE, '</hierarchy>', received)
                    elif DEBUG_RECEIVED:
                        print("UiAutomator Killed: NOT FOUND!")
                    # It seems that API18 uiautomator spits this message to stdout
                    dumpedToDevTtyRE = re.compile('</hierarchy>[\n\S]*UI hierchary dumped to: /dev/tty.*', re.MULTILINE)
                    if dumpedToDevTtyRE.search(received):
                        received = re.sub(dumpedToDevTtyRE, '</hierarchy>', received)
                    if DEBUG_RECEIVED:
                        print("received=", received, file=sys.stderr)
                # API19 seems to send this warning as part of the XML.
                # Let's remove it if present
                received = received.replace(
                    'WARNING: linker: libdvm.so has text relocations. This is wasting memory and is a security risk. Please fix.\r\n',
                    '')
                if re.search('\[: not found', received):
                    raise RuntimeError('''ERROR: Some emulator images (i.e. android 4.1.2 API 16 generic_x86) does not include the '[' command.
    While UiAutomator back-end might be supported 'uiautomator' command fails.
    You should force ViewServer back-end.''')

                if received.startswith('ERROR: could not get idle state.'):
                    # See https://android.googlesource.com/platform/frameworks/testing/+/jb-mr2-release/uiautomator/cmds/uiautomator/src/com/android/commands/uiautomator/DumpCommand.java
                    raise RuntimeError('''The views are being refreshed too frequently to dump.''')
                if received.find('Only ROTATION_0 supported') != -1:
                    raise RuntimeError('''UiAutomatorHelper backend with support for only ROTATION_0 found.''')

            self.setViewsFromUiAutomatorDump(received)
        else:
            if isinstance(window, str):
                if window != '-1':
                    self.list(sleep=0)
                    found = False
                    for wId in self.windows:
                        try:
                            if window == self.windows[wId]:
                                window = wId
                                found = True
                                break
                        except:
                            pass
                        try:
                            if int(window) == wId:
                                window = wId
                                found = True
                                break
                        except:
                            pass
                        try:
                            if int(window, 16) == wId:
                                window = wId
                                found = True
                                break
                        except:
                            pass

                    if not found:
                        raise RuntimeError("ERROR: Cannot find window '%s' in %s" % (window, self.windows))
                else:
                    window = -1

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((VIEW_SERVER_HOST, self.localPort))
            except socket.error as ex:
                raise RuntimeError("ERROR: Connecting to %s:%d: %s" % (VIEW_SERVER_HOST, self.localPort, ex))
            cmd = 'dump %x\r\n' % window
            if DEBUG:
                print("executing: '%s'" % cmd, file=sys.stderr)
            s.send(cmd)
            received = ""
            doneRE = re.compile("DONE")
            ViewClient.setAlarm(120)
            while True:
                if DEBUG_RECEIVED:
                    print("    reading from socket...", file=sys.stderr)
                received += s.recv(1024)
                if doneRE.search(received[-7:]):
                    break
            s.close()
            ViewClient.setAlarm(0)
            if DEBUG:
                self.received = received
            if DEBUG_RECEIVED:
                print("received %d chars" % len(received), file=sys.stderr)
                print(file=sys.stderr)
                print(received, file=sys.stderr)
                print(file=sys.stderr)
            if received:
                for c in received:
                    if ord(c) > 127:
                        received = str(received, encoding='utf-8', errors='replace')
                        break
            self.setViews(received, hex(window)[2:])

            if DEBUG_TREE:
                self.traverse(self.root)

        return self.views

    def list(self, sleep=1):
        '''
        List the windows.

        Sleep is useful to wait some time before obtaining the new content when something in the
        window has changed.
        This also sets L{self.windows} as the list of windows.

        @type sleep: int
        @param sleep: sleep in seconds before proceeding to dump the content

        @return: the list of windows
        '''

        if sleep > 0:
            time.sleep(sleep)

        if self.useUiAutomator:
            raise Exception("Not implemented yet: listing windows with UiAutomator")
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((VIEW_SERVER_HOST, self.localPort))
            except socket.error as ex:
                raise RuntimeError("ERROR: Connecting to %s:%d: %s" % (VIEW_SERVER_HOST, self.localPort, ex))
            s.send('list\r\n')
            received = ""
            doneRE = re.compile("DONE")
            while True:
                received += s.recv(1024)
                if doneRE.search(received[-7:]):
                    break
            s.close()
            if DEBUG:
                self.received = received
            if DEBUG_RECEIVED:
                print("received %d chars" % len(received), file=sys.stderr)
                print(file=sys.stderr)
                print(received, file=sys.stderr)
                print(file=sys.stderr)

            self.windows = {}
            for line in received.split('\n'):
                if not line:
                    break
                if doneRE.search(line):
                    break
                values = line.split()
                if len(values) > 1:
                    package = values[1]
                else:
                    package = "UNKNOWN"
                if len(values) > 0:
                    wid = values[0]
                else:
                    wid = '00000000'
                self.windows[int('0x' + wid, 16)] = package
            return self.windows

    def findViewById(self, viewId, root="ROOT", viewFilter=None):
        """
        Finds the View with the specified viewId.

        @type viewId: str
        @param viewId: the ID of the view to find
        @type root: str
        @type root: View
        @param root: the root node of the tree where the View will be searched
        @type: viewFilter: function
        @param viewFilter: a function that will be invoked providing the candidate View as a parameter
                           and depending on the return value (C{True} or C{False}) the View will be
                           selected and returned as the result of C{findViewById()} or ignored.
                           This can be C{None} and no extra filtering is applied.

        @return: the C{View} found or C{None}
        """

        if self.uiAutomatorHelper:
            # If we are using uiAutomatorHelper let's find object directly without traversing the tree
            return self.uiAutomatorHelper.ui_device.find_object(by_selector=f'res@{viewId}')

        if not root:
            return None

        if root == "ROOT":
            return self.findViewById(viewId, self.root, viewFilter)

        try:
            rootId = root.getId()
        except AttributeError as ex:
            try:
                rootId = root.resource_id
            except AttributeError as ex:
                rootId = root.id

        if rootId == viewId:
            if viewFilter:
                if viewFilter(root):
                    return root
            else:
                return root

        if re.match('^id/no_id', viewId) or re.match('^id/.+/.+', viewId):
            try:
                unique_id = root.getUniqueId()
            except AttributeError as ex:
                try:
                    unique_id = root.unique_id
                except AttributeError as ex:
                    unique_id = -1

            if unique_id == viewId:
                if viewFilter:
                    if viewFilter(root):
                        return root;
                else:
                    return root

        for ch in root.children:
            foundView = self.findViewById(viewId, ch, viewFilter)
            if foundView:
                if viewFilter:
                    if viewFilter(foundView):
                        return foundView
                else:
                    return foundView

    def findViewByIdOrRaise(self, viewId, root="ROOT", viewFilter=None):
        """
        Finds the View or raise a ViewNotFoundException.

        @type viewId: str
        @param viewId: the ID of the view to find
        @type root: str
        @type root: View
        @param root: the root node of the tree where the View will be searched
        @type: viewFilter: function
        @param viewFilter: a function that will be invoked providing the candidate View as a parameter
                           and depending on the return value (C{True} or C{False}) the View will be
                           selected and returned as the result of C{findViewById()} or ignored.
                           This can be C{None} and no extra filtering is applied.
        @return: the View found
        @raise ViewNotFoundException: raise the exception if View not found
        """

        view = self.findViewById(viewId, root, viewFilter)
        if view:
            return view
        else:
            raise ViewNotFoundException("ID", viewId, root)

    def findViewByTag(self, tag, root="ROOT"):
        '''
        Finds the View with the specified tag
        '''

        return self.findViewWithAttribute('getTag()', tag, root)

    def findViewByTagOrRaise(self, tag, root="ROOT"):
        '''
        Finds the View with the specified tag or raise a ViewNotFoundException
        '''

        view = self.findViewWithAttribute('getTag()', tag, root)
        if view:
            return view
        else:
            raise ViewNotFoundException("tag", tag, root)

    def __findViewsWithAttributeInTree(self, attr, val, root):
        # Note the plural in this method name
        matchingViews = []
        if not self.root:
            print("ERROR: no root, did you forget to call dump()?", file=sys.stderr)
            return matchingViews

        if root == "ROOT":
            root = self.root

        if DEBUG: print("__findViewWithAttributeInTree: type val=", type(val), file=sys.stderr)
        if DEBUG: print(
            "__findViewWithAttributeInTree: checking if root=%s has attr=%s == %s" % (root.__smallStr__(), attr, val),
            file=sys.stderr)

        if root and attr in root.map and root.map[attr] == val:
            if DEBUG: print("__findViewWithAttributeInTree:  FOUND: %s" % root.__smallStr__(), file=sys.stderr)
            matchingViews.append(root)
        for ch in root.children:
            matchingViews += self.__findViewsWithAttributeInTree(attr, val, ch)

        return matchingViews

    def __findViewWithAttributeInTree(self, attr, val, root):
        if self.uiAutomatorHelper:
            if attr == 'content-desc':
                attr = 'desc'
            by_selector = f'{attr}@{val}'
            return self.uiAutomatorHelper.ui_device.find_object(by_selector=by_selector)

        if DEBUG:
            print("    __findViewWithAttributeInTree: type(val)=", type(val), file=sys.stderr)
            if type(val) != str and type(val) != re._pattern_type:
                u = str(val, encoding='utf-8', errors='ignore')
            else:
                u = val
            print('''__findViewWithAttributeInTree({0}'''.format(attr), end=' ', file=sys.stderr)
            try:
                print(''', {0}'''.format(u), end=' ', file=sys.stderr)
            except:
                pass
            print('>>>>>>>>>>>>>>>>>>', type(root), file=sys.stderr)
            if type(root) == bytes:
                print('>>>>>>>>>>>>>>>>>>', root, file=sys.stderr)
                print(''', {0})'''.format(root), file=sys.stderr)
            else:
                print(''', {0})'''.format(root.__smallStr__()), file=sys.stderr)

        if not self.root:
            print("ERROR: no root, did you forget to call dump()?", file=sys.stderr)
            return None

        if root == "ROOT":
            root = self.root

        if DEBUG: print("__findViewWithAttributeInTree: type val=", type(val), file=sys.stderr)
        if DEBUG:
            # print >> sys.stderr, u'''__findViewWithAttributeInTree: checking if root={0}: '''.format(root),
            print('''has  {0} == '''.format(attr), end=' ', file=sys.stderr)
            if type(val) == str:
                u = val
            elif type(val) != re._pattern_type:
                u = str(val, encoding='utf-8', errors='replace')
            try:
                print('''{0}'''.format(u), file=sys.stderr)
            except:
                pass

        if isinstance(val, RegexType):
            return self.__findViewWithAttributeInTreeThatMatches(attr, val, root)
        else:
            try:
                if DEBUG:
                    print('''__findViewWithAttributeInTree: comparing {0}: '''.format(attr), end=' ', file=sys.stderr)
                    print('''{0} == '''.format(root.map[attr]), end=' ', file=sys.stderr)
                    print('''{0}'''.format(val), file=sys.stderr)
            except:
                pass
            if root and attr in root.map and root.map[attr] == val:
                if DEBUG: print("__findViewWithAttributeInTree:  FOUND: %s" % root.__smallStr__(), file=sys.stderr)
                return root
            else:
                for ch in root.children:
                    v = self.__findViewWithAttributeInTree(attr, val, ch)
                    if v:
                        return v

        return None

    def __findViewWithAttributeInTreeOrRaise(self, attr, val, root):
        view = self.__findViewWithAttributeInTree(attr, val, root)
        if view:
            return view
        else:
            raise ViewNotFoundException(attr, val, root)

    def __findViewWithAttributeInTreeThatMatches(self, attr, regex, root, rlist=[]):
        if not self.root:
            print("ERROR: no root, did you forget to call dump()?", file=sys.stderr)
            return None

        if root == "ROOT":
            root = self.root

        if DEBUG: print("__findViewWithAttributeInTreeThatMatches: checking if root=%s attr=%s matches %s" % (
            root.__smallStr__(), attr, regex), file=sys.stderr)

        if root and attr in root.map and regex.match(root.map[attr]):
            if DEBUG: print("__findViewWithAttributeInTreeThatMatches:  FOUND: %s" % root.__smallStr__(),
                            file=sys.stderr)
            return root
        else:
            for ch in root.children:
                v = self.__findViewWithAttributeInTreeThatMatches(attr, regex, ch, rlist)
                if v:
                    return v

        return None

    def __findViewsWithAttributeInTreeThatMatches(self, attr, regex, root, rlist=[]):
        # Note the plural in this method name
        matchingViews = []
        if not self.root:
            print("ERROR: no root, did you forget to call dump()?", file=sys.stderr)
            return matchingViews

        if isinstance(root, str) and root == "ROOT":
            root = self.root

        if DEBUG:
            print("__findViewsWithAttributeInTreeThatMatches: checking if root=%s attr=%s matches %s" % (
                root.__smallStr__(), attr, regex), file=sys.stderr)

        if root and attr in root.map and regex.match(root.map[attr]):
            if DEBUG:
                print("__findViewsWithAttributeInTreeThatMatches:  FOUND: %s" % root.__smallStr__(), file=sys.stderr)
            matchingViews.append(root)
        for ch in root.children:
            matchingViews += self.__findViewsWithAttributeInTreeThatMatches(attr, regex, ch)

        return matchingViews

    def findViewWithAttribute(self, attr, val, root="ROOT"):
        '''
        Finds the View with the specified attribute and value
        '''
        if DEBUG:
            try:
                print('findViewWithAttribute({0}, {1}, {2})'.format(attr, str(val, encoding='utf-8', errors='replace'),
                                                                    root), file=sys.stderr)
            except:
                pass
            print("    findViewWithAttribute: type(val)=", type(val), file=sys.stderr)

        return self.__findViewWithAttributeInTree(attr, val, root)

    def findViewsWithAttribute(self, attr, val, root="ROOT"):
        '''
        Finds the Views with the specified attribute and value.
        This allows you to see all items that match your criteria in the view hierarchy

        Usage:
          buttons = v.findViewsWithAttribute("class", "android.widget.Button")

        '''

        return self.__findViewsWithAttributeInTree(attr, val, root)

    def findViewsWithAttributeThatMatches(self, attr, regex, root="ROOT"):
        '''
        Finds the Views with the specified attribute matching regex.
        This allows you to see all items that match your criteria in the view hierarchy
        '''

        return self.__findViewsWithAttributeInTreeThatMatches(attr, regex, root)

    def findViewWithAttributeOrRaise(self, attr, val, root="ROOT"):
        '''
        Finds the View or raise a ViewNotFoundException.

        @return: the View found
        @raise ViewNotFoundException: raise the exception if View not found
        '''

        view = self.findViewWithAttribute(attr, val, root)
        if view:
            return view
        else:
            raise ViewNotFoundException(attr, val, root)

    def findViewWithAttributeThatMatches(self, attr, regex, root="ROOT"):
        '''
        Finds the list of Views with the specified attribute matching
        regex
        '''

        return self.__findViewWithAttributeInTreeThatMatches(attr, regex, root)

    def findViewWithText(self, text, root="ROOT"):
        if DEBUG:
            try:
                print('''findViewWithText({0}, {1})'''.format(text, root), file=sys.stderr)
                print("    findViewWithText: type(text)=", type(text), file=sys.stderr)
            except:
                pass

        if isinstance(text, RegexType):
            return self.findViewWithAttributeThatMatches(self.textProperty, text, root)
            # l = self.findViewWithAttributeThatMatches(TEXT_PROPERTY, text)
            # ll = len(l)
            # if ll == 0:
            #    return None
            # elif ll == 1:
            #    return l[0]
            # else:
            #    print >>sys.stderr, "WARNING: findViewWithAttributeThatMatches invoked by findViewWithText returns %d items." % ll
            #    return l
        else:
            return self.findViewWithAttribute(self.textProperty, text, root)

    def findViewWithTextOrRaise(self, text, root="ROOT"):
        '''
        Finds the View or raise a ViewNotFoundException.

        @return: the View found
        @raise ViewNotFoundException: raise the exception if View not found
        '''

        if DEBUG:
            print("findViewWithTextOrRaise(%s, %s)" % (text, root), file=sys.stderr)
        view = self.findViewWithText(text, root)
        if view:
            return view
        else:
            raise ViewNotFoundException("text", text, root)

    def findViewWithContentDescription(self, contentdescription, root="ROOT"):
        '''
        Finds the View with the specified content description
        '''

        return self.__findViewWithAttributeInTree('content-desc', contentdescription, root)

    def findViewWithContentDescriptionOrRaise(self, contentdescription, root="ROOT"):
        '''
        Finds the View with the specified content description
        '''

        return self.__findViewWithAttributeInTreeOrRaise('content-desc', contentdescription, root)

    def findViewsContainingPoint(self, xxx_todo_changeme1, _filter=None):
        '''
        Finds the list of Views that contain the point (x, y).
        '''
        (x, y) = xxx_todo_changeme1
        if not _filter:
            _filter = lambda v: True

        return [v for v in self.views if (v.containsPoint((x, y)) and _filter(v))]

    def findObject(self, **kwargs):
        if self.uiAutomatorHelper:
            if DEBUG_UI_AUTOMATOR_HELPER:
                print("Finding object with %s through UiAutomatorHelper" % kwargs, file=sys.stderr)
            return self.uiAutomatorHelper.findObject(**kwargs)
        else:
            warnings.warn("findObject only implemented using UiAutomatorHelper. Use ViewClient.findView...() instead.")
            return None

    def click(self, x=-1, y=-1, selector=None):
        """
        An alias for touch.

        :param x:
        :param y:
        :param selector:
        :return:
        """

        self.touch(x=x, y=y, selector=selector)

    def touch(self, x=-1, y=-1, selector=None):
        if self.uiAutomatorHelper:
            if selector:
                if DEBUG_UI_AUTOMATOR_HELPER:
                    print("Touching View by selector=%s through UiAutomatorHelper" % selector, file=sys.stderr)
                # FIXME: is `selector` a `bySlector`?
                object_ref = self.uiAutomatorHelper.findObject(by_selector=selector)
                if DEBUG_UI_AUTOMATOR_HELPER:
                    print("♦️ object_ref=%s" % object_ref, file=sys.stderr)
                self.uiAutomatorHelper.click(oid=object_ref.oid)
            else:
                if DEBUG_UI_AUTOMATOR_HELPER:
                    print("Touching (%d, %d) through UiAutomatorHelper" % (x, y), file=sys.stderr)
                self.uiAutomatorHelper.click(x=int(x), y=int(y))
        else:
            self.device.touch(x, y)

    def longTouch(self, x=-1, y=-1, selector=None):
        if self.uiAutomatorHelper:
            if selector:
                if DEBUG_UI_AUTOMATOR_HELPER:
                    print("ViewClient: Long-touching View by selector=%s through UiAutomatorHelper" % (selector),
                          file=sys.stderr)
                self.uiAutomatorHelper.findObject(selector=selector).longClick()
            else:
                if DEBUG_UI_AUTOMATOR_HELPER:
                    print("ViewClient: Long-touching (%d, %d) through UiAutomatorHelper" % (x, y), file=sys.stderr)
                self.uiAutomatorHelper.swipe(startX=int(x), startY=int(y), endX=int(x), endY=int(y), steps=400)
        else:
            self.device.longTouch(x, y)

    def swipe(self, startX=-1, startY=-1, endX=-1, endY=-1, steps=400, segments=[], segmentSteps=5, start=None,
              end=None):
        if startX == -1 and startY == -1 and start:
            startX = start[0]
            startY = start[1]
        if endX == -1 and endY == -1 and end:
            endX = end[0]
            endY = end[1]
        if self.uiAutomatorHelper:
            if DEBUG_UI_AUTOMATOR_HELPER:
                print("Swipe through UiAutomatorHelper", (startX, startY, endX, endY, steps, segments, segmentSteps),
                      file=sys.stderr)
            self.uiAutomatorHelper.swipe(startX=startX, startY=startY, endX=endX, endY=endY, steps=steps,
                                         segments=segments, segmentSteps=segmentSteps)
        else:
            duration = steps / 2.0
            self.device.drag((startX, startY), (endX, endY), duration, steps)

    def pressBack(self):
        if self.uiAutomatorHelper:
            self.uiAutomatorHelper.pressBack()
        else:
            warnings.warn("pressBak only implemented using UiAutomatorHelper.  Use AdbClient.type() instead")

    def pressHome(self):
        if self.uiAutomatorHelper:
            self.uiAutomatorHelper.pressHome()
        else:
            warnings.warn("pressHome only implemented using UiAutomatorHelper.  Use AdbClient.type() instead")

    def pressRecentApps(self):
        if self.uiAutomatorHelper:
            self.uiAutomatorHelper.pressRecentApps()
        else:
            warnings.warn("pressRecentApps only implemented using UiAutomatorHelper.  Use AdbClient.type() instead")

    def pressKeyCode(self, keycode, metaState=0):
        '''By default no meta state'''
        if self.uiAutomatorHelper:
            if DEBUG_UI_AUTOMATOR_HELPER:
                print("pressKeyCode(%d, %d)" % (keycode, metaState), file=sys.stderr)
            self.uiAutomatorHelper.pressKeyCode(keycode, metaState)
        else:
            warnings.warn("pressKeyCode only implemented using UiAutomatorHelper.  Use AdbClient.type() instead")

    def setText(self, v, text):
        if DEBUG:
            print("setText(%s, '%s')" % (v.__tinyStr__(), text), file=sys.stderr)
        if self.uiAutomatorHelper:
            if DEBUG_UI_AUTOMATOR_HELPER:
                print("Setting text through UiAutomatorHelper for View with ID=%s" % v.getId(), file=sys.stderr)
            if v.getId():
                oid = self.uiAutomatorHelper.findObject(selector='res@%s' % v.getId())
                if DEBUG_UI_AUTOMATOR_HELPER:
                    print("oid=", oid, "text=", text, file=sys.stderr)
                self.uiAutomatorHelper.setText(oid, text)
            else:
                # The View has no ID so we cannot use the ID to create a selector to find it using findObject()
                # Let's fall back to this method.
                v.setText(text)
        else:
            # This is deleting the existing text, which should be asked in the dialog, but I would have to implement
            # the dialog myself
            v.setText(text)
            # This is not deleting the text, so appending if there's something
            # v.type(text)

    @staticmethod
    def sayText(text, voice=None, verbose=False):
        if ViewClient.isLinux:
            if verbose:
                # FIXME: should use Colors, but for now it's fine
                # print in magenta (35)
                print("\x1b[{}{}m>> saying: {}\x1b[0m".format(35, '', text))
            time.sleep(2)
            if DEBUG:
                print('Saying "%s" using festival' % text, file=sys.stderr)
            pipe = subprocess.Popen(['/usr/bin/festival'])
            pipe.communicate('(SayText "%s")' % text)
            pipe.terminate()
            time.sleep(5)
        elif ViewClient.isDarwin:
            if verbose:
                # FIXME: should use Colors, but for now it's fine
                # print in magenta (35)
                print("\x1b[{}{}m>> saying: {}\x1b[0m".format(35, '', text))
            time.sleep(1)
            if not voice:
                voice = 'Samantha'
            if DEBUG:
                print('Saying "%s" as %s' % (text, voice), file=sys.stderr)
            subprocess.check_call(['/usr/bin/say', '-v', voice, text])
            time.sleep(5)
        else:
            print("sayText: Unsupported OS: {}".format(ViewClient.osName), file=sys.stderr)

    def getViewIds(self):
        '''
        @deprecated: Use L{getViewsById} instead.

        Returns the Views map.
        '''

        return self.viewsById

    def getViewsById(self):
        '''
        Returns the Views map. The keys are C{uniqueIds} and the values are C{View}s.
        '''

        return self.viewsById

    def __getFocusedWindowPosition(self):
        return self.__getFocusedWindowId()

    def getSdkVersion(self):
        '''
        Gets the SDK version.
        '''

        return self.build[VERSION_SDK_PROPERTY]

    def isKeyboardShown(self):
        '''
        Whether the keyboard is displayed.
        '''

        return self.device.isKeyboardShown()

    def writeImageToFile(self, filename, _format="PNG", deviceart=None, dropshadow=True, screenglare=True):
        '''
        Write the View image to the specified filename in the specified format.

        @type filename: str
        @param filename: Absolute path and optional filename receiving the image. If this points to
                         a directory, then the filename is determined by the serialno of the device and
                         format extension.
        @type _format: str
        @param _format: Image format (default format is PNG)
        '''

        # FIXME: if we try to use uiAutomatorHelper only we don't have device
        if isinstance(self.device, AdbClient):
            filename = self.device.substituteDeviceTemplate(filename)
        else:
            filename = substituteDeviceTemplate(filename)
        if not os.path.isabs(filename):
            raise ValueError("writeImageToFile expects an absolute path (filename='%s')" % filename)
        if os.path.isdir(filename):
            filename = os.path.join(filename, self.serialno + '.' + _format.lower())
        if DEBUG:
            print("writeImageToFile: saving image to '%s' in %s format (reconnect=%s)" % (
                filename, _format, self.device.reconnect), file=sys.stderr)
        if self.uiAutomatorHelper:
            if DEBUG_UI_AUTOMATOR_HELPER:
                print("Taking screenshot using UiAutomatorHelper", file=sys.stderr)
            received = self.uiAutomatorHelper.takeScreenshot()
            stream = io.BytesIO(received.read())
            try:
                from PIL import Image
                image = Image.open(stream)
            except ImportError as ex:
                self.pilNotInstalledWarning()
                sys.exit(1)
            except IOError as ex:
                print(ex, file=sys.stderr)
                print(repr(stream))
                sys.exit(1)
        else:
            image = self.device.takeSnapshot(reconnect=self.device.reconnect)
        if deviceart:
            if 'STUDIO_DIR' in os.environ:
                PLUGIN_DIR = 'plugins/android/lib/device-art-resources'
                osName = platform.system()
                if osName == 'Darwin':
                    deviceArtDir = os.environ['STUDIO_DIR'] + '/Contents/' + PLUGIN_DIR
                else:
                    deviceArtDir = os.environ['STUDIO_DIR'] + '/' + PLUGIN_DIR
                # FIXME: should parse XML
                deviceArtXml = deviceArtDir + '/device-art.xml'
                if not os.path.exists(deviceArtXml):
                    warnings.warn("Cannot find device art definition file")
                # <device id="nexus_5" name="Nexus 5">
                #       <orientation name="port" size="1370,2405" screenPos="144,195" screenSize="1080,1920" shadow="port_shadow.png" back="port_back.png" lights="port_fore.png"/>
                #       <orientation name="land" size="2497,1235" screenPos="261,65" screenSize="1920,1080" shadow="land_shadow.png" back="land_back.png" lights="land_fore.png"/>
                # </device>
                orientation = self.display['orientation']
                if orientation == 0 or orientation == 2:
                    orientationName = 'port'
                elif orientation == 1 or orientation == 3:
                    orientationName = 'land'
                else:
                    warnings.warn("Unknown orientation=" + orientation)
                    orientationName = 'port'
                separator = '_'
                if deviceart == 'auto':
                    hardware = self.device.getProperty('ro.hardware')
                    if hardware == 'hammerhead':
                        deviceart = 'nexus_5'
                    elif hardware == 'mako':
                        deviceart = 'nexus_4'
                    elif hardware == 'grouper':
                        deviceart = 'nexus_7'  # 2012
                    elif hardware == 'flo':
                        deviceart = 'nexus_7_2013'
                    elif hardware in ['mt5861', 'mt5890', 'maserati', 'maxim']:
                        deviceart = 'tv_1080p'
                    elif hardware == 'universal5410':
                        deviceart = 'samsung_s4'

                SUPPORTED_DEVICES = ['nexus_5', 'nexus_4', 'nexus_7', 'nexus_7_2013', 'tv_1080p', 'samsung_s4']
                if deviceart not in SUPPORTED_DEVICES:
                    warnings.warn("Only %s is supported now, more devices coming soon" % SUPPORTED_DEVICES)
                if deviceart == 'auto':
                    # it wasn't detected yet, let's assume generic phone
                    deviceart = 'phone'

                screenSize = None
                if deviceart == 'nexus_5':
                    if orientationName == 'port':
                        screenPos = (144, 195)
                    else:
                        screenPos = (261, 65)
                elif deviceart == 'nexus_4':
                    if orientationName == 'port':
                        screenPos = (94, 187)
                    else:
                        screenPos = (257, 45)
                elif deviceart == 'nexus_7':  # 2012
                    if orientationName == 'port':
                        screenPos = (142, 190)
                    else:
                        screenPos = (260, 105)
                elif deviceart == 'nexus_7_2013':
                    if orientationName == 'port':
                        screenPos = (130, 201)
                        screenSize = (800, 1280)
                    else:
                        screenPos = (282, 80)
                        screenSize = (1280, 800)
                elif deviceart == 'tv_1080p':
                    screenPos = (85, 59)
                    orientationName = ''
                    separator = ''
                elif deviceart == 'samsung_s4':
                    if orientationName == 'port':
                        screenPos = (76, 220)
                        screenSize = (1078, 1902)  # FIXME: (1080, 1920) is the original size
                    else:
                        screenPos = (0, 0)
                elif deviceart == 'phone':
                    if orientationName == 'port':
                        screenPos = (113, 93)
                        screenSize = (343, 46)  # 46?, this is in device-art.xml
                    else:
                        screenPos = (141, 36)
                        screenSize = (324, 255)

                deviceArtModelDir = deviceArtDir + '/' + deviceart
                if not os.path.isdir(deviceArtModelDir):
                    warnings.warn("Cannot find device art for " + deviceart + ' at ' + deviceArtModelDir)
                try:
                    from PIL import Image
                    if dropshadow:
                        dropShadowImage = Image.open(
                            deviceArtModelDir + '/%s%sshadow.png' % (orientationName, separator))
                    deviceBack = Image.open(deviceArtModelDir + '/%s%sback.png' % (orientationName, separator))
                    if dropshadow:
                        dropShadowImage.paste(deviceBack, (0, 0), deviceBack)
                        deviceBack = dropShadowImage
                    if screenSize:
                        image = image.resize(screenSize, Image.ANTIALIAS)
                    deviceBack.paste(image, screenPos)
                    if screenglare:
                        screenGlareImage = Image.open(
                            deviceArtModelDir + '/%s%sfore.png' % (orientationName, separator))
                        deviceBack.paste(screenGlareImage, (0, 0), screenGlareImage)
                    image = deviceBack
                except IOError as ex:
                    warnings.warn(
                        "ViewClient.writeImageToFile: Some new devices have webp art which is still not supported by ViewClient")
                except ImportError as ex:
                    self.pilNotInstalledWarning()
            else:
                warnings.warn(
                    "ViewClient.writeImageToFile: Cannot add device art because STUDIO_DIR environment variable was not set")
        image.save(filename, _format)

    def pilNotInstalledWarning(self):
        warnings.warn('''PIL or Pillow is needed for image manipulation

On Ubuntu install

   $ sudo apt-get install python-imaging python-imaging-tk

On OSX install

   $ brew install homebrew/python/pillow
''')

    def installPackage(self, apk, allowTestApk=False, grantAllPermissions=False):
        command = [self.adb, "-s", self.serialno, "install", "-r"]

        if allowTestApk:
            command.append("-t")

        if grantAllPermissions:
            command.append("-g")

        command.append(apk)
        subprocess.check_call(command, shell=False)

    def uninstallPackage(self, package):
        return subprocess.check_call([self.adb, "-s", self.serialno, "uninstall", package], shell=False)

    @staticmethod
    def writeViewImageToFileInDir(view):
        '''
        Write the View image to the directory specified in C{ViewClient.imageDirectory}.

        @type view: View
        @param view: The view
        '''

        if not ViewClient.imageDirectory:
            raise RuntimeError('You must set ViewClient.imageDiretory in order to use this method')
        view.writeImageToFile(ViewClient.imageDirectory)

    @staticmethod
    def __pickleable(tree):
        '''
        Makes the tree pickleable.
        '''

        def removeDeviceReference(view):
            '''
            Removes the reference to a L{MonkeyDevice}.
            '''

            view.device = None

        ###########################################################################################
        # FIXME: Unfortunately deepcopy does not work with MonkeyDevice objects, which is
        # sadly the reason why we cannot pickle the tree and we need to remove the MonkeyDevice
        # references.
        # We wanted to copy the tree to preserve the original and make piclkleable the copy.
        # treeCopy = copy.deepcopy(tree)
        treeCopy = tree
        # IMPORTANT:
        # This assumes that the first element in the list is the tree root
        ViewClient.__traverse(treeCopy[0], transform=removeDeviceReference)
        ###########################################################################################
        return treeCopy

    def distanceTo(self, tree):
        '''
        Calculates the distance between the current state and the tree passed as argument.

        @type tree: list of Views
        @param tree: Tree of Views
        @return: the distance
        '''
        return ViewClient.distance(ViewClient.__pickleable(self.views), tree)

    @staticmethod
    def distance(tree1, tree2):
        '''
        Calculates the distance between the two trees.

        @type tree1: list of Views
        @param tree1: Tree of Views
        @type tree2: list of Views
        @param tree2: Tree of Views
        @return: the distance
        '''
        ################################################################
        # FIXME: this should copy the entire tree and then transform it #
        ################################################################
        pickleableTree1 = ViewClient.__pickleable(tree1)
        pickleableTree2 = ViewClient.__pickleable(tree2)
        s1 = pickle.dumps(pickleableTree1)
        s2 = pickle.dumps(pickleableTree2)

        if DEBUG_DISTANCE:
            print("distance: calculating distance between", s1[:20], "and", s2[:20], file=sys.stderr)

        l1 = len(s1)
        l2 = len(s2)
        t = float(max(l1, l2))

        if l1 == l2:
            if DEBUG_DISTANCE:
                print("distance: trees have same length, using Hamming distance", file=sys.stderr)
            return ViewClient.__hammingDistance(s1, s2) / t
        else:
            if DEBUG_DISTANCE:
                print("distance: trees have different length, using Levenshtein distance", file=sys.stderr)
            return ViewClient.__levenshteinDistance(s1, s2) / t

    @staticmethod
    def __hammingDistance(s1, s2):
        '''
        Finds the Hamming distance between two strings.

        @param s1: string
        @param s2: string
        @return: the distance
        @raise ValueError: if the lenght of the strings differ
        '''

        l1 = len(s1)
        l2 = len(s2)

        if l1 != l2:
            raise ValueError("Hamming distance requires strings of same size.")

        return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))

    def hammingDistance(self, tree):
        '''
        Finds the Hamming distance between this tree and the one passed as argument.
        '''

        s1 = ' '.join(map(View.__str__, self.views))
        s2 = ' '.join(map(View.__str__, tree))

        return ViewClient.__hammingDistance(s1, s2)

    @staticmethod
    def __levenshteinDistance(s, t):
        '''
        Find the Levenshtein distance between two Strings.

        Python version of Levenshtein distance method implemented in Java at
        U{http://www.java2s.com/Code/Java/Data-Type/FindtheLevenshteindistancebetweentwoStrings.htm}.

        This is the number of changes needed to change one String into
        another, where each change is a single character modification (deletion,
        insertion or substitution).

        The previous implementation of the Levenshtein distance algorithm
        was from U{http://www.merriampark.com/ld.htm}

        Chas Emerick has written an implementation in Java, which avoids an OutOfMemoryError
        which can occur when my Java implementation is used with very large strings.
        This implementation of the Levenshtein distance algorithm
        is from U{http://www.merriampark.com/ldjava.htm}::

            StringUtils.getLevenshteinDistance(null, *)             = IllegalArgumentException
            StringUtils.getLevenshteinDistance(*, null)             = IllegalArgumentException
            StringUtils.getLevenshteinDistance("","")               = 0
            StringUtils.getLevenshteinDistance("","a")              = 1
            StringUtils.getLevenshteinDistance("aaapppp", "")       = 7
            StringUtils.getLevenshteinDistance("frog", "fog")       = 1
            StringUtils.getLevenshteinDistance("fly", "ant")        = 3
            StringUtils.getLevenshteinDistance("elephant", "hippo") = 7
            StringUtils.getLevenshteinDistance("hippo", "elephant") = 7
            StringUtils.getLevenshteinDistance("hippo", "zzzzzzzz") = 8
            StringUtils.getLevenshteinDistance("hello", "hallo")    = 1

        @param s:  the first String, must not be null
        @param t:  the second String, must not be null
        @return: result distance
        @raise ValueError: if either String input C{null}
        '''
        if s is None or t is None:
            raise ValueError("Strings must not be null")

        n = len(s)
        m = len(t)

        if n == 0:
            return m
        elif m == 0:
            return n

        if n > m:
            tmp = s
            s = t
            t = tmp
            n = m;
            m = len(t)

        p = [None] * (n + 1)
        d = [None] * (n + 1)

        for i in range(0, n + 1):
            p[i] = i

        for j in range(1, m + 1):
            if DEBUG_DISTANCE:
                if j % 100 == 0:
                    print("DEBUG:", int(j / (m + 1.0) * 100), "%\r", end=' ', file=sys.stderr)
            t_j = t[j - 1]
            d[0] = j

            for i in range(1, n + 1):
                cost = 0 if s[i - 1] == t_j else 1
                #  minimum of cell to the left+1, to the top+1, diagonally left and up +cost
                d[i] = min(min(d[i - 1] + 1, p[i] + 1), p[i - 1] + cost)

            _d = p
            p = d
            d = _d

        if DEBUG_DISTANCE:
            print("\n", file=sys.stderr)
        return p[n]

    def levenshteinDistance(self, tree):
        '''
        Finds the Levenshtein distance between this tree and the one passed as argument.
        '''

        s1 = ' '.join(map(View.__microStr__, self.views))
        s2 = ' '.join(map(View.__microStr__, tree))

        return ViewClient.__levenshteinDistance(s1, s2)

    @staticmethod
    def excerpt(_str, execute=False):
        code = Excerpt2Code().Parse(_str)
        if execute:
            exec(code)
        else:
            return code


class ConnectedDevice:
    def __init__(self, device, vc, serialno):
        self.device = device
        self.vc = vc
        self.serialno = serialno


class CulebraOptions:
    '''
    Culebra options helper class
    '''

    HELP = 'help'
    VERBOSE = 'verbose'
    VERSION = 'version'
    IGNORE_SECURE_DEVICE = 'ignore-secure-device'
    IGNORE_VERSION_CHECK = 'ignore-version-check'
    FORCE_VIEW_SERVER_USE = 'force-view-server-use'  # Same a ViewClientOptions.FORCE_VIEW_SERVER_USE but with dashes
    DO_NOT_START_VIEW_SERVER = 'do-not-start-view-server'
    DO_NOT_IGNORE_UIAUTOMATOR_KILLED = 'do-not-ignore-uiautomator-killed'
    FIND_VIEWS_BY_ID = 'find-views-by-id'
    FIND_VIEWS_WITH_TEXT = 'find-views-with-text'
    FIND_VIEWS_WITH_CONTENT_DESCRIPTION = 'find-views-with-content-description'
    USE_REGEXPS = 'use-regexps'
    VERBOSE_COMMENTS = 'verbose-comments'
    UNIT_TEST_CLASS = 'unit-test-class'
    UNIT_TEST_METHOD = 'unit-test-method'
    USE_JAR = 'use-jar'
    USE_DICTIONARY = 'use-dictionary'
    DICTIONARY_KEYS_FROM = 'dictionary-keys-from'
    AUTO_REGEXPS = 'auto-regexps'
    START_ACTIVITY = 'start-activity'
    OUTPUT = 'output'
    INTERACTIVE = 'interactive'
    WINDOW = 'window'
    APPEND_TO_SYS_PATH = 'append-to-sys-path'
    PREPEND_TO_SYS_PATH = 'prepend-to-sys-path'
    SAVE_SCREENSHOT = 'save-screenshot'
    SAVE_VIEW_SCREENSHOTS = 'save-view-screenshots'
    GUI = 'gui'
    SCALE = 'scale'
    DO_NOT_VERIFY_SCREEN_DUMP = 'do-not-verify-screen-dump'
    ORIENTATION_LOCKED = 'orientation-locked'
    SERIALNO = 'serialno'
    MULTI_DEVICE = 'multi-device'
    LOG_ACTIONS = 'log-actions'
    DEVICE_ART = 'device-art'
    DROP_SHADOW = 'drop-shadow'
    SCREEN_GLARE = 'glare'
    NULL_BACK_END = 'null-back-end'
    USE_UIAUTOMATOR_HELPER = 'use-uiautomator-helper'
    CONCERTINA = 'concertina'
    CONCERTINA_CONFIG = 'concertina-config'
    INSTALL_APK = 'install-apk'

    SHORT_OPTS = 'HVvIEFSkw:i:t:d:rCUM:j:D:K:R:a:o:pf:W:GuP:Os:mLA:ZB0hcJ:1:X:'
    LONG_OPTS = [HELP, VERBOSE, VERSION, IGNORE_SECURE_DEVICE, IGNORE_VERSION_CHECK, FORCE_VIEW_SERVER_USE,
                 DO_NOT_START_VIEW_SERVER,
                 DO_NOT_IGNORE_UIAUTOMATOR_KILLED,
                 WINDOW + '=',
                 FIND_VIEWS_BY_ID + '=', FIND_VIEWS_WITH_TEXT + '=', FIND_VIEWS_WITH_CONTENT_DESCRIPTION + '=',
                 USE_REGEXPS, VERBOSE_COMMENTS, UNIT_TEST_CLASS, UNIT_TEST_METHOD + '=',
                 USE_JAR + '=', USE_DICTIONARY + '=', DICTIONARY_KEYS_FROM + '=', AUTO_REGEXPS + '=',
                 START_ACTIVITY + '=',
                 OUTPUT + '=', PREPEND_TO_SYS_PATH,
                 SAVE_SCREENSHOT + '=', SAVE_VIEW_SCREENSHOTS + '=',
                 GUI,
                 DO_NOT_VERIFY_SCREEN_DUMP,
                 SCALE + '=',
                 ORIENTATION_LOCKED,
                 SERIALNO + '=',
                 MULTI_DEVICE,
                 LOG_ACTIONS,
                 DEVICE_ART + '=', DROP_SHADOW, SCREEN_GLARE,
                 NULL_BACK_END,
                 USE_UIAUTOMATOR_HELPER,
                 CONCERTINA,
                 CONCERTINA_CONFIG + '=',
                 INSTALL_APK + '=',
                 'debug' + '=',
                 ]
    LONG_OPTS_ARG = {WINDOW: 'WINDOW',
                     FIND_VIEWS_BY_ID: 'BOOL', FIND_VIEWS_WITH_TEXT: 'BOOL',
                     FIND_VIEWS_WITH_CONTENT_DESCRIPTION: 'BOOL',
                     USE_JAR: 'BOOL', USE_DICTIONARY: 'BOOL', DICTIONARY_KEYS_FROM: 'VALUE', AUTO_REGEXPS: 'LIST',
                     START_ACTIVITY: 'COMPONENT',
                     OUTPUT: 'FILENAME',
                     SAVE_SCREENSHOT: 'FILENAME', SAVE_VIEW_SCREENSHOTS: 'DIR',
                     UNIT_TEST_METHOD: 'NAME',
                     SCALE: 'FLOAT',
                     SERIALNO: 'LIST',
                     DEVICE_ART: 'MODEL',
                     CONCERTINA_CONFIG: 'FILENAME',
                     INSTALL_APK: 'FILENAME',
                     'debug': 'LIST', }
    OPTS_HELP = {
        'H': 'prints this help',
        'V': 'verbose comments',
        'v': 'prints version number and exists',
        'k': 'don\'t ignore UiAutomator killed',
        'w': 'use WINDOW content (default: -1, all windows)',
        'i': 'whether to use findViewById() in script',
        't': 'whether to use findViewWithText() in script',
        'd': 'whether to use findViewWithContentDescription',
        'r': 'use regexps in matches',
        'U': 'generates unit test class and script',
        'M': 'generates unit test method. Can be used with or without -U',
        'j': 'use jar and appropriate shebang to run script (deprecated)',
        'D': 'use a dictionary to store the Views found',
        'K': 'dictionary keys from: id, text, content-description',
        'R': 'auto regexps (i.e. clock), implies -r. help list options',
        'a': 'starts Activity before dump',
        'o': 'output filename',
        'p': 'prepend environment variables values to sys.path',
        'f': 'save screenshot to file',
        'W': 'save View screenshots to files in directory',
        'E': 'ignores ADB version check',
        'G': 'presents the GUI (EXPERIMENTAL)',
        'P': 'scale percentage (i.e. 0.5)',
        'u': 'do not verify screen state after dump',
        'O': 'orientation locked in generated test',
        's': 'device serial number (can be more than 1)',
        'm': 'enables multi-device test generation',
        'L': 'log actions using logcat',
        'A': 'device art model to frame screenshot (auto: autodetected)',
        'Z': 'drop shadow for device art screenshot',
        'B': 'screen glare over screenshot',
        '0': 'use a null back-end (no View tree obtained)',
        'h': 'use UiAutomatorHelper',
        'c': 'enable concertina mode (EXPERIMENTAL)',
        'J': 'concertina config file (JSON)',
        '1': 'install APK as precondition (use with -U)',
        'X': 'debug options',
    }


class CulebraTestCase(unittest.TestCase):
    '''
    The base class for all CulebraTests.

    Class variables
    ---------------
    There are some class variables that can be used to change the behavior of the tests.

    B{serialno}: The serial number of the device. This can also be a list of devices for I{mutli-devices}
    tests or the keyword C{all} to run the tests on all available devices or C{default} to run the tests
    only on the default (first) device.

    When a I{multi-device} test is running the available devices are available in a list named
    L{self.devices} which has the corresponding L{ConnectedDevices} entries.

    Also, in the case of I{multi-devices} tests and to be backward compatible with I{single-device} tests
    the default device, the first one in the devices list, is assigned to L{self.device}, L{self.vc} and
    L{self.serialno} too.

    B{verbose}: The verbosity of the tests. This can be changed from the test command line using the
    command line option C{-v} or C{--verbose}.
    '''

    kwargs1 = None
    kwargs2 = None
    devices = None
    ''' The list of connected devices '''
    globalDevices = []
    ''' The list of connected devices (class instance) '''
    defaultDevice = None
    ''' The default L{ConnectedDevice}. Set to the first one found for multi-device cases '''
    serialno = None
    ''' The default connected device C{serialno} '''
    device = None
    ''' The default connected device '''
    vc = None
    ''' The default connected device C{ViewClient} '''
    verbose = False
    options = {}

    @classmethod
    def setUpClass(cls):
        cls.kwargs1 = {'ignoreversioncheck': False, 'verbose': False, 'ignoresecuredevice': False}
        cls.kwargs2 = {'startviewserver': True, 'forceviewserveruse': False, 'autodump': False,
                       'ignoreuiautomatorkilled': True}

    @classmethod
    def tearDownClass(cls):
        if 'useuiautomatorhelper' in cls.kwargs2 and cls.kwargs2['useuiautomatorhelper']:
            for d in cls.globalDevices:
                d.vc.uiAutomatorHelper.quit()

    def __init__(self, methodName='runTest'):
        self.Log = CulebraTestCase.__Log(self)
        unittest.TestCase.__init__(self, methodName=methodName)

    def setUp(self):
        __devices = None

        # Handle the special case for utrunner.py (Pycharm test runner)
        progname = os.path.basename(sys.argv[0])
        if progname == 'utrunner.py':
            testname = sys.argv[1]
            # a string containing the args
            testargs = sys.argv[2] if len(sys.argv) >= 3 else ""
            # used by utrunner.py (usually `true`) but depends on the number of args
            otherarg = sys.argv[3] if len(sys.argv) >= 4 else None
            argslist = testargs.split()
            i = 0
            while i < len(argslist):
                a = argslist[i]
                if a in ['-v', '--verbose']:
                    # make CulebraTestCase.verbose the same as unittest verbose
                    CulebraTestCase.verbose = True
                elif a in ['-s', '--serialno']:
                    if len(argslist) > (i + 1):
                        CulebraTestCase.serialno = argslist[i + 1]
                        i += 1
                    else:
                        raise RuntimeError('serial number missing')
                i += 1
            # remove the test runner arguments, otherwise they will be found by connectToDeviceOrExit()
            try:
                sys.argv.remove(testname)
                sys.argv.remove(testargs)
                sys.argv.remove(otherarg)
            except:
                pass

        if self.kwargs2.get('useuiautomatorhelper'):
            # FIXME: we could find better alternatives for device and serialno when UiAutomatorHelper is used
            # Searialno could be obtained form UiAutomatorHelper too.
            self.vc = ViewClient("UI_AUTOMATOR_HELPER_DEVICE", "UI_AUTOMATOR_HELPER_SERIALNO", **self.kwargs2)
            return

        if self.serialno:
            # serialno can be 1 serialno, multiple serialnos, 'all' or 'default'
            if self.serialno.lower() == 'all':
                __devices = [d.serialno for d in adbclient.AdbClient().getDevices()]
            elif self.serialno.lower() == 'default':
                __devices = [adbclient.AdbClient().getDevices()[0].serialno]
            else:
                __devices = self.serialno.split()
            if len(__devices) > 1:
                self.devices = __devices

        # FIXME: both cases should be unified
        if self.devices:
            __devices = self.devices
            self.devices = []
            for serialno in __devices:
                device, serialno = ViewClient.connectToDeviceOrExit(serialno=serialno, **self.kwargs1)
                if self.options[CulebraOptions.START_ACTIVITY]:
                    # FIXME: we are not considering the uiAutomatorHelper case
                    # see if in lines 4832..4836
                    device.startActivity(component=self.options[CulebraOptions.START_ACTIVITY])
                vc = ViewClient(device, serialno, **self.kwargs2)
                connectedDevice = ConnectedDevice(serialno=serialno, device=device, vc=vc)
                self.devices.append(connectedDevice)
                CulebraTestCase.globalDevices.append(connectedDevice)
            # Select the first devices as default
            self.defaultDevice = self.devices[0]
            self.device = self.defaultDevice.device
            self.serialno = self.defaultDevice.serialno
            self.vc = self.defaultDevice.vc
        else:
            self.devices = []
            if __devices:
                # A list containing only one device was specified
                self.serialno = __devices[0]
            self.device, self.serialno = ViewClient.connectToDeviceOrExit(serialno=self.serialno, **self.kwargs1)
            if CulebraOptions.START_ACTIVITY in self.options and self.options[CulebraOptions.START_ACTIVITY]:
                # FIXME: we are not considering the uiAutomatorHelper case
                # see if in lines 4832..4836
                self.device.startActivity(component=self.options[CulebraOptions.START_ACTIVITY])
            self.vc = ViewClient(self.device, self.serialno, **self.kwargs2)
            # Set the default device, to be consistent with multi-devices case
            connectedDevice = ConnectedDevice(serialno=self.serialno, device=self.device, vc=self.vc)
            self.devices.append(connectedDevice)
            CulebraTestCase.globalDevices.append(connectedDevice)

    def tearDown(self):
        pass

    def preconditions(self):
        if CulebraOptions.ORIENTATION_LOCKED in self.options and self.options[
            CulebraOptions.ORIENTATION_LOCKED] is not None:
            # If orientation locked was set to a valid orientation value then use it to compare
            # against current orientation (when the test is run)
            return (self.device.display['orientation'] == self.options[CulebraOptions.ORIENTATION_LOCKED])
        return True

    def isTestRunningOnMultipleDevices(self):
        return (len(self.devices) > 1)

    @staticmethod
    def __passAll(arg):
        return True

    def all(self, arg, _filter=None):
        # CulebraTestCase.__passAll cannot be specified as the default argument value
        if _filter is None:
            _filter = CulebraTestCase.__passAll
        if DEBUG_MULTI:
            print("all(%s, %s)" % (arg, _filter), file=sys.stderr)
            l = (getattr(d, arg) for d in self.devices)
            for i in l:
                print("    i=", i, file=sys.stderr)
        return list(filter(_filter, (getattr(d, arg) for d in self.devices)))

    def allVcs(self, _filter=None):
        return self.all('vc', _filter)

    def allDevices(self, _filter=None):
        return self.all('device', _filter)

    def allSerialnos(self, _filter=None):
        return self.all('serialno', _filter)

    def log(self, message, priority='D'):
        '''
        Logs a message with the specified priority.
        '''

        self.device.log('CULEBRA', message, priority, CulebraTestCase.verbose)

    class __Log():
        '''
        Log class to simulate C{android.util.Log}
        '''

        def __init__(self, culebraTestCase):
            self.culebraTestCase = culebraTestCase

        def __getattr__(self, attr):
            '''
            Returns the corresponding log method or @C{AttributeError}.
            '''

            if attr in ['v', 'd', 'i', 'w', 'e']:
                return lambda message: self.culebraTestCase.log(message, priority=attr.upper())
            raise AttributeError(self.__class__.__name__ + ' has no attribute "%s"' % attr)

    @staticmethod
    def main(*args, **kwargs):
        # If you want to specify tests classes and methods in the command line you will be forced
        # to include -s or --serialno and the serial number of the device (could be a regexp)
        # as ViewClient would have no way of determine what it is.
        # This could be also a list of devices (delimited by whitespaces) and in such case all of
        # them will be used.
        # The special argument 'all' means all the connected devices.
        ser = ['-s', '--serialno']
        old = '%(failfast)'
        new = '  %s s The serial number[s] to connect to or \'all\'\n%s' % (', '.join(ser), old)
        try:
            unittest.TestProgram.USAGE = unittest.TestProgram.USAGE.replace(old, new)
        except AttributeError as ex:
            print(ex, file=sys.stderr)
        argsToRemove = []
        i = 0
        while i < len(sys.argv):
            a = sys.argv[i]
            if a in ['-v', '--verbose']:
                # make CulebraTestCase.verbose the same as unittest verbose
                CulebraTestCase.verbose = True
            elif a in ser:
                # remove arguments not handled by unittest
                if len(sys.argv) > (i + 1):
                    argsToRemove.append(sys.argv[i])
                    CulebraTestCase.serialno = sys.argv[i + 1]
                    argsToRemove.append(CulebraTestCase.serialno)
                    i += 1
                else:
                    raise RuntimeError('serial number missing')
            i += 1
        for a in argsToRemove:
            sys.argv.remove(a)
        unittest.main(*args, **kwargs)


if __name__ == "__main__":
    try:
        vc = ViewClient(None)
    except:
        print("%s: Don't expect this to do anything" % __file__)
