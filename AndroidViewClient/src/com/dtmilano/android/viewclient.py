# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2014  Diego Torres Milano
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
'''

__version__ = '7.1.2'

import sys
import warnings
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
import types
import time
import signal
import copy
import pickle
import platform
import xml.parsers.expat
from com.dtmilano.android.adb import adbclient

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
WS = "\xfe" # the whitespace replacement char for TEXT_PROPERTY
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

# visibility
VISIBLE = 0x0
INVISIBLE = 0x4
GONE = 0x8

RegexType = type(re.compile(''))
IP_RE = re.compile('^(\d{1,3}\.){3}\d{1,3}$')
ID_RE = re.compile('id/([^/]*)(/(\d+))?')

def _nd(name):
    '''
    @return: Returns a named decimal regex
    '''
    return '(?P<%s>\d+)' % name

def _nh(name):
    '''
    @return: Returns a named hex regex
    '''
    return '(?P<%s>[0-9a-f]+)' % name

def _ns(name, greedy=False):
    '''
    NOTICE: this is using a non-greedy (or minimal) regex

    @type name: str
    @param name: the name used to tag the expression
    @type greedy: bool
    @param greedy: Whether the regex is greedy or not

    @return: Returns a named string regex (only non-whitespace characters allowed)
    '''
    return '(?P<%s>\S+%s)' % (name, '' if greedy else '?')


class Window:
    '''
    Window class
    '''

    def __init__(self, num, winId, activity, wvx, wvy, wvw, wvh, px, py, visibility):
        '''
        Constructor

        @type num: int
        @param num: Ordering number in Window Manager
        @type winId: str
        @param winId: the window ID
        @type activity: str
        @param activity: the activity (or sometimes other component) owning the window
        @type wvx: int
        @param wvx: window's virtual X
        @type wvy: int
        @param wvy: window's virtual Y
        @type wvw: int
        @param wvw: window's virtual width
        @type wvh: int
        @param wvh: window's virtual height
        @type px: int
        @param px: parent's X
        @type py: int
        @param py: parent's Y
        @type visibility: int
        @param visibility: visibility of the window
        '''

        if DEBUG_COORDS: print >> sys.stderr, "Window(%d, %s, %s, %d, %d, %d, %d, %d, %d, %d)" % \
                (num, winId, activity, wvx, wvy, wvw, wvh, px, py, visibility)
        self.num = num
        self.winId = winId
        self.activity = activity
        self.wvx = wvx
        self.wvy = wvy
        self.wvw = wvw
        self.wvh = wvh
        self.px = px
        self.py = py
        self.visibility = visibility

    def __str__(self):
        return "Window(%d, wid=%s, a=%s, x=%d, y=%d, w=%d, h=%d, px=%d, py=%d, v=%d)" % \
                (self.num, self.winId, self.activity, self.wvx, self.wvy, self.wvw, self.wvh, self.px, self.py, self.visibility)


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
    def factory(arg1, arg2, version=-1, forceviewserveruse=False):
        '''
        View factory

        @type arg1: ClassType or dict
        @type arg2: View instance or AdbClient
        '''

        if type(arg1) == types.ClassType:
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

        if attrs and attrs.has_key('class'):
            clazz = attrs['class']
            if clazz == 'android.widget.TextView':
                return TextView(attrs, device, version, forceviewserveruse)
            elif clazz == 'android.widget.EditText':
                return EditText(attrs, device, version, forceviewserveruse)
            else:
                return View(attrs, device, version, forceviewserveruse)
        elif cls:
            if view:
                return cls.__copy(view)
            else:
                return cls(attrs, device, version, forceviewserveruse)
        elif view:
            return copy.copy(view)
        else:
            return View(attrs, device, version, forceviewserveruse)

    @classmethod
    def __copy(cls, view):
        '''
        Copy constructor
        '''

        return cls(view.map, view.device, view.version, view.forceviewserveruse)

    def __init__(self, map, device, version=-1, forceviewserveruse=False):
        '''
        Constructor

        @type map: map
        @param map: the map containing the (attribute, value) pairs
        @type device: MonkeyDevice
        @param device: the device containing this View
        @type version: int
        @param version: the Android SDK version number of the platform where this View belongs. If
                        this is C{-1} then the Android SDK version will be obtained in this
                        constructor.
        @type forceviewserveruse: boolean
        @param forceviewserveruse: Force the use of C{ViewServer} even if the conditions were given
                        to use C{UiAutomator}.
        '''

        self.map = map
        ''' The map that contains the C{attr},C{value} pairs '''
        self.device = device
        ''' The MonkeyDevice '''
        self.children = []
        ''' The children of this View '''
        self.parent = None
        ''' The parent of this View '''
        self.windows = {}
        self.currentFocus = None
        ''' The current focus '''
        self.build = {}
        ''' Build properties '''
        self.version = version
        ''' API version number '''
        self.forceviewserveruse = forceviewserveruse
        ''' Force ViewServer use '''

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
        self.leftProperty = None
        ''' The left property depending on the View attribute format '''
        self.topProperty = None
        ''' The top property depending on the View attribute format '''
        self.widthProperty = None
        ''' The width property depending on the View attribute format '''
        self.heightProperty = None
        ''' The height property depending on the View attribute format '''
        if version >= 16 and self.useUiAutomator:
            self.idProperty = ID_PROPERTY_UI_AUTOMATOR
            self.textProperty = TEXT_PROPERTY_UI_AUTOMATOR
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
        elif version > 10 and (version < 16 or self.useUiAutomator):
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
        elif version == 10:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY_API_10
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
        elif version >= 7 and version < 10:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY_API_10
            self.leftProperty = LEFT_PROPERTY_API_8
            self.topProperty = TOP_PROPERTY_API_8
            self.widthProperty = WIDTH_PROPERTY_API_8
            self.heightProperty = HEIGHT_PROPERTY_API_8
        elif version > 0 and version < 7:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY_API_10
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
        elif version == -1:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
        else:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
            self.leftProperty = LEFT_PROPERTY
            self.topProperty = TOP_PROPERTY
            self.widthProperty = WIDTH_PROPERTY
            self.heightProperty = HEIGHT_PROPERTY
        
    def __getitem__(self, key):
        return self.map[key]

    def __getattr__(self, name):
        if DEBUG_GETATTR:
            print >>sys.stderr, "__getattr__(%s)    version: %d" % (name, self.build[VERSION_SDK_PROPERTY])

        # NOTE:
        # I should try to see if 'name' is a defined method
        # but it seems that if I call locals() here an infinite loop is entered

        if self.map.has_key(name):
            r = self.map[name]
        elif self.map.has_key(name + '()'):
            # the method names are stored in the map with their trailing '()'
            r = self.map[name + '()']
        elif name.count("_") > 0:
            mangledList = self.allPossibleNamesWithColon(name)
            mangledName = self.intersection(mangledList, self.map.keys())
            if len(mangledName) > 0 and self.map.has_key(mangledName[0]):
                r = self.map[mangledName[0]]
            else:
                # Default behavior
                raise AttributeError, name
        else:
            # try removing 'is' prefix
            if DEBUG_GETATTR:
                print >> sys.stderr, "    __getattr__: trying without 'is' prefix"
            suffix = name[2:].lower()
            if self.map.has_key(suffix):
                r = self.map[suffix]
            else:
                # Default behavior
                raise AttributeError, name

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
                print >>sys.stderr, "innerMethod: %s returning %s" % (innerMethod.__name__, r)
            return r

        innerMethod.__name__ = name

        # this should work, but then there's problems with the arguments of innerMethod
        # even if innerMethod(self) is added
        #setattr(View, innerMethod.__name__, innerMethod)
        #setattr(self, innerMethod.__name__, innerMethod)

        return innerMethod

    def __call__(self, *args, **kwargs):
        if DEBUG_CALL:
            print >>sys.stderr, "__call__(%s)" % (args if args else None)

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

    def getParent(self):
        '''
        Gets the parent.
        '''

        return self.parent

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

        if DEBUG_COORDS:
            print >>sys.stderr, "getX(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())
        x = 0

        if self.useUiAutomator:
            x = self.map['bounds'][0][0]
        else:
            try:
                if GET_VISIBILITY_PROPERTY in self.map and self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
                    _x = int(self.map[self.leftProperty])
                    if DEBUG_COORDS: print >>sys.stderr, "   getX: VISIBLE adding %d" % _x
                    x += _x
            except:
                warnings.warn("View %s has no '%s' property" % (self.getId(), self.leftProperty))

        if DEBUG_COORDS: print >>sys.stderr, "   getX: returning %d" % (x)
        return x

    def getY(self):
        '''
        Gets the View Y coordinate
        '''

        if DEBUG_COORDS:
            print >>sys.stderr, "getY(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())
        y = 0

        if self.useUiAutomator:
            y = self.map['bounds'][0][1]
        else:
            try:
                if GET_VISIBILITY_PROPERTY in self.map and self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
                    _y = int(self.map[self.topProperty])
                    if DEBUG_COORDS: print >>sys.stderr, "   getY: VISIBLE adding %d" % _y
                    y += _y
            except:
                warnings.warn("View %s has no '%s' property" % (self.getId(), self.topProperty))

        if DEBUG_COORDS: print >>sys.stderr, "   getY: returning %d" % (y)
        return y

    def getXY(self, debug=False):
        '''
        Returns the I{screen} coordinates of this C{View}.

        @return: The I{screen} coordinates of this C{View}
        '''

        if DEBUG_COORDS or debug:
            try:
                id = self.getId()
            except:
                id = "NO_ID"
            print >> sys.stderr, "getXY(%s %s ## %s)" % (self.getClass(), id, self.getUniqueId())

        x = self.getX()
        y = self.getY()
        if self.useUiAutomator:
            return (x, y)

        parent = self.parent
        if DEBUG_COORDS: print >> sys.stderr, "   getXY: x=%s y=%s parent=%s" % (x, y, parent.getUniqueId() if parent else "None")
        hx = 0
        ''' Hierarchy accumulated X '''
        hy = 0
        ''' Hierarchy accumulated Y '''

        if DEBUG_COORDS: print >> sys.stderr, "   getXY: not using UiAutomator, calculating parent coordinates"
        while parent != None:
            if DEBUG_COORDS: print >> sys.stderr, "      getXY: parent: %s %s <<<<" % (parent.getClass(), parent.getId())
            if SKIP_CERTAIN_CLASSES_IN_GET_XY_ENABLED:
                if parent.getClass() in [ 'com.android.internal.widget.ActionBarView',
                                   'com.android.internal.widget.ActionBarContextView',
                                   'com.android.internal.view.menu.ActionMenuView',
                                   'com.android.internal.policy.impl.PhoneWindow$DecorView' ]:
                    if DEBUG_COORDS: print >> sys.stderr, "   getXY: skipping %s %s (%d,%d)" % (parent.getClass(), parent.getId(), parent.getX(), parent.getY())
                    parent = parent.parent
                    continue
            if DEBUG_COORDS: print >> sys.stderr, "   getXY: parent=%s x=%d hx=%d y=%d hy=%d" % (parent.getId(), x, hx, y, hy)
            hx += parent.getX()
            hy += parent.getY()
            parent = parent.parent

        (wvx, wvy) = self.__dumpWindowsInformation(debug=debug)
        if DEBUG_COORDS or debug:
            print >>sys.stderr, "   getXY: wv=(%d, %d) (windows information)" % (wvx, wvy)
        try:
            fw = self.windows[self.currentFocus]
            if DEBUG_STATUSBAR:
                print >> sys.stderr, "    getXY: focused window=", fw
                print >> sys.stderr, "    getXY: deciding whether to consider statusbar offset because current focused windows is at", (fw.wvx, fw.wvy), "parent", (fw.px, fw.py)
        except KeyError:
            fw = None
        (sbw, sbh) = self.__obtainStatusBarDimensionsIfVisible()
        if DEBUG_COORDS or debug:
            print >>sys.stderr, "   getXY: sb=(%d, %d) (statusbar dimensions)" % (sbw, sbh)
        statusBarOffset = 0
        pwx = 0
        pwy = 0

        if fw:
            if DEBUG_COORDS:
                print >>sys.stderr, "    getXY: focused window=", fw, "sb=", (sbw, sbh)
            if fw.wvy <= sbh: # it's very unlikely that fw.wvy < sbh, that is a window over the statusbar
                if DEBUG_STATUSBAR: print >>sys.stderr, "        getXY: yes, considering offset=", sbh
                statusBarOffset = sbh
            else:
                if DEBUG_STATUSBAR: print >>sys.stderr, "        getXY: no, ignoring statusbar offset fw.wvy=", fw.wvy, ">", sbh

            if fw.py == fw.wvy:
                if DEBUG_STATUSBAR: print >>sys.stderr, "        getXY: but wait, fw.py == fw.wvy so we are adjusting by ", (fw.px, fw.py)
                pwx = fw.px
                pwy = fw.py
            else:
                if DEBUG_STATUSBAR: print >>sys.stderr, "    getXY: fw.py=%d <= fw.wvy=%d, no adjustment" % (fw.py, fw.wvy)

        if DEBUG_COORDS or DEBUG_STATUSBAR or debug:
            print >>sys.stderr, "   getXY: returning (%d, %d) ***" % (x+hx+wvx+pwx, y+hy+wvy-statusBarOffset+pwy)
            print >>sys.stderr, "                     x=%d+%d+%d+%d" % (x,hx,wvx,pwx)
            print >>sys.stderr, "                     y=%d+%d+%d-%d+%d" % (y,hy,wvy,statusBarOffset,pwy)
        return (x+hx+wvx+pwx, y+hy+wvy-statusBarOffset+pwy)

    def getCoords(self):
        '''
        Gets the coords of the View

        @return: A tuple containing the View's coordinates ((L, T), (R, B))
        '''

        if DEBUG_COORDS:
            print >>sys.stderr, "getCoords(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())

        (x, y) = self.getXY();
        w = self.getWidth()
        h = self.getHeight()
        return ((x, y), (x+w, y+h))

    def getPositionAndSize(self):
        '''
        Gets the position and size (X,Y, W, H)

        @return: A tuple containing the View's coordinates (X, Y, W, H)
        '''

        (x, y) = self.getXY();
        w = self.getWidth()
        h = self.getHeight()
        return (x, y, w, h)


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
            if DEBUG_COORDS: print >> sys.stderr, "      __obtainStatusBarDimensionsIfVisible: w=", w, "   w.activity=", w.activity, "%%%"
            if w.activity == 'StatusBar':
                if w.wvy == 0 and w.visibility == 0:
                    if DEBUG_COORDS: print >> sys.stderr, "      __obtainStatusBarDimensionsIfVisible: statusBar=", (w.wvw, w.wvh)
                    sbw = w.wvw
                    sbh = w.wvh
                break

        return (sbw, sbh)

    def __obtainVxVy(self, m):
        wvx = int(m.group('vx'))
        wvy = int(m.group('vy'))
        return wvx, wvy

    def __obtainVwVh(self, m):
        (wvx, wvy) = self.__obtainVxVy(m)
        wvx1 = int(m.group('vx1'))
        wvy1 = int(m.group('vy1'))
        return (wvx1-wvx, wvy1-wvy)

    def __obtainPxPy(self, m):
        px = int(m.group('px'))
        py = int(m.group('py'))
        return (px, py)

    def __dumpWindowsInformation(self, debug=False):
        self.windows = {}
        self.currentFocus = None
        dww = self.device.shell('dumpsys window windows')
        if DEBUG_WINDOWS or debug: print >> sys.stderr, dww
        lines = dww.split('\n')
        widRE = re.compile('^ *Window #%s Window{%s (u\d+ )?%s?.*}:' %
                            (_nd('num'), _nh('winId'), _ns('activity', greedy=True)))
        currentFocusRE = re.compile('^  mCurrentFocus=Window{%s .*' % _nh('winId'))
        viewVisibilityRE = re.compile(' mViewVisibility=0x%s ' % _nh('visibility'))
        # This is for 4.0.4 API-15
        containingFrameRE = re.compile('^   *mContainingFrame=\[%s,%s\]\[%s,%s\] mParentFrame=\[%s,%s\]\[%s,%s\]' %
                             (_nd('cx'), _nd('cy'), _nd('cw'), _nd('ch'), _nd('px'), _nd('py'), _nd('pw'), _nd('ph')))
        contentFrameRE = re.compile('^   *mContentFrame=\[%s,%s\]\[%s,%s\] mVisibleFrame=\[%s,%s\]\[%s,%s\]' %
                             (_nd('x'), _nd('y'), _nd('w'), _nd('h'), _nd('vx'), _nd('vy'), _nd('vx1'), _nd('vy1')))
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

                for l2 in range(l+1, len(lines)):
                    m = widRE.search(lines[l2])
                    if m:
                        l += (l2-1)
                        break
                    m = viewVisibilityRE.search(lines[l2])
                    if m:
                        visibility = int(m.group('visibility'))
                        if DEBUG_COORDS: print >> sys.stderr, "__dumpWindowsInformation: visibility=", visibility
                    if self.build[VERSION_SDK_PROPERTY] >= 17:
                        wvx, wvy = (0, 0)
                        wvw, wvh = (0, 0)
                    if self.build[VERSION_SDK_PROPERTY] >= 16:
                        m = framesRE.search(lines[l2])
                        if m:
                            px, py = self.__obtainPxPy(m)
                            m = contentRE.search(lines[l2+1])
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
                            m = contentFrameRE.search(lines[l2+1])
                            if m:
                                wvx, wvy = self.__obtainVxVy(m)
                                wvw, wvh = self.__obtainVwVh(m)
                    elif self.build[VERSION_SDK_PROPERTY] == 10:
                        m = containingFrameRE.search(lines[l2])
                        if m:
                            px, py = self.__obtainPxPy(m)
                            m = contentFrameRE.search(lines[l2+1])
                            if m:
                                wvx, wvy = self.__obtainVxVy(m)
                                wvw, wvh = self.__obtainVwVh(m)
                    else:
                        warnings.warn("Unsupported Android version %d" % self.build[VERSION_SDK_PROPERTY])

                    #print >> sys.stderr, "Searching policyVisibility in", lines[l2]
                    m = policyVisibilityRE.search(lines[l2])
                    if m:
                        policyVisibility = 0x0 if m.group('policyVisibility') == 'true' else 0x8

                self.windows[winId] = Window(num, winId, activity, wvx, wvy, wvw, wvh, px, py, visibility + policyVisibility)
            else:
                m = currentFocusRE.search(lines[l])
                if m:
                    self.currentFocus = m.group('winId')

        if self.currentFocus in self.windows and self.windows[self.currentFocus].visibility == 0:
            if DEBUG_COORDS or debug:
                print >> sys.stderr, "__dumpWindowsInformation: focus=", self.currentFocus
                print >> sys.stderr, "__dumpWindowsInformation:", self.windows[self.currentFocus]
            w = self.windows[self.currentFocus]
            return (w.wvx, w.wvy)
        else:
            if DEBUG_COORDS: print >> sys.stderr, "__dumpWindowsInformation: (0,0)"
            return (0,0)

    def touch(self, type=adbclient.DOWN_AND_UP):
        '''
        Touches the center of this C{View}
        '''

        (x, y) = self.getCenter()
        if DEBUG_TOUCH:
            print >>sys.stderr, "should touch @ (%d, %d)" % (x, y)
        if VIEW_CLIENT_TOUCH_WORKAROUND_ENABLED and type == adbclient.DOWN_AND_UP:
            if WARNINGS:
                print >> sys.stderr, "ViewClient: touch workaround enabled"
            self.device.touch(x, y, adbclient.DOWN)
            time.sleep(50/1000.0)
            self.device.touch(x+10, y+10, adbclient.UP)
        else:
            self.device.touch(x, y, type)

    def allPossibleNamesWithColon(self, name):
        l = []
        for i in range(name.count("_")):
            name = name.replace("_", ":", 1)
            l.append(name)
        return l

    def intersection(self, l1, l2):
        return list(set(l1) & set(l2))

    def containsPoint(self, (x, y)):
        (X, Y, W, H) = self.getPositionAndSize()
        return (((x >= X) and (x <= (X+W)) and ((y >= Y) and (y <= (Y+H)))))

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

    def variableNameFromId(self):
        _id = self.getId()
        if _id:
            var = _id.replace('.', '_').replace(':', '___').replace('/', '_')
        else:
            _id = self.getUniqueId()
            m = ID_RE.match(_id)
            if m:
                var = m.group(1)
                if m.group(3):
                    var += m.group(3)
                if re.match('^\d', var):
                    var = 'id_' + var
        return var

    def writeImageToFile(self, filename, format="PNG"):
        '''
        Write the View image to the specified filename in the specified format.

        @type filename: str
        @param filename: Absolute path and optional filename receiving the image. If this points to
                         a directory, then the filename is determined by this View unique ID and
                         format extension.
        @type format: str
        @param format: Image format (default format is PNG)
        '''

        if not os.path.isabs(filename):
            raise ValueError("writeImageToFile expects an absolute path")
        if os.path.isdir(filename):
            filename = os.path.join(filename, self.variableNameFromId() + '.' + format.lower())
        if DEBUG:
            print >> sys.stderr, "writeImageToFile: saving image to '%s' in %s format" % (filename, format)
        #self.device.takeSnapshot().getSubImage(self.getPositionAndSize()).writeToFile(filename, format)
        # crop:
        # im.crop(box) ⇒ image
        # Returns a copy of a rectangular region from the current image.
        # The box is a 4-tuple defining the left, upper, right, and lower pixel coordinate.
        ((l, t), (r, b)) = self.getCoords()
        box = (l, t, r, b)
        if DEBUG:
            print >> sys.stderr, "writeImageToFile: cropping", box, "    reconnect=", self.device.reconnect
        self.device.takeSnapshot(reconnect=self.device.reconnect).crop(box).save(filename, format)

    def __smallStr__(self):
        __str = unicode("View[", 'utf-8', 'replace')
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
        __str = unicode("View[", 'utf-8', 'replace')
        if "class" in self.map:
            __str += " class=" + re.sub('.*\.', '', self.map['class'])
        __str += " id=%s" % self.getId()
        __str += " ]"

        return __str

    def __microStr__(self):
        __str = unicode('', 'utf-8', 'replace')
        if "class" in self.map:
            __str += re.sub('.*\.', '', self.map['class'])
        id = self.getId().replace('id/no_id/', '-')
        __str += id
        ((L, T), (R, B)) = self.getCoords()
        __str += '@%04d%04d%04d%04d' % (L, T, R, B)
        __str += ''

        return __str


    def __str__(self):
        __str = unicode("View[", 'utf-8', 'replace')
        if "class" in self.map:
            __str += " class=" + self.map["class"].__str__() + " "
        for a in self.map:
            __str += a + "="
            # decode() works only on python's 8-bit strings
            if isinstance(self.map[a], unicode):
                __str += self.map[a]
            else:
                __str += unicode(str(self.map[a]), 'utf-8', errors='replace')
            __str += " "
        __str += "]   parent="
        if self.parent:
            if "class" in self.parent.map:
                __str += "%s" % self.parent.map["class"]
            else:
                __str += self.parent.getId().__str__()
        else:
            __str += "None"

        return __str

class TextView(View):
    '''
    TextView class.
    '''

    pass

class EditText(TextView):
    '''
    EditText class.
    '''
    
    def type(self, text):
        self.touch()
        time.sleep(0.5)
        escaped = text.replace('%s', '\\%s')
        encoded = escaped.replace(' ', '%s')
        self.device.type(encoded)
        time.sleep(0.5)

    def backspace(self):
        self.touch()
        time.sleep(1)
        self.device.press('KEYCODE_DEL', adbclient.DOWN_AND_UP)

class UiAutomator2AndroidViewClient():
    '''
    UiAutomator XML to AndroidViewClient
    '''

    def __init__(self, device, version):
        self.device = device
        self.version = version
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
                print >> sys.stderr, "bounds=", attributes['bounds']
            self.idCount += 1
            child = View.factory(attributes, self.device, self.version)
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
        parser = xml.parsers.expat.ParserCreate()
        # Set the Expat event handlers to our methods
        parser.StartElementHandler = self.StartElement
        parser.EndElementHandler = self.EndElement
        parser.CharacterDataHandler = self.CharacterData
        # Parse the XML File
        try:
            parserStatus = parser.Parse(uiautomatorxml.encode(encoding='utf-8', errors='replace'), True)
        except xml.parsers.expat.ExpatError, ex:
            print >>sys.stderr, "ERROR: Offending XML:\n", repr(uiautomatorxml)
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
        parser = xml.parsers.expat.ParserCreate()
        # Set the Expat event handlers to our methods
        parser.StartElementHandler = self.StartElement
        parser.EndElementHandler = self.EndElement
        parser.CharacterDataHandler = self.CharacterData
        # Parse the XML
        parserStatus = parser.Parse(excerpt, 1)
        return self.data

class ViewClient:
    '''
    ViewClient is a I{ViewServer} client.

    ViewServer backend
    ==================
    If not running the ViewServer is started on the target device or emulator and then the port
    mapping is created.

    UiAutomator backend
    ===================
    No service is started.
    '''

    def __init__(self, device, serialno, adb=None, autodump=True, forceviewserveruse=False, localport=VIEW_SERVER_PORT, remoteport=VIEW_SERVER_PORT, startviewserver=True, ignoreuiautomatorkilled=False):
        '''
        Constructor

        @type device: MonkeyDevice
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
        '''

        if not device:
            raise Exception('Device is not connected')
        self.device = device
        ''' The C{MonkeyDevice} device instance '''

        if not serialno:
            raise ValueError("Serialno cannot be None")
        self.serialno = self.__mapSerialNo(serialno)
        ''' The serial number of the device '''

        if DEBUG_DEVICE: print >> sys.stderr, "ViewClient: using device with serialno", self.serialno

        if adb:
            if not os.access(adb, os.X_OK):
                raise Exception('adb="%s" is not executable' % adb)
        else:
            # Using adbclient we don't need adb executable yet (maybe it's needed if we want to
            # start adb if not running)
            adb = ViewClient.__obtainAdbPath()

        self.adb = adb
        ''' The adb command '''
        self.root = None
        ''' The root node '''
        self.viewsById = {}
        ''' The map containing all the L{View}s indexed by their L{View.getUniqueId()} '''
        self.display = {}
        ''' The map containing the device's display properties: width, height and density '''
        for prop in [ 'width', 'height', 'density' ]:
            self.display[prop] = -1
            if USE_ADB_CLIENT_TO_GET_BUILD_PROPERTIES:
                try:
                    self.display[prop] = int(device.getProperty('display.' + prop))
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
        for prop in ['secure', 'debuggable']:
            try:
                self.ro[prop] = device.shell('getprop ro.' + prop)[:-2]
            except:
                if WARNINGS:
                    warnings.warn("Couldn't determine ro %s" % prop)
                self.ro[prop] = 'UNKNOWN'

        self.forceViewServerUse = forceviewserveruse
        ''' Force the use of ViewServer even if the conditions to use UiAutomator are satisfied '''
        self.useUiAutomator = (self.build[VERSION_SDK_PROPERTY] >= 16) and not forceviewserveruse # jelly bean 4.1 & 4.2
        if DEBUG:
            print >> sys.stderr, "    ViewClient.__init__: useUiAutomator=", self.useUiAutomator, "sdk=", self.build[VERSION_SDK_PROPERTY], "forceviewserveruse=", forceviewserveruse
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

        if autodump:
            self.dump()

    def __del__(self):
        # should clean up some things
        pass

    @staticmethod
    def __obtainAdbPath():
        '''
        Obtains the ADB path attempting know locations for different OSs
        '''

        osName = platform.system()
        isWindows = False
        if osName.startswith('Windows'):
            adb = 'adb.exe'
            isWindows = True
        else:
            adb = 'adb'

        ANDROID_HOME = os.environ['ANDROID_HOME'] if os.environ.has_key('ANDROID_HOME') else '/opt/android-sdk'
        HOME = os.environ['HOME'] if os.environ.has_key('HOME') else ''

        possibleChoices = [ os.path.join(ANDROID_HOME, 'platform-tools', adb),
                           os.path.join(HOME,  "android", 'platform-tools', adb),
                           os.path.join(HOME,  "android-sdk", 'platform-tools', adb),
                           adb,
                           ]

        if osName.startswith('Windows'):
            possibleChoices.append(os.path.join("""C:\Program Files\Android\android-sdk\platform-tools""", adb))
            possibleChoices.append(os.path.join("""C:\Program Files (x86)\Android\android-sdk\platform-tools""", adb))
        elif osName.startswith('Linux'):
            possibleChoices.append(os.path.join("opt", "android-sdk-linux",  'platform-tools', adb))
            possibleChoices.append(os.path.join(HOME,  "opt", "android-sdk-linux",  'platform-tools', adb))
            possibleChoices.append(os.path.join(HOME,  "android-sdk-linux",  'platform-tools', adb))
        elif osName.startswith('Mac'):
            possibleChoices.append(os.path.join("opt", "android-sdk-mac_x86",  'platform-tools', adb))
            possibleChoices.append(os.path.join(HOME,  "opt", "android-sdk-mac", 'platform-tools', adb))
            possibleChoices.append(os.path.join(HOME,  "android-sdk-mac", 'platform-tools', adb))
            possibleChoices.append(os.path.join(HOME,  "opt", "android-sdk-mac_x86",  'platform-tools', adb))
            possibleChoices.append(os.path.join(HOME,  "android-sdk-mac_x86",  'platform-tools', adb))
        else:
            # Unsupported OS
            pass

        for exeFile in possibleChoices:
            if os.access(exeFile, os.X_OK):
                return exeFile

        for path in os.environ["PATH"].split(os.pathsep):
            exeFile = os.path.join(path, adb)
            if exeFile != None and os.access(exeFile, os.X_OK if not isWindows else os.F_OK):
                return exeFile

        raise Exception('adb="%s" is not executable. Did you forget to set ANDROID_HOME in the environment?' % adb)

    @staticmethod
    def __mapSerialNo(serialno):
        serialno = serialno.strip()
        #ipRE = re.compile('^\d+\.\d+.\d+.\d+$')
        if IP_RE.match(serialno):
            if DEBUG_DEVICE: print >>sys.stderr, "ViewClient: adding default port to serialno", serialno, ADB_DEFAULT_PORT
            return serialno + ':%d' % ADB_DEFAULT_PORT

        ipPortRE = re.compile('^\d+\.\d+.\d+.\d+:\d+$')
        if ipPortRE.match(serialno):
            # nothing to map
            return serialno

        if re.search("[.*()+]", serialno):
            raise ValueError("Regular expression not supported as serialno in ViewClient")

        return serialno

    @staticmethod
    def __obtainDeviceSerialNumber(device):
        if DEBUG_DEVICE: print >>sys.stderr, "ViewClient: obtaining serial number for connected device"
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
            if DEBUG_DEVICE: print >>sys.stderr, "    using adb=%s" % adb
            s = subprocess.Popen([adb, 'get-serialno'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={}).communicate()[0][:-1]
            if s != 'unknown':
                serialno = s
        if DEBUG_DEVICE: print >>sys.stderr, "    serialno=%s" % serialno
        if not serialno:
            warnings.warn("Couldn't obtain the serialno of the connected device")
        return serialno

    @staticmethod
    def setAlarm(timeout):
        osName = platform.system()
        if osName.startswith('Windows'): # alarm is not implemented in Windows
            return
        signal.alarm(timeout)

    @staticmethod
    def connectToDeviceOrExit(timeout=60, verbose=False, ignoresecuredevice=False, serialno=None):
        '''
        Connects to a device which serial number is obtained from the script arguments if available
        or using the default regex C{.*}.

        If the connection is not successful the script exits.
        L{MonkeyRunner.waitForConnection()} returns a L{MonkeyDevice} even if the connection failed.
        Then, to detect this situation, C{device.wake()} is attempted and if it fails then it is
        assumed the previous connection failed.

        @type timeout: int
        @param timeout: timeout for the connection
        @type verbose: bool
        @param verbose: Verbose output
        @type ignoresecuredevice: bool
        @param ignoresecuredevice: Ignores the check for a secure device
        @type serialno: str
        @param serialno: The device or emulator serial number

        @return: the device and serialno used for the connection
        '''

        progname = os.path.basename(sys.argv[0])
        if serialno is None:
            # eat all the extra options the invoking script may have added
            args = sys.argv
            while len(args) > 1 and args[1][0] == '-':
                args.pop(1)
            serialno = args[1] if len(args) > 1 else \
                    os.environ['ANDROID_SERIAL'] if os.environ.has_key('ANDROID_SERIAL') \
                    else '.*'
        if IP_RE.match(serialno):
            # If matches an IP address format and port was not specified add the default
            serialno += ':%d' % ADB_DEFAULT_PORT
        if verbose:
            print >> sys.stderr, 'Connecting to a device with serialno=%s with a timeout of %d secs...' % \
                (serialno, timeout)
        ViewClient.setAlarm(timeout+5)
        device = adbclient.AdbClient(serialno)
        ViewClient.setAlarm(0)
        if verbose:
            print >> sys.stderr, 'Connected to device with serialno=%s' % serialno
        secure = device.getSystemProperty('ro.secure')
        debuggable = device.getSystemProperty('ro.debuggable')
        versionProperty = device.getProperty(VERSION_SDK_PROPERTY)
        if versionProperty:
            version = int(versionProperty)
        else:
            if verbose:
                print "Couldn't obtain device SDK version"
            version = -1

        # we are going to use UiAutomator for versions >= 16 that's why we ignore if the device
        # is secure if this is true
        if secure == '1' and debuggable == '0' and not ignoresecuredevice and version < 16:
            print >> sys.stderr, "%s: ERROR: Device is secure, AndroidViewClient won't work." % progname
            if verbose:
                print >> sys.stderr, "    secure=%s debuggable=%s version=%d ignoresecuredevice=%s" % \
                    (secure, debuggable, version, ignoresecuredevice)
            sys.exit(2)
        if re.search("[.*()+]", serialno) and not re.search("(\d{1,3}\.){3}\d{1,3}", serialno):
            # if a regex was used we have to determine the serialno used
            serialno = ViewClient.__obtainDeviceSerialNumber(device)
        if verbose:
            print >> sys.stderr, 'Actual device serialno=%s' % serialno
        return device, serialno

    @staticmethod
    def traverseShowClassIdAndText(view, extraInfo=None, noextrainfo=None):
        '''
        Shows the View class, id and text if available.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @type extraInfo: method
        @param extraInfo: the View method to add extra info
        @type noextrainfo: bool
        @param noextrainfo: Don't add extra info

        @return: the string containing class, id, and text if available
        '''

        try:
            eis = ''
            if extraInfo:
                eis = extraInfo(view).__str__()
                if not eis and noextrainfo:
                    eis = noextrainfo
            if eis:
                eis = ' ' + eis
            return u'%s %s %s%s' % (view.getClass(), view.getId(), view.getText(), eis)
        except Exception, e:
            return u'Exception in view=%s: %s' % (view.__smallStr__(), e)

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
        Shows the View class, id, text if available and unique id.
        This function can be used as a transform function to L{ViewClient.traverse()}

        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available and the content description
        '''

        return ViewClient.traverseShowClassIdAndText(view, View.getContentDescription, 'NAF')

    @staticmethod
    def traverseShowClassIdTextAndCenter(view):
        '''
        Shows the View class, id and text if available.
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

    # methods that can be used to transform ViewClient.traverse output
    TRAVERSE_CIT = traverseShowClassIdAndText
    ''' An alias for L{traverseShowClassIdAndText(view)} '''
    TRAVERSE_CITUI = traverseShowClassIdTextAndUniqueId
    ''' An alias for L{traverseShowClassIdTextAndUniqueId(view)} '''
    TRAVERSE_CITCD = traverseShowClassIdTextAndContentDescription
    ''' An alias for L{traverseShowClassIdTextAndContentDescription(view)} '''
    TRAVERSE_CITC = traverseShowClassIdTextAndCenter
    ''' An alias for L{traverseShowClassIdTextAndCenter(view)} '''
    TRAVERSE_CITPS = traverseShowClassIdTextPositionAndSize
    ''' An alias for L{traverseShowClassIdTextPositionAndSize(view)} '''

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
            print >>sys.stderr, "serviceResponse: comparing '%s' vs Parcel(%s)" % (response, PARCEL_TRUE)
        return response == PARCEL_TRUE

    def setViews(self, received):
        '''
        Sets L{self.views} to the received value splitting it into lines.

        @type received: str
        @param received: the string received from the I{View Server}
        '''

        if not received or received == "":
            raise ValueError("received is empty")
        self.views = []
        ''' The list of Views represented as C{str} obtained after splitting it into lines after being received from the server. Done by L{self.setViews()}. '''
        self.__parseTree(received.split("\n"))
        if DEBUG:
            print >>sys.stderr, "there are %d views in this dump" % len(self.views)

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
        self.__parseTreeFromUiAutomatorDump(received)
        if DEBUG:
            print >>sys.stderr, "there are %d views in this dump" % len(self.views)


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
                print >>sys.stderr, "found view with id=%s" % viewId

        for attr in strArgs.split():
            m = attrRE.match(attr)
            if m:
                __attr = m.group('attr')
                __parens = '()' if m.group('parens') else ''
                __len = int(m.group('len'))
                __val = m.group('val')
                if WARNINGS and __len != len(__val):
                    warnings.warn("Invalid len: expected: %d   found: %d   s=%s   e=%s" % (__len, len(__val), __val[:50], __val[-50:]))
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
                        print >>sys.stderr, attr, "doesn't match"

        if True: # was assignViewById
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
                    print >>sys.stderr, "adding viewById %s" % viewId
            # We are assigning a new attribute to keep the original id preserved, which could have
            # been NO_ID repeated multiple times
            attrs['uniqueId'] = viewId

        return attrs

    def __parseTree(self, receivedLines):
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
                self.root = View.factory(attrs, self.device, self.build[VERSION_SDK_PROPERTY], self.forceViewServerUse)
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
                child = View.factory(attrs, self.device, self.build[VERSION_SDK_PROPERTY], self.forceViewServerUse)
                if DEBUG: child.raw = v
                if newLevel == treeLevel:
                    parent.add(child)
                    lastView = child
                elif newLevel > treeLevel:
                    if (newLevel - treeLevel) != 1:
                        raise Exception("newLevel jumps %d levels, v=%s" % ((newLevel-treeLevel), v))
                    parent = lastView
                    parents.append(parent)
                    parent.add(child)
                    lastView = child
                    treeLevel = newLevel
                else: # newLevel < treeLevel
                    for i in range(treeLevel - newLevel):
                        parents.pop()
                    parent = parents.pop()
                    parents.append(parent)
                    parent.add(child)
                    treeLevel = newLevel
                    lastView = child
            self.views.append(lastView)
            self.viewsById[lastView.getUniqueId()] = lastView

    def __parseTreeFromUiAutomatorDump(self, receivedXml):
        parser = UiAutomator2AndroidViewClient(self.device, self.build[VERSION_SDK_PROPERTY])
        self.root = parser.Parse(receivedXml)
        self.views = parser.views
        self.viewsById = {}
        for v in self.views:
            self.viewsById[v.getUniqueId()] = v

    def getRoot(self):
        '''
        Gets the root node of the C{View} tree

        @return: the root node of the C{View} tree
        '''
        return self.root

    def traverse(self, root="ROOT", indent="", transform=View.__str__, stream=sys.stdout):
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
        '''

        if type(root) == types.StringType and root == "ROOT":
            root = self.root

        return ViewClient.__traverse(root, indent, transform, stream)
#         if not root:
#             return
#
#         s = transform(root)
#         if s:
#             print >>stream, "%s%s" % (indent, s)
#
#         for ch in root.children:
#             self.traverse(ch, indent=indent+"   ", transform=transform, stream=stream)

    @staticmethod
    def __traverse(root, indent="", transform=View.__str__, stream=sys.stdout):
        if not root:
            return

        s = transform(root)
        if s:
            ius = "%s%s" % (indent, s if isinstance(s, unicode) else unicode(s, 'utf-8', 'replace'))
            print >>stream, ius.encode('utf-8', 'replace')

        for ch in root.children:
            ViewClient.__traverse(ch, indent=indent+"   ", transform=transform, stream=stream)

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
            # NOTICE:
            # Using /dev/tty this works even on devices with no sdcard
            received = unicode(self.device.shell('uiautomator dump /dev/tty >/dev/null'), encoding='utf-8', errors='replace')
            if not received:
                raise RuntimeError('ERROR: Empty UiAutomator dump was received')
            if DEBUG:
                self.received = received
            if DEBUG_RECEIVED:
                print >>sys.stderr, "received %d chars" % len(received)
                print >>sys.stderr
                print >>sys.stderr, repr(received)
                print >>sys.stderr
            onlyKilledRE = re.compile('[\n\S]*Killed[\n\r\S]*', re.MULTILINE)
            if onlyKilledRE.search(received):
                raise RuntimeError('''ERROR: UiAutomator output contains no valid information. UiAutomator was killed, no reason given.''')
            if self.ignoreUiAutomatorKilled:
                if DEBUG_RECEIVED:
                    print >>sys.stderr, "ignoring UiAutomator Killed"
                killedRE = re.compile('</hierarchy>[\n\S]*Killed', re.MULTILINE)
                if killedRE.search(received):
                    received = re.sub(killedRE, '</hierarchy>', received)
                elif DEBUG_RECEIVED:
                    print "UiAutomator Killed: NOT FOUND!"
                # It seems that API18 uiautomator spits this message to stdout
                dumpedToDevTtyRE = re.compile('</hierarchy>[\n\S]*UI hierchary dumped to: /dev/tty.*', re.MULTILINE)
                if dumpedToDevTtyRE.search(received):
                    received = re.sub(dumpedToDevTtyRE, '</hierarchy>', received)
                # API19 seems to send this warning as part of the XML.
                # Let's remove it if present
                received = received.replace('WARNING: linker: libdvm.so has text relocations. This is wasting memory and is a security risk. Please fix.\r\n', '')
                if DEBUG_RECEIVED:
                    print >>sys.stderr, "received=", received
            if re.search('\[: not found', received):
                raise RuntimeError('''ERROR: Some emulator images (i.e. android 4.1.2 API 16 generic_x86) does not include the '[' command.
While UiAutomator back-end might be supported 'uiautomator' command fails.
You should force ViewServer back-end.''')
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
            except socket.error, ex:
                raise RuntimeError("ERROR: Connecting to %s:%d: %s" % (VIEW_SERVER_HOST, self.localPort, ex))
            cmd = 'dump %x\r\n' % window
            if DEBUG:
                print >>sys.stderr, "executing: '%s'" % cmd
            s.send(cmd)
            received = ""
            doneRE = re.compile("DONE")
            ViewClient.setAlarm(120)
            while True:
                if DEBUG_RECEIVED:
                    print >>sys.stderr, "    reading from socket..."
                received += s.recv(1024)
                if doneRE.search(received[-7:]):
                    break
            s.close()
            ViewClient.setAlarm(0)
            if DEBUG:
                self.received = received
            if DEBUG_RECEIVED:
                print >>sys.stderr, "received %d chars" % len(received)
                print >>sys.stderr
                print >>sys.stderr, received
                print >>sys.stderr
            if received:
                for c in received:
                    if ord(c) > 127:
                        received = unicode(received, encoding='utf-8', errors='replace')
                        break
            self.setViews(received)

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
            except socket.error, ex:
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
                print >>sys.stderr, "received %d chars" % len(received)
                print >>sys.stderr
                print >>sys.stderr, received
                print >>sys.stderr

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
        '''
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
        '''

        if not root:
            return None

        if type(root) == types.StringType and root == "ROOT":
            return self.findViewById(viewId, self.root, viewFilter)

        if root.getId() == viewId:
            if viewFilter:
                if viewFilter(root):
                    return root
            else:
                return root

        if re.match('^id/no_id', viewId) or re.match('^id/.+/.+', viewId):
            if root.getUniqueId() == viewId:
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
        '''
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
        '''

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

    def __findViewWithAttributeInTree(self, attr, val, root):
        if not self.root:
            print >>sys.stderr, "ERROR: no root, did you forget to call dump()?"
            return None

        if type(root) == types.StringType and root == "ROOT":
            root = self.root

        if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTree: type val=", type(val)
        if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTree: checking if root=%s has attr=%s == %s" % (root.__smallStr__(), attr, val)

        if isinstance(val, RegexType):
            return self.__findViewWithAttributeInTreeThatMatches(attr, val, root)
        else:
            if root and attr in root.map and root.map[attr] == val:
                if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTree:  FOUND: %s" % root.__smallStr__()
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
            print >>sys.stderr, "ERROR: no root, did you forget to call dump()?"
            return None

        if type(root) == types.StringType and root == "ROOT":
            root = self.root

        if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTreeThatMatches: checking if root=%s attr=%s matches %s" % (root.__smallStr__(), attr, regex)

        if root and attr in root.map and regex.match(root.map[attr]):
            if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTreeThatMatches:  FOUND: %s" % root.__smallStr__()
            return root
            #print >>sys.stderr, "appending root=%s to rlist=%s" % (root.__smallStr__(), rlist)
            #return rlist.append(root)
        else:
            for ch in root.children:
                v = self.__findViewWithAttributeInTreeThatMatches(attr, regex, ch, rlist)
                if v:
                    return v
                    #print >>sys.stderr, "appending v=%s to rlist=%s" % (v.__smallStr__(), rlist)
                    #return rlist.append(v)

        return None
        #return rlist

    def findViewWithAttribute(self, attr, val, root="ROOT"):
        '''
        Finds the View with the specified attribute and value
        '''

        return self.__findViewWithAttributeInTree(attr, val, root)

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
            print >>sys.stderr, "findViewWithText(%s, %s)" % (text, root)
        if isinstance(text, RegexType):
            return self.findViewWithAttributeThatMatches(self.textProperty, text, root)
            #l = self.findViewWithAttributeThatMatches(TEXT_PROPERTY, text)
            #ll = len(l)
            #if ll == 0:
            #    return None
            #elif ll == 1:
            #    return l[0]
            #else:
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
            print >>sys.stderr, "findViewWithTextOrRaise(%s, %s)" % (text, root)
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

    def findViewsContainingPoint(self, (x, y), filter=None):
        '''
        Finds the list of Views that contain the point (x, y).
        '''

        if not filter:
            filter = lambda v: True

        return [v for v in self.views if (v.containsPoint((x,y)) and filter(v))]

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

        dim = self.device.shell('dumpsys input_method')
        if dim:
            # FIXME: API >= 15 ?
            return "mInputShown=true" in dim
        return False

    def writeImageToFile(self, filename, format="PNG"):
        '''
        Write the View image to the specified filename in the specified format.

        @type filename: str
        @param filename: Absolute path and optional filename receiving the image. If this points to
                         a directory, then the filename is determined by the serialno of the device and
                         format extension.
        @type format: str
        @param format: Image format (default format is PNG)
        '''

        if not os.path.isabs(filename):
            raise ValueError("writeImageToFile expects an absolute path")
        if os.path.isdir(filename):
            filename = os.path.join(filename, self.serialno + '.' + format.lower())
        if DEBUG:
            print >> sys.stderr, "writeImageToFile: saving image to '%s' in %s format" % (filename, format)
        self.device.takeSnapshot().save(filename, format)

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
        # FIXME: Unfortunatelly deepcopy does not work with MonkeyDevice objects, which is
        # sadly the reason why we cannot pickle the tree and we need to remove the MonkeyDevice
        # references.
        # We wanted to copy the tree to preserve the original and make piclkleable the copy.
        #treeCopy = copy.deepcopy(tree)
        treeCopy = tree
        # IMPORTANT:
        # This assumes that the first element in the list is the tree root
        ViewClient.__traverse(treeCopy[0], transform=removeDeviceReference)
        ###########################################################################################
        return treeCopy

    def distance(self, tree):
        '''
        Calculates the distance between this tree and the tree passed as argument.

        @type tree: list of Views
        @param tree: Tree of Views
        @return: the distance
        '''
        ################################################################
        #FIXME: this should copy the entire tree and then transform it #
        ################################################################
        pickleableViews = ViewClient.__pickleable(self.views)
        pickleableTree = ViewClient.__pickleable(tree)
        s1 = pickle.dumps(pickleableViews)
        s2 = pickle.dumps(pickleableTree)

        if DEBUG_DISTANCE:
            print >>sys.stderr, "distance: calculating distance between", s1[:20], "and", s2[:20]

        l1 = len(s1)
        l2 = len(s2)
        t = float(max(l1, l2))

        if l1 == l2:
            if DEBUG_DISTANCE:
                print >>sys.stderr, "distance: trees have same length, using Hamming distance"
            return ViewClient.__hammingDistance(s1, s2)/t
        else:
            if DEBUG_DISTANCE:
                print >>sys.stderr, "distance: trees have different length, using Levenshtein distance"
            return ViewClient.__levenshteinDistance(s1, s2)/t

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

        p = [None]*(n+1)
        d = [None]*(n+1)

        for i in range(0, n+1):
            p[i] = i

        for j in range(1, m+1):
            if DEBUG_DISTANCE:
                if j % 100 == 0:
                    print >>sys.stderr, "DEBUG:", int(j/(m+1.0)*100),"%\r",
            t_j = t[j-1]
            d[0] = j

            for i in range(1, n+1):
                cost = 0 if s[i-1] == t_j else 1
                #  minimum of cell to the left+1, to the top+1, diagonally left and up +cost
                d[i] = min(min(d[i-1]+1, p[i]+1), p[i-1]+cost)

            _d = p
            p = d
            d = _d

        if DEBUG_DISTANCE:
            print >> sys.stderr, "\n"
        return p[n]

    def levenshteinDistance(self, tree):
        '''
        Finds the Levenshtein distance between this tree and the one passed as argument.
        '''

        s1 = ' '.join(map(View.__microStr__, self.views))
        s2 = ' '.join(map(View.__microStr__, tree))

        return ViewClient.__levenshteinDistance(s1, s2)

    @staticmethod
    def excerpt(str, execute=False):
        code = Excerpt2Code().Parse(str)
        if execute:
            exec code
        else:
            return code


if __name__ == "__main__":
    try:
        vc = ViewClient(None)
    except:
        print "%s: Don't expect this to do anything" % __file__


