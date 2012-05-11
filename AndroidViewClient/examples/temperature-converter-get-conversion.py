#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 3, 2012

This example starts the TemperatureConverter activity then type '123' into the 'Celsius' field.
Then a ViewClient is created to obtain the view dump and the current values of the views with
id/celsius and id/fahrenheith are obtained and the conversion printed to stdout.
  
@author: diego
'''


import re
import sys
import os

# this must be imported before MonkeyRunner and MonkeyDevice,
# otherwise the import fails
try:
    ANDROID_VIEW_CLIENT_HOME = os.environ['ANDROID_VIEW_CLIENT_HOME']
except KeyError:
    print >>sys.stderr, "%s: ERROR: ANDROID_VIEW_CLIENT_HOME not set in environment" % __file__
    sys.exit(1)
sys.path.append(ANDROID_VIEW_CLIENT_HOME + '/src')
from com.dtmilano.android.viewclient import ViewClient

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice


package = 'com.example.i2at.tc'                                          
activity = '.TemperatureConverterActivity'                           
componentName = package + "/" + activity                        
device = MonkeyRunner.waitForConnection(60, "emulator-5554")
if not device:
	raise Exception('Cannot connect to device')

device.startActivity(component=componentName)
MonkeyRunner.sleep(5)

device.type("123")

vc = ViewClient(device)
vc.dump()

# obtain the views by id
celsius = vc.findViewById("id/celsius")
fahrenheit = vc.findViewById("id/fahrenheit")
    

# in android-15 this is text:mText while in previous versions it was just mText
try:
    c = float(celsius.text_mText())
    f = float(fahrenheit.text_mText())

    print "%.2f C => %.2f F" % (c, f)
except:
    try:
        c = float(celsius.mText())
        f = float(fahrenheit.mText())

        print "%.2f C => %.2f F" % (c, f)
    except:
        print "Unexpected error:", sys.exc_info()[0]

# obtain the views by tag
celsius = vc.findViewByTag("celsius")
fahrenheit = vc.findViewByTag("fahrenheit")

# in android-15 this is text:mText while in previous versions it was just mText
try:
    c = float(celsius.text_mText())
    f = float(fahrenheit.text_mText())

    print "%.2f C => %.2f F" % (c, f)
except:
    try:
        c = float(celsius.mText())
        f = float(fahrenheit.mText())

        print "%.2f C => %.2f F" % (c, f)
    except:
        print "Unexpected error:", sys.exc_info()[0]
