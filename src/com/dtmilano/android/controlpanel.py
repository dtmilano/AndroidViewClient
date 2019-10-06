# -*- coding: utf-8 -*-
'''
    Copyright (C) 2012-2019  Diego Torres Milano
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
    @author: Ahmed Kasem
    '''
import platform

__version__ = '15.8.0'

import Tkinter
import ttk
import subprocess

from com.dtmilano.android.culebron import Operation, Color


class Key:
    GOOGLE_NOW = 'KEYCODE_ASSIST'
    PERIOD = 'KEYCODE_PERIOD'
    GO = 'KEYCODE_ENTER'


class Layout:
    BUTTON_WIDTH = 13
    BUTTONS_NUMBER = 9


class ControlPanel(Tkinter.Toplevel):
    osName = platform.system()
    ''' The OS name. We sometimes need specific behavior. '''
    isDarwin = (osName == 'Darwin')
    ''' Is it Mac OSX? '''

    def __init__(self, culebron, printOperation, **kwargs):
        self.culebron = culebron
        self.printOperation = printOperation
        self.parent = culebron.window
        self.childWindow = Tkinter.Toplevel(self.parent)
        self.notebook = ttk.Notebook(self.childWindow)
        self.notebook.pack(fill=Tkinter.BOTH, padx=2, pady=3)
        self.keycodeTab = ttk.Frame(self.notebook)
        self.keyboardTab = ttk.Frame(self.notebook)
        self.notebook.add(self.keycodeTab, text='KEYCODE')
        self.notebook.add(self.keyboardTab, text='KEYBOARD')
        self.childWindow.title('Control Panel')
        self.childWindow.resizable(width=Tkinter.FALSE, height=Tkinter.FALSE)
        self.childWindow.printOperation = printOperation
        self.childWindow.grid()
        self.childWindow.column = 0
        self.childWindow.row = 0
        if self.isDarwin:
            out = subprocess.check_output(["defaults", "read", "-g", "AppleInterfaceStyle"])
            self.isDarkMode = ('Dark' in out)
        else:
            self.isDarkMode = False
        if self.isDarkMode:
            self.fg = Color.DARK_GRAY
            self.bg = Color.LIGHT_GRAY
            self.highlightbackground = Color.LIGHT_GRAY
        else:
            self.fg = Color.DARK_GRAY
            self.bg = Color.LIGHT_GRAY
            self.highlightbackground = Color.DARK_GRAY
        self.createKeycodeTab()
        self.createKeyboardTab()
        self.childWindow.update()
        if self.isDarwin:
            if platform.mac_ver()[0].startswith("10.14"):
                self.childWindow.after(0, self.fix)

    def fix(self):
        """
        Fix a problem with Tkinter Buttons in Mojave.
        See https://stackoverflow.com/questions/52529403/button-text-of-tkinter-not-works-in-mojave
        """
        a = self.childWindow.winfo_geometry().split('+')[0]
        b = a.split('x')
        w = int(b[0])
        h = int(b[1])
        self.childWindow.geometry('%dx%d' % (w + 1, h + 1))

    def createKeycodeTab(self):
        ''' KEYCODE '''
        _keycodeList = [
            'KEYCODE_HOME', 'KEYCODE_DPAD_UP', 'KEYCODE_BACK', 'KEYCODE_SEARCH', 'KEYCODE_CHANNEL_UP', 'KEYCODE_TV',
            'KEYCODE_MUSIC', 'KEYCODE_EXPLORER', 'KEYCODE_CAMERA', 'KEYCODE_POWER', 'KEYCODE_DPAD_LEFT',
            'KEYCODE_DPAD_DOWN',
            'KEYCODE_DPAD_RIGHT', 'KEYCODE_PAGE_UP', 'KEYCODE_CHANNEL_DOWN', 'KEYCODE_VOLUME_UP', 'KEYCODE_MEDIA_PLAY',
            'KEYCODE_CONTACTS', 'KEYCODE_ZOOM_IN', 'SNAPSHOPT', 'KEYCODE_MENU', 'KEYCODE_DPAD_CENTER', 'KEYCODE_ENTER',
            'KEYCODE_PAGE_DOWN', 'KEYCODE_BRIGHTNESS_DOWN', 'KEYCODE_VOLUME_DOWN', 'KEYCODE_MEDIA_PAUSE',
            'KEYCODE_BOOKMARK',
            'KEYCODE_ZOOM_OUT', 'REFRESH', 'KEYCODE_APP_SWITCH', 'KEYCODE_GOOGLE_NOW', 'KEYCODE_CALL', 'KEYCODE_ESCAPE',
            'KEYCODE_BRIGHTNESS_UP', 'KEYCODE_VOLUME_MUTE', 'KEYCODE_MEDIA_STOP', 'KEYCODE_CALCULATOR',
            'KEYCODE_SETTINGS', 'QUIT'
        ]
        for keycode in _keycodeList:
            _cpb = ControlPanelButton(self.keycodeTab, self.culebron, self.printOperation, value=keycode,
                                      text=keycode[8:],
                                      width=Layout.BUTTON_WIDTH,
                                      bg=self.bg, fg=self.fg,
                                      highlightbackground=self.highlightbackground)

            if keycode == 'REFRESH':
                _cpb.configure(fg=Color.BLUE, bg=Color.DARK_GRAY, text=keycode, command=_cpb.refreshScreen)
            elif keycode == 'SNAPSHOPT':
                _cpb.configure(fg=Color.BLUE, bg=Color.DARK_GRAY, text=keycode, command=_cpb.takeSnapshot)
            elif keycode == 'QUIT':
                _cpb.configure(fg=Color.BLUE, bg=Color.DARK_GRAY, text=keycode, command=self.childWindow.destroy)
            else:
                _cpb.configure(command=_cpb.command)
            _cpb.grid(column=self.childWindow.column, row=self.childWindow.row)
            self.tabLayout()

    def createKeyboardTab(self):
        ''' KEYBOARD '''
        _keyboardList = [
            'KEYCODE_1', 'KEYCODE_2', 'KEYCODE_3', 'KEYCODE_4', 'KEYCODE_5', 'KEYCODE_6', 'KEYCODE_7', 'KEYCODE_8',
            'KEYCODE_9', 'KEYCODE_0',
            'KEYCODE_Q', 'KEYCODE_W', 'KEYCODE_E', 'KEYCODE_R', 'KEYCODE_T', 'KEYCODE_Y', 'KEYCODE_U', 'KEYCODE_I',
            'KEYCODE_O', 'KEYCODE_P',
            'KEYCODE_A', 'KEYCODE_S', 'KEYCODE_D', 'KEYCODE_F', 'KEYCODE_G', 'KEYCODE_H', 'KEYCODE_J', 'KEYCODE_K',
            'KEYCODE_L',
            'KEYCODE_DEL', 'KEYCODE_Z', 'KEYCODE_X', 'KEYCODE_C', 'KEYCODE_V', 'KEYCODE_B', 'KEYCODE_N', 'KEYCODE_M',
            'KEYCODE_.', 'KEYCODE_SPACE', 'KEYCODE_GO'
        ]

        for keyboard in _keyboardList:
            _cpb = ControlPanelButton(self.keyboardTab, self.culebron, self.printOperation, value=keyboard,
                                      text=keyboard[8:],
                                      width=Layout.BUTTON_WIDTH, bg=self.bg, fg=self.fg,
                                      highlightbackground=self.highlightbackground)

            _cpb.configure(command=_cpb.command)
            _cpb.grid(column=self.childWindow.column, row=self.childWindow.row)
            self.tabLayout()

    def tabLayout(self):
        ''' For all tabs, specify the number of buttons in a row '''
        self.childWindow.column += 1
        if self.childWindow.column > Layout.BUTTONS_NUMBER:
            self.childWindow.column = 0
            self.childWindow.row += 1


class ControlPanelButton(Tkinter.Button):

    def __init__(self, parent, culebron, printOperation, value=None, **kwargs):
        Tkinter.Button.__init__(self, parent, kwargs)
        self.culebron = culebron
        self.printOperation = printOperation
        self.value = value
        self.device = culebron.device

    def command(self):
        key = self.value
        if key == 'KEYCODE_GOOGLE_NOW':
            self.device.press(Key.GOOGLE_NOW)
            self.printOperation(None, Operation.PRESS, Key.GOOGLE_NOW)
        elif key == 'KEYCODE_.':
            self.device.press(Key.PERIOD)
            self.printOperation(None, Operation.PRESS, Key.PERIOD)
        elif key == 'KEYCODE_GO':
            self.device.press(Key.GO)
            self.printOperation(None, Operation.PRESS, Key.GO)
        else:
            self.device.press(key)
            self.printOperation(None, Operation.PRESS, key)

    def refreshScreen(self):
        self.culebron.refresh()

    def takeSnapshot(self):
        # No need to retake snapshot as it is already shown
        self.culebron.saveSnapshot()
