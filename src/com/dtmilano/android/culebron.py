# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2022  Diego Torres Milano
Created on oct 6, 2014

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
from __future__ import print_function

import io
import random
import re
import time

import numpy
from culebratester_client import WindowHierarchy

from com.dtmilano.android.common import profileEnd
from com.dtmilano.android.common import profileStart
from com.dtmilano.android.concertina import Concertina
from com.dtmilano.android.keyevent import KEY_EVENT
from com.dtmilano.android.viewclient import ViewClient, View

__version__ = '21.4.2'

import sys
import threading
import warnings
import copy
import os
import platform
from pkg_resources import Requirement, resource_filename

try:
    import PIL
    from PIL import Image

    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False

try:
    from PIL import ImageTk
    import tkinter
    import tkinter.simpledialog
    import tkinter.filedialog
    import tkinter.font
    import tkinter.scrolledtext
    import tkinter.ttk
    from tkinter.constants import DISABLED, NORMAL

    TKINTER_AVAILABLE = True
except:
    try:
        import Tkinter as tkinter
        import tkSimpleDialog
        import tkFileDialog
        import tkFont
        import ScrolledText
        import ttk
        from Tkconstants import DISABLED, NORMAL

        TKINTER_AVAILABLE = True
    except:
        TKINTER_AVAILABLE = False

from ast import literal_eval as make_tuple

CHECK_KEYBOARD_SHOWN = False
PROFILE = False

DEBUG = False
DEBUG_MOVE = DEBUG and False
DEBUG_TOUCH = DEBUG and False
DEBUG_POINT = DEBUG and False
DEBUG_KEY = DEBUG and False
DEBUG_ISCCOF = DEBUG and False
DEBUG_FIND_VIEW = DEBUG and False
DEBUG_CONTEXT_MENU = DEBUG and False
DEBUG_CONCERTINA = DEBUG and False
DEBUG_UI_AUTOMATOR_HELPER = DEBUG and False


class Color:
    GOLD = '#d19615'
    GREEN = '#15d137'
    BLUE = '#1551d1'
    MAGENTA = '#d115af'
    DARK_GRAY = '#222222'
    LIGHT_GRAY = '#dddddd'


class Unit:
    PX = 'PX'
    DIP = 'DIP'


class Operation:
    ASSIGN = 'assign'
    CHANGE_LANGUAGE = 'change_language'
    DEFAULT = 'default'
    DRAG = 'drag'
    DUMP = 'dump'
    FLING_BACKWARD = 'fling_backward'
    FLING_FORWARD = 'fling_forward'
    FLING_TO_BEGINNING = 'fling_to_beginning'
    FLING_TO_END = 'fling_to_end'
    TEST = 'test'
    TEST_TEXT = 'test_text'
    TOUCH_VIEW = 'touch_view'
    TOUCH_VIEW_UI_AUTOMATOR_HELPER = 'touch_view_ui_automator_helper'
    TOUCH_POINT = 'touch_point'
    LONG_TOUCH_POINT = 'long_touch_point'
    LONG_TOUCH_VIEW = 'long_touch_view'
    LONG_TOUCH_VIEW_UI_AUTOMATOR_HELPER = 'long_touch_view_ui_automator_helper'
    LONG_PRESS = 'long_press'
    OPEN_NOTIFICATION = 'open_notification'
    OPEN_QUICK_SETTINGS = 'open_quick_settings'
    TYPE = 'type'
    PRESS = 'press'
    PRESS_UI_AUTOMATOR_HELPER = 'press_ui_automator_helper'
    PRESS_BACK = 'press_back'
    PRESS_BACK_UI_AUTOMATOR_HELPER = 'press_back_ui_automator_helper'
    PRESS_HOME = 'press_home'
    PRESS_HOME_UI_AUTOMATOR_HELPER = 'press_home_ui_automator_helper'
    PRESS_RECENT_APPS = 'press_recent_apps'
    PRESS_RECENT_APPS_UI_AUTOMATOR_HELPER = 'press_recent_apps_ui_automator_helper'
    SAY_TEXT = 'say_text'
    SET_TEXT = 'set_text'
    SNAPSHOT = 'snapshot'
    START_ACTIVITY = 'start_activity'
    SLEEP = 'sleep'
    SWIPE_UI_AUTOMATOR_HELPER = 'swipe_ui_automator_helper'
    TRAVERSE = 'traverse'
    VIEW_SNAPSHOT = 'view_snapshot'
    WAIT_FOR_IDLE_UI_AUTOMATOR_HELPER = 'wait_for_idle_ui_automator_helper'
    WAIT_FOR_WINDOW_UPDATE_UI_AUTOMATOR_HELPER = 'wait_for_window_update_ui_automator_helper'
    WAKE = 'wake'

    COMMAND_NAME_OPERATION_MAP = {'flingBackward': FLING_BACKWARD, 'flingForward': FLING_FORWARD,
                                  'flingToBeginning': FLING_TO_BEGINNING, 'flingToEnd': FLING_TO_END,
                                  'openNotification': OPEN_NOTIFICATION, 'openQuickSettings': OPEN_QUICK_SETTINGS,
                                  }

    @staticmethod
    def fromCommandName(commandName):
        return Operation.COMMAND_NAME_OPERATION_MAP[commandName]

    @staticmethod
    def toCommandName(operation):
        return next((cmd for cmd, op in list(Operation.COMMAND_NAME_OPERATION_MAP.items()) if op == operation), None)


class Culebron:
    APPLICATION_NAME = "Culebra"

    UPPERCASE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    KEYSYM_TO_KEYCODE_MAP = {
        'Home': 'HOME',
        'abovedot': 'HOME',  # Option+H on macOS
        'BackSpace': 'BACK',
        'Left': 'DPAD_LEFT',
        'Right': 'DPAD_RIGHT',
        'Up': 'DPAD_UP',
        'Down': 'DPAD_DOWN',
        'F12': 'F12',
    }

    KEYSYM_CULEBRON_COMMANDS = {
        'F1': None,
        'F5': None
    }

    canvas = None
    imageId = None
    vignetteId = None
    areTargetsMarked = False
    isDragDialogShowed = False
    isGrabbingTouch = False
    isGeneratingTestCondition = False
    isTouchingPoint = False
    isLongTouchingPoint = False
    isLongTouchingView = False
    onTouchListener = None
    snapshotDir = '/tmp'
    snapshotFormat = 'PNG'
    deviceArt = None
    dropShadow = False
    screenGlare = False
    osName = platform.system()
    ''' The OS name. We sometimes need specific behavior. '''
    isDarwin = (osName == 'Darwin')
    ''' Is it Mac OSX? '''

    @staticmethod
    def checkSupportedSdkVersion(sdkVersion):
        if sdkVersion <= 10:
            raise Exception('''culebra GUI requires Android API > 10 to work''')

    @staticmethod
    def checkDependencies():
        if not PIL_AVAILABLE:
            raise Exception('''PIL or Pillow is needed for GUI mode

On Ubuntu install

   $ sudo apt-get install python-imaging python-imaging-tk

On OSX install

   $ brew install homebrew/python/pillow

or, preferred since El Capitan

   $ sudo easy_install pip
   $ sudo pip install pillow

''')
        if not TKINTER_AVAILABLE:
            raise Exception('''Tkinter is needed for GUI mode

This is usually installed by python package. Check your distribution details.
''')

    def __init__(self, vc, device, serialno, printOperation, scale=1, concertina=False, concertinaConfigFile=None):
        '''
        Culebron constructor.
        
        @param vc: The ViewClient used by this Culebron instance. Can be C{None} if no back-end is used.
        @type vc: ViewClient
        @param device: The device
        @type device: L{AdbClient}
        @param serialno: The device's serial number
        @type serialno: str
        @param printOperation: the method invoked to print operations to the script
        @type printOperation: method
        @param scale: the scale of the device screen used to show it on the window
        @type scale: float
        @param concertina: enable concertina mode (see documentation)
        @type concertina: bool
        @param concertinaConfigFile: configuration file for concertina
        @type concertinaConfigFile: str
        '''

        self.vc = vc
        self.dump = None
        if 'CONCERTINA' in self.vc.debug:
            global DEBUG_CONCERTINA
            DEBUG_CONCERTINA = self.vc.debug['CONCERTINA'] is not None
        self.printOperation = printOperation
        self.device = device
        self.sdkVersion = device.getSdkVersion()
        self.serialno = serialno
        self.scale = scale
        self.concertina = concertina
        self.concertinaConfig = dict()
        self.concertinaConfigFile = concertinaConfigFile
        self.window = tkinter.Tk()
        try:
            f = resource_filename(Requirement.parse("androidviewclient"),
                                  "share/pixmaps/culebra.png")
            icon = ImageTk.PhotoImage(file=f)
        except:
            icon = None
        if icon:
            self.window.tk.call('wm', 'iconphoto', self.window._w, icon)
        self.mainMenu = MainMenu(self)
        self.window.config(menu=self.mainMenu)
        self.mainFrame = tkinter.Frame(self.window)
        self.placeholder = tkinter.Frame(self.mainFrame, width=400, height=400, background=Color.LIGHT_GRAY)
        self.placeholder.grid(row=1, column=1, rowspan=4)
        self.sideFrame = tkinter.Frame(self.window)
        self.viewTree = ViewTree(self.sideFrame)
        self.viewDetails = ViewDetails(self.sideFrame)
        self.mainFrame.grid(row=1, column=1, columnspan=1, rowspan=4, sticky=tkinter.N + tkinter.S)
        self.isSideFrameShown = False
        self.isViewTreeShown = False
        self.isViewDetailsShown = False
        self.statusBar = StatusBar(self.window)
        self.statusBar.grid(row=5, column=1, columnspan=2)
        self.statusBar.set("Always press F1 for help")
        self.window.update_idletasks()
        self.markedTargetIds = {}
        self.isTouchingPoint = self.vc is None
        self.coordinatesUnit = Unit.DIP
        self.isLongTouchingPoint = False
        self.isLongTouchingView = False
        self.permanentlyDisableEvents = False
        self.unscaledScreenshot = None
        self.image = None
        self.screenshot = None
        self.iterations = 0
        self.noTargetViewsCount = 0
        if DEBUG:
            try:
                self.printGridInfo()
            except:
                pass

    def printGridInfo(self):
        print("window:", repr(self.window), file=sys.stderr)
        print("main:", repr(self.mainFrame), file=sys.stderr)
        print("main:", self.mainFrame.grid_info(), file=sys.stderr)
        print("side:", repr(self.sideFrame), file=sys.stderr)
        print("side:", self.sideFrame.grid_info(), file=sys.stderr)
        print("tree:", repr(self.viewTree), file=sys.stderr)
        print("tree:", self.viewTree.grid_info(), file=sys.stderr)
        print("details:", repr(self.viewDetails), file=sys.stderr)
        print("details:", self.viewDetails.grid_info(), file=sys.stderr)

    def takeScreenshotAndShowItOnWindow(self):
        '''
        Takes the current screenshot and shows it on the main window.
        It also:
         - sizes the window
         - create the canvas
         - set the focus
         - enable the events
         - create widgets
         - finds the targets (as explained in L{findTargets})
         - hides the vignette (that could have been showed before)
        '''

        if PROFILE:
            print("PROFILING: takeScreenshotAndShowItOnWindow()", file=sys.stderr)
            profileStart()

        if DEBUG:
            print("takeScreenshotAndShowItOnWindow()", file=sys.stderr)
        if self.vc and self.vc.uiAutomatorHelper:
            received = self.vc.uiAutomatorHelper.ui_device.take_screenshot()
            stream = io.BytesIO(received.read())
            try:
                self.unscaledScreenshot = Image.open(stream)
            except IOError as ex:
                print(ex, file=sys.stderr)
                print(repr(stream))
                sys.exit(1)
        else:
            self.unscaledScreenshot = self.device.takeSnapshot(reconnect=True)
        self.image = self.unscaledScreenshot
        (width, height) = self.image.size
        if self.scale != 1:
            scaledWidth = int(width * self.scale)
            scaledHeight = int(height * self.scale)
            self.image = self.image.resize((scaledWidth, scaledHeight), PIL.Image.ANTIALIAS)
            (width, height) = self.image.size
            if self.isDarwin and 14 < self.sdkVersion < 23:
                if sys.version_info[0] < 3:
                    stream = io.StringIO()
                else:
                    stream = io.BytesIO()
                self.image.save(stream, 'GIF')
                import base64
                gif = base64.b64encode(stream.getvalue())
                stream.close()
        if self.canvas is None:
            if DEBUG:
                print("⬜️ Creating canvas", width, 'x', height, file=sys.stderr)
            self.placeholder.grid_forget()
            self.canvas = tkinter.Canvas(self.mainFrame, width=width, height=height)
            if DEBUG:
                print("⬜️ canvas", self.canvas, file=sys.stderr)
            self.canvas.focus_set()
            self.enableEvents()
            self.createMessageArea(width, height)
            self.createVignette(width, height)
        if self.isDarwin and self.scale != 1 and 14 < self.sdkVersion < 23:
            # Extremely weird Tkinter bug, I guess
            # If the image was rotated and then resized if ImageTk.PhotoImage(self.image)
            # is used as usual then the result is a completely transparent image and only
            # the "Please wait..." is seen.
            # Converting it to GIF seems to solve the problem
            self.screenshot = tkinter.PhotoImage(data=gif)
        else:
            self.screenshot = ImageTk.PhotoImage(self.image)
        if self.imageId is not None:
            self.canvas.delete(self.imageId)
        self.imageId = self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.screenshot, tag="screenshot")
        if DEBUG:
            try:
                print("⬜️ Grid info", self.canvas.grid_info(), file=sys.stderr)
            except:
                print("⬜️ Exception getting grid info", file=sys.stderr)
        gridInfo = None
        try:
            gridInfo = self.canvas.grid_info()
        except:
            if DEBUG:
                print("⬜️ Adding canvas to grid (1,1)", file=sys.stderr)
            self.canvas.grid(row=1, column=1, rowspan=4)
        if not gridInfo:
            self.canvas.grid(row=1, column=1, rowspan=4)
        try:
            self.findTargets()
            self.hideVignette()
        except Exception as ex:
            print("⛔️ %s" % ex, file=sys.stderr)
        if DEBUG:
            try:
                self.printGridInfo()
            except:
                pass
        if PROFILE:
            profileEnd()

    def createMessageArea(self, width, height):
        self.__message = tkinter.Label(self.window, text='', background=Color.GOLD, font=('Helvetica', 16),
                                       anchor=tkinter.W)
        self.__message.configure(width=width)
        self.__messageAreaId = self.canvas.create_window(0, 0, anchor=tkinter.NW, window=self.__message)
        self.canvas.itemconfig(self.__messageAreaId, state='hidden')
        self.isMessageAreaVisible = False

    def showMessageArea(self):
        if self.__messageAreaId:
            self.canvas.itemconfig(self.__messageAreaId, state='normal')
            self.isMessageAreaVisible = True
            self.canvas.update_idletasks()

    def hideMessageArea(self):
        if self.__messageAreaId and self.isMessageAreaVisible:
            self.canvas.itemconfig(self.__messageAreaId, state='hidden')
            self.isMessageAreaVisible = False
            self.canvas.update_idletasks()

    def toggleMessageArea(self):
        if self.isMessageAreaVisible:
            self.hideMessageArea()
        else:
            self.showMessageArea()

    def message(self, text, background=None):
        self.__message.config(text=text)
        if background:
            self.__message.config(background=background)
        self.showMessageArea()

    def toast(self, text, background=None, timeout=5):
        if DEBUG:
            print("toast(", text, ",", background, ")", file=sys.stderr)
        self.message(text, background)
        if text:
            t = threading.Timer(timeout, self.hideMessageArea)
            t.start()
        else:
            self.hideMessageArea()

    def createVignette(self, width, height):
        if DEBUG:
            print("🟪 createVignette(%d, %d)" % (width, height), file=sys.stderr)
        self.vignetteId = self.canvas.create_rectangle(0, 0, width, height, fill=Color.MAGENTA,
                                                       stipple='gray50')
        if sys.version_info > (3, 0):
            font = tkinter.font.Font(family='Helvetica', size=int(144 * self.scale))
        else:
            font = tkFont.Font(family='Helvetica', size=int(144 * self.scale))
        msg = "Please\nwait..."
        self.waitMessageShadowId = self.canvas.create_text(width / 2 + 2, height / 2 + 2, text=msg,
                                                           fill=Color.DARK_GRAY, font=font)
        self.waitMessageId = self.canvas.create_text(width / 2, height / 2, text=msg,
                                                     fill=Color.LIGHT_GRAY, font=font)
        self.canvas.update_idletasks()

    def showVignette(self):
        if DEBUG:
            print("🟪 showVignette()", file=sys.stderr)
        if self.canvas is None:
            return
        if self.vignetteId:
            if DEBUG:
                print("🟪     showing vignette id=%d" % self.vignetteId, file=sys.stderr)
            # disable events while we are processing one
            self.disableEvents()
            self.canvas.tag_lower('screenshot')
            self.canvas.lift(self.vignetteId)
            self.canvas.lift(self.waitMessageShadowId)
            self.canvas.lift(self.waitMessageId)
            self.canvas.update_idletasks()

    def hideVignette(self):
        if DEBUG:
            print("🟪 hideVignette()", file=sys.stderr)
        if self.canvas is None:
            return
        if self.vignetteId:
            if DEBUG:
                print("🟪     hiding vignette", file=sys.stderr)
            try:
                self.canvas.tag_lift('screenshot')
            except Exception as ex:
                if DEBUG:
                    print("🟪     exception=%s" % ex, file=sys.stderr)
                self.canvas.lift(self.imageId)
            self.canvas.update_idletasks()
            self.enableEvents()

    def deleteVignette(self):
        if DEBUG:
            print("🟪 deleteVignette()", file=sys.stderr)
        if self.canvas is not None:
            self.canvas.delete(self.vignetteId)
            self.vignetteId = None
            self.canvas.delete(self.waitMessageShadowId)
            self.waitMessageShadowId = None
            self.canvas.delete(self.waitMessageId)
            self.waitMessageId = None

    def showPopupMenu(self, event):
        (scaledX, scaledY) = (event.x / self.scale, event.y / self.scale)
        v = self.findViewContainingPointInTargets(scaledX, scaledY)
        ContextMenu(self, view=v).showPopupMenu(event)

    def showHelp(self):
        d = HelpDialog(self)
        self.window.wait_window(d)

    def showSideFrame(self):
        if not self.isSideFrameShown:
            self.sideFrame.grid(row=1, column=2, rowspan=4, sticky=tkinter.N + tkinter.S)
            self.isSideFrameShown = True
        if DEBUG:
            self.printGridInfo()

    def hideSideFrame(self):
        self.sideFrame.grid_forget()
        self.isSideFrameShown = False
        if DEBUG:
            self.printGridInfo()

    def showViewTree(self):
        self.showSideFrame()
        self.viewTree.grid(row=1, column=1, rowspan=3, sticky=tkinter.N + tkinter.S)
        self.isViewTreeShown = True
        if DEBUG:
            self.printGridInfo()

    def hideViewTree(self):
        self.unmarkTargets()
        self.viewTree.grid_forget()
        self.isViewTreeShown = False
        if not self.isViewDetailsShown:
            self.hideSideFrame()
        if DEBUG:
            self.printGridInfo()

    def showViewDetails(self):
        self.showSideFrame()
        row = 4
        # if self.viewTree.grid_info() != {}:
        #    row += 1
        self.viewDetails.grid(row=row, column=1, rowspan=1, sticky=tkinter.S)
        self.isViewDetailsShown = True
        if DEBUG:
            self.printGridInfo()

    def hideViewDetails(self):
        self.viewDetails.grid_forget()
        self.isViewDetailsShown = False
        if not self.isViewTreeShown:
            self.hideSideFrame()
        if DEBUG:
            self.printGridInfo()

    def viewTreeItemClicked(self, event):
        if DEBUG:
            print("viewTreeitemClicked:", event.__dict__, file=sys.stderr)
        self.unmarkTargets()
        vuid = self.viewTree.viewTree.identify_row(event.y)
        if vuid:
            view = self.vc.viewsById[vuid]
            if view:
                coords = view.getCoords()
                if view.isTarget():
                    self.markTarget(coords[0][0], coords[0][1], coords[1][0], coords[1][1])
                self.viewDetails.set(view)

    def populateViewTree(self, view):
        '''
        Populates the View tree.
        '''

        print('culebron.populateViewTree: getting unique id for %s' % view.__class__.__name__, file=sys.stderr)
        if type(view) == WindowHierarchy:
            print('culebron.populateViewTree: skipping HierarchyView', file=sys.stderr)
            return
        else:
            print('culebron.populateViewTree: %s' % type(view), file=sys.stderr)

        parent_unique_id = ''
        try:
            vuid = view.getUniqueId()
            text = view.__smallStr__()
            parent = view.getParent()
            is_target = view.isTarget()
            if parent:
                parent_unique_id = parent.getUniqueId()
        except AttributeError:
            vuid = view.unique_id
            # FIXME
            # is_target = view.is_target
            is_target = False
            text = view.text
            parent = view.parent
            if parent:
                # FIXME:
                # parent is an int
                # parent_unique_id = parent.unique_id
                parent_unique_id = 0
        if parent is None:
            self.viewTree.insert('', tkinter.END, vuid, text=text)
        else:
            self.viewTree.insert(parent_unique_id, tkinter.END, vuid, text=text, tags=('ttk'))
            self.viewTree.set(vuid, 'T', '*' if is_target else ' ')
            self.viewTree.tag_bind('ttk', '<1>', self.viewTreeItemClicked)

    def findTargets(self):
        '''
        Finds the target Views (i.e. for touches).
        '''

        if DEBUG:
            print("findTargets()", file=sys.stderr)
        LISTVIEW_CLASS = 'android.widget.ListView'
        ''' The ListView class name '''
        self.targets = []
        ''' The list of target coordinates (x1, y1, x2, y2) '''
        self.targetViews = []
        ''' The list of target Views '''
        if CHECK_KEYBOARD_SHOWN:
            if self.device.isKeyboardShown():
                print("#### keyboard is show but handling it is not implemented yet ####", file=sys.stderr)
                # FIXME: still no windows in uiautomator
                window = -1
            else:
                window = -1
        else:
            window = -1
        if self.vc:
            dump = self.vc.dump(window=window, sleep=0.1)
            if not self.vc.uiAutomatorHelper:
                self.printOperation(None, Operation.DUMP, window, dump)
        else:
            dump = []
        self.dump = dump
        # the root element cannot be deleted from Treeview once added.
        # We have no option but to recreate it
        self.viewTree = ViewTree(self.sideFrame)
        for v in dump:
            if DEBUG:
                print("    findTargets: analyzing", v.getClass(), v.getId(), file=sys.stderr)
            if v.getClass() == LISTVIEW_CLASS:
                # We may want to touch ListView elements, not just the ListView
                continue
            parent = v.getParent()
            if (parent and parent.getClass() == LISTVIEW_CLASS and self.isClickableCheckableOrFocusable(parent)) \
                    or self.isClickableCheckableOrFocusable(v):
                # If this is a touchable ListView, let's add its children instead
                # or add it if it's touchable, focusable, whatever
                ((x1, y1), (x2, y2)) = v.getCoords()
                if DEBUG:
                    print("appending target", ((x1, y1, x2, y2)), file=sys.stderr)
                v.setTarget(True)
                self.targets.append((x1, y1, x2, y2))
                self.targetViews.append(v)
                target = True
            else:
                target = False

        # FIXME: we are not populating the view tree now
        # there are some problems with culebratester2
        # if self.vc:
        #    self.vc.traverse(transform=self.populateViewTree)

    def getViewContainingPointAndGenerateTestCondition(self, x, y):
        if DEBUG:
            print('getViewContainingPointAndGenerateTestCondition(%d, %d)' % (x, y), file=sys.stderr)
        self.finishGeneratingTestCondition()
        vlist = self.vc.findViewsContainingPoint((x, y))
        vlist.reverse()
        for v in vlist:
            text = v.getText()
            if text:
                self.toast('Asserting view with text=%s' % text, timeout=5)
                # FIXME: only getText() is invoked by the generated assert(), a parameter
                # should be used to provide different alternatives to printOperation()
                self.printOperation(v, Operation.TEST, text)
                break

    def findViewContainingPointInTargets(self, x, y):
        if self.vc:
            vlist = self.vc.findViewsContainingPoint((x, y))
            if DEBUG_FIND_VIEW:
                print("Views found:", file=sys.stderr)
                for v in vlist:
                    print("   ", v.__smallStr__(), file=sys.stderr)
            vlist.reverse()
            for v in vlist:
                if DEBUG:
                    print("checking if", v, "is in", self.targetViews, file=sys.stderr)
                if v in self.targetViews:
                    if DEBUG_TOUCH:
                        print(file=sys.stderr)
                        print("I guess you are trying to touch:", v, file=sys.stderr)
                        print(file=sys.stderr)
                    return v

        return None

    def getViewContainingPointAndTouch(self, x, y):
        if DEBUG:
            print('getViewContainingPointAndTouch(%d, %d)' % (x, y), file=sys.stderr)
        if self.areEventsDisabled:
            if DEBUG:
                print("Ignoring event", file=sys.stderr)
            self.canvas.update_idletasks()
            return

        self.showVignette()
        if DEBUG_POINT:
            print("getViewsContainingPointAndTouch(x=%s, y=%s)" % (x, y), file=sys.stderr)
            print("self.vc=", self.vc, file=sys.stderr)
        v = self.findViewContainingPointInTargets(x, y)

        if v is None:
            self.hideVignette()
            msg = "There are no explicitly touchable or clickable views here!  Touching with [x,y]"
            self.toast(msg)
            # A partial hack which temporarily toggles touch point
            self.toggleTouchPoint()
            self.touchPoint(x, y)
            self.toggleTouchPoint()
        else:
            if self.vc.uiAutomatorHelper:
                # These operations are only available through uiAutomatorHelper
                if v == self.vc.navBack:
                    self.pressBack()
                    return
                elif v == self.vc.navHome:
                    self.pressHome()
                    return
                elif v == self.vc.navRecentApps:
                    self.pressRecentApps()
                    return

            clazz = v.getClass()
            if clazz == 'android.widget.EditText':
                title = "EditText"
                kwargs = {}
                if DEBUG:
                    print(v, file=sys.stderr)
                if v.isPassword():
                    title = "Password"
                    kwargs = {'show': '*'}
                text = tkinter.simpledialog.askstring(title, "Enter text to type into this field", **kwargs)
                self.canvas.focus_set()
                if text:
                    self.vc.setText(v, text)
                    self.printOperation(v, Operation.SET_TEXT, text)
                else:
                    self.hideVignette()
                    return
            else:
                candidates = [v]

                def findBestCandidate(view):
                    isccf = Culebron.isClickableCheckableOrFocusable(view)
                    cd = view.getContentDescription()
                    text = view.getText()
                    if (cd or text) and not isccf:
                        # because isccf==False this view was not added to the list of targets
                        # (i.e. Settings)
                        candidates.insert(0, view)
                    return None

                if not (v.getText() or v.getContentDescription()) and v.getChildren():
                    self.vc.traverse(root=v, transform=findBestCandidate, stream=None)
                if len(candidates) > 2:
                    warnings.warn("We are in trouble, we have more than one candidate to touch", stacklevel=0)
                candidate = candidates[0]
                self.touchView(candidate, v if candidate != v else None)

        if self.vc.uiAutomatorHelper:
            self.printOperation(None, Operation.WAIT_FOR_WINDOW_UPDATE_UI_AUTOMATOR_HELPER, Operation.DEFAULT)
        else:
            self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
        self.vc.sleep(5)
        self.takeScreenshotAndShowItOnWindow()

    def pressBack(self):
        self.showVignette()
        self.vc.pressBack()
        if self.vc.uiAutomatorHelper:
            self.printOperation(None, Operation.PRESS_BACK_UI_AUTOMATOR_HELPER)
        else:
            self.printOperation(None, Operation.PRESS_BACK)
        self.takeScreenshotAndShowItOnWindow()

    def pressHome(self):
        self.showVignette()
        self.vc.pressHome()
        if self.vc.uiAutomatorHelper:
            self.printOperation(None, Operation.PRESS_HOME_UI_AUTOMATOR_HELPER)
        else:
            self.printOperation(None, Operation.PRESS_HOME)
        self.takeScreenshotAndShowItOnWindow()

    def pressRecentApps(self):
        self.showVignette()
        self.vc.pressRecentApps()
        if self.vc.uiAutomatorHelper:
            self.printOperation(None, Operation.PRESS_RECENT_APPS_UI_AUTOMATOR_HELPER)
        else:
            self.printOperation(None, Operation.PRESS_RECENT_APPS)
        self.vc.sleep(1)
        self.takeScreenshotAndShowItOnWindow()

    def setText(self, v, text):
        if DEBUG:
            print("setText(%s, '%s')" % (v.__tinyStr__(), text), file=sys.stderr)
        # This is deleting the existing text, which should be asked in the dialog, but I would have to implement
        # the dialog myself
        v.setText(text)
        # This is not deleting the text, so appending if there's something
        # v.type(text)
        self.printOperation(v, Operation.TYPE, text)

    def sayText(self, text):
        if DEBUG:
            print("sayText('%s')" % text, file=sys.stderr)
        ViewClient.sayText(text)
        self.printOperation(None, Operation.SAY_TEXT, text)

    def touchView(self, v: View, root=None) -> None:
        # FIXME: v.touch() handles the 2 cases for CulebraTester2-public and adbclient
        # also, we should obtain the selector only once
        v.touch()
        if v.uiAutomatorHelper:
            self.printOperation(v, Operation.TOUCH_VIEW_UI_AUTOMATOR_HELPER, v.obtain_selector())
        else:
            # we pass root=v as an argument so the corresponding findView*() searches in this
            # subtree instead of the full tree
            self.printOperation(v, Operation.TOUCH_VIEW, root)

    def touchPoint(self, x, y):
        '''
        Touches a point in the device screen.
        The generated operation will use the units specified in L{coordinatesUnit} and the
        orientation in L{vc.display['orientation']}.
        '''

        if DEBUG:
            print('touchPoint(%d, %d)' % (x, y), file=sys.stderr)
            print('touchPoint:', type(x), type(y), file=sys.stderr)
        if self.areEventsDisabled:
            if DEBUG:
                print("Ignoring event", file=sys.stderr)
            self.canvas.update_idletasks()
            return
        if DEBUG:
            print("Is touching point:", self.isTouchingPoint, file=sys.stderr)
        if self.isTouchingPoint:
            self.showVignette()
            if self.vc:
                self.vc.touch(x, y)
            if self.coordinatesUnit == Unit.DIP:
                x = round(x / self.device.display['density'], 2)
                y = round(y / self.device.display['density'], 2)
            self.printOperation(None, Operation.TOUCH_POINT, x, y, self.coordinatesUnit,
                                self.device.display['orientation'])
            self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
            # FIXME: can we reduce this sleep? (was 5)
            time.sleep(1)
            self.isTouchingPoint = self.vc is None
            self.takeScreenshotAndShowItOnWindow()
            # self.hideVignette()
            self.statusBar.clear()
            return

    def longTouchPoint(self, x, y):
        '''
        Long-touches a point in the device screen.
        The generated operation will use the units specified in L{coordinatesUnit} and the
        orientation in L{vc.display['orientation']}.
        '''

        if DEBUG:
            print('longTouchPoint(%d, %d)' % (x, y), file=sys.stderr)
        if self.areEventsDisabled:
            if DEBUG:
                print("Ignoring event", file=sys.stderr)
            self.canvas.update_idletasks()
            return
        if DEBUG:
            print("Is long touching point:", self.isLongTouchingPoint, file=sys.stderr)
        if self.isLongTouchingPoint:
            self.showVignette()
            self.vc.longTouch(x, y)
            if self.coordinatesUnit == Unit.DIP:
                x = round(x / self.device.display['density'], 2)
                y = round(y / self.device.display['density'], 2)
            self.printOperation(None, Operation.LONG_TOUCH_POINT, x, y, 2000, self.coordinatesUnit,
                                self.device.display['orientation'])
            self.sleep(5)
            self.isLongTouchingPoint = False
            self.takeScreenshotAndShowItOnWindow()
            # self.hideVignette()
            self.statusBar.clear()
            return

    def longTouchView(self, v: View, root=None) -> None:
        # FIXME: v.longTouch() handles the 2 cases for CulebraTester2-public and adbclient
        # also, we should obtain the selector only once
        v.longTouch()
        if v.uiAutomatorHelper:
            self.printOperation(v, Operation.LONG_TOUCH_VIEW_UI_AUTOMATOR_HELPER, v.obtain_selector())
        else:
            # we pass root=v as an argument so the corresponding findView*() searches in this
            # subtree instead of the full tree
            self.printOperation(v, Operation.LONG_TOUCH_VIEW, root)
        self.isLongTouchingView = False

    def onButton1Pressed(self, event):
        if DEBUG:
            print("onButton1Pressed((", event.x, ", ", event.y, "))", file=sys.stderr)
        (scaledX, scaledY) = (event.x / self.scale, event.y / self.scale)
        if DEBUG:
            print("    onButton1Pressed: scaled: (", scaledX, ", ", scaledY, ")", file=sys.stderr)
            print("    onButton1Pressed: is grabbing:", self.isGrabbingTouch, file=sys.stderr)

        if self.isGrabbingTouch:
            self.onTouchListener((scaledX, scaledY))
            self.isGrabbingTouch = False
        elif self.isDragDialogShowed:
            self.toast("No touch events allowed while setting drag parameters", background=Color.GOLD)
            return
        elif self.isTouchingPoint:
            self.touchPoint(scaledX, scaledY)
        elif self.isLongTouchingPoint:
            self.longTouchPoint(scaledX, scaledY)
        elif self.isLongTouchingView:
            self.getViewContainingPointAndLongTouch(scaledX, scaledY)
        elif self.isGeneratingTestCondition:
            self.getViewContainingPointAndGenerateTestCondition(scaledX, scaledY)
        else:
            if self.vc:
                self.getViewContainingPointAndTouch(scaledX, scaledY)
            else:
                # If we don't have Views, there no other option than touching points
                self.touchPoint(scaledX, scaledY)

    def onCtrlButton1Pressed(self, event):
        if DEBUG:
            print(f"onCtrlButton1Pressed(({event.x}, {event.y}))", file=sys.stderr)
        (scaledX, scaledY) = (event.x / self.scale, event.y / self.scale)
        l = self.vc.findViewsContainingPoint((scaledX, scaledY))
        if l and len(l) > 0:
            self.saveViewSnapshot(l[-1])
        else:
            msg = "There are no views here!"
            self.toast(msg)
            return

    def onButton2Pressed(self, event):
        if DEBUG:
            print("onButton2Pressed((", event.x, ", ", event.y, "))", file=sys.stderr)
        osName = platform.system()
        if osName == 'Darwin':
            self.showPopupMenu(event)

    def onButton3Pressed(self, event):
        if DEBUG:
            print("onButton3Pressed((", event.x, ", ", event.y, "))", file=sys.stderr)
        self.showPopupMenu(event)

    def command(self, keycode: str) -> None:
        """
        Presses a key.
        Generates the actual key press on the device and prints the line in the script.

        :param keycode the keycode name
        """

        if self.vc.uiAutomatorHelper:
            try:
                if not keycode.startswith('KEYCODE_'):
                    keycode = f'KEYCODE_{keycode}'
                self.vc.uiAutomatorHelper.ui_device.press_key_code(KEY_EVENT[f'{keycode}'])
                self.printOperation(None, Operation.PRESS_UI_AUTOMATOR_HELPER, keycode)
            except Exception as e:
                print(e, file=sys.stderr)
        else:
            self.device.press(keycode)
            self.printOperation(None, Operation.PRESS, keycode)

    def onKeyPressed(self, event):
        if DEBUG_KEY:
            print("onKeyPressed(", repr(event), ")", file=sys.stderr)
            print(f'    char: type={type(event.char)} len={len(event.char)} repr={repr(event.char)}\n' +
                  f'    keysym={event.keysym}, keycode={event.keycode}, type={event.type}, state={event.state}',
                  file=sys.stderr)
            print("    events disabled:", self.areEventsDisabled, file=sys.stderr)
        if self.areEventsDisabled:
            if DEBUG_KEY:
                print("    ignoring event", file=sys.stderr)
            self.canvas.update_idletasks()
            return

        char = event.char
        keysym = event.keysym
        state = event.state

        # Manual way to get the modifiers
        # https://stackoverflow.com/a/34482048/236465
        ctrl = (state & 0x4) != 0
        alt = (state & 0x8) != 0 or (state & 0x80) != 0
        shift = (state & 0x1) != 0

        if ctrl:
            try:
                return getattr(self, f'onCtrl{keysym.upper()}')(event)
            except AttributeError:
                pass

        if len(char) == 0 and not (
                keysym in Culebron.KEYSYM_TO_KEYCODE_MAP or keysym in Culebron.KEYSYM_CULEBRON_COMMANDS):
            if DEBUG_KEY:
                print(f'    returning because len(char) == 0 keysym={keysym}', file=sys.stderr)
            return

        ###
        ### internal commands: no output to generated script
        ###
        if keysym == 'F1':
            self.showHelp()
            return
        elif keysym == 'F5':
            self.refresh()
            return
        elif keysym == 'F8':
            self.printGridInfo()
            return
        elif keysym == 'Alt_L':
            return
        elif keysym == 'Control_L':
            return
        elif keysym == 'Escape':
            # we cannot send Escape to the device, but I think it's fine
            self.cancelOperation()
            return

        ### empty char (modifier) ###
        # here does not process events  like Home where char is ''
        # if char == '':
        #    return

        ###
        ### target actions
        ###
        self.showVignette()

        if keysym in Culebron.KEYSYM_TO_KEYCODE_MAP:
            if DEBUG_KEY:
                print("Pressing", Culebron.KEYSYM_TO_KEYCODE_MAP[keysym], file=sys.stderr)
            # ALT-F12 is handled as a special case
            if keysym == 'F12' and (event.state == 8 or event.state == 24):
                if DEBUG_KEY:
                    print("Special ALT-F12 case", file=sys.stderr)
                for d in ['/dev/input/event2', '/dev/input/event6']:
                    self.device.longPress('MOVE_HOME', duration=0.1, dev=d, scancode=0x700e3, repeat=50)
                    self.printOperation(None, Operation.LONG_PRESS, 'MOVE_HOME', 0.1, d, 0x700e3, 50)
            else:
                self.command(Culebron.KEYSYM_TO_KEYCODE_MAP[keysym])
        # ALT-M
        elif keysym == 'm' and alt:
            if DEBUG_KEY:
                print("Sending MENU", file=sys.stderr)
            self.command('MENU')
        # OPTION-ENTER (mac)
        elif keysym == 'Return' and event.state == 16:
            if DEBUG_KEY:
                print("Sending DPAD_CENTER", file=sys.stderr)
            self.command('DPAD_CENTER')
        elif char == '\r':
            self.command('ENTER')
        elif char == '':
            # do nothing
            pass
        else:
            self.command(char)
        self.takeScreenshotAndShowItOnWindow()

    def wake(self):
        self.refresh()
        self.printOperation(None, Operation.WAKE)

    def refresh(self):
        self.showVignette()
        self.device.wake()
        display = copy.copy(self.device.display)
        self.device.initDisplayProperties()
        changed = False
        for prop in display:
            if display[prop] != self.device.display[prop]:
                changed = True
                break
        if changed:
            self.deleteVignette()
            self.canvas.destroy()
            self.canvas = None
            self.window.update_idletasks()
        self.takeScreenshotAndShowItOnWindow()

    def cancelOperation(self):
        '''
        Cancels the ongoing operation if any.
        '''
        if self.isLongTouchingPoint:
            self.toggleLongTouchPoint()
        elif self.isTouchingPoint:
            self.toggleTouchPoint()
        elif self.isGeneratingTestCondition:
            self.toggleGenerateTestCondition()

    def printStartActivityAtTop(self):
        self.printOperation(None, Operation.START_ACTIVITY, self.device.getTopActivityName())

    def onCtrlA(self, event):
        if DEBUG:
            print("onCtrlA(", event, ")", file=sys.stderr)
        self.printStartActivityAtTop()

    def showDragDialog(self):
        d = DragDialog(self)
        self.window.wait_window(d)
        self.setDragDialogShowed(False)

    def onCtrlD(self, event):
        self.showDragDialog()

    def onCtrlF(self, event):
        self.saveSnapshot()

    def saveSnapshot(self):
        '''
        Saves the current shanpshot to the specified file.
        Current snapshot is the image being displayed on the main window.
        '''

        filename = self.snapshotDir + os.sep + '${serialno}-${focusedwindowname}-${timestamp}' + '.' + self.snapshotFormat.lower()
        # We have the snapshot already taken, no need to retake
        d = FileDialog(self, self.device.substituteDeviceTemplate(filename))
        saveAsFilename = d.askSaveAsFilename()
        if saveAsFilename:
            _format = os.path.splitext(saveAsFilename)[1][1:].upper()
            self.printOperation(None, Operation.SNAPSHOT, filename, _format, self.deviceArt, self.dropShadow,
                                self.screenGlare)
            # FIXME: we should add deviceArt, dropShadow and screenGlare to the saved image
            # self.unscaledScreenshot.save(saveAsFilename, _format, self.deviceArt, self.dropShadow, self.screenGlare)
            self.unscaledScreenshot.save(saveAsFilename, _format)

    def saveViewSnapshot(self, view):
        '''
        Saves the View snapshot.
        '''

        if not view:
            raise ValueError("view must be provided to take snapshot")
        filename = self.snapshotDir + os.sep + '${serialno}-' + View.variableNameFromId(
            view) + '-${timestamp}' + '.' + self.snapshotFormat.lower()
        d = FileDialog(self, self.device.substituteDeviceTemplate(filename))
        saveAsFilename = d.askSaveAsFilename()
        if saveAsFilename:
            _format = os.path.splitext(saveAsFilename)[1][1:].upper()
            self.printOperation(view, Operation.VIEW_SNAPSHOT, filename, _format)
            view.writeImageToFile(saveAsFilename, _format)

    def toggleTouchPointDip(self):
        '''
        Toggles the touch point operation using L{Unit.DIP}.
        This invokes L{toggleTouchPoint}.
        '''

        self.coordinatesUnit = Unit.DIP
        self.toggleTouchPoint()

    def onCtrlI(self, event):
        self.toggleTouchPointDip()

    def toggleLongTouchPoint(self):
        '''
        Toggles the long touch point operation.
        '''
        if not self.isLongTouchingPoint:
            msg = 'Long touching point'
            self.toast(msg, background=Color.GREEN)
            self.statusBar.set(msg)
            self.isLongTouchingPoint = True
            # FIXME: There should be 2 methods DIP & PX
            self.coordinatesUnit = Unit.PX
        else:
            self.toast(None)
            self.statusBar.clear()
            self.isLongTouchingPoint = False

    def toggleLongTouchView(self):
        '''
        Toggles the long touch View operation.
        :return:
        '''
        if not self.isLongTouchingView:
            msg = 'Long touching View'
            self.toast(msg, background=Color.GREEN)
            self.statusBar.set(msg)
            self.isLongTouchingView = True
        else:
            self.toast(None)
            self.statusBar.clear()
            self.isLongTouchingView = False

    def onCtrlL(self, event):
        self.toggleLongTouchPoint()

    def toggleTouchPoint(self):
        '''
        Toggles the touch point operation using the units specified in L{coordinatesUnit}.

        When there are L{View}s (obtained from the back-end) we have to determine if the
        intention when something is touched on the window if we want to touch the L{View}
        or the point.

        If there's no back-end, we don't allow L{self.isTouchingPoint} to be disabled so we will
        never be attempting to touch L{View}s.
        '''

        if not self.isTouchingPoint:
            msg = 'Touching point (units=%s)' % self.coordinatesUnit
            self.toast(msg, background=Color.GREEN)
            self.statusBar.set(msg)
            self.isTouchingPoint = True
        else:
            self.toast(None)
            self.statusBar.clear()
            self.isTouchingPoint = self.vc is None

    def toggleTouchPointPx(self):
        self.coordinatesUnit = Unit.PX
        self.toggleTouchPoint()

    def onCtrlP(self, event):
        self.toggleTouchPointPx()

    def onCtrlQ(self, event):
        if DEBUG:
            print("onCtrlQ(%s)" % event, file=sys.stderr)
        self.quit()

    def quit(self):
        if self.vc.uiAutomatorHelper:
            if DEBUG or True:
                print("Quitting UiAutomatorHelper...", file=sys.stderr)
            self.vc.uiAutomatorHelper.quit()
        self.window.destroy()

    def showSleepDialog(self):
        seconds = tkinter.simpledialog.askfloat('Sleep Interval', 'Value in seconds:', initialvalue=1, minvalue=0,
                                                parent=self.window)
        if seconds is not None:
            self.printOperation(None, Operation.SLEEP, seconds)
        self.canvas.focus_set()

    def onCtrlS(self, event):
        self.showSleepDialog()

    def startGeneratingTestCondition(self):
        self.message('Generating test condition...', background=Color.GREEN)
        self.isGeneratingTestCondition = True

    def finishGeneratingTestCondition(self):
        self.isGeneratingTestCondition = False
        self.hideMessageArea()

    def toggleGenerateTestCondition(self):
        '''
        Toggles generating test condition
        '''

        if self.vc is None:
            self.toast('Test conditions can be generated when a back-end is defined')
            return
        if self.isGeneratingTestCondition:
            self.finishGeneratingTestCondition()
        else:
            self.startGeneratingTestCondition()

    def onCtrlT(self, event):
        if DEBUG:
            print("onCtrlT()", file=sys.stderr)
        if self.vc is None:
            self.toast('Test conditions can be generated when a back-end is defined')
            return
        # FIXME: This is only valid if we are generating a test case
        self.toggleGenerateTestCondition()

    def onCtrlU(self, event):
        if DEBUG:
            print("onCtrlU()", file=sys.stderr)

    def onCtrlV(self, event):
        if DEBUG:
            print("onCtrlV()", file=sys.stderr)
        self.printOperation(None, Operation.TRAVERSE)

    def toggleTargetZones(self):
        self.toggleTargets()
        self.canvas.update_idletasks()

    def onCtrlZ(self, event):
        if DEBUG:
            print("onCtrlZ()", file=sys.stderr)
        self.toggleTargetZones()

    def showControlPanel(self):
        from com.dtmilano.android.controlpanel import ControlPanel

        self.controlPanel = ControlPanel(self, self.printOperation)

    def onCtrlK(self, event):
        self.showControlPanel()

    def drag(self, start, end, duration, steps, units=Unit.DIP):
        self.showVignette()
        # the operation on this current device is always done in PX
        # so let's do it before any conversion takes place
        self.device.drag(start, end, duration, steps)
        if units == Unit.DIP:
            x0 = round(start[0] / self.device.display['density'], 2)
            y0 = round(start[1] / self.device.display['density'], 2)
            x1 = round(end[0] / self.device.display['density'], 2)
            y1 = round(end[1] / self.device.display['density'], 2)
            start = (x0, y0)
            end = (x1, y1)
        if self.vc.uiAutomatorHelper:
            self.printOperation(None, Operation.SWIPE_UI_AUTOMATOR_HELPER, x0, y0, x1, y1, steps, units,
                                self.device.display['orientation'])
        else:
            self.printOperation(None, Operation.DRAG, start, end, duration, steps, units,
                                self.device.display['orientation'])
        self.printOperation(None, Operation.SLEEP, 1)
        time.sleep(1)
        self.takeScreenshotAndShowItOnWindow()

    def enableEvents(self):
        if self.permanentlyDisableEvents:
            return
        self.canvas.update_idletasks()
        self.canvas.bind("<Button-1>", self.onButton1Pressed)
        self.canvas.bind("<Control-Button-1>", self.onCtrlButton1Pressed)
        self.canvas.bind("<Button-2>", self.onButton2Pressed)
        self.canvas.bind("<Button-3>", self.onButton3Pressed)
        self.canvas.bind("<BackSpace>", self.onKeyPressed)
        # self.canvas.bind("<Control-Key-S>", self.onCtrlS)
        self.canvas.bind("<Key>", self.onKeyPressed)
        self.areEventsDisabled = False

    def disableEvents(self, permanently=False):
        self.permanentlyDisableEvents = permanently
        if self.canvas is not None:
            self.canvas.update_idletasks()
            self.areEventsDisabled = True
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<Control-Button-1>")
            self.canvas.unbind("<Button-2>")
            self.canvas.unbind("<Button-3>")
            self.canvas.unbind("<BackSpace>")
            # self.canvas.unbind("<Control-Key-S>")
            self.canvas.unbind("<Key>")

    def toggleTargets(self):
        if DEBUG:
            print("toggletargets: aretargetsmarked=", self.areTargetsMarked, file=sys.stderr)
        if not self.areTargetsMarked:
            self.markTargets()
        else:
            self.unmarkTargets()

    def markTargets(self):
        if DEBUG:
            print("marktargets: aretargetsmarked=", self.areTargetsMarked, file=sys.stderr)
            print("    marktargets: targets=", self.targets, file=sys.stderr)
        colors = ["#ff00ff", "#ffff00", "#00ffff"]

        self.markedTargetIds = {}
        c = 0
        for (x1, y1, x2, y2) in self.targets:
            if DEBUG:
                print("adding rectangle:", x1, y1, x2, y2)
            self.markTarget(x1, y1, x2, y2, colors[c % len(colors)])
            c += 1
        self.areTargetsMarked = True

    def markTarget(self, x1, y1, x2, y2, color='#ff00ff'):
        '''
        @return the id of the rectangle added
        '''

        # self.areTargetsMarked = True
        _id = self.canvas.create_rectangle(x1 * self.scale, y1 * self.scale, x2 * self.scale, y2 * self.scale,
                                           fill=color,
                                           stipple="gray25")
        self.markedTargetIds[_id] = (x1, y1, x2, y2)
        return _id

    def unmarkTarget(self, _id):
        self.canvas.delete(_id)

    def unmarkTargets(self):
        if not self.areTargetsMarked:
            return
        for _id in self.markedTargetIds:
            self.unmarkTarget(_id)
        self.markedTargetIds = {}
        self.areTargetsMarked = False

    def setDragDialogShowed(self, showed):
        self.isDragDialogShowed = showed
        if showed:
            pass
        else:
            self.isGrabbingTouch = False

    def drawTouchedPoint(self, x, y):
        if DEBUG:
            print("drawTouchedPoint(", x, ",", y, ")", file=sys.stderr)
        size = 50
        return self.canvas.create_oval((x - size) * self.scale, (y - size) * self.scale, (x + size) * self.scale,
                                       (y + size) * self.scale, fill=Color.MAGENTA)

    def drawDragLine(self, x0, y0, x1, y1):
        if DEBUG:
            print("drawDragLine(", x0, ",", y0, ",", x1, ",", y1, ")", file=sys.stderr)
        width = 15
        return self.canvas.create_line(x0 * self.scale, y0 * self.scale, x1 * self.scale, y1 * self.scale, width=width,
                                       fill=Color.MAGENTA, arrow="last", arrowshape=(50, 50, 30), dash=(50, 25))

    def executeCommandAndRefresh(self, command):
        self.showVignette()
        if DEBUG:
            print('DEBUG: command=', command, command.__name__, file=sys.stderr)
            print('DEBUG: command=', command.__self__, command.__self__.view, file=sys.stderr)
        try:
            view = command.__self__.view
        except AttributeError:
            view = None
        # FIXME: If we are not dumping the Views and assigning to variables (i.e -u was used on command line) then
        # when we try to do an operation on the View via its variable name it's going to fail when the saved script
        # is executed
        self.printOperation(view, Operation.fromCommandName(command.__name__))
        command()
        self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
        self.vc.sleep(5)
        # FIXME: perhaps refresh() should be invoked here just in case size or orientation changed
        self.takeScreenshotAndShowItOnWindow()

    def changeLanguage(self):
        code = tkinter.simpledialog.askstring("Change language", "Enter the language code")
        self.vc.uiDevice.changeLanguage(code)
        self.printOperation(None, Operation.CHANGE_LANGUAGE, code)
        self.refresh()

    def setOnTouchListener(self, listener):
        self.onTouchListener = listener

    def setGrab(self, state):
        if DEBUG:
            print("Culebron.setGrab(%s)" % state, file=sys.stderr)
        if state and not self.onTouchListener:
            warnings.warn('Starting to grab but no onTouchListener')
        self.isGrabbingTouch = state
        if state:
            self.toast('Grabbing drag points...', background=Color.GREEN)
        else:
            self.hideMessageArea()

    @staticmethod
    def isClickableCheckableOrFocusable(v):
        if DEBUG_ISCCOF:
            print("isClickableCheckableOrFocusable(", v.__tinyStr__(), ")", file=sys.stderr)
        try:
            if not v.isEnabled():
                # if not enabled, then it cannot be a target
                return False
        except AttributeError:
            pass
        try:
            return v.isClickable()
        except AttributeError:
            pass
        try:
            return v.isCheckable()
        except AttributeError:
            pass
        try:
            return v.isFocusable()
        except AttributeError:
            pass
        return False

    def mainloop(self):
        self.window.title("%s v%s" % (Culebron.APPLICATION_NAME, __version__))
        self.window.resizable(width=tkinter.FALSE, height=tkinter.FALSE)
        self.window.lift()
        if self.concertina:
            self.concertinaConfig = Concertina.readConcertinaConfig(self.concertinaConfigFile)
            self.concertinaLoop()
        else:
            self.window.mainloop()

    def concertinaLoop(self):
        random.seed()
        self.disableEvents(permanently=True)
        self.concertinaLoopCallback(dontinteract=True)
        self.window.mainloop()

    def concertinaLoopCallback(self, dontinteract=False):
        needToSleep = False
        if not dontinteract:
            if DEBUG_CONCERTINA:
                if len(self.targetViews) > 0:
                    print("CONCERTINA: should select one of these {} targets:".format(len(self.targetViews)),
                          file=sys.stderr)
                    for v in self.targetViews:
                        print("    ", str(v.__tinyStr__()), v.getContentDescription(), file=sys.stderr)
                else:
                    print("CONCERTINA: empty target list, nothing to select", file=sys.stderr)
            rand = random.random()
            if DEBUG_CONCERTINA:
                print("CONCERTINA: random=%f" % rand, file=sys.stderr)
            probabilities = self.concertinaConfig['probabilities']
            if rand > (1 - probabilities['systemKeys']):
                # Send key events
                systemKeys = self.concertinaConfig['systemKeys']
                k = numpy.random.choice(systemKeys['keys'], 1, p=systemKeys['probabilities'])[0]
                if DEBUG_CONCERTINA:
                    print("CONCERTINA: system key=" + k, file=sys.stderr)
                self.command(k)
                self.sleepAndRefreshScreen()
            else:
                # Right now we have p[systemKeys] + p[views] = 1
                # Act on views
                _len = len(self.targetViews)
                if _len > 0:
                    self.noTargetViewsCount = 0
                    views = self.concertinaConfig['views']
                    selector = numpy.random.choice(views['selector'], 1, p=views['probabilities'])[0]
                    _regex = numpy.random.choice(views[selector]['regexs'], 1, p=views[selector]['probabilities'])[0]
                    _tvli = []
                    for _i in range(len(self.targetViews)):
                        if selector == 'classes':
                            if re.match(_regex, self.targetViews[_i].getClass()):
                                _tvli.append(_i)
                        elif selector == 'contentDescriptions':
                            if re.match(_regex, self.targetViews[_i].getContentDescription()):
                                _tvli.append(_i)
                        else:
                            print("CONCERTINA: unknown selector: {}".format(selector), file=sys.stderr)
                    # i = random.randrange(len(self.targetViews))
                    if _tvli:
                        i = random.choice(_tvli)
                        target = self.targetViews[i]
                        box = self.targets[i]
                        if DEBUG_CONCERTINA:
                            print("CONCERTINA: selected", str(
                                target.__smallStr__()), target.getContentDescription(), file=sys.stderr)
                            print("CONCERTINA: selected", box, file=sys.stderr)
                            print("CONCERTINA: filter class", _regex, file=sys.stderr)
                            print("CONCERTINA: filtered views", file=sys.stderr)
                            for _i in _tvli:
                                print("CONCERTINA:    view class", self.targetViews[_i].getClass(), \
                                      self.targetViews[_i].getContentDescription(), file=sys.stderr)
                            for _v in self.targetViews:
                                print("CONCERTINA: view class", _v.getClass(), file=sys.stderr)
                        _id = self.markTarget(*box)
                        self.window.update_idletasks()
                        time.sleep(1)
                        self.unmarkTarget(_id)
                        self.window.update_idletasks()
                        clazz = target.getClass()
                        parent = target.getParent()
                        if parent:
                            parentClass = parent.getClass()
                        else:
                            parentClass = None
                        isScrollable = target.isScrollable()
                        if DEBUG_CONCERTINA:
                            print("CONCERTINA: class", clazz, file=sys.stderr)
                            print("CONCERTINA: parent", parentClass, file=sys.stderr)
                            print("CONCERTINA: is scrollable: ", isScrollable, file=sys.stderr)
                            if parent:
                                print("CONCERTINA: is scrollable parent: ", parent.isScrollable(), file=sys.stderr)
                                # cond = (isScrollable or parent.isScrollable() or parentClass == 'android.widget.ScrollView')
                                # DEBUG ONLY!
                                # print >> sys.stderr, "CONCERTINA: check:", cond
                                # if not cond:
                                #     self.window.after(500, self.concertinaLoopCallback)
                                #     return
                        if probabilities['views'] > 0 and clazz == 'android.widget.EditText':
                            id = target.getId()
                            txt = target.getText()
                            if target.isPassword() or re.search('password', id, re.IGNORECASE) or re.search('password',
                                                                                                            txt,
                                                                                                            re.IGNORECASE):
                                text = Concertina.getRandomPassword()
                            elif re.search('email', id, re.IGNORECASE) or re.search('email', txt, re.IGNORECASE):
                                text = Concertina.getRandomEmail()
                            else:
                                text = Concertina.getRandomText()
                            if DEBUG_CONCERTINA:
                                print("Entering text: ", text, file=sys.stderr)
                            if not text:
                                raise RuntimeError('text is None')
                            self.setText(target, text)
                            needToSleep = True
                        elif target.getContentDescription() in ['Voice Search', 'Tap to speak']:
                            self.touchView(target)
                            self.sayText(Concertina.sayRandomText())
                            self.sleep(5)
                            needToSleep = True
                        elif target.getContentDescription() in ['Ask Alexa']:
                            if DEBUG_CONCERTINA:
                                print("Alexa detected, speaking...", file=sys.stderr)
                            self.touchView(target)
                            self.sleep(2)
                            self.sayText(Concertina.sayRandomText('alexa'))
                            # alexa might be speaking, so let's wait a bit
                            self.sleep(15)
                            needToSleep = True
                        elif probabilities['views'] > 0 and random.choice(['SCROLL', 'TOUCH']) == 'SCROLL' and (
                                isScrollable or parent.isScrollable() or parentClass == 'android.widget.ScrollView'):
                            # NOTE: The order here is important because some EditText are inside ScrollView's and we want to
                            # capture the case of other ScrollViews
                            if isScrollable:
                                ((l, t), (r, b)) = target.getBounds()
                            else:
                                if DEBUG_CONCERTINA:
                                    print("CONCERTINA: using parent bounds because it's scrollable", file=sys.stderr)
                                ((l, t), (r, b)) = parent.getBounds()
                            if DEBUG_CONCERTINA:
                                print("CONCERTINA: bounds=", ((l, t), (r, b)), file=sys.stderr)
                            if random.choice(['VERTICAL', 'HORIZONTAL']) == 'VERTICAL':
                                if DEBUG_CONCERTINA:
                                    print('CONCERTINA: VERTICAL', file=sys.stderr)
                                sp = (l + (r - l) / 2, t + 50)
                                ep = (l + (r - l) / 2, b - 50)
                            else:
                                if DEBUG_CONCERTINA:
                                    print('CONCERTINA: HORIZONTAL', file=sys.stderr)
                                sp = (l + 50, t + (b - t) / 2)
                                ep = (r - 50, t + (b - t) / 2)
                            if random.choice(['FORWARD', 'REVERSE']) == 'REVERSE':
                                if DEBUG_CONCERTINA:
                                    print('CONCERTINA: REVERSE', file=sys.stderr)
                                temp = sp
                                sp = ep
                                ep = temp
                            else:
                                if DEBUG_CONCERTINA:
                                    print('CONCERTINA: FORWARD', file=sys.stderr)
                            d = 500
                            s = 20
                            _id = self.canvas.create_rectangle(l * self.scale, t * self.scale, r * self.scale,
                                                               b * self.scale,
                                                               fill="#00ffff", stipple="gray12")
                            self.window.update_idletasks()
                            units = Unit.PX
                            self.drawTouchedPoint(sp[0], sp[1])
                            self.window.update_idletasks()
                            self.drawDragLine(sp[0], sp[1], ep[0], ep[1])
                            self.window.update_idletasks()
                            time.sleep(5)
                            if DEBUG_CONCERTINA:
                                print("CONCERTINA: dragging %s %s %s %s %s" % (sp, ep, d, s, units), file=sys.stderr)
                            self.drag(sp, ep, d, s, units)
                            needToSleep = True
                        else:
                            if probabilities['views'] > 0:
                                self.touchView(target)
                                needToSleep = True
                            else:
                                needToSleep = False
                                if DEBUG_CONCERTINA:
                                    print("CONCERTINA: touchOtherViews probability == 0", file=sys.stderr)
                        if needToSleep:
                            self.sleepAndRefreshScreen()
                    else:
                        # _tvli
                        if DEBUG_CONCERTINA:
                            print("CONCERTINA: Filter results in empty target list", file=sys.stderr)
                else:
                    # There are many cases where the Views are not touchable/selectable/focusable/etc so they don't
                    # appear in targetViews, like popups, menus, lisviews, etc. so let's give them a change
                    if self.dump and probabilities['views'] > 0:
                        target = random.choice(self.dump)
                        if DEBUG_CONCERTINA:
                            print("CONCERTINA: touching non-target view {}".format(target), file=sys.stderr)
                        self.touchView(target)
                        self.sleepAndRefreshScreen()
                        needToSleep = True
                    else:
                        # Let's wait to see if some View appear
                        needToSleep = True
                        self.noTargetViewsCount += 1
                        if DEBUG_CONCERTINA:
                            print("CONCERTINA: No target views", self.noTargetViewsCount, file=sys.stderr)
                        if self.noTargetViewsCount >= self.concertinaConfig['limits']['maxNoTargetViewsIterations']:
                            print("CONCERTINA: Cannot detect target Views after {} iterations".format(
                                self.noTargetViewsCount), file=sys.stderr)
                            sys.exit(1)
        if self.iterations >= self.concertinaConfig['limits']['iterations']:
            print("CONCERTINA: Maximum number of iterations reached", file=sys.stderr)
            sys.exit(0)
        self.iterations += 1
        self.window.after(5000 if dontinteract or needToSleep else 0, self.concertinaLoopCallback)

    def sleepAndRefreshScreen(self):
        self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
        if DEBUG_CONCERTINA:
            print("CONCERTINA: waiting 5 secs", file=sys.stderr)
        time.sleep(5)
        if DEBUG_CONCERTINA:
            print("CONCERTINA: updating window", file=sys.stderr)
        self.takeScreenshotAndShowItOnWindow()

    def sleep(self, s):
        time.sleep(s)
        self.printOperation(None, Operation.SLEEP, s)

    def getViewContainingPointAndLongTouch(self, x, y):
        # FIXME: this method is almost exactly as getViewContainingPointAndTouch()
        if DEBUG:
            print('getViewContainingPointAndLongTouch(%d, %d)' % (x, y), file=sys.stderr)
        if self.areEventsDisabled:
            if DEBUG:
                print("Ignoring event", file=sys.stderr)
            self.canvas.update_idletasks()
            return

        self.showVignette()
        if DEBUG_POINT:
            print("getViewsContainingPointAndLongTouch(x=%s, y=%s)" % (x, y), file=sys.stderr)
            print("self.vc=", self.vc, file=sys.stderr)
        v = self.findViewContainingPointInTargets(x, y)

        if v is None:
            # FIXME: We can touch by DIP by default if no Views were found
            self.hideVignette()
            msg = "There are no touchable or clickable views here!"
            self.toast(msg)
            return

        clazz = v.getClass()
        candidates = [v]

        def findBestCandidate(view):
            isccf = Culebron.isClickableCheckableOrFocusable(view)
            cd = view.getContentDescription()
            text = view.getText()
            if (cd or text) and not isccf:
                # because isccf==False this view was not added to the list of targets
                # (i.e. Settings)
                candidates.insert(0, view)
            return None

        if not (v.getText() or v.getContentDescription()) and v.getChildren():
            self.vc.traverse(root=v, transform=findBestCandidate, stream=None)
        if len(candidates) > 2:
            warnings.warn("We are in trouble, we have more than one candidate to touch", stacklevel=0)
        candidate = candidates[0]
        self.longTouchView(candidate, v if candidate != v else None)

        self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
        self.vc.sleep(5)
        self.takeScreenshotAndShowItOnWindow()


if TKINTER_AVAILABLE:
    class MainMenu(tkinter.Menu):
        def __init__(self, culebron):
            tkinter.Menu.__init__(self, culebron.window)
            self.culebron = culebron

            self.fileMenu = tkinter.Menu(self, tearoff=False)
            self.fileMenu.add_command(label="Quit", underline=0, accelerator='Command-Q', command=self.culebron.quit)
            self.add_cascade(label="File", underline=0, menu=self.fileMenu)

            self.viewMenu = tkinter.Menu(self, tearoff=False)
            self.showViewTree = tkinter.BooleanVar()
            self.showViewTree.set(False)
            state = NORMAL if culebron.vc else DISABLED
            self.viewMenu.add_checkbutton(label="Tree", underline=0, accelerator='Command-T', onvalue=True,
                                          offvalue=False, variable=self.showViewTree, state=state,
                                          command=self.onshowViewTreeChanged)
            self.showViewDetails = tkinter.BooleanVar()
            self.showViewDetails.set(False)
            state = NORMAL if culebron.vc else DISABLED
            self.viewMenu.add_checkbutton(label="View details", underline=0, accelerator='Command-V', onvalue=True,
                                          offvalue=False, variable=self.showViewDetails, state=state,
                                          command=self.onShowViewDetailsChanged)
            self.add_cascade(label="View", underline=0, menu=self.viewMenu)

            self.uiDeviceMenu = tkinter.Menu(self, tearoff=False)
            state = NORMAL if culebron.vc else DISABLED
            self.uiDeviceMenu.add_command(label="Open Notification", underline=6, state=state,
                                          command=lambda: culebron.executeCommandAndRefresh(
                                              self.culebron.vc.uiDevice.openNotification))
            state = NORMAL if culebron.vc else DISABLED
            self.uiDeviceMenu.add_command(label="Open Quick settings", underline=6, state=state,
                                          command=lambda: culebron.executeCommandAndRefresh(
                                              command=self.culebron.vc.uiDevice.openQuickSettings))
            state = NORMAL if culebron.vc else DISABLED
            self.uiDeviceMenu.add_command(label="Change Language", underline=7, state=state,
                                          command=self.culebron.changeLanguage)
            self.add_cascade(label="UiDevice", menu=self.uiDeviceMenu)

            self.helpMenu = tkinter.Menu(self, tearoff=False)
            self.helpMenu.add_command(label="Keyboard shortcuts", underline=0, accelerator='Command-K',
                                      command=self.culebron.showHelp)
            self.add_cascade(label="Help", underline=0, menu=self.helpMenu)

        def callback(self):
            pass

        def onshowViewTreeChanged(self):
            if self.showViewTree.get() == 1:
                self.culebron.showViewTree()
            else:
                self.culebron.hideViewTree()

        def onShowViewDetailsChanged(self):
            if self.showViewDetails.get() == 1:
                self.culebron.showViewDetails()
            else:
                self.culebron.hideViewDetails()


    class ViewTree(tkinter.Frame):
        def __init__(self, parent):
            tkinter.Frame.__init__(self, parent)
            if sys.version_info > (3, 0):
                self.viewTree = tkinter.ttk.Treeview(self, columns=['T'], height=35)
            else:
                self.viewTree = ttk.Treeview(self, columns=['T'], height=35)
            self.viewTree.column(0, width=20)
            self.viewTree.heading('#0', None, text='View', anchor=tkinter.W)
            self.viewTree.heading(0, None, text='T', anchor=tkinter.W)
            if sys.version_info > (3, 0):
                self.scrollbar = tkinter.ttk.Scrollbar(self, orient=tkinter.HORIZONTAL, command=self.__xscroll)
            else:
                self.scrollbar = ttk.Scrollbar(self, orient=tkinter.HORIZONTAL, command=self.__xscroll)
            self.viewTree.grid(row=1, rowspan=1, column=1, sticky=tkinter.N + tkinter.S)
            self.scrollbar.grid(row=2, rowspan=1, column=1, sticky=tkinter.E + tkinter.W)
            self.viewTree.configure(xscrollcommand=self.scrollbar.set)

        def __xscroll(self, *args):
            if DEBUG:
                print("__xscroll:", args, file=sys.stderr)
            self.viewTree.xview(*args)

        def insert(self, parent, index, iid=None, **kw):
            """Creates a new item and return the item identifier of the newly
            created item.
    
            parent is the item ID of the parent item, or the empty string
            to create a new top-level item. index is an integer, or the value
            end, specifying where in the list of parent's children to insert
            the new item. If index is less than or equal to zero, the new node
            is inserted at the beginning, if index is greater than or equal to
            the current number of children, it is inserted at the end. If iid
            is specified, it is used as the item identifier, iid must not
            already exist in the tree. Otherwise, a new unique identifier
            is generated."""

            return self.viewTree.insert(parent, index, iid, **kw)

        def set(self, item, column=None, value=None):
            """With one argument, returns a dictionary of column/value pairs
            for the specified item. With two arguments, returns the current
            value of the specified column. With three arguments, sets the
            value of given column in given item to the specified value."""

            return self.viewTree.set(item, column, value)

        def tag_bind(self, tagname, sequence=None, callback=None):
            if DEBUG:
                print('ViewTree.tag_bind(', tagname, ',', sequence, ',', callback, ')', file=sys.stderr)
            return self.viewTree.tag_bind(tagname, sequence, callback)


    class ViewDetails(tkinter.Frame):
        VIEW_DETAILS = "View Details:\n"

        def __init__(self, parent):
            tkinter.Frame.__init__(self, parent)
            self.label = tkinter.Label(self, bd=1, width=30, wraplength=200, justify=tkinter.LEFT, anchor=tkinter.NW)
            self.label.configure(text=self.VIEW_DETAILS)
            self.label.configure(bg="white")
            self.label.grid(row=3, column=1, rowspan=1)

        def set(self, view):
            self.label.configure(text=self.VIEW_DETAILS + view.__str__())


    class StatusBar(tkinter.Frame):

        def __init__(self, parent):
            tkinter.Frame.__init__(self, parent)
            self.label = tkinter.Label(self, bd=1, relief=tkinter.SUNKEN, anchor=tkinter.W)
            self.label.grid(row=1, column=1, columnspan=2, sticky=tkinter.E + tkinter.W)

        def set(self, fmt, *args):
            self.label.config(text=fmt % args)
            self.label.update_idletasks()

        def clear(self):
            self.label.config(text="")
            self.label.update_idletasks()


    class LabeledEntry():
        def __init__(self, parent, text, validate, validatecmd):
            self.f = tkinter.Frame(parent)
            tkinter.Label(self.f, text=text, anchor="w", padx=8).grid(row=1, column=1, sticky=tkinter.E)
            self.entry = tkinter.Entry(self.f, validate=validate, validatecommand=validatecmd)
            self.entry.grid(row=1, column=2, padx=5, sticky=tkinter.E)

        def grid(self, **kwargs):
            self.f.grid(kwargs)

        def get(self):
            return self.entry.get()

        def set(self, text):
            self.entry.delete(0, tkinter.END)
            self.entry.insert(0, text)


    class LabeledEntryWithButton(LabeledEntry):
        def __init__(self, parent, text, buttonText, command, validate, validatecmd):
            LabeledEntry.__init__(self, parent, text, validate, validatecmd)
            self.button = tkinter.Button(self.f, text=buttonText, command=command)
            self.button.grid(row=1, column=3)


    class DragDialog(tkinter.Toplevel):

        DEFAULT_DURATION = 1000
        DEFAULT_STEPS = 20

        spX = None
        spY = None
        epX = None
        epY = None
        spId = None
        epId = None

        def __init__(self, culebron):
            self.culebron = culebron
            self.parent = culebron.window
            tkinter.Toplevel.__init__(self, self.parent)
            self.transient(self.parent)
            self.culebron.setDragDialogShowed(True)
            self.title("Drag: selecting parameters")
            self.__grabbing = None
            self.ok = None

            # valid percent substitutions (from the Tk entry man page)
            # %d = Type of action (1=insert, 0=delete, -1 for others)
            # %i = index of char string to be inserted/deleted, or -1
            # %P = value of the entry if the edit is allowed
            # %s = value of entry prior to editing
            # %S = the text string being inserted or deleted, if any
            # %v = the type of validation that is currently set
            # %V = the type of validation that triggered the callback
            #      (key, focusin, focusout, forced)
            # %W = the tk name of the widget
            self.validate = (self.parent.register(self.onValidate), '%P')
            self.sp = LabeledEntryWithButton(self, "Start point", "Grab", command=self.onGrabSp, validate="focusout",
                                             validatecmd=self.validate)
            self.sp.grid(row=1, column=1, columnspan=3, pady=5)

            self.ep = LabeledEntryWithButton(self, "End point", "Grab", command=self.onGrabEp, validate="focusout",
                                             validatecmd=self.validate)
            self.ep.grid(row=2, column=1, columnspan=3, pady=5)

            l = tkinter.Label(self, text="Units")
            l.grid(row=3, column=1, sticky=tkinter.E)

            self.units = tkinter.StringVar()
            self.units.set(Unit.DIP)
            col = 2
            for u in dir(Unit):
                if u.startswith('_'):
                    continue
                rb = tkinter.Radiobutton(self, text=u, variable=self.units, value=u)
                rb.grid(row=3, column=col, padx=20, sticky=tkinter.E)
                col += 1

            self.d = LabeledEntry(self, "Duration", validate="focusout", validatecmd=self.validate)
            self.d.set(DragDialog.DEFAULT_DURATION)
            self.d.grid(row=4, column=1, columnspan=3, pady=5)

            self.s = LabeledEntry(self, "Steps", validate="focusout", validatecmd=self.validate)
            self.s.set(DragDialog.DEFAULT_STEPS)
            self.s.grid(row=5, column=1, columnspan=2, pady=5)

            self.buttonBox()

        def buttonBox(self):
            # add standard button box. override if you don't want the
            # standard buttons

            box = tkinter.Frame(self)

            self.ok = tkinter.Button(box, text="OK", width=10, command=self.onOk, default=tkinter.ACTIVE,
                                     state=tkinter.DISABLED)
            self.ok.grid(row=6, column=1, sticky=tkinter.E, padx=5, pady=5)
            w = tkinter.Button(box, text="Cancel", width=10, command=self.onCancel)
            w.grid(row=6, column=2, sticky=tkinter.E, padx=5, pady=5)

            self.bind("<Return>", self.onOk)
            self.bind("<Escape>", self.onCancel)

            box.grid(row=6, column=1, columnspan=3)

        def onValidate(self, value):
            if self.sp.get() and self.ep.get() and self.d.get() and self.s.get():
                self.ok.configure(state=tkinter.NORMAL)
            else:
                self.ok.configure(state=tkinter.DISABLED)

        def onOk(self, event=None):
            if DEBUG:
                print("onOK()", file=sys.stderr)
                print("values are:", end=' ', file=sys.stderr)
                print(self.sp.get(), end=' ', file=sys.stderr)
                print(self.ep.get(), end=' ', file=sys.stderr)
                print(self.d.get(), end=' ', file=sys.stderr)
                print(self.s.get(), end=' ', file=sys.stderr)
                print(self.units.get(), file=sys.stderr)

            sp = make_tuple(self.sp.get())
            ep = make_tuple(self.ep.get())
            d = int(self.d.get())
            s = int(self.s.get())
            self.cleanUp()
            # put focus back to the parent window's canvas
            self.culebron.canvas.focus_set()
            self.destroy()
            self.culebron.drag(sp, ep, d, s, self.units.get())

        def onCancel(self, event=None):
            self.culebron.setGrab(False)
            self.cleanUp()
            # put focus back to the parent window's canvas
            self.culebron.canvas.focus_set()
            self.destroy()

        def onGrabSp(self):
            '''
            Grab starting point
            '''

            self.sp.entry.focus_get()
            self.onGrab(self.sp)

        def onGrabEp(self):
            '''
            Grab ending point
            '''

            self.ep.entry.focus_get()
            self.onGrab(self.ep)

        def onGrab(self, entry):
            '''
            Generic grab method.
            
            @param entry: the entry being grabbed
            @type entry: Tkinter.Entry
            '''

            self.culebron.setOnTouchListener(self.onTouchListener)
            self.__grabbing = entry
            self.culebron.setGrab(True)

        def onTouchListener(self, point):
            '''
            Listens for touch events and draws the corresponding shapes on the Culebron canvas.
            If the starting point is being grabbed it draws the touching point via
            C{Culebron.drawTouchedPoint()} and if the end point is being grabbed it draws
            using C{Culebron.drawDragLine()}.
            
            @param point: the point touched
            @type point: tuple
            '''

            x = point[0]
            y = point[1]
            value = "(%d,%d)" % (x, y)
            self.__grabbing.set(value)
            self.onValidate(value)
            self.culebron.setGrab(False)
            if self.__grabbing == self.sp:
                self.__cleanUpSpId()
                self.__cleanUpEpId()
                self.spX = x
                self.spY = y
            elif self.__grabbing == self.ep:
                self.__cleanUpEpId()
                self.epX = x
                self.epY = y
            if self.spX and self.spY and not self.spId:
                self.spId = self.culebron.drawTouchedPoint(self.spX, self.spY)
            if self.spX and self.spY and self.epX and self.epY and not self.epId:
                self.epId = self.culebron.drawDragLine(self.spX, self.spY, self.epX, self.epY)
            self.__grabbing = None
            self.culebron.setOnTouchListener(None)

        def __cleanUpSpId(self):
            if self.spId:
                self.culebron.canvas.delete(self.spId)
                self.spId = None

        def __cleanUpEpId(self):
            if self.epId:
                self.culebron.canvas.delete(self.epId)
                self.epId = None

        def cleanUp(self):
            self.__cleanUpSpId()
            self.__cleanUpEpId()


    class ContextMenu(tkinter.Menu):
        # FIXME: should get rid of the nested classes, otherwise it's not possible to create a parent class
        # SubMenu for UiScrollableSubMenu
        '''
        The context menu (popup).
        '''

        PADDING = '  '
        ''' Padding used to separate menu entries from border '''

        class Separator():
            SEPARATOR = 'SEPARATOR'

            def __init__(self):
                self.description = self.SEPARATOR

        class Command():
            def __init__(self, description, underline, shortcut, event, command):
                self.description = description
                self.underline = underline
                self.shortcut = shortcut
                self.event = event
                self.command = command

        class UiScrollableSubMenu(tkinter.Menu):
            def __init__(self, menu, description, view, culebron):
                # Tkninter.Menu is not extending object, so we can't do this:
                # super(ContextMenu, self).__init__(culebron.window, tearoff=False)
                tkinter.Menu.__init__(self, menu, tearoff=False)
                self.description = description
                self.add_command(label='Fling backward',
                                 command=lambda: culebron.executeCommandAndRefresh(view.uiScrollable.flingBackward))
                self.add_command(label='Fling forward',
                                 command=lambda: culebron.executeCommandAndRefresh(view.uiScrollable.flingForward))
                self.add_command(label='Fling to beginning',
                                 command=lambda: culebron.executeCommandAndRefresh(view.uiScrollable.flingToBeginning))
                self.add_command(label='Fling to end',
                                 command=lambda: culebron.executeCommandAndRefresh(view.uiScrollable.flingToEnd))

        def __init__(self, culebron, view):
            # Tkninter.Menu is not extending object, so we can't do this:
            # super(ContextMenu, self).__init__(culebron.window, tearoff=False)
            tkinter.Menu.__init__(self, culebron.window, tearoff=False)
            if DEBUG_CONTEXT_MENU:
                print("Creating ContextMenu for", view.__smallStr__() if view else "No View", file=sys.stderr)
            self.view = view
            items = []

            if self.view:
                _saveViewSnapshotForSelectedView = lambda: culebron.saveViewSnapshot(self.view)
                items.append(ContextMenu.Command('Take view snapshot and save to file', 5, 'Ctrl+W', '<Control-W>',
                                                 _saveViewSnapshotForSelectedView))
                if self.view.uiScrollable:
                    items.append(ContextMenu.UiScrollableSubMenu(self, 'UiScrollable', view, culebron))
                else:
                    parent = self.view.parent
                    while parent:
                        if parent.uiScrollable:
                            # WARNING:
                            # A bit dangerous, but may work
                            # If we click ona ListView then the View pased to this ContextMenu is the child,
                            # perhaps we want to scroll the parent
                            items.append(ContextMenu.UiScrollableSubMenu(self, 'UiScrollable', parent, culebron))
                            break
                        parent = parent.parent
                items.append(ContextMenu.Separator())

            items.append(ContextMenu.Command('Drag dialog', 0, 'Ctrl+D', '<Control-D>', culebron.showDragDialog))
            items.append(ContextMenu.Command('Take snapshot and save to file', 26, 'Ctrl+F', '<Control-F>',
                                             culebron.saveSnapshot))
            items.append(ContextMenu.Command('Control Panel', 0, 'Ctrl+K', '<Control-K>', culebron.showControlPanel))
            items.append(ContextMenu.Command('Long touch point using PX', 0, 'Ctrl+L', '<Control-L>',
                                             culebron.toggleLongTouchPoint))
            items.append(ContextMenu.Command('Long touch View', 0, None, None,
                                             culebron.toggleLongTouchView))
            items.append(
                ContextMenu.Command('Touch using DIP', 13, 'Ctrl+I', '<Control-I>', culebron.toggleTouchPointDip))
            items.append(
                ContextMenu.Command('Touch using PX', 12, 'Ctrl+P', '<Control-P>', culebron.toggleTouchPointPx))
            items.append(ContextMenu.Command('Generates a Sleep() on output script', 12, 'Ctrl+S', '<Control-S>',
                                             culebron.showSleepDialog))
            if culebron.vc is not None:
                items.append(ContextMenu.Command('Toggle generating Test Condition', 18, 'Ctrl+T', '<Control-T>',
                                                 culebron.toggleGenerateTestCondition))
            items.append(ContextMenu.Command('Touch Zones', 6, 'Ctrl+Z', '<Control-Z>', culebron.toggleTargetZones))
            items.append(ContextMenu.Command('Generates a startActivity()', 17, 'Ctrl+A', '<Control-A>',
                                             culebron.printStartActivityAtTop))
            items.append(ContextMenu.Command('Refresh', 0, 'F5', '<F5>', culebron.refresh))
            items.append(ContextMenu.Command('Wake up', 0, None, None, culebron.wake))
            items.append(ContextMenu.Separator())
            items.append(ContextMenu.Command('Quit', 0, 'Ctrl+Q', '<Control-Q>', culebron.quit))

            for item in items:
                self.addItem(item)

        def addItem(self, item):
            if isinstance(item, ContextMenu.Separator):
                self.addSeparator()
            elif isinstance(item, ContextMenu.Command):
                self.addCommand(item)
            elif isinstance(item, ContextMenu.UiScrollableSubMenu):
                self.addSubMenu(item)
            else:
                raise RuntimeError("Unsupported item=" + str(item))

        def addSeparator(self):
            self.add_separator()

        def addCommand(self, item):
            self.add_command(label=self.PADDING + item.description, underline=item.underline + len(self.PADDING),
                             command=item.command, accelerator=item.shortcut)
            # if item.event:
            #    # These bindings remain even after the menu has been dismissed, so it seems not a good idea
            #    #self.bind_all(item.event, item.command)
            #    pass

        def addSubMenu(self, item):
            self.add_cascade(label=self.PADDING + item.description, menu=item)

        def showPopupMenu(self, event):
            try:
                self.tk_popup(event.x_root, event.y_root)
            finally:
                # make sure to release the grab (Tk 8.0a1 only)
                # self.grab_release()
                pass


    class HelpDialog(tkinter.Toplevel):

        def __init__(self, culebron):
            self.culebron = culebron
            self.parent = culebron.window
            tkinter.Toplevel.__init__(self, self.parent)
            # self.transient(self.parent)
            self.title("%s: help" % Culebron.APPLICATION_NAME)

            self.text = tkinter.scrolledtext.ScrolledText(self, width=60, height=40)
            self.text.insert(tkinter.INSERT, '''
    Special keys
    ------------
    
    F1: Help
    F5: Refresh
    
    Mouse Buttons
    -------------
    <1>: Touch the underlying View
    
    Commands
    --------
    Ctrl-A: Generates startActivity() call on output script
    Ctrl-D: Drag dialog
    Ctrl-F: Take snapshot and save to file
    Ctrl-K: Control Panel
    Ctrl-L: Long touch point using PX
    Ctrl-I: Touch using DIP
    Ctrl-P: Touch using PX
    Ctrl-Q: Quit
    Ctrl-S: Generates a sleep() on output script
    Ctrl-T: Toggle generating test condition
    Ctrl-V: Verifies the content of the screen dump
    Ctrl-Z: Touch zones
    ''')
            self.text.grid(row=1, column=1)

            self.buttonBox()

        def buttonBox(self):
            # add standard button box. override if you don't want the
            # standard buttons

            box = tkinter.Frame(self)

            w = tkinter.Button(box, text="Dismiss", width=10, command=self.onDismiss, default=tkinter.ACTIVE)
            w.grid(row=1, column=1, padx=5, pady=5)

            self.bind("<Return>", self.onDismiss)
            self.bind("<Escape>", self.onDismiss)

            box.grid(row=2, column=1)

        def onDismiss(self, event=None):
            # put focus back to the parent window's canvas
            self.culebron.canvas.focus_set()
            self.destroy()


    class FileDialog():
        def __init__(self, culebron, filename):
            self.parent = culebron.window
            self.filename = filename
            self.basename = os.path.basename(self.filename)
            self.dirname = os.path.dirname(self.filename)
            self.ext = os.path.splitext(self.filename)[1]
            self.fileTypes = [('images', self.ext)]

        def askSaveAsFilename(self):
            return tkinter.filedialog.asksaveasfilename(parent=self.parent, filetypes=self.fileTypes,
                                                        defaultextension=self.ext, initialdir=self.dirname,
                                                        initialfile=self.basename)
