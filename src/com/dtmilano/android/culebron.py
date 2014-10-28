# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2014  Diego Torres Milano
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

__version__ = '8.10.1'

import sys
import threading
import warnings

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False

try:
    import Tkinter
    import tkSimpleDialog
    import tkFont
    TKINTER_AVAILABLE = True
except:
    TKINTER_AVAILABLE = False

from ast import literal_eval as make_tuple

DEBUG = False
DEBUG_MOVE = DEBUG and False
DEBUG_TOUCH = DEBUG and False
DEBUG_POINT = DEBUG and True
DEBUG_KEY = DEBUG and True


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
    DEFAULT = 'default'
    DRAG = 'drag'
    DUMP = 'dump'
    TEST = 'test'
    TEST_TEXT = 'test_text'
    TOUCH_VIEW = 'touch_view'
    TOUCH_POINT = 'touch_point'
    LONG_TOUCH_POINT = 'long_touch_point'
    TYPE = 'type'
    PRESS = 'press'
    SLEEP = 'sleep'

class Culebron:
    KEYSYM_TO_KEYCODE_MAP = {
        'Home': 'HOME',
        'BackSpace': 'BACK',
        'Left': 'DPAD_LEFT',
        'Right': 'DPAD_RIGHT',
        'Up': 'DPAD_UP',
        'Down': 'DPAD_DOWN',
         }
     
    KEYSYM_CULEBRON_COMMANDS = {
        'F5': None
        }

    canvas = None
    imageId = None
    vignetteId = None
    areTargetsMarked = False
    isGrabbing = False
    isGeneratingTestCondition = False
    isTouchingPoint = False
    isLongTouchingPoint = False
    
    @staticmethod
    def checkDependencies():
        if not PIL_AVAILABLE:
            raise Exception('''PIL is needed for GUI mode

On Ubuntu install

   $ sudo apt-get install python-imaging python-imaging-tk

On OSX install

   $ brew install pil
''')
        if not TKINTER_AVAILABLE:
            raise Exception('''Tkinter is needed for GUI mode

This is usually installed by python package. Check your distribution details.
''')

    def __init__(self, vc, printOperation, scale=1):
        '''
        Culebron constructor.
        
        @param vc: The ViewClient used by this Culebron instance
        @type vc: ViewClient
        @param printOperation: the method invoked to print operations to the script
        @type printOperation: method
        '''
        
        self.vc = vc
        self.printOperation = printOperation
        self.device = vc.device
        self.serialno = vc.serialno
        self.scale = scale
        self.window = Tkinter.Tk()

    def takeScreenshotAndShowItOnWindow(self):
        image = self.device.takeSnapshot(reconnect=True)
        # FIXME: allow scaling
        (width, height) = image.size
        if self.scale != 1:
            image = image.resize((int(width*self.scale), int(height*self.scale)), Image.ANTIALIAS)
            (width, height) = image.size
        if self.canvas is None:
            if DEBUG:
                print >> sys.stderr, "Creating canvas", width, 'x', height
            self.canvas = Tkinter.Canvas(self.window, width=width, height=height)
            self.canvas.focus_set()
            self.enableEvents()
            self.createMessageArea(width, height)
            self.createVignette(width, height)
        self.screenshot = ImageTk.PhotoImage(image)
        if self.imageId is not None:
            self.canvas.delete(self.imageId)
        self.imageId = self.canvas.create_image(0, 0, anchor=Tkinter.NW, image=self.screenshot)
        try:
            self.canvas.pack_info()
        except:
            self.canvas.pack(fill=Tkinter.BOTH)
        self.findTargets()
        self.hideVignette()
        
    def createMessageArea(self, width, height):
        self.__message = Tkinter.Label(self.window, text='', background=Color.GOLD, font=('Helvetica', 16), anchor=Tkinter.W)
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

    def toast(self, text, background=None):
        if DEBUG:
            print >> sys.stderr, "toast(", text, ",", background,  ")"
        self.message(text, background)
        t = threading.Timer(5, self.hideMessageArea)
        t.start()

    def createVignette(self, width, height):
        self.vignetteId = self.canvas.create_rectangle(0, 0, width, height, fill=Color.MAGENTA,
            stipple='gray50')
        font = tkFont.Font(family='Helvetica',size=int(144*self.scale))
        msg = "Please\nwait..."
        self.waitMessageShadowId = self.canvas.create_text(width/2+2, height/2+2, text=msg,
            fill=Color.DARK_GRAY, font=font)
        self.waitMessageId = self.canvas.create_text(width/2, height/2, text=msg,
            fill=Color.LIGHT_GRAY, font=font)
    
    def showVignette(self):
        if self.vignetteId:
            if DEBUG:
                print >> sys.stderr, "showing vignette"
            # disable events while we are processing one
            self.disableEvents()
            self.canvas.lift(self.vignetteId)
            self.canvas.lift(self.waitMessageShadowId)
            self.canvas.lift(self.waitMessageId)
            self.canvas.update_idletasks()
    
    def hideVignette(self):
        if self.vignetteId:
            if DEBUG:
                print >> sys.stderr, "hidding vignette"
            self.canvas.lift(self.imageId)
            self.canvas.update_idletasks()
            self.enableEvents()
    
    def findTargets(self):
        self.targets = []
        if self.device.isKeyboardShown():
            print >> sys.stderr, "#### keyboard is show but handling it is not implemented yet ####"
            # fixme: still no windows in uiautomator
            window = -1
        else:
            window = -1
        self.printOperation(None, Operation.DUMP, window)
        for v in self.vc.dump(window=window):
            if self.isClickableCheckableOrFocusable(v):
                ((x1, y1), (x2, y2)) = v.getCoords()
                # workaround to avoid whole phone screen
                #if (x1, y1, x2, y2) == (0, 108, , 1216):
                #    continue
                if DEBUG:
                    print >> sys.stderr, "appending target", ((x1, y1, x2, y2))
                self.targets.append((x1, y1, x2, y2))
            else:
                #print v
                pass
    
    def getViewContainingPointAndGenerateTestCondition(self, x, y):
        if DEBUG:
            print >> sys.stderr, 'getViewContainingPointAndGenerateTestCondition(%d, %d)' % (x, y)
        self.finishGeneratingTestCondition()
        vlist = self.vc.findViewsContainingPoint((x, y))
        vlist.reverse()
        for v in vlist:
            text = v.getText()
            if text:
                # FIXME: only getText() is invoked by the generated assert(), a parameter
                # should be used to provide different alternatives to printOperation()
                self.printOperation(v, Operation.TEST, text)
                break
                

    def getViewContainingPointAndTouch(self, x, y):
        if DEBUG:
            print >> sys.stderr, 'getViewContainingPointAndTouch(%d, %d)' % (x, y)
        if self.areEventsDisabled:
            if DEBUG:
                print >> sys.stderr, "Ignoring event"
            self.canvas.update_idletasks()
            return
        if DEBUG:
            print >> sys.stderr, "Is grabbing:", self.isGrabbing
        if self.isGrabbing:
            if DEBUG:
                print >> sys.stderr, "Grabbing event"
            self.onTouchListener((x, y))
            self.isGrabbing = False
            return
            
        self.showVignette()
        if DEBUG_POINT:
            print >> sys.stderr, "getViewsContainingPointAndTouch(x=%s, y=%s)" % (x, y)
            print >> sys.stderr, "self.vc=", self.vc
        vlist = self.vc.findViewsContainingPoint((x, y))
        vlist.reverse()
        found = False
        for v in vlist:
            if self.isClickableCheckableOrFocusable(v):
                if DEBUG_TOUCH:
                    print >> sys.stderr
                    print >> sys.stderr, "I guess you are trying to touch:", v
                    print >> sys.stderr
                found = True
                break
        if not found:
            self.hideVignette()
            msg = "There are not clickable views here!"
            print >> sys.stderr, msg
            self.toast(msg)
            return
        clazz = v.getClass()
        if clazz == 'android.widget.EditText':
            if DEBUG:
                print >>sys.stderr, v
            text = tkSimpleDialog.askstring("EditText", "Enter text to type into this EditText")
            self.canvas.focus_set()
            if text:
                v.type(text)
                self.printOperation(v, Operation.TYPE, text)
        else:
            v.touch()
            self.printOperation(v, Operation.TOUCH_VIEW)

        self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
        self.vc.sleep(5)
        self.takeScreenshotAndShowItOnWindow()

    def touchPoint(self, x, y):
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
            self.device.touch(x, y)
            if self.coordinatesUnit == Unit.DIP:
                x = x / self.vc.display['density']
                y = y / self.vc.display['density']
            self.printOperation(None, Operation.TOUCH_POINT, x, y, self.coordinatesUnit)
            self.printOperation(None, Operation.SLEEP, Operation.DEFAULT)
            self.vc.sleep(5)
            self.isTouchingPoint = False
            self.takeScreenshotAndShowItOnWindow()
            self.hideVignette()
            return
    
    def longTouchPoint(self, x, y):
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
            self.device.longTouch(x, y)
            self.printOperation(None, Operation.LONG_TOUCH_POINT, x, y, 2000)
            self.printOperation(None, Operation.SLEEP, 5)
            self.vc.sleep(5)
            self.isLongTouchingPoint = False
            self.takeScreenshotAndShowItOnWindow()
            self.hideVignette()
            return
    
    def onButton1Pressed(self, event):
        if DEBUG:
            print >> sys.stderr, "onButton1Pressed((", event.x, ", ", event.y, "))"
        (scaledX, scaledY) = (event.x/self.scale, event.y/self.scale)
        if DEBUG:
            print >> sys.stderr, "    onButton1Pressed: scaled: (", scaledX, ", ", scaledY, ")"
        if self.isTouchingPoint:
            self.touchPoint(scaledX, scaledY)
        elif self.isLongTouchingPoint:
            self.longTouchPoint(scaledX, scaledY)
        elif self.isGeneratingTestCondition:
            self.getViewContainingPointAndGenerateTestCondition(scaledX, scaledY)
        else:
            self.getViewContainingPointAndTouch(scaledX, scaledY)
        
    def pressKey(self, keycode):
        '''
        Presses a key.
        Generates the actual key press on the device and prints the line in the script.
        '''
        
        self.device.press(keycode)
        self.printOperation(None, Operation.PRESS, keycode)
            
    def onKeyPressed(self, event):
        if DEBUG_KEY:
            print >> sys.stderr, "onKeyPressed(", repr(event), ")"
            print >> sys.stderr, "    event", type(event.char), len(event.char), repr(event.char), event.keysym, event.keycode, event.type
        if self.areEventsDisabled:
            if DEBUG_KEY:
                print >> sys.stderr, "ignoring event"
            self.canvas.update_idletasks()
            return


        char = event.char
        keysym = event.keysym

        if len(char) == 0 and not (keysym in Culebron.KEYSYM_TO_KEYCODE_MAP or keysym in Culebron.KEYSYM_CULEBRON_COMMANDS):
            if DEBUG_KEY:
                print >> sys.stderr, "returning because len(char) == 0"
            return
        
        ###
        ### internal commands: no output to generated script
        ###
        # FIXME: use a map
        if char == '\x01':
            self.onCtrlA(event)
            return
        elif char == '\x04':
            self.onCtrlD(event)
            return
        elif char == '\x09':
            self.onCtrlI(event)
            return
        elif char == '\x0c':
            self.onCtrlL(event)
            return
        elif char == '\x10':
            self.onCtrlP(event)
            return
        elif char == '\x11':
            self.onCtrlQ(event)
            return 
        elif char == '\x13':
            self.onCtrlS(event)
            return
        elif char == '\x14':
            self.onCtrlT(event)
            return
        elif char == '\x15':
            self.onCtrlU(event)
            return
        elif char == '\x1a':
            self.onCtrlZ(event)
            return
        elif keysym == 'F5':
            self.showVignette()
            self.takeScreenshotAndShowItOnWindow()
            return
        elif keysym == 'Alt_L':
            return
        elif keysym == 'Control_L':
            return

        ### empty char (modifier) ###
        # here does not process events  like Home where char is ''
        #if char == '':
        #    return

        ###
        ### target actions
        ###
        self.showVignette()

        if keysym in Culebron.KEYSYM_TO_KEYCODE_MAP:
            if DEBUG_KEY:
                print >> sys.stderr, "Pressing", Culebron.KEYSYM_TO_KEYCODE_MAP[keysym]
            self.pressKey(Culebron.KEYSYM_TO_KEYCODE_MAP[keysym])
        elif char == '\r':
            self.pressKey('ENTER')
        elif char == '':
            # do nothing
            pass
        else:
            self.pressKey(char.decode('ascii', errors='replace'))
        self.vc.sleep(1)
        self.takeScreenshotAndShowItOnWindow()

    
    def onCtrlA(self, event):
        if DEBUG:
            self.toggleMessageArea()

    def onCtrlD(self, event):
        d = DragDialog(self)
        self.window.wait_window(d.top)

    def onCtrlI(self, event):
        self.coordinatesUnit = Unit.DIP
        self.toggleTouchPoint()
    
    def onCtrlL(self, event):
        if not self.isLongTouchingPoint:
            self.toast('Long touching point', background=Color.GREEN)
            self.isLongTouchingPoint = True
        else:
            self.isLongTouchingPoint = False

    def toggleTouchPoint(self):
        if not self.isTouchingPoint:
            self.toast('Touching point (units=%s)' % self.coordinatesUnit, background=Color.GREEN)
            self.isTouchingPoint = True
        else:
            self.isTouchingPoint = False

    def onCtrlP(self, event):
        self.coordinatesUnit = Unit.PX
        self.toggleTouchPoint()
        
    def onCtrlQ(self, event):
        self.window.quit()
        
    def onCtrlS(self, event):
        self.printOperation(None, Operation.SLEEP, 1)
    
    def startGeneratingTestCondition(self):
        self.message('Generating test condition...', background=Color.GREEN)
        self.isGeneratingTestCondition = True

    def finishGeneratingTestCondition(self):
        self.isGeneratingTestCondition = False
        self.hideMessageArea()

    def onCtrlT(self, event):
        '''
        Toggles generating test condition
        '''

        if DEBUG:
            print >>sys.stderr, "onCtrlT()"
        if self.isGeneratingTestCondition:
            self.finishGeneratingTestCondition()
        else:
            self.startGeneratingTestCondition()
    
    def onCtrlU(self, event):
        if DEBUG:
            print >>sys.stderr, "onCtrlU()"
    
    def onCtrlZ(self, event):
        if DEBUG:
            print >> sys.stderr, "onCtrlZ()"
        self.toggleTargets()
        self.canvas.update_idletasks()
    
    def drag(self, start, end, duration, steps):
        self.showVignette()
        self.device.drag(start, end, duration, steps)
        self.printOperation(None, Operation.DRAG, start, end, duration, steps)
        self.printOperation(None, Operation.SLEEP, 1)
        self.vc.sleep(1)
        self.takeScreenshotAndShowItOnWindow()
        
    def enableEvents(self):
        self.canvas.update_idletasks()
        self.canvas.bind("<Button-1>", self.onButton1Pressed)
        self.canvas.bind("<BackSpace>", self.onKeyPressed)
        #self.canvas.bind("<Control-Key-S>", self.onCtrlS)
        self.canvas.bind("<Key>", self.onKeyPressed)
        self.areEventsDisabled = False

    def disableEvents(self):
        self.canvas.update_idletasks()
        self.areEventsDisabled = True
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<BackSpace>")
        #self.canvas.unbind("<Control-Key-S>")
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

        self.targetIds = []
        c = 0
        for (x1, y1, x2, y2) in self.targets:
            if DEBUG:
                print "adding rectangle:", x1, y1, x2, y2
            self.targetIds.append(self.canvas.create_rectangle(x1*self.scale, y1*self.scale, x2*self.scale, y2*self.scale, fill=colors[c%len(colors)], stipple="gray25"))
            c += 1
        self.areTargetsMarked = True

    def unmarkTargets(self):
        if not self.areTargetsMarked:
            return
        for t in self.targetIds:
            self.canvas.delete(t)
        self.areTargetsMarked = False

    def setOnTouchListener(self, listener):
        self.onTouchListener = listener

    def setGrab(self, state):
        if DEBUG:
            print >> sys.stderr, "Culebron.setGrab(%s)" % state
        if not self.onTouchListener:
            warnings.warn('Starting to grab but no onTouchListener')
        self.isGrabbing = state
        if state:
            self.toast('Grabbing drag points...', background=Color.GREEN)
        else:
            self.hideMessageArea()


    @staticmethod
    def isClickableCheckableOrFocusable(v):
        try:
            return (v.isclickable() or v.ischeckable() or v.isfocusable())
        except AttributeError:
            return False
    
    def mainloop(self):
        self.window.mainloop()

class LabeledEntry():
    def __init__(self, parent, text):
        self.f = Tkinter.Frame(parent)
        Tkinter.Label(self.f, text=text, anchor="w", padx=8).pack(fill="x")
        self.entry = Tkinter.Entry(self.f, validate="focusout", validatecommand=self.focusout)
        self.entry.pack(padx=5)

    def pack(self, **kwargs):
        self.f.pack(kwargs)

    def focusout(self):
        if DEBUG:
            print >> sys.stderr, "FOCUSOUT"

    def get(self):
        return self.entry.get()

    def set(self, text):
        self.entry.delete(0, Tkinter.END)
        self.entry.insert(0, text)
        
class LabeledEntryWithButton(LabeledEntry):
    def __init__(self, parent, text, buttonText, command):
        LabeledEntry.__init__(self, parent, text)
        self.button = Tkinter.Button(self.f, text=buttonText, command=command)
        self.button.pack(side="right")

class DragDialog:
    
    def __init__(self, culebron):
        self.culebron = culebron
        parent = culebron.window
        top = self.top = Tkinter.Toplevel(parent)

        self.sp = LabeledEntryWithButton(top, "Start point", "Grab", command=self.onGrabSp)
        self.sp.pack(pady=5)

        self.ep = LabeledEntryWithButton(top, "End point", "Grab", command=self.onGrabEp)
        self.ep.pack(pady=5)

        self.d = LabeledEntry(top, "Duration")
        self.d.set("1000")
        self.d.pack(pady=5)

        self.s = LabeledEntry(top, "Steps")
        self.s.set("20")
        self.s.pack(pady=5)

        b = Tkinter.Button(top, text="OK", command=self.onOk)
        b.pack(pady=5)

    def onOk(self):
        if DEBUG:
            print >> sys.stderr, "values are:",
            print >> sys.stderr, self.sp.get(),
            print >> sys.stderr, self.ep.get(),
            print >> sys.stderr, self.d.get(),
            print >> sys.stderr, self.s.get()

        sp = make_tuple(self.sp.get())
        ep = make_tuple(self.ep.get())
        d = int(self.d.get())
        s = int(self.s.get())
        self.top.destroy()
        self.culebron.drag(sp, ep, d, s)

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
        '''
        
        if DEBUG:
            print >> sys.stderr, "GRAB"
        self.culebron.setOnTouchListener(self.onTouchListener)
        self.__grabbing = entry
        self.culebron.setGrab(True)

    def onTouchListener(self, point):
        if DEBUG:
            print >> sys.stderr, "TOUCHED", point
        self.__grabbing.set("(%d,%d)" % (point[0], point[1]))
        self.culebron.setGrab(False)
        self.__grabbing = None
        self.culebron.setOnTouchListener(None)

