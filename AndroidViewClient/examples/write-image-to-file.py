#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2013  Diego Torres Milano
Created on 2014-03-10 by Culebra v4.10.1

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


import re
import sys
import os


from com.dtmilano.android.viewclient import ViewClient

if len(sys.argv) < 2:
    sys.exit("usage: %s /path/to/filename.png [serialno]" % sys.argv[0])

filename = sys.argv.pop(1)
kwargs1 = {'verbose': False, 'ignoresecuredevice': False}
device, serialno = ViewClient.connectToDeviceOrExit(**kwargs1)
kwargs2 = {'startviewserver': True, 'forceviewserveruse': False, 'autodump': False, 'ignoreuiautomatorkilled': True}
vc = ViewClient(device, serialno, **kwargs2)
vc.dump(window='-1')

vc.findViewWithContentDescriptionOrRaise('''Home screen 3''').writeImageToFile(filename, 'PNG')
