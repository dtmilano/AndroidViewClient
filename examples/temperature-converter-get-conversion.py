#! /usr/bin/env python
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 3, 2012

This example starts the TemperatureConverter activity then type '123' into the 'Celsius' field.
Then a ViewClient is created to obtain the view dump and the current values of the views with
id/celsius and id/fahrenheit are obtained and the conversion printed to stdout.
Finally, the fields are obtained by using their tags and again, conversion printed to stdout.

If --localViewServer is passed in the command line then LocalViewServer provided by
TemperatureConverter is used. This is very useful when the device is secure and ViewServer
cannot be started.

@author: diego
'''


import re
import sys
import os
import time

# PyDev sets PYTHONPATH, use it
try:
    for p in os.environ['PYTHONPATH'].split(':'):
        if not p in sys.path:
            sys.path.append(p)
except:
    pass

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient

localViewServer = False
if len(sys.argv) > 1 and sys.argv[1] == '--localViewServer':
    localViewServer = True
    sys.argv.pop(1)

device, serialno = ViewClient.connectToDeviceOrExit(ignoresecuredevice=localViewServer)

FLAG_ACTIVITY_NEW_TASK = 0x10000000
package = 'com.example.i2at.tc'
activity = '.TemperatureConverterActivity'
componentName = package + "/" + activity

device.startActivity(component=componentName, flags=FLAG_ACTIVITY_NEW_TASK)
time.sleep(5)


device.type("123")
time.sleep(3)

vc = ViewClient(device, serialno, startviewserver=(not localViewServer))

if vc.build['ro.build.version.sdk'] >= 16:
    # obtain the views by contentDescription
    celsius = vc.findViewWithContentDescriptionOrRaise("celsius")
    fahrenheit = vc.findViewWithContentDescriptionOrRaise("fahrenheit")
else:
    # obtain the views by id
    celsius = vc.findViewByIdOrRaise("id/celsius")
    fahrenheit = vc.findViewByIdOrRaise("id/fahrenheit")

ct = celsius.getText()
if ct:
   c = float(ct)
else:
   print >> sys.stderr, "Celsius is empty"
   sys.exit(1)
ft = fahrenheit.getText()
if ft:
   f = float(ft)
else:
   print >> sys.stderr, "Fahrenheit is empty"
   sys.exit(1)
print "by id: %.2f C => %.2f F" % (c, f)

# obtain the views by tag
#celsius = vc.findViewByTagOrRaise("celsius")
#fahrenheit = vc.findViewByTagOrRaise("fahrenheit")
#
#c = float(celsius.getText())
#f = float(fahrenheit.getText())
#print "by tag: %.2f C => %.2f F" % (c, f)
