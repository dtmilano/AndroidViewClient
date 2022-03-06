#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# - Start CulebraTester2-public server (https://github.com/dtmilano/CulebraTester2-public/wiki/Start-server)
# Then this script:
# - Finds an EditText
# - Enters text

from com.dtmilano.android.viewclient import ViewClient

vc = ViewClient(*ViewClient.connectToDeviceOrExit(), useuiautomatorhelper=True)

oid = vc.uiAutomatorHelper.ui_device.find_object(clazz='android.widget.EditText').oid
vc.uiAutomatorHelper.ui_object2.set_text(oid, '你好世界 😄')
