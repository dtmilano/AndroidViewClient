#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2013-2022  Diego Torres Milano
Created on 2022-05-24 by Culebra v21.4.2
                      __    __    __    __
                     /  \  /  \  /  \  /  \ 
____________________/  __\/  __\/  __\/  __\_____________________________
___________________/  /__/  /__/  /__/  /________________________________
                   | / \   / \   / \   / \   \___
                   |/   \_/   \_/   \_/   \    o \ 
                                           \_____/--<
@author: Diego Torres Milano
@author: Jennifer E. Swofford (ascii art snake)
"""

from com.dtmilano.android.viewclient import ViewClient

device, serialno = ViewClient.connectToDeviceOrExit()

kwargs2 = {'useuiautomatorhelper': True}
vc = ViewClient(device, serialno, **kwargs2)

vc.uiAutomatorHelper.target_context.start_activity('com.android.chrome', 'com.google.android.apps.chrome.Main',
                                                   uri='https://google.com')
