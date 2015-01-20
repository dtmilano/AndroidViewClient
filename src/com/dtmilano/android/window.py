# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2015  Diego Torres Milano
Created on Jan 5, 2015

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

import sys

DEBUG = False

class Window(object):
    '''
    Window class
    '''

    def __init__(self, num, winId, activity, wvx, wvy, wvw, wvh, px, py, visibility, focused=False):
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

        if DEBUG: print >> sys.stderr, "Window(%d, %s, %s, %d, %d, %d, %d, %d, %d, %d)" % \
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
        self.focused = focused

    def __str__(self):
        return "Window(%d, wid=%s, a=%s, x=%d, y=%d, w=%d, h=%d, px=%d, py=%d, v=%d, f=%s)" % \
                (self.num, self.winId, self.activity, self.wvx, self.wvy, self.wvw, self.wvh, self.px, self.py, self.visibility, self.focused)

