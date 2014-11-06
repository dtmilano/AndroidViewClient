# -*- coding: utf-8 -*-
'''
    Copyright (C) 2012-2014  Diego Torres Milano
    Created on oct 30, 2014
    
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
    @author: AK
    '''

__version__ = '8.13.1'

import Tkinter
import sys

from com.dtmilano.android.culebron import Operation, Unit, Color


class ControlPanel(Tkinter.Toplevel):

    def __init__(self, culebron, vc, printOperation, **kwargs):
        self.culebron = culebron
        self.parent = culebron.window
        Tkinter.Toplevel.__init__(self, self.parent)
        self.title("Control Panel")
        self.resizable(0, 0)
        self.printOperation = printOperation
        self.vc = vc
        self.grid()
        self.column = 0
        self.row = 0

        
        buttons_list = [
                   'KEYCODE_1', 'KEYCODE_6', 'KEYCODE_BACK', 'KEYCODE_DPAD_UP', 'KEYCODE_PAGE_UP',
                   'KEYCODE_2', 'KEYCODE_7', 'KEYCODE_SPACE', 'KEYCODE_DPAD_DOWN', 'KEYCODE_PAGE_DOWN',
                   'KEYCODE_3', 'KEYCODE_8', 'KEYCODE_ENTER', 'KEYCODE_DPAD_LEFT', 'KEYCODE_VOLUME_UP',
                   'KEYCODE_4', 'KEYCODE_9', 'KEYCODE_DEL', 'KEYCODE_DPAD_RIGHT', 'KEYCODE_VOLUME_DOWN',
                   'KEYCODE_5', 'KEYCODE_0', 'KEYCODE_SEARCH', 'KEYCODE_DPAD_CENTER', 'KEYCODE_VOLUME_MUTE',
                   'KEYCODE_TV',  'KEYCODE_POWER', 'KEYCODE_EXPLORER', 'KEYCODE_MENU', 'KEYCODE_CALENDAR',
                   'KEYCODE_CHANNEL_UP', 'KEYCODE_GUIDE', 'KEYCODE_ZOOM_IN', 'KEYCODE_APP_SWITCH', 'KEYCODE_CALCULATOR',
                   'KEYCODE_CHANNEL_DOWN', 'KEYCODE_SETTINGS', 'KEYCODE_ZOOM_OUT', 'KEYCODE_HOME', 'KEYCODE_CAMERA',
                   'KEYCODE_MUSIC', 'KEYCODE_BOOKMARK', 'KEYCODE_CALL', 'KEYCODE_BRIGHTNESS_UP', 'KEYCODE_BRIGHTNESS_DOWN',
                   'KEYCODE_FORWARD', 'KEYCODE_BUTTON_MODE', 'SNAPSHOPT', 'REFRESH', 'QUIT'
                  ]


        for button in buttons_list:
            self.button = ControlPanelButton(self, culebron, vc, printOperation, value=button, text=button, width=25,
                                     bg=Color.DARK_GRAY, fg=Color.LIGHT_GRAY, highlightbackground=Color.DARK_GRAY)

            if button == 'REFRESH':
                self.button.configure(fg=Color.BLUE, bg=Color.DARK_GRAY, command=self.button.refreshScreen)
                self.button.grid(column=self.column, row=self.row)
            elif button == 'SNAPSHOPT':
                self.button.configure(fg=Color.BLUE, bg=Color.DARK_GRAY, command=self.button.takeSnapshoot)
                self.button.grid(column=self.column, row=self.row)
            elif button == 'QUIT':
                self.button.configure(fg=Color.BLUE, bg=Color.DARK_GRAY, command=self.destroy)
                self.button.grid(column=self.column, row=self.row)
            else:
                self.button.configure(command=self.button.pressKeyCode)
                self.button.grid(column=self.column, row=self.row)

            self.column += 1
            if self.column > 4:
                self.column = 0
                self.row += 1


class ControlPanelButton(Tkinter.Button):

    def __init__(self, parent, culebron, vc, printOperation, value=None, **kwargs):
        Tkinter.Button.__init__(self, parent, kwargs)
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

    def takeSnapshoot(self):
        self.device.takeSnapshot().save('Snapshot', 'PNG')
