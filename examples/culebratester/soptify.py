#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2013-2018  Diego Torres Milano
Created on 2018-01-30 by CulebraTester 
                      __    __    __    __
                     /  \  /  \  /  \  /  \ 
____________________/  __\/  __\/  __\/  __\_____________________________
___________________/  /__/  /__/  /__/  /________________________________
                   | / \   / \   / \   / \   \___
                   |/   \_/   \_/   \_/   \    o \ 
                                           \_____/--<
@author: Diego Torres Milano
@author: Jennifer E. Swofford (ascii art snake)
'''

#
# This example was created as a response to https://github.com/dtmilano/AndroidViewClient/issues/238
# It was automatically created by CulebraTester (http://culebra.dtmilano.com/) just interacting
#  with the device under test and playing on Spotify and selecting "Connect to a device".
#

import os
import sys

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

import pkg_resources
pkg_resources.require('androidviewclient>=12.4.0')
from com.dtmilano.android.viewclient import CulebraTestCase
from com.dtmilano.android.uiautomator.uiautomatorhelper import UiScrollable

TAG = 'CULEBRA'


class CulebraTests(CulebraTestCase):

    @classmethod
    def setUpClass(cls):
        cls.kwargs1 = {'ignoreversioncheck': False, 'verbose': False, 'ignoresecuredevice': False}
        cls.kwargs2 = {'forceviewserveruse': False, 'useuiautomatorhelper': True, 'ignoreuiautomatorkilled': True, 'autodump': False, 'startviewserver': True, 'compresseddump': True}
        cls.options = {'start-activity': None, 'concertina': False, 'device-art': None, 'use-jar': False, 'multi-device': False, 'unit-test-class': True, 'save-screenshot': None, 'use-dictionary': False, 'glare': False, 'dictionary-keys-from': 'id', 'scale': 1, 'find-views-with-content-description': True, 'window': -1, 'orientation-locked': None, 'save-view-screenshots': None, 'find-views-by-id': True, 'log-actions': False, 'use-regexps': False, 'null-back-end': False, 'auto-regexps': None, 'do-not-verify-screen-dump': True, 'verbose-comments': False, 'gui': False, 'find-views-with-text': True, 'prepend-to-sys-path': False, 'install-apk': None, 'drop-shadow': False, 'output': None, 'unit-test-method': None, 'interactive': False}
        cls.sleep = 5

    def setUp(self):
        super(CulebraTests, self).setUp()

    def tearDown(self):
        super(CulebraTests, self).tearDown()

    def preconditions(self):
        if not super(CulebraTests, self).preconditions():
            return False
        return True

    def testSomething(self):
        if not self.preconditions():
            self.fail('Preconditions failed')

        _s = CulebraTests.sleep
        _v = CulebraTests.verbose

        UiScrollable(self.vc.uiAutomatorHelper, uiSelector='clazz@com.android.launcher3.Workspace,res@com.google.android.apps.nexuslauncher:id/workspace,index@0,parentIndex@0,package@com.google.android.apps.nexuslauncher').getChildByDescription(uiSelector='desc@Spotify', description="Spotify", allowScrollSearch=True).click()
        self.vc.uiAutomatorHelper.findObject(bySelector='res@com.spotify.music:id/home_tab,desc@Home,clazz@android.widget.TextView,text@Home,package@com.spotify.music').clickAndWait(eventCondition='until:newWindow', timeout=_s*1000)
        self.vc.uiAutomatorHelper.findObject(bySelector='res@com.spotify.music:id/playPause,desc@Play,clazz@android.widget.ImageButton,text@$,package@com.spotify.music').clickAndWait(eventCondition='until:newWindow', timeout=_s*1000)
        self.vc.uiAutomatorHelper.findObject(bySelector='res@com.spotify.music:id/player_navigation_unit_container,desc@Show Now Playing,clazz@android.widget.FrameLayout,text@$,package@com.spotify.music').clickAndWait(eventCondition='until:newWindow', timeout=_s*1000)
        self.vc.uiAutomatorHelper.findObject(bySelector='res@com.spotify.music:id/btn_play,desc@Pause,clazz@android.widget.ImageButton,text@$,package@com.spotify.music').clickAndWait(eventCondition='until:newWindow', timeout=_s*1000)
        self.vc.uiAutomatorHelper.findObject(bySelector='res@com.spotify.music:id/btn_play,desc@Play,clazz@android.widget.ImageButton,text@$,package@com.spotify.music').clickAndWait(eventCondition='until:newWindow', timeout=_s*1000)
        self.vc.uiAutomatorHelper.findObject(bySelector='res@com.spotify.music:id/btn_play,desc@Pause,clazz@android.widget.ImageButton,text@$,package@com.spotify.music').clickAndWait(eventCondition='until:newWindow', timeout=_s*1000)
        self.vc.uiAutomatorHelper.findObject(bySelector='res@com.spotify.music:id/connect_view_root,clazz@android.widget.LinearLayout,text@$,package@com.spotify.music').clickAndWait(eventCondition='until:newWindow', timeout=_s*1000)

if __name__ == '__main__':
    CulebraTests.main()
