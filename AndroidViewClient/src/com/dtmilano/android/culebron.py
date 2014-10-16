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

__version__ = '8.2.1'

import sys

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

class Operation:
    ASSIGN = 'assign'
    DUMP = 'dump'
    TEST = 'test'
    TEST_TEXT = 'test_text'
    TOUCH = 'touch'
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
     
    canvas = None
    imageId = None
    vignetteId = None
    areTargetsMarked = False
    isGrabbing = False
    isGeneratingTestCondition = False
    
    @staticmethod
    def checkDependencies():
        if not PIL_AVAILABLE:
            raise Exception("PIL is needed for GUI mode")
        if not TKINTER_AVAILABLE:
            raise Exception("Tkinter is needed for GUI mode")

    def __init__(self, vc, printOperation):
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
        self.window = Tkinter.Tk()

    def takeScreenshotAndShowItOnWindow(self):
        image = self.device.takeSnapshot(reconnect=True)
        # FIXME: allow scaling
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
        self.__message = Tkinter.Label(self.window, text='', background=Color.GREEN, font=('Helvetica', 16), anchor=Tkinter.W)
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

    def createVignette(self, width, height):
        self.vignetteId = self.canvas.create_rectangle(0, 0, width, height, fill=Color.MAGENTA,
            stipple='gray50')
        font = tkFont.Font(family='Helvetica',size=144)
        self.waitMessageShadowId = self.canvas.create_text(width/2+2, height/2+2, text="Please\nwait...",
            fill=Color.DARK_GRAY, font=font)
        self.waitMessageId = self.canvas.create_text(width/2, height/2, text="Please\nwait...",
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
            print >> sys.stderr, "there are not clickable views here!"
            self.hideVignette()
            return
        clazz = v.getClass()
        if clazz == 'android.widget.EditText':
            if DEBUG:
                print >>sys.stderr, v
            text = tkSimpleDialog.askstring("EditText", "enter text to type into this EditText")
            self.canvas.focus_set()
            if text:
                v.type(text)
                self.printOperation(v, Operation.TYPE, text)
        else:
            v.touch()
            self.printOperation(v, Operation.TOUCH)

        self.printOperation(None, Operation.SLEEP, 5)
        self.vc.sleep(5)
        self.takeScreenshotAndShowItOnWindow()

    
    def button1Pressed(self, event):
        if self.isGeneratingTestCondition:
            self.getViewContainingPointAndGenerateTestCondition(event.x, event.y)
        else:
            self.getViewContainingPointAndTouch(event.x, event.y)
        
    def pressKey(self, keycode):
        self.device.press(keycode)
        self.printOperation(None, Operation.PRESS, keycode)
            
    def keyPressed(self, event):
        if DEBUG_KEY:
            print >> sys.stderr, "keyPressed(", repr(event), ")"
            print >> sys.stderr, "    event", type(event.char), len(event.char), repr(event.char), event.keysym, event.keycode, event.type
        if self.areEventsDisabled:
            if DEBUG:
                print >> sys.stderr, "ignoring event"
            self.canvas.update_idletasks()
            return


        char = event.char
        keysym = event.keysym

        if len(char) == 0 and keysym not in Culebron.KEYSYM_TO_KEYCODE_MAP:
            if DEBUG_KEY:
                print >> sys.stderr, "returning because len(char) == 0"
            return
        
        ###
        ### internal commands: no output to generated script
        ###
        # FIXME: use a map
        if char == '\x01':
            self.ctrlA(event)
            return
        elif char == '\x04':
            self.ctrlD(event)
            return
        elif char == '\x11':
            self.ctrlQ(event)
            return 
        elif char == '\x13':
            self.ctrlS(event)
            return
        elif char == '\x14':
            self.ctrlT(event)
            return
        elif char == '\x15':
            self.ctrlU()
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

    
    def ctrlA(self, event):
        self.toggleMessageArea()
        pass

    def ctrlQ(self, event):
        self.window.quit()
        
    def ctrlS(self, event):
        pass
    
    def startGeneratingTestCondition(self):
        self.message('Generating test condition...', background=Color.GOLD)
        self.isGeneratingTestCondition = True

    def finishGeneratingTestCondition(self):
        self.isGeneratingTestCondition = False
        self.hideMessageArea()

    def ctrlT(self, event):
        if DEBUG:
            print >>sys.stderr, "ctrlT()"
        if self.isGeneratingTestCondition:
            self.finishGeneratingTestCondition(self)
        else:
            self.startGeneratingTestCondition()
    
    def ctrlU(self):
        if DEBUG:
            print >>sys.stderr, "ctrlU()"
        self.showMessageArea()
    
    def enableEvents(self):
        self.canvas.update_idletasks()
        self.canvas.bind("<Button-1>", self.button1Pressed)
        self.canvas.bind("<BackSpace>", self.keyPressed)
        #self.canvas.bind("<Control-Key-S>", self.ctrlS)
        self.canvas.bind("<Key>", self.keyPressed)
        self.areEventsDisabled = False

    def disableEvents(self):
        self.canvas.update_idletasks()
        self.areEventsDisabled = True
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<BackSpace>")
        #self.canvas.unbind("<Control-Key-S>")
        self.canvas.unbind("<Key>")
    
    @staticmethod
    def isClickableCheckableOrFocusable(v):
        try:
            return (v.isclickable() or v.ischeckable() or v.isfocusable())
        except AttributeError:
            return False
    
    def mainloop(self):
        self.window.mainloop()
