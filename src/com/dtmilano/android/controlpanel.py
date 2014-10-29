#! /usr/bin/env python

'''
    Copyright (C) 2014
    Created on Oct 28, 2014
    
    @author: AK
'''

__version__ = '0.1'

import Tkinter
import tkFont
import sys


class Operation:
    PRESS = 'press'


class ControlPanel(Tkinter.Frame):

    def __init__(self, master, culebron, vc, printOperation, **kwargs):
        Tkinter.Frame.__init__(self, master, kwargs)
        self.culebron = culebron
        self.printOperation = printOperation
        self.vc = vc
        self.grid()
        self.Column = 0
        self.Row = 0


        buttons = [
                   'KEYCODE_1', 'KEYCODE_6', 'KEYCODE_BACK', 'KEYCODE_DPAD_UP', 'KEYCODE_PAGE_UP',
                   'KEYCODE_2', 'KEYCODE_7', 'KEYCODE_SPACE', 'KEYCODE_DPAD_DOWN', 'KEYCODE_PAGE_DOWN',
                   'KEYCODE_3', 'KEYCODE_8', 'KEYCODE_ENTER', 'KEYCODE_DPAD_LEFT', 'KEYCODE_VOLUME_UP',
                   'KEYCODE_4', 'KEYCODE_9', 'KEYCODE_DEL', 'KEYCODE_DPAD_RIGHT', 'KEYCODE_VOLUME_DOWN',
                   'KEYCODE_5', 'KEYCODE_0', 'KEYCODE_SEARCH', 'KEYCODE_DPAD_CENTER', 'KEYCODE_VOLUME_MUTE',
                   'KEYCODE_TV',  'KEYCODE_POWER', 'KEYCODE_EXPLORER', 'KEYCODE_MENU', 'KEYCODE_CALENDAR',
                   'KEYCODE_CHANNEL_UP', 'KEYCODE_GUIDE', 'KEYCODE_ZOOM_IN', 'KEYCODE_APP_SWITCH', 'KEYCODE_CALCULATOR',
                   'KEYCODE_CHANNEL_DOWN', 'KEYCODE_SETTINGS', 'KEYCODE_ZOOM_OUT', 'KEYCODE_HOME', 'KEYCODE_CAMERA',
                   'KEYCODE_MUSIC', 'KEYCODE_BOOKMARK', 'KEYCODE_CALL', 'KEYCODE_BRIGHTNESS_UP', 'KEYCODE_BRIGHTNESS_DOWN',
                   'KEYCODE_FORWARD', 'KEYCODE_BUTTON_MODE', 'CUSTOM__SNAPSHOPT', 'CUSTOM__REFRESH', 'CUSTOM__QUIT'
                  ]


        for button in buttons:
            self.cpButton = CpButton(self, culebron, vc, printOperation, value=button, text=button[8:], width=14,
                                     bg="tan", fg="#000000", highlightbackground="tan")
                

            if button == 'CUSTOM__REFRESH':
                self.cpButton.configure(fg="red", command=self.cpButton.refreshScreen)
                self.cpButton.grid(column=self.Column, row=self.Row)
            elif button == 'CUSTOM__SNAPSHOPT':
                self.cpButton.configure(fg="red", command=self.cpButton.snapShot)
                self.cpButton.grid(column=self.Column, row=self.Row)
            elif button == 'CUSTOM__QUIT':
                self.cpButton.configure(fg="red", command=self.master.destroy)
                self.cpButton.grid(column=self.Column, row=self.Row)
            else:
                self.cpButton.configure(command=self.cpButton.pressKeyCode)
                self.cpButton.grid(column=self.Column, row=self.Row)

            self.Column += 1
            if self.Column > 4:
                self.Column = 0
                self.Row += 1


class CpButton(Tkinter.Button):

    def __init__(self, master, culebron, vc, printOperation, value=None, **kwargs):
        Tkinter.Button.__init__(self, master, kwargs)
        self.culebron = culebron
        self.printOperation = printOperation
        self.value = value
        self.vc = vc
        self.device = vc.device
    
    def pressKeyCode(self):
        keycode = self.value
        self.device.press(keycode)
        self.printOperation(None, Operation.PRESS, keycode)

    def refreshScreen(self):
        self.culebron.showVignette()
        self.culebron.takeScreenshotAndShowItOnWindow()
    
    def snapShot(self):
        self.device.takeSnapshot().save('Snapshot', 'PNG')
