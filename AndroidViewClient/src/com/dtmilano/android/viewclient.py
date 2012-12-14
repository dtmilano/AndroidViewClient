'''
Copyright (C) 2012  Diego Torres Milano
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

@author: diego
'''

__version__ = '2.3.1'

import sys
import subprocess
import re
import socket
import os
import java
import types
import time
import signal
import warnings
import xml.parsers.expat
from com.android.monkeyrunner import MonkeyDevice, MonkeyRunner

DEBUG = False
DEBUG_DEVICE = DEBUG and False
DEBUG_RECEIVED = DEBUG and False
DEBUG_TREE = DEBUG and False
DEBUG_GETATTR = DEBUG and False
DEBUG_COORDS = DEBUG and True
DEBUG_TOUCH = DEBUG and False
DEBUG_STATUSBAR = DEBUG and False
DEBUG_WINDOWS = DEBUG and False
DEBUG_BOUNDS = DEBUG and False

WARNINGS = False

VIEW_SERVER_HOST = 'localhost'
VIEW_SERVER_PORT = 4939


OFFSET = 25
''' This assumes the smallest touchable view on the screen is approximately 50px x 50px
    and touches it at M{(x+OFFSET, y+OFFSET)} '''

USE_MONKEYRUNNER_TO_GET_BUILD_PROPERTIES = True
''' Use monkeyrunner (C{MonkeyDevice.getProperty()}) to obtain the needed properties. If this is
    C{False} then C{adb shell getprop} is used '''

SKIP_CERTAIN_CLASSES_IN_GET_XY_ENABLED = False
''' Skips some classes related with the Action Bar and the PhoneWindow$DecorView in the
    coordinates calculation
    @see: L{View.getXY()} '''

# some device properties
VERSION_SDK_PROPERTY = 'version.sdk'

# some constants for the attributes
ID_PROPERTY = 'mID'
ID_PROPERTY_UI_AUTOMATOR = 'uniqueId'
TEXT_PROPERTY = 'text:mText'
TEXT_PROPERTY_API_10 = 'mText'
TEXT_PROPERTY_UI_AUTOMATOR = 'text'
WS = "\xfe" # the whitespace replacement char for TEXT_PROPERTY
GET_VISIBILITY_PROPERTY = 'getVisibility()'
LAYOUT_TOP_MARGIN_PROPERTY = 'layout:layout_topMargin'

# visibility
VISIBLE = 0x0
INVISIBLE = 0x4
GONE = 0x8

def __nd(name):
    '''
    @return: Returns a named decimal
    '''
    return '(?P<%s>\d+)' % name

def __nh(name):
    '''
    @return: Returns a named hex
    '''
    return '(?P<%s>[0-9a-f]+)' % name

def __ns(name, greedy=False):
    '''
    NOTICE: this is using a non-greedy (or minimal) regex
    
    @type name: str
    @param name: the name used to tag the expression
    @type greedy: bool
    @param greedy: Whether the regex is greedy or not
    
    @return: Returns a named string (only non-whitespace characters allowed)
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
        @type px: int
        @param px: parent's X
        @type py: int
        @param py: parent's Y
        @param wvh: window's virtual height
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
        return "Window(%d, %s, %s, %d, %d, %d, %d, %d, %d, %d)" % \
                (self.num, self.winId, self.activity, self.wvx, self.wvy, self.wvw, self.wvh, self.px, self.py, self.visibility)


class ViewNotFoundException(Exception):
    pass

class View:
    '''
    View class
    '''

    @staticmethod
    def factory(attrs, device, version=-1):
        '''
        View factory
        '''
        
        if attrs.has_key('class'):
            clazz = attrs['class']
            if clazz == 'android.widget.TextView':
                return TextView(attrs, device, version)
            elif clazz == 'android.widget.EditText':
                return EditText(attrs, device, version)
            else:
                return View(attrs, device, version)
        else:
            return View(attrs, device, version)
    
    def __init__(self, map, device, version=-1):
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
        self.build = {}

        if version != -1:
            self.build[VERSION_SDK_PROPERTY] = version
        else:
            try:
                if USE_MONKEYRUNNER_TO_GET_BUILD_PROPERTIES:
                    self.build[VERSION_SDK_PROPERTY] = int(device.getProperty('build.' + VERSION_SDK_PROPERTY))
                else:
                    self.build[VERSION_SDK_PROPERTY] = int(device.shell('getprop ro.build.' + VERSION_SDK_PROPERTY)[:-2])
            except:
                self.build[VERSION_SDK_PROPERTY] = -1
        
        version = self.build[VERSION_SDK_PROPERTY]
        self.useUiAutomator = (version >= 16)
        ''' Whether to use UIAutomator or ViewServer '''
        self.idProperty = None
        ''' The id property depending on the View attribute format '''
        self.textProperty = None
        ''' The text property depending on the View attribute format '''
        if version >= 16:
            self.idProperty = ID_PROPERTY_UI_AUTOMATOR
            self.textProperty = TEXT_PROPERTY_UI_AUTOMATOR
        elif version > 10 and version < 16:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
        elif version > 0 and version <= 10:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY_API_10
        elif version == -1:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
        else:
            self.idProperty = ID_PROPERTY
            self.textProperty = TEXT_PROPERTY
        
    def __getitem__(self, key):
        return self.map[key]
        
    def __getattr__(self, name):
        if DEBUG_GETATTR:
            print >>sys.stderr, "__getattr__(%s)" % (name)
        
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
            if len(mangledName) > 0:
                r = self.map[mangledName[0]]
            else:
                # Default behavior
                raise AttributeError, name
        else:
            # Default behavior
            raise AttributeError, name
        
        # if the method name starts with 'is' let's assume its return value is boolean
        if name[:2] == 'is':
            r = True if r == 'true' else False
        
        # this should not cached in some way
        def innerMethod():
            if DEBUG:
                print >>sys.stderr, "innerMethod: %s returning %s" % (innerMethod.__name__, r)
            return r
        
        innerMethod.__name__ = name
        
        # this should work, but then there's problems with the arguments of innerMethod 
        # even if innerMethod(self) is added
        #setattr(View, innerMethod.__name__, innerMethod)
        #setattr(self, innerMethod.__name__, innerMethod)
        
        return innerMethod
    
    def __call__(self, *args, **kwargs):
        if DEBUG:
            print >>sys.stderr, "__call__(%s)" % (args if args else None)
            
    def getClass(self):
        '''
        Gets the View class
        
        @return:  the View class or None if not defined
        '''
        
        try:
            return self.map['class']
        except:
            return None

    def getId(self):
        '''
        Gets the View Id
        
        @return: the View Id or None if not defined
        @see: L{getUniqueId()}
        '''
        
        try:
            return self.map[self.idProperty]
        except:
            return None

    def getContentDescription(self):
        '''
        Gets the content description
        '''
        
        try:
            return self.map['content-desc']
        except:
            return None
    
    def getParent(self):
        return self.parent
    
    def getText(self):
        '''
        Gets the text attribute
        
        @return: the text attribute or None if not defined
        '''
        
        try:
            return self.map[self.textProperty]
        except Exception:
            return None

    def getHeight(self):
        if self.useUiAutomator:
            return self.map['bounds'][1][1] - self.map['bounds'][0][1]
        else:
            try:
                return int(self.map['layout:getHeight()'])
            except:
                return 0

    def getWidth(self):
        if self.useUiAutomator:
            return self.map['bounds'][1][0] - self.map['bounds'][0][0]
        else:
            try:
                return int(self.map['layout:getWidth()'])
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
                    if DEBUG_COORDS: print >>sys.stderr, "   getX: VISIBLE adding %d" % int(self.map['layout:mLeft'])
                    x += int(self.map['layout:mLeft'])
            except:
                warnings.warn("View %s has no 'layout:mLeft' property" % self.getId())
        
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
                    if DEBUG_COORDS: print >>sys.stderr, "   getY: VISIBLE adding %d" % int(self.map['layout:mTop'])
                    y += int(self.map['layout:mTop'])
            except:
                warnings.warn("View %s has no 'layout:mTop' property" % self.getId())

        if DEBUG_COORDS: print >>sys.stderr, "   getY: returning %d" % (y)
        return y
    
    def getXY(self):
        '''
        Returns the I{screen} coordinates of this C{View}.
        
        @return: The I{screen} coordinates of this C{View}
        '''
        
        if DEBUG_COORDS:
            print >> sys.stderr, "getXY(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())

        x = self.getX()
        y = self.getY()
        parent = self.parent
        if DEBUG_COORDS: print >> sys.stderr, "   getXY: x=%s y=%s parent=%s" % (x, y, parent.getId() if parent else "None")
        hx = 0
        hy = 0
        
        if not self.useUiAutomator:
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

        (wvx, wvy) = self.__dumpWindowsInformation()
        if DEBUG_COORDS:
            print >>sys.stderr, "   getXY: wv=(%d, %d)" % (wvx, wvy)
        try:
            fw = self.windows[self.currentFocus]
            if DEBUG_STATUSBAR:
                print >> sys.stderr, "focused window=", fw
                print >> sys.stderr, "deciding whether to consider statusbar offset because current focused windows is at", (fw.wvx, fw.wvy), "parent", (fw.px, fw.py)
        except KeyError:
            fw = None
        (sbw, sbh) = self.__obtainStatusBarDimensionsIfVisible()
        statusBarOffset = 0
        pwx = 0
        pwy = 0
        
        if fw:
            if fw.wvy <= sbh: # it's very unlikely that fw.wvy < sbh, that is a window over the statusbar
                if DEBUG_STATUSBAR: print >>sys.stderr, "yes, considering offset=", sbh
                statusBarOffset = sbh
            else:
                if DEBUG_STATUSBAR: print >>sys.stderr, "no, ignoring statusbar offset fw.wvy=", fw.wvy, ">", sbh
                
            if fw.py == fw.wvy:
                if DEBUG_STATUSBAR: print >>sys.stderr, "but wait, fw.py == fw.wvy so we are adjusting by ", (fw.px, fw.py)
                pwx = fw.px
                pwy = fw.py
            else:
                if DEBUG_STATUSBAR: print >>sys.stderr, "fw.py=%d <= fw.wvy=%d, no adjustment" % (fw.py, fw.wvy)
            
        if DEBUG_COORDS or DEBUG_STATUSBAR:
            print >>sys.stderr, "   getXY: returning (%d, %d) ***" % (x+hx+wvx+pwx, y+hy+wvy-statusBarOffset+pwy)
        return (x+hx+wvx+pwx, y+hy+wvy-statusBarOffset+pwy)

    def getCoords(self):
        '''
        Gets the coords of the View
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
    
    def __dumpWindowsInformation(self):
        self.windows = {}
        self.currentFocus = None
        dww = self.device.shell('dumpsys window windows')
        if DEBUG_WINDOWS: print >> sys.stderr, dww
        lines = dww.split('\n')
        widRE = re.compile('^ *Window #%s Window{%s (u\d+ )?%s.*}:' %
                            (__nd('num'), __nh('winId'), __ns('activity', greedy=True)))
        currentFocusRE = re.compile('^  mCurrentFocus=Window{%s .*' % __nh('winId'))
        viewVisibilityRE = re.compile(' mViewVisibility=0x%s ' % __nh('visibility'))
        # This is for 4.0.4 API-15
        containingFrameRE = re.compile('^   *mContainingFrame=\[%s,%s\]\[%s,%s\] mParentFrame=\[%s,%s\]\[%s,%s\]' %
                             (__nd('cx'), __nd('cy'), __nd('cw'), __nd('ch'), __nd('px'), __nd('py'), __nd('pw'), __nd('ph')))
        contentFrameRE = re.compile('^   *mContentFrame=\[%s,%s\]\[%s,%s\] mVisibleFrame=\[%s,%s\]\[%s,%s\]' %
                             (__nd('x'), __nd('y'), __nd('w'), __nd('h'), __nd('vx'), __nd('vy'), __nd('vx1'), __nd('vy1')))
        # This is for 4.1 API-16
        framesRE = re.compile('^   *Frames: containing=\[%s,%s\]\[%s,%s\] parent=\[%s,%s\]\[%s,%s\]' %
                               (__nd('cx'), __nd('cy'), __nd('cw'), __nd('ch'), __nd('px'), __nd('py'), __nd('pw'), __nd('ph')))
        contentRE = re.compile('^     *content=\[%s,%s\]\[%s,%s\] visible=\[%s,%s\]\[%s,%s\]' % 
                               (__nd('x'), __nd('y'), __nd('w'), __nd('h'), __nd('vx'), __nd('vy'), __nd('vx1'), __nd('vy1')))
        policyVisibilityRE = re.compile('mPolicyVisibility=%s ' % __ns('policyVisibility', greedy=True))
        
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
                    if self.build[VERSION_SDK_PROPERTY] >= 16:
                        m = framesRE.search(lines[l2])
                        if m:
                            px, py = self.__obtainPxPy(m)
                            m = contentRE.search(lines[l2+1])
                            if m:
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
            if DEBUG_COORDS:
                print >> sys.stderr, "__dumpWindowsInformation: focus=", self.currentFocus
                print >> sys.stderr, "__dumpWindowsInformation:", self.windows[self.currentFocus]
            w = self.windows[self.currentFocus]
            return (w.wvx, w.wvy)
        else:
            if DEBUG_COORDS: print >> sys.stderr, "__dumpWindowsInformation: (0,0)"
            return (0,0)
    
    def touch(self, type=MonkeyDevice.DOWN_AND_UP):
        '''
        Touches the center of this C{View}
        '''
        
        (x, y) = self.getCenter()
        if DEBUG_TOUCH:
            print >>sys.stderr, "should touch @ (%d, %d)" % (x, y)
        if type == MonkeyDevice.DOWN_AND_UP:
            if WARNINGS:
                print >> sys.stderr, "ViewClient: touch workaround enabled"
            self.device.touch(x, y, MonkeyDevice.DOWN)
            time.sleep(50/1000.0)
            self.device.touch(x+10, y+10, MonkeyDevice.UP)
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
    
    def add(self, child):
        '''
        Adds a child
        
        @type child: View
        @param child: The child to add
        '''
        child.parent = self
        self.children.append(child)
        
    def __smallStr__(self):
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
        __str = "View["
        if "class" in self.map:
            __str += " class=" + re.sub('.*\.', '', self.map['class'])
        __str += " id=%s" % self.getId()
        __str += " ]"

        return __str
            
    def __str__(self):
        __str = "View["
        if "class" in self.map:
            __str += " class=" + self.map["class"].__str__() + " "
        for a in self.map:
            __str += a + "=" + self.map[a].__str__() + " "
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
        MonkeyRunner.sleep(1)
        self.device.type(text)
        MonkeyRunner.sleep(1)

    def backspace(self):
        self.touch()
        MonkeyRunner.sleep(1)
        self.device.press('KEYCODE_DEL', MonkeyDevice.DOWN_AND_UP)

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
        self.viewsById = []
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
            self.viewsById.append(child)
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
            self.nodeStack.pop( )

    def CharacterData(self, data):
        '''
        Expat character data event handler
        '''
        
        if data.strip( ):
            data = data.encode( )
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
        parserStatus = parser.Parse(uiautomatorxml, 1)
        return self.root

class ViewClient:
    '''
    ViewClient is a I{ViewServer} client.
    
    If not running the ViewServer is started on the target device or emulator and then the port
    mapping is created.
    '''

    def __init__(self, device, serialno, adb=None, autodump=True, localport=VIEW_SERVER_PORT, remoteport=VIEW_SERVER_PORT, startviewserver=True):
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
        @type localport: int
        @param localport: the local port used in the redirection
        @type remoteport: int
        @param remoteport: the remote port used to start the C{ViewServer} in the device or
                           emulator
        @type startviewserverparam: boolean
        @param startviewserverparam: Whether to start the B{global} ViewServer
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
                raise Exception('adb="%s" is not executable')
        else:
            adb = ViewClient.__obtainAdbPath()

        self.root = None
        ''' The root node '''
        self.viewsById = {}
        ''' The map containing all the L{View}s indexed by their L{uniqueId} '''
        self.display = {}
        ''' The map containing the device's display properties: width, height and density '''
        for prop in [ 'width', 'height', 'density' ]:
            self.display[prop] = -1
            if USE_MONKEYRUNNER_TO_GET_BUILD_PROPERTIES:
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
        for prop in [VERSION_SDK_PROPERTY, 'version.release']:
            self.build[prop] = -1
            try:
                if USE_MONKEYRUNNER_TO_GET_BUILD_PROPERTIES:
                    self.build[prop] = device.getProperty('build.' + prop)
                else:
                    self.build[prop] = device.shell('getprop ro.build.' + prop)[:-2]
            except:
                if WARNINGS:
                    warnings.warn("Couldn't determine build %s" % prop)
                
            if prop == VERSION_SDK_PROPERTY:
                # we expect it to be an int
                self.build[prop] = int(self.build[prop] if self.build[prop] else -1)

        self.useUiAutomator = (self.build[VERSION_SDK_PROPERTY] >= 16) # jelly bean 4.1 & 4.2
        ''' If UIAutomator is supported by the device it will be used '''

        if self.useUiAutomator:
            self.textProperty = TEXT_PROPERTY_UI_AUTOMATOR
        else:
            # FIXME: not true for API <= 10
            self.textProperty = TEXT_PROPERTY
            if startviewserver:
                if not self.serviceResponse(device.shell('service call window 3')):
                    try:
                        self.assertServiceResponse(device.shell('service call window 1 i32 %d' %
                                                        remoteport))
                    except:
                        raise Exception('Cannot start View server.\n'
                                        'This only works on emulator and devices running developer versions.\n'
                                        'Does hierarchyviewer work on your device ?')

            self.localPort = localport
            self.remotePort = remoteport
            # FIXME: it seems there's no way of obtaining the serialno from the MonkeyDevice
            subprocess.check_call([adb, '-s', self.serialno, 'forward', 'tcp:%d' % self.localPort,
                                    'tcp:%d' % self.remotePort])

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
        
        osName = java.lang.System.getProperty('os.name')
        if osName.startswith('Windows'):
            adb = 'adb.exe'
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
            if exeFile != None and os.access(exeFile, os.X_OK):
                return exeFile

        raise Exception('adb="%s" is not executable. Did you forget to set ANDROID_HOME in the environment?' % adb)

    @staticmethod
    def __mapSerialNo(serialno):
        ipRE = re.compile('^\d+\.\d+.\d+.\d+$')
        if ipRE.match(serialno):
            if DEBUG_DEVICE: print >>sys.stderr, "ViewClient: adding default port to serialno", serialno, '5555'
            return serialno + ':5555'
        
        ipPortRE = re.compile('^\d+\.\d+.\d+.\d+:\d+$')
        if ipPortRE.match(serialno):
            # nothing to map
            return serialno
        
        if re.search("[.*()+]", serialno):
            raise ValueError("Regular expression not supported as serialno in ViewClient")

        return serialno
    
    @staticmethod
    def __obtainDeviceSerialNumber(device):
        serialno = device.getProperty('ro.serialno')
        if not serialno:
            serialno = device.shell('getprop ro.serialno')[:-2]
        if not serialno:
            if int(device.shell('getprop ro.kernel.qemu')[:-2]) == 1:
                # FIXME !!!!!
                # this must be calculated from somewhere, though using a fixed serialno for now
                warnings.warn("Running on emulator but no serial number was specified then 'emulator-5554' is used")
                serialno = 'emulator-5554'
        return serialno

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
            # FIXME: perhaps we should restore the popped arguments
            while len(sys.argv) > 1 and sys.argv[1][0] == '-':
                sys.argv.pop(1)
            serialno = sys.argv[1] if len(sys.argv) > 1 else \
                    os.environ['ANDROID_SERIAL'] if os.environ.has_key('ANDROID_SERIAL') \
                    else '.*'
        if verbose:
            print 'Connecting to a device with serialno=%s with a timeout of %d secs...' % (serialno, timeout)
        # Sometimes MonkeyRunner doesn't even timeout (i.e. two connections from same process), so let's
        # handle it here
        setAlarm = True
        osName = java.lang.System.getProperty('os.name')
        if osName.startswith('Windows'):
            # alarm is not implemented in Windows
            setAlarm = False
        if setAlarm:
            signal.alarm(timeout+5)
        device = MonkeyRunner.waitForConnection(timeout, serialno)
        if setAlarm:
            signal.alarm(0)
        try:
            device.wake()
        except java.lang.NullPointerException, e:
            print >> sys.stderr, "%s: ERROR: Couldn't connect to %s: %s" % (progname, serialno, e)
            sys.exit(3)
        if verbose:
            print 'Connected to device with serialno=%s' % serialno
        secure = device.getSystemProperty('ro.secure')
        debuggable = device.getSystemProperty('ro.debuggable')
        version = int(device.getProperty('build.' + VERSION_SDK_PROPERTY))

        # we are going to use UiAutomator for versions >= 16 that's why we ignore if the device
        # is secure if this is true
        if secure == '1' and debuggable == '0' and not ignoresecuredevice and version < 16:
            print >> sys.stderr, "%s: ERROR: Device is secure, AndroidViewClient won't work." % progname
            sys.exit(2)
        if re.search("[.*()+]", serialno) and not re.search("(\d{1,3}\.){3}\d{1,3}", serialno):
            # if a regex was used we have to determine the serialno used
            serialno = ViewClient.__obtainDeviceSerialNumber(device)
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
            return "%s %s %s%s" % (view.getClass(), view.getId(), view.getText(), eis)
        except Exception, e:
            return "Exception in view=%s: %s" % (view.__smallStr__(), e)
        
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
        if DEBUG:
            print >>sys.stderr, "serviceResponse: comparing '%s' vs Parcel(%s)" % (response, PARCEL_TRUE)
        return response == PARCEL_TRUE

    def setViews(self, received):
        '''
        Sets L{self.views} to the received value splitting it into lines.
        
        @type received: str
        @param received: the string received from the I{View server}
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
        
        
    def __splitAttrs(self, strArgs, addViewToViewsById=False):
        '''
        Splits the C{View} attributes in C{strArgs} and optionally adds the view id to the C{viewsById} list.
        
        Unique Ids
        ==========
        It is very common to find C{View}s having B{NO_ID} as the Id. This turns very difficult to 
        use L{self.findViewById()}. To help in this situation this method assigns B{unique Ids} if
        C{addViewToViewsById} is C{True}.
        
        The B{unique Ids} are generated using the pattern C{id/no_id/<number>} with C{<number>} starting
        at 1.
        
        @type strArgs: str
        @param strArgs: the string containing the raw list of attributes and values
        @type addViewToViewsById: boolean
        @param addViewToViewsById: whether to add the parsed list of attributes and values to the
                                   map C{self.viewsById}
        
        @return: Returns the attributes map.
        '''
        
        if self.useUiAutomator:
            raise RuntimeError("This method is not compatible with UIAutomator")
        # replace the spaces in text:mText to preserve them in later split
        # they are translated back after the attribute matches
        textRE = re.compile('%s=%s,' % (TEXT_PROPERTY, __nd('len')))
        m = textRE.search(strArgs)
        if m:
            __textStart = m.end()
            __textLen = int(m.group('len'))
            __textEnd = m.end() + __textLen
            s1 = strArgs[__textStart:__textEnd]
            s2 = s1.replace(' ', WS)
            strArgs = strArgs.replace(s1, s2, 1)

        idRE = re.compile("(?P<viewId>id/\S+)")
        attrRE = re.compile('%s(?P<parens>\(\))?=%s,(?P<val>[^ ]*)' % (__ns('attr'), __nd('len')), flags=re.DOTALL)
        hashRE = re.compile('%s@%s' % (__ns('class'), __nh('oid')))
        
        attrs = {}
        viewId = None
        m = idRE.search(strArgs)
        if m:
            viewId = m.group('viewId')
            if DEBUG:
                print >>sys.stderr, "found %s" % viewId

        for attr in strArgs.split():
            m = attrRE.match(attr)
            if m:
                __attr = m.group('attr')
                __parens = '()' if m.group('parens') else ''
                __len = int(m.group('len'))
                __val = m.group('val')
                if WARNINGS and __len != len(__val):
                    warnings.warn("Invalid len: expected: %d   found: %d   s=%s   e=%s" % (__len, len(__val), __val[:50], __val[-50:]))
                if __attr == TEXT_PROPERTY:
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
        
        if addViewToViewsById:
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
            self.viewsById[viewId] = attrs
                          
        return attrs
    
    def __parseTree(self, receivedLines):
        '''
        Parses the View tree contained in L{self.views}. The tree is created and the root node assigned to L{self.root}.
        '''
        
        self.root = None
        self.viewsById = {}
        parent = None
        parents = []
        treeLevel = -1
        newLevel = -1
        lastView = None
        for v in receivedLines:
            if v == '' or v == 'DONE' or v == 'DONE.':
                break
            self.views.append(v)
            attrs = self.__splitAttrs(v, addViewToViewsById=True)
            if not self.root:
                if v[0] == ' ':
                    raise Exception("Unexpected root element starting with ' '.")
                self.root = View.factory(attrs, self.device, self.build[VERSION_SDK_PROPERTY])
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
                child = View.factory(attrs, self.device, self.build[VERSION_SDK_PROPERTY])
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
    
    def __parseTreeFromUiAutomatorDump(self, receivedXml):
        parser = UiAutomator2AndroidViewClient(self.device, self.build[VERSION_SDK_PROPERTY])
        self.root = parser.Parse(receivedXml)
        self.views = parser.viewsById

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
        if not root:
            return

        if type(root) == types.StringType and root == "ROOT":
            root = self.root

        s = transform(root)
        if s:
            print >>stream, "%s%s" % (indent, s)
        
        for ch in root.children:
            self.traverse(ch, indent=indent+"   ", transform=transform, stream=stream)

    def dump(self, windowId=-1, sleep=1):
        '''
        Dumps the window content.
        
        Sleep is useful to wait some time before obtaining the new content when something in the
        window has changed.
        
        @type windowId: int
        @param windowId: the window id of the window to dump or -1 to dump all windows
        @type sleep: int
        @param sleep: sleep in seconds before proceeding to dump the content
        
        @return: the list of Views as C{str} received from the server after being split into lines
        '''
        
        if sleep > 0:
            MonkeyRunner.sleep(sleep)
            
        if self.useUiAutomator:
            windowDump = '/mnt/sdcard/window_dump.xml'
            if not re.search('dumped', self.device.shell('uiautomator dump %s' % windowDump)):
                raise RuntimeError('ERROR: Getting UIAutomator dump')
            received = self.device.shell('cat %s 2>/dev/null' % windowDump)
            if received:
                received = received.encode('ascii', 'ignore')
            else:
                raise RuntimeError("ERROR: Received empty UIAutomator dump")
            if DEBUG:
                self.received = received
            if DEBUG_RECEIVED:
                print >>sys.stderr, "received %d chars" % len(received)
                print >>sys.stderr
                print >>sys.stderr, received
                print >>sys.stderr
            self.setViewsFromUiAutomatorDump(received)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((VIEW_SERVER_HOST, self.localPort))
            except socket.error, ex:
                raise RuntimeError("ERROR: Connecting to %s:%d: %s" % (VIEW_SERVER_HOST, self.localPort, ex))
            s.send('dump %d\r\n' % windowId)
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
            self.setViews(received)

            if DEBUG_TREE:
                self.traverse(self.root)
            
        return self.views

    def findViewById(self, viewId, root="ROOT"):
        '''
        Finds the View with the specified viewId.
        '''

        if not root:
            return None

        if type(root) == types.StringType and root == "ROOT":
            return self.findViewById(viewId, self.root)

        if root.getId() == viewId:
            return root

        if re.match('^id/no_id', viewId):
            if root.getUniqueId() == viewId:
                return root;
        
        for ch in root.children:
            foundView = self.findViewById(viewId, ch)
            if foundView:
                return foundView

    def findViewByIdOrRaise(self, viewId, root="ROOT"):
        '''
        Finds the View or raise a ViewNotFoundException.
        
        @return: the View found
        @raise ViewNotFoundException: raise the exception if View not found
        '''
        
        view = self.findViewById(viewId, root)
        if view:
            return view
        else:
            raise ViewNotFoundException("Couldn't find view with ID=%s in tree with root=%s" % (viewId, root))
        
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
            raise ViewNotFoundException("Couldn't find view with tag=%s in tree with root=%s" % (tag, root))
    
    def __findViewWithAttributeInTree(self, attr, val, root):
        if not self.root:
            print >>sys.stderr, "ERROR: no root, did you forget to call dump()?"
            return None

        if type(root) == types.StringType and root == "ROOT":
            root = self.root

        if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTree: checking if root=%s has attr=%s == %s" % (root.__smallStr__(), attr, val)
        
        if root and attr in root.map and root.map[attr] == val:
            if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTree:  FOUND: %s" % root.__smallStr__()
            return root
        else:
            for ch in root.children:
                v = self.__findViewWithAttributeInTree(attr, val, ch)
                if v:
                    return v
        
        return None
         
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
            raise ViewNotFoundException("Couldn't find View with %s='%s' in tree with root=%s" % (attr, val, root))
        
    def findViewWithAttributeThatMatches(self, attr, regex, root="ROOT"):
        '''
        Finds the list of Views with the specified attribute matching
        regex
        '''
        
        return self.__findViewWithAttributeInTreeThatMatches(attr, regex, root)
        
    def findViewWithText(self, text, root="ROOT"):
        if type(text).__name__ == 'PatternObject':
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
        
        view = self.findViewWithText(text, root)
        if view:
            return view
        else:
            raise ViewNotFoundException("Coulnd't find View with text='%s' in tree with root=%s" % (text, root))
    
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
    
    def getViewIds(self):
        '''
        Returns the Views map.
        '''

        return self.viewsById
    
    def __getFocusedWindowPosition(self):
        return self.__getFocusedWindowId()


if __name__ == "__main__":
    try:
        vc = ViewClient(None)
    except:
        print "%s: Don't expect this to do anything" % __file__


