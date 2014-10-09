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

__version__ = '8.0.4'

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

DEBUG = True
DEBUG_MOVE = DEBUG and False
DEBUG_TOUCH = DEBUG and False
DEBUG_POINT = DEBUG and True
DEBUG_KEY = DEBUG and True

class Culebron:
    canvas = None
    imageId = None
    vignetteId = None
    areTargetsMarked = False
    isGrabbing = False
    
    @staticmethod
    def checkDependencies():
        if not PIL_AVAILABLE:
            raise Exception("PIL is needed for GUI mode")
        if not TKINTER_AVAILABLE:
            raise Exception("Tkinter is needed for GUI mode")

    def __init__(self, vc):
        self.vc = vc
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
            self.createVignette(width, height)
        if DEBUG:
            print >> sys.stderr, "    canvas=", self.canvas
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
        
    def createVignette(self, width, height):
        pass
    
    def showVignette(self):
        pass
    
    def hideVignette(self):
        pass
    
    def findTargets(self):
        pass
    
    def getViewContainingPointAndTouch(self, x, y):
        if DEBUG:
            print >> sys.stderr, 'getViewContainingPointAndTouch(%d, %d)' % (x, y)
        pass
    
    def button1Pressed(self, event):
        self.getViewContainingPointAndTouch(event.x, event.y)
        
    def keyPressed(self):
        pass
    
    def ctrlS(self):
        pass
    
    def enableEvents(self):
        self.canvas.update_idletasks()
        self.canvas.bind("<Button-1>", self.button1Pressed)
        self.canvas.bind("<BackSpace>", self.keyPressed)
        self.canvas.bind("<Control-Key-S>", self.ctrlS)
        self.canvas.bind("<Key>", self.keyPressed)
        self.areEventsDisabled = False

    def disableEvents(self):
        self.canvas.update_idletasks()
        self.areEventsDisabled = True
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<BackSpace>")
        self.canvas.unbind("<Key>")

    def mainloop(self):
        self.window.mainloop()
