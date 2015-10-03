# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2015  Diego Torres Milano
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
import random
import time
import re
from com.dtmilano.android.common import profileStart
from com.dtmilano.android.common import profileEnd
from com.dtmilano.android.concertina import Concertina

__version__ = '10.8.1'

import sys
import threading
import warnings
import copy
import string
import os
import platform
from pkg_resources import Requirement, resource_filename

try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False

try:
    import Tkinter
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
    TOUCH_POINT = 'touch_point'
    LONG_TOUCH_POINT = 'long_touch_point'
    OPEN_NOTIFICATION = 'open_notification'
    OPEN_QUICK_SETTINGS = 'open_quick_settings'
    TYPE = 'type'
    PRESS = 'press'
    SNAPSHOT = 'snapshot'
    START_ACTIVITY = 'start_activity'
    SLEEP = 'sleep'
    TRAVERSE = 'traverse'
    VIEW_SNAPSHOT = 'view_snapshot'

    @staticmethod
    def fromCommandName(commandName):
        MAP = {'flingBackward': Operation.FLING_BACKWARD, 'flingForward': Operation.FLING_FORWARD,
               'flingToBeginning': Operation.FLING_TO_BEGINNING, 'flingToEnd': Operation.FLING_TO_END,
               'openNotification': Operation.OPEN_NOTIFICATION, 'openQuickSettings': Operation.OPEN_QUICK_SETTINGS,
               }
        return MAP[commandName]


class Culebron:
    APPLICATION_NAME = "Culebra"

    UPPERCASE_CHARS = string.uppercase[:26]

    KEYSYM_TO_KEYCODE_MAP = {
        'Home': 'HOME',
        'BackSpace': 'BACK',
        'Left': 'DPAD_LEFT',
        'Right': 'DPAD_RIGHT',
        'Up': 'DPAD_UP',
        'Down': 'DPAD_DOWN',
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
    onTouchListener = None
    snapshotDir = '/tmp'
    snapshotFormat = 'PNG'
    deviceArt = None
    dropShadow = False
    screenGlare = False

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
''')
        if not TKINTER_AVAILABLE:
            raise Exception('''Tkinter is needed for GUI mode

This is usually installed by python package. Check your distribution details.
''')

    def __init__(self, vc, device, serialno, printOperation, scale=1, concertina=False):
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
        @:param concertina: bool
        @:type concertina: enable concertina mode (see documentation)
        '''

        self.vc = vc
        self.printOperation = printOperation
        self.device = device
        self.serialno = serialno
        self.scale = scale
        self.concertina = concertina
        self.window = Tkinter.Tk()
        icon = resource_filename(Requirement.parse("androidviewclient"),
                                 "share/pixmaps/culebra.png")
        self.window.tk.call('wm', 'iconphoto', self.window._w,
                            ImageTk.PhotoImage(file=icon))
        self.mainMenu = MainMenu(self)
        self.window.config(menu=self.mainMenu)
        self.mainFrame = Tkinter.Frame(self.window)
        self.placeholder = Tkinter.Frame(self.mainFrame, width=400, height=400, background=Color.LIGHT_GRAY)
        self.placeholder.grid(row=1, column=1, rowspan=4)
        self.sideFrame = Tkinter.Frame(self.window)
        self.viewTree = ViewTree(self.sideFrame)
        self.viewDetails = ViewDetails(self.sideFrame)
        self.mainFrame.grid(row=1, column=1, columnspan=1, rowspan=4, sticky=Tkinter.N + Tkinter.S)
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
        self.permanentlyDisableEvents = False
        if DEBUG:
            try:
                self.printGridInfo()
            except:
                pass

    def printGridInfo(self):
        print >> sys.stderr, "window:", repr(self.window)
        print >> sys.stderr, "main:", repr(self.mainFrame)
        print >> sys.stderr, "main:", self.mainFrame.grid_info()
        print >> sys.stderr, "side:", repr(self.sideFrame)
        print >> sys.stderr, "side:", self.sideFrame.grid_info()
        print >> sys.stderr, "tree:", repr(self.viewTree)
        print >> sys.stderr, "tree:", self.viewTree.grid_info()
        print >> sys.stderr, "details:", repr(self.viewDetails)
        print >> sys.stderr, "details:", self.viewDetails.grid_info()

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
            print >> sys.stderr, "PROFILING: takeScreenshotAndShowItOnWindow()"
            profileStart()

        if DEBUG:
            print >> sys.stderr, "takeScreenshotAndShowItOnWindow()"
        self.unscaledScreenshot = self.device.takeSnapshot(reconnect=True)
        self.image = self.unscaledScreenshot
        (width, height) = self.image.size
        if self.scale != 1:
            self.image = self.image.resize((int(width * self.scale), int(height * self.scale)), Image.ANTIALIAS)
            (width, height) = self.image.size
        if self.canvas is None:
            if DEBUG:
                print >> sys.stderr, "Creating canvas", width, 'x', height
            self.placeholder.grid_forget()
            self.canvas = Tkinter.Canvas(self.mainFrame, width=width, height=height)
            self.canvas.focus_set()
            self.enableEvents()
            self.createMessageArea(width, height)
            self.createVignette(width, height)
        self.screenshot = ImageTk.PhotoImage(self.image)
        if self.imageId is not None:
            self.canvas.delete(self.imageId)
        self.imageId = self.canvas.create_image(0, 0, anchor=Tkinter.NW, image=self.screenshot)
        if DEBUG:
            try:
                print >> sys.stderr, "Grid info", self.canvas.grid_info()
            except:
                print >> sys.stderr, "Exception getting grid info"
        gridInfo = None
        try:
            gridInfo = self.canvas.grid_info()
        except:
            if DEBUG:
                print >> sys.stderr, "Adding canvas to grid (1,1)"
            self.canvas.grid(row=1, column=1, rowspan=4)
        if not gridInfo:
            self.canvas.grid(row=1, column=1, rowspan=4)
        self.findTargets()
        self.hideVignette()
        if DEBUG:
            try:
                self.printGridInfo()
            except:
                pass
        if PROFILE:
            profileEnd()

    def createMessageArea(self, width, height):
        self.__message = Tkinter.Label(self.window, text='', background=Color.GOLD, font=('Helvetica', 16),
                                       anchor=Tkinter.W)
        self.__message.configure(width=width)
        self.__messageAreaId = self.canvas.create_window(0, 0, anchor=Tkinter.NW, window=self.__message)
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
            print >> sys.stderr, "toast(", text, ",", background, ")"
        self.message(text, background)
        if text:
            t = threading.Timer(timeout, self.hideMessageArea)
            t.start()
        else:
            self.hideMessageArea()

    def createVignette(self, width, height):
        if DEBUG:
            print >> sys.stderr, "createVignette(%d, %d)" % (width, height)
        self.vignetteId = self.canvas.create_rectangle(0, 0, width, height, fill=Color.MAGENTA,
                                                       stipple='gray50')
        font = tkFont.Font(family='Helvetica', size=int(144 * self.scale))
        msg = "Please\nwait..."
        self.waitMessageShadowId = self.canvas.create_text(width / 2 + 2, height / 2 + 2, text=msg,
                                                           fill=Color.DARK_GRAY, font=font)
        self.waitMessageId = self.canvas.create_text(width / 2, height / 2, text=msg,
                                                     fill=Color.LIGHT_GRAY, font=font)
        self.canvas.update_idletasks()

    def showVignette(self):
        if DEBUG:
            print >> sys.stderr, "showVignette()"
        if self.canvas is None:
            return
        if self.vignetteId:
            if DEBUG:
                print >> sys.stderr, "    showing vignette"
            # disable events while we are processing one
            self.disableEvents()
            self.canvas.lift(self.vignetteId)
            self.canvas.lift(self.waitMessageShadowId)
            self.canvas.lift(self.waitMessageId)
            self.canvas.update_idletasks()

    def hideVignette(self):
        if DEBUG:
            print >> sys.stderr, "hideVignette()"
        if self.canvas is None:
            return
        if self.vignetteId:
            if DEBUG:
                print >> sys.stderr, "    hiding vignette"
            self.canvas.lift(self.imageId)
            self.canvas.update_idletasks()
            self.enableEvents()

    def deleteVignette(self):
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
            self.sideFrame.grid(row=1, column=2, rowspan=4, sticky=Tkinter.N + Tkinter.S)
            self.isSideFrameSown = True
        if DEBUG:
            self.printGridInfo()

    def hideSideFrame(self):
        self.sideFrame.grid_forget()
        self.isSideFrameShown = False
        if DEBUG:
            self.printGridInfo()

    def showViewTree(self):
        self.showSideFrame()
        self.viewTree.grid(row=1, column=1, rowspan=3, sticky=Tkinter.N + Tkinter.S)
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
        self.viewDetails.grid(row=row, column=1, rowspan=1, sticky=Tkinter.S)
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
            print >> sys.stderr, "viewTreeitemClicked:", event.__dict__
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

        vuid = view.getUniqueId()
        text = view.__smallStr__()
        if view.getParent() is None:
            self.viewTree.insert('', Tkinter.END, vuid, text=text)
        else:
            self.viewTree.insert(view.getParent().getUniqueId(), Tkinter.END, vuid, text=text, tags=('ttk'))
            self.viewTree.set(vuid, 'T', '*' if view.isTarget() else ' ')
            self.viewTree.tag_bind('ttk', '<1>', self.viewTreeItemClicked)

    def findTargets(self):
        '''
        Finds the target Views (i.e. for touches).
        '''

        if DEBUG:
            print >> sys.stderr, "findTargets()"
        LISTVIEW_CLASS = 'android.widget.ListView'
        ''' The ListView class name '''
        self.targets = []
        ''' The list of target coordinates (x1, y1, x2, y2) '''
        self.targetViews = []
        ''' The list of target Views '''
        if CHECK_KEYBOARD_SHOWN:
            if self.device.isKeyboardShown():
                print >> sys.stderr, "#### keyboard is show but handling it is not implemented yet ####"
                # FIXME: still no windows in uiautomator
                window = -1
            else:
                window = -1
        else:
            window = -1
        if self.vc:
            dump = self.vc.dump(window=window, sleep=0.1)
            self.printOperation(None, Operation.DUMP, window, dump)
        else:
            dump = []
        # the root element cannot be deleted from Treeview once added.
        # We have no option but to recreate it
        self.viewTree = ViewTree(self.sideFrame)
        for v in dump:
            if DEBUG:
                print >> sys.stderr, "    findTargets: analyzing", v.getClass(), v.getId()
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
                    print >> sys.stderr, "appending target", ((x1, y1, x2, y2))
                v.setTarget(True)
                self.targets.append((x1, y1, x2, y2))
                self.targetViews.append(v)
                target = True
            else:
                target = False

        if self.vc:
            self.vc.traverse(transform=self.populateViewTree)

    def getViewContainingPointAndGenerateTestCondition(self, x, y):
        if DEBUG:
            print >> sys.stderr, 'getViewContainingPointAndGenerateTestCondition(%d, %d)' % (x, y)
        self.finishGeneratingTestCondition()
        vlist = self.vc.findViewsContainingPoint((x, y))
        vlist.reverse()
        for v in vlist:
            text = v.getText()
            if text:
                self.toast(u'Asserting view with text=%s' % text, timeout=2)
                # FIXME: only getText() is invoked by the generated assert(), a parameter
                # should be used to provide different alternatives to printOperation()
                self.printOperation(v, Operation.TEST, text)
                break

    def findViewContainingPointInTargets(self, x, y):
        if self.vc:
            vlist = self.vc.findViewsContainingPoint((x, y))
            if DEBUG_FIND_VIEW:
                print >> sys.stderr, "Views found:"
                for v in vlist:
                    print >> sys.stderr, "   ", v.__smallStr__()
            vlist.reverse()
            for v in vlist:
                if DEBUG:
                    print >> sys.stderr, "checking if", v, "is in", self.targetViews
                if v in self.targetViews:
                    if DEBUG_TOUCH:
                        print >> sys.stderr
                        print >> sys.stderr, "I guess you are trying to touch:", v
                        print >> sys.stderr
                    return v

        return None

    def getViewContainingPointAndTouch(self, x, y):
        if DEBUG:
            print >> sys.stderr, 'getViewContainingPointAndTouch(%d, %d)' % (x, y)
        if self.areEventsDisabled:
            if DEBUG:
                print >> sys.stderr, "Ignoring event"
            self.canvas.update_idletasks()
            return

        self.showVignette()
        if DEBUG_POINT:
            print >> sys.stderr, "getViewsContainingPointAndTouch(x=%s, y=%s)" % (x, y)
            print >> sys.stderr, "self.vc=", self.vc
        v = self.findViewContainingPointInTargets(x, y)
        if v is None:
            # FIXME: We can touch by DIP by default if no Views were found
            self.hideVignette()
            msg = "There are no touchable or clickable views here!"
            self.toast(msg)
            return
        clazz = v.getClass()
        if clazz == 'android.widget.EditText':
            title = "EditText"
            kwargs = {}
            if DEBUG:
                print >> sys.stderr, v
            if v.isPassword():
                title = "Password"
                kwargs = {'show': '*'}
            text = tkSimpleDialog.askstring(title, "Enter text to type into this field", **kwargs)
            self.canvas.focus_set()
            if text:
                self.vc.setText(v, text)
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

        self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
        self.vc.sleep(5)
        self.takeScreenshotAndShowItOnWindow()

    def setText(self, v, text):
        if DEBUG:
            print >> sys.stderr, "setText(%s, '%s')" % (v.__tinyStr__(), text)
        # This is deleting the existing text, which should be asked in the dialog, but I would have to implement
        # the dialog myself
        v.setText(text)
        # This is not deleting the text, so appending if there's something
        # v.type(text)
        self.printOperation(v, Operation.TYPE, text)

    def touchView(self, v, root=None):
        v.touch()
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
            print >> sys.stderr, 'touchPoint(%d, %d)' % (x, y)
            print >> sys.stderr, 'touchPoint:', type(x), type(y)
        if self.areEventsDisabled:
            if DEBUG:
                print >> sys.stderr, "Ignoring event"
            self.canvas.update_idletasks()
            return
        if DEBUG:
            print >> sys.stderr, "Is touching point:", self.isTouchingPoint
        if self.isTouchingPoint:
            self.showVignette()
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
            print >> sys.stderr, 'longTouchPoint(%d, %d)' % (x, y)
        if self.areEventsDisabled:
            if DEBUG:
                print >> sys.stderr, "Ignoring event"
            self.canvas.update_idletasks()
            return
        if DEBUG:
            print >> sys.stderr, "Is long touching point:", self.isLongTouchingPoint
        if self.isLongTouchingPoint:
            self.showVignette()
            self.vc.longTouch(x, y)
            if self.coordinatesUnit == Unit.DIP:
                x = round(x / self.device.display['density'], 2)
                y = round(y / self.device.display['density'], 2)
            self.printOperation(None, Operation.LONG_TOUCH_POINT, x, y, 2000, self.coordinatesUnit,
                                self.device.display['orientation'])
            self.printOperation(None, Operation.SLEEP, 5)
            time.sleep(5)
            self.isLongTouchingPoint = False
            self.takeScreenshotAndShowItOnWindow()
            # self.hideVignette()
            self.statusBar.clear()
            return

    def onButton1Pressed(self, event):
        if DEBUG:
            print >> sys.stderr, "onButton1Pressed((", event.x, ", ", event.y, "))"
        (scaledX, scaledY) = (event.x / self.scale, event.y / self.scale)
        if DEBUG:
            print >> sys.stderr, "    onButton1Pressed: scaled: (", scaledX, ", ", scaledY, ")"
            print >> sys.stderr, "    onButton1Pressed: is grabbing:", self.isGrabbingTouch

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
            print >> sys.stderr, "onCtrlButton1Pressed((", event.x, ", ", event.y, "))"
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
            print >> sys.stderr, "onButton2Pressed((", event.x, ", ", event.y, "))"
        osName = platform.system()
        if osName == 'Darwin':
            self.showPopupMenu(event)

    def onButton3Pressed(self, event):
        if DEBUG:
            print >> sys.stderr, "onButton3Pressed((", event.x, ", ", event.y, "))"
        self.showPopupMenu(event)

    def command(self, keycode):
        '''
        Presses a key.
        Generates the actual key press on the device and prints the line in the script.
        '''

        self.device.press(keycode)
        self.printOperation(None, Operation.PRESS, keycode)

    def onKeyPressed(self, event):
        if DEBUG_KEY:
            print >> sys.stderr, "onKeyPressed(", repr(event), ")"
            print >> sys.stderr, "    event", type(event.char), len(event.char), repr(
                event.char), event.keysym, event.keycode, event.type
            print >> sys.stderr, "    events disabled:", self.areEventsDisabled
        if self.areEventsDisabled:
            if DEBUG_KEY:
                print >> sys.stderr, "ignoring event"
            self.canvas.update_idletasks()
            return

        char = event.char
        keysym = event.keysym

        if len(char) == 0 and not (
                        keysym in Culebron.KEYSYM_TO_KEYCODE_MAP or keysym in Culebron.KEYSYM_CULEBRON_COMMANDS):
            if DEBUG_KEY:
                print >> sys.stderr, "returning because len(char) == 0"
            return

        ###
        ### internal commands: no output to generated script
        ###
        try:
            handler = getattr(self, 'onCtrl%s' % self.UPPERCASE_CHARS[ord(char) - 1])
        except:
            handler = None
        if handler:
            return handler(event)
        elif keysym == 'F1':
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
                print >> sys.stderr, "Pressing", Culebron.KEYSYM_TO_KEYCODE_MAP[keysym]
            self.command(Culebron.KEYSYM_TO_KEYCODE_MAP[keysym])
        elif char == '\r':
            self.command('ENTER')
        elif char == '':
            # do nothing
            pass
        else:
            self.command(char.decode('ascii', errors='replace'))
        # commented out (profile)
        #time.sleep(1)
        self.takeScreenshotAndShowItOnWindow()

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
            self.window.geometry('%dx%d' % (self.device.display['width'] * self.scale,
                                            self.device.display['height'] * self.scale + int(
                                                self.statusBar.winfo_height())))
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
            print >> sys.stderr, "onCtrlA(", event, ")"
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
        filename = self.snapshotDir + os.sep + '${serialno}-' + view.variableNameFromId() + '-${timestamp}' + '.' + self.snapshotFormat.lower()
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
            print >> sys.stderr, "onCtrlQ(%s)" % event
        self.quit()

    def quit(self):
        if self.vc.uiAutomatorHelper:
            if DEBUG or True:
                print >> sys.stderr, "Quitting UiAutomatorHelper..."
            self.vc.uiAutomatorHelper.quit()
        self.window.destroy()

    def showSleepDialog(self):
        seconds = tkSimpleDialog.askfloat('Sleep Interval', 'Value in seconds:', initialvalue=1, minvalue=0,
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
            print >> sys.stderr, "onCtrlT()"
        if self.vc is None:
            self.toast('Test conditions can be generated when a back-end is defined')
            return
        # FIXME: This is only valid if we are generating a test case
        self.toggleGenerateTestCondition()

    def onCtrlU(self, event):
        if DEBUG:
            print >> sys.stderr, "onCtrlU()"

    def onCtrlV(self, event):
        if DEBUG:
            print >> sys.stderr, "onCtrlV()"
        self.printOperation(None, Operation.TRAVERSE)

    def toggleTargetZones(self):
        self.toggleTargets()
        self.canvas.update_idletasks()

    def onCtrlZ(self, event):
        if DEBUG:
            print >> sys.stderr, "onCtrlZ()"
        self.toggleTargetZones()

    def showControlPanel(self):
        from com.dtmilano.android.controlpanel import ControlPanel

        self.controlPanel = ControlPanel(self, self.printOperation)

    def onCtrlK(self, event):
        self.showControlPanel()

    def drag(self, start, end, duration, steps, units=Unit.DIP):
        self.showVignette()
        # the operation on this device is always done in PX
        self.device.drag(start, end, duration, steps)
        if units == Unit.DIP:
            x0 = round(start[0] / self.device.display['density'], 2)
            y0 = round(start[1] / self.device.display['density'], 2)
            x1 = round(end[0] / self.device.display['density'], 2)
            y1 = round(end[1] / self.device.display['density'], 2)
            start = (x0, y0)
            end = (x1, y1)
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
            print >> sys.stderr, "toggletargets: aretargetsmarked=", self.areTargetsMarked
        if not self.areTargetsMarked:
            self.markTargets()
        else:
            self.unmarkTargets()

    def markTargets(self):
        if DEBUG:
            print >> sys.stderr, "marktargets: aretargetsmarked=", self.areTargetsMarked
            print >> sys.stderr, "    marktargets: targets=", self.targets
        colors = ["#ff00ff", "#ffff00", "#00ffff"]

        self.markedTargetIds = {}
        c = 0
        for (x1, y1, x2, y2) in self.targets:
            if DEBUG:
                print "adding rectangle:", x1, y1, x2, y2
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
            print >> sys.stderr, "drawTouchedPoint(", x, ",", y, ")"
        size = 50
        return self.canvas.create_oval((x - size) * self.scale, (y - size) * self.scale, (x + size) * self.scale,
                                       (y + size) * self.scale, fill=Color.MAGENTA)

    def drawDragLine(self, x0, y0, x1, y1):
        if DEBUG:
            print >> sys.stderr, "drawDragLine(", x0, ",", y0, ",", x1, ",", y1, ")"
        width = 15
        return self.canvas.create_line(x0 * self.scale, y0 * self.scale, x1 * self.scale, y1 * self.scale, width=width,
                                       fill=Color.MAGENTA, arrow="last", arrowshape=(50, 50, 30), dash=(50, 25))

    def executeCommandAndRefresh(self, command):
        self.showVignette()
        if DEBUG:
            print >> sys.stderr, 'DEBUG: command=', command, command.__name__
            print >> sys.stderr, 'DEBUG: command=', command.__self__, command.__self__.view
        try:
            view = command.__self__.view
        except AttributeError:
            view = None
        self.printOperation(view, Operation.fromCommandName(command.__name__))
        command()
        self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
        self.vc.sleep(5)
        # FIXME: perhaps refresh() should be invoked here just in case size or orientation changed
        self.takeScreenshotAndShowItOnWindow()

    def changeLanguage(self):
        code = tkSimpleDialog.askstring("Change language", "Enter the language code")
        self.vc.uiDevice.changeLanguage(code)
        self.printOperation(None, Operation.CHANGE_LANGUAGE, code)
        self.refresh()

    def setOnTouchListener(self, listener):
        self.onTouchListener = listener

    def setGrab(self, state):
        if DEBUG:
            print >> sys.stderr, "Culebron.setGrab(%s)" % state
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
            print >> sys.stderr, "isClickableCheckableOrFocusable(", v.__tinyStr__(), ")"
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
        self.window.resizable(width=Tkinter.FALSE, height=Tkinter.FALSE)
        self.window.lift()
        if self.concertina:
            self.concertinaLoop()
        else:
            self.window.mainloop()

    def concertinaLoop(self):
        random.seed()
        self.disableEvents(permanently=True)
        self.concertinaLoopCallback(dontinteract=True)
        self.window.mainloop()

    def concertinaLoopCallback(self, dontinteract=False):
        if not dontinteract:
            if DEBUG_CONCERTINA:
                print >> sys.stderr, "CONCERTINA: should select one of these targets:"
                for v in self.targetViews:
                    print >> sys.stderr, "    ", unicode(v.__tinyStr__())
            rand = random.random()
            if DEBUG_CONCERTINA:
                print >> sys.stderr, "CONCERTINA: random=%f" % rand
            if rand > 0.85:
                # Send key events
                k = random.choice(['ENTER', 'BACK', 'HOME', 'MENU'])
                if DEBUG_CONCERTINA:
                    print >> sys.stderr, "CONCERTINA: key=" + k
                # DEBUG ONLY!
                # print >> sys.stderr, "Not sending key event"
                self.command(k)
            else:
                # Act on views
                _len = len(self.targetViews)
                if _len > 0:
                    i = random.randrange(len(self.targetViews))
                    target = self.targetViews[i]
                    z = self.targets[i]
                    if DEBUG_CONCERTINA:
                        print >> sys.stderr, "CONCERTINA: selected", unicode(target.__smallStr__())
                        print >> sys.stderr, "CONCERTINA: selected", z
                    _id = self.markTarget(*z)
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
                        print >> sys.stderr, "CONCERTINA: is scrollable: ", isScrollable
                        if parent:
                            print >> sys.stderr, "CONCERTINA: is scrollable parent: ", parent.isScrollable()
                            # cond = (isScrollable or parent.isScrollable() or parentClass == 'android.widget.ScrollView')
                            # DEBUG ONLY!
                            # print >> sys.stderr, "CONCERTINA: check:", cond
                            # if not cond:
                            #     self.window.after(500, self.concertinaLoopCallback)
                            #     return
                    if clazz == 'android.widget.EditText':
                        id = target.getId()
                        txt = target.getText()
                        if target.isPassword() or re.search('password', id, re.IGNORECASE) or re.search('password', txt,
                                                                                                        re.IGNORECASE):
                            text = Concertina.getRandomPassword()
                        elif re.search('email', id, re.IGNORECASE) or re.search('email', txt, re.IGNORECASE):
                            text = Concertina.getRandomEmail()
                        else:
                            text = Concertina.getRandomText()
                        if DEBUG_CONCERTINA:
                            print >> sys.stderr, "Entering text: ", text
                        if not text:
                            raise RuntimeError('text is None')
                        self.setText(target, text)
                    elif target.getContentDescription() in ['Voice Search', 'Tap to speak']:
                        Concertina.sayRandomText()
                        time.sleep(5)
                    elif random.choice(['SCROLL', 'TOUCH']) == 'SCROLL' and (
                            isScrollable or parent.isScrollable() or parentClass == 'android.widget.ScrollView'):
                        # NOTE: The order here is important because some EditText are inside ScrollView's and we want to
                        # capture the case of other ScrollViews
                        if isScrollable:
                            ((l, t), (r, b)) = target.getBounds()
                        else:
                            if DEBUG_CONCERTINA:
                                print >> sys.stderr, "CONCERTINA: using parent bounds because it's scrollable"
                            ((l, t), (r, b)) = parent.getBounds()
                        if DEBUG_CONCERTINA:
                            print >> sys.stderr, "CONCERTINA: bounds=", ((l, t), (r, b))
                        if random.choice(['VERTICAL', 'HORIZONTAL']) == 'VERTICAL':
                            if DEBUG_CONCERTINA:
                                print >> sys.stderr, 'CONCERTINA: VERTICAL'
                            sp = (l + (r - l) / 2, t + 50)
                            ep = (l + (r - l) / 2, b - 50)
                        else:
                            if DEBUG_CONCERTINA:
                                print >> sys.stderr, 'CONCERTINA: HORIZONTAL'
                            sp = (l + 50, t + (b - t) / 2)
                            ep = (r - 50, t + (b - t) / 2)
                        if random.choice(['FORWARD', 'REVERSE']) == 'REVERSE':
                            if DEBUG_CONCERTINA:
                                print >> sys.stderr, 'CONCERTINA: REVERSE'
                            temp = sp
                            sp = ep
                            ep = temp
                        else:
                            if DEBUG_CONCERTINA:
                                print >> sys.stderr, 'CONCERTINA: FORWARD'
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
                            print >> sys.stderr, "CONCERTINA: dragging %s %s %s %s %s" % (sp, ep, d, s, units)
                        self.drag(sp, ep, d, s, units)
                    else:
                        self.touchView(target)
                    self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
                    if DEBUG_CONCERTINA:
                        print >> sys.stderr, "CONCERTINA: waiting 5 secs"
                    time.sleep(5)
                    if DEBUG_CONCERTINA:
                        print >> sys.stderr, "CONCERTINA: taking screenshot"
                    self.takeScreenshotAndShowItOnWindow()
                else:
                    print >> sys.stderr, "CONCERTINA: No target views"
        self.window.after(5000, self.concertinaLoopCallback)


if TKINTER_AVAILABLE:
    class MainMenu(Tkinter.Menu):
        def __init__(self, culebron):
            Tkinter.Menu.__init__(self, culebron.window)
            self.culebron = culebron

            self.fileMenu = Tkinter.Menu(self, tearoff=False)
            self.fileMenu.add_command(label="Quit", underline=0, accelerator='Command-Q', command=self.culebron.quit)
            self.add_cascade(label="File", underline=0, menu=self.fileMenu)

            self.viewMenu = Tkinter.Menu(self, tearoff=False)
            self.showViewTree = Tkinter.BooleanVar()
            self.showViewTree.set(False)
            state = NORMAL if culebron.vc else DISABLED
            self.viewMenu.add_checkbutton(label="Tree", underline=0, accelerator='Command-T', onvalue=True,
                                          offvalue=False, variable=self.showViewTree, state=state,
                                          command=self.onshowViewTreeChanged)
            self.showViewDetails = Tkinter.BooleanVar()
            self.showViewDetails.set(False)
            state = NORMAL if culebron.vc else DISABLED
            self.viewMenu.add_checkbutton(label="View details", underline=0, accelerator='Command-V', onvalue=True,
                                          offvalue=False, variable=self.showViewDetails, state=state,
                                          command=self.onShowViewDetailsChanged)
            self.add_cascade(label="View", underline=0, menu=self.viewMenu)

            self.uiDeviceMenu = Tkinter.Menu(self, tearoff=False)
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

            self.helpMenu = Tkinter.Menu(self, tearoff=False)
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


    class ViewTree(Tkinter.Frame):
        def __init__(self, parent):
            Tkinter.Frame.__init__(self, parent)
            self.viewTree = ttk.Treeview(self, columns=['T'], height=35)
            self.viewTree.column(0, width=20)
            self.viewTree.heading('#0', None, text='View', anchor=Tkinter.W)
            self.viewTree.heading(0, None, text='T', anchor=Tkinter.W)
            self.scrollbar = ttk.Scrollbar(self, orient=Tkinter.HORIZONTAL, command=self.__xscroll)
            self.viewTree.grid(row=1, rowspan=1, column=1, sticky=Tkinter.N + Tkinter.S)
            self.scrollbar.grid(row=2, rowspan=1, column=1, sticky=Tkinter.E + Tkinter.W)
            self.viewTree.configure(xscrollcommand=self.scrollbar.set)

        def __xscroll(self, *args):
            if DEBUG:
                print >> sys.stderr, "__xscroll:", args
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
                print >> sys.stderr, 'ViewTree.tag_bind(', tagname, ',', sequence, ',', callback, ')'
            return self.viewTree.tag_bind(tagname, sequence, callback)


    class ViewDetails(Tkinter.Frame):
        VIEW_DETAILS = "View Details:\n"

        def __init__(self, parent):
            Tkinter.Frame.__init__(self, parent)
            self.label = Tkinter.Label(self, bd=1, width=30, wraplength=200, justify=Tkinter.LEFT, anchor=Tkinter.NW)
            self.label.configure(text=self.VIEW_DETAILS)
            self.label.configure(bg="white")
            self.label.grid(row=3, column=1, rowspan=1)

        def set(self, view):
            self.label.configure(text=self.VIEW_DETAILS + view.__str__())


    class StatusBar(Tkinter.Frame):

        def __init__(self, parent):
            Tkinter.Frame.__init__(self, parent)
            self.label = Tkinter.Label(self, bd=1, relief=Tkinter.SUNKEN, anchor=Tkinter.W)
            self.label.grid(row=1, column=1, columnspan=2, sticky=Tkinter.E + Tkinter.W)

        def set(self, fmt, *args):
            self.label.config(text=fmt % args)
            self.label.update_idletasks()

        def clear(self):
            self.label.config(text="")
            self.label.update_idletasks()


    class LabeledEntry():
        def __init__(self, parent, text, validate, validatecmd):
            self.f = Tkinter.Frame(parent)
            Tkinter.Label(self.f, text=text, anchor="w", padx=8).grid(row=1, column=1, sticky=Tkinter.E)
            self.entry = Tkinter.Entry(self.f, validate=validate, validatecommand=validatecmd)
            self.entry.grid(row=1, column=2, padx=5, sticky=Tkinter.E)

        def grid(self, **kwargs):
            self.f.grid(kwargs)

        def get(self):
            return self.entry.get()

        def set(self, text):
            self.entry.delete(0, Tkinter.END)
            self.entry.insert(0, text)


    class LabeledEntryWithButton(LabeledEntry):
        def __init__(self, parent, text, buttonText, command, validate, validatecmd):
            LabeledEntry.__init__(self, parent, text, validate, validatecmd)
            self.button = Tkinter.Button(self.f, text=buttonText, command=command)
            self.button.grid(row=1, column=3)


    class DragDialog(Tkinter.Toplevel):

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
            Tkinter.Toplevel.__init__(self, self.parent)
            self.transient(self.parent)
            self.culebron.setDragDialogShowed(True)
            self.title("Drag: selecting parameters")

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

            l = Tkinter.Label(self, text="Units")
            l.grid(row=3, column=1, sticky=Tkinter.E)

            self.units = Tkinter.StringVar()
            self.units.set(Unit.DIP)
            col = 2
            for u in dir(Unit):
                if u.startswith('_'):
                    continue
                rb = Tkinter.Radiobutton(self, text=u, variable=self.units, value=u)
                rb.grid(row=3, column=col, padx=20, sticky=Tkinter.E)
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

            box = Tkinter.Frame(self)

            self.ok = Tkinter.Button(box, text="OK", width=10, command=self.onOk, default=Tkinter.ACTIVE,
                                     state=Tkinter.DISABLED)
            self.ok.grid(row=6, column=1, sticky=Tkinter.E, padx=5, pady=5)
            w = Tkinter.Button(box, text="Cancel", width=10, command=self.onCancel)
            w.grid(row=6, column=2, sticky=Tkinter.E, padx=5, pady=5)

            self.bind("<Return>", self.onOk)
            self.bind("<Escape>", self.onCancel)

            box.grid(row=6, column=1, columnspan=3)

        def onValidate(self, value):
            if self.sp.get() and self.ep.get() and self.d.get() and self.s.get():
                self.ok.configure(state=Tkinter.NORMAL)
            else:
                self.ok.configure(state=Tkinter.DISABLED)

        def onOk(self, event=None):
            if DEBUG:
                print >> sys.stderr, "onOK()"
                print >> sys.stderr, "values are:",
                print >> sys.stderr, self.sp.get(),
                print >> sys.stderr, self.ep.get(),
                print >> sys.stderr, self.d.get(),
                print >> sys.stderr, self.s.get(),
                print >> sys.stderr, self.units.get()

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


    class ContextMenu(Tkinter.Menu):
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

        class UiScrollableSubMenu(Tkinter.Menu):
            def __init__(self, menu, description, view, culebron):
                # Tkninter.Menu is not extending object, so we can't do this:
                # super(ContextMenu, self).__init__(culebron.window, tearoff=False)
                Tkinter.Menu.__init__(self, menu, tearoff=False)
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
            Tkinter.Menu.__init__(self, culebron.window, tearoff=False)
            if DEBUG_CONTEXT_MENU:
                print >> sys.stderr, "Creating ContextMenu for", view.__smallStr__() if view else "No View"
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


    class HelpDialog(Tkinter.Toplevel):

        def __init__(self, culebron):
            self.culebron = culebron
            self.parent = culebron.window
            Tkinter.Toplevel.__init__(self, self.parent)
            # self.transient(self.parent)
            self.title("%s: help" % Culebron.APPLICATION_NAME)

            self.text = ScrolledText.ScrolledText(self, width=60, height=40)
            self.text.insert(Tkinter.INSERT, '''
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

            box = Tkinter.Frame(self)

            w = Tkinter.Button(box, text="Dismiss", width=10, command=self.onDismiss, default=Tkinter.ACTIVE)
            w.grid(row=1, column=1, padx=5, pady=5)

            self.bind("<Return>", self.onDismiss)
            self.bind("<Escape>", self.onDismiss)

            box.grid(row=1, column=1)

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
            return tkFileDialog.asksaveasfilename(parent=self.parent, filetypes=self.fileTypes,
                                                  defaultextension=self.ext, initialdir=self.dirname,
                                                  initialfile=self.basename)
