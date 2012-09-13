#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 3, 2012

@author: diego
'''


import re
import sys
import os

# This must be imported before MonkeyRunner and MonkeyDevice,
# otherwise the import fails.
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
from com.dtmilano.android.viewclient import ViewClient, View
from com.dtmilano.android.viewclient import TRAVERSE_CIT

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice


def getUniqueIdAndCoords(view):
    try:
        return "%s %s   %s" % (view.getUniqueId(), view.getCoords(), view.getText())
    except Exception, e:
        return "Exception in view=%s: %s" % (view.__smallStr__(), e)

def getClassAndId(view):
    try:
        return "%s %s" % (view.getClass(), view.getId())
    except Exception, e:
        return "Exception in view=%s: %s" % (view.__smallStr__(), e)

def getClassIdAndText(view):
    s = ""
    try:
        s = "%s %s" % (view.getClass(), view.getId())
    except Exception, e:
        return "Exception in view=%s: %s" % (view.__smallStr__(), e)

#    if view.getClass() == 'android.widget.TextView':
#        #print >>sys.stderr, view
#        print >>sys.stderr, "text=", view.getText()

    try:
        t = view.getText()
        if t:
            s += ( " '" + t + "' @@@" )
        else:
            s + " NONE"
    except:
        s += " NO TEXT"

    return s

def onlyButtonWithId(view):
    try:
        if view.getId() == 'id/button_with_id':
            return "%s %s" % (view.getUniqueId(), view.getCoords())
    except:
        return ""

serialno = sys.argv[1] if len(sys.argv) > 1 else 'emulator-5554'

device = MonkeyRunner.waitForConnection(60, serialno)
if not device:
    raise Exception('Cannot connect to device')

vc = ViewClient(device, serialno=serialno)
vc.traverse(root=vc.root, transform=TRAVERSE_CIT)
#print
#print
#print
#vc.traverse(vc.root, transform=getClassIdAndText)
#vc.traverse(vc.root, transform=getUniqueIdAndCoords)
#vc.traverse(vc.root, transform=onlyButtonWithId)

#display = vc.findViewWithText('Display')
#if display:
#    print display.__smallStr__()
#    display.touch()
#else:
#    print >>sys.stderr, "Not found"
#sys.exit(1)

#title = vc.findViewWithText('No Ids')
#if title:
    #print title.__smallStr__()
#sys.exit(1)


#button1 = vc.findViewWithText(re.compile('Button 1 .*'))
#if button1:
#    button1.touch()
#else:
#    print >>sys.stderr, "Not found"


#button2 = vc.findViewWithText(re.compile('Button 2 .*'))
#if button2:
#    button2.touch()
#else:
#    print >>sys.stderr, "Not found"


#buttonWithId = vc.findViewById('id/button_with_id')
#if buttonWithId:
#    #print buttonWithId.getCoords()
#    buttonWithId.touch()
#else:
#    print >>sys.stderr, "Not found"

#uniqueId = 'id/celsius'
#view = vc.findViewWithAttribute('uniqueId', uniqueId);
#print view.getCoords()
#view.touch()

#uniqueId = 'id/fahrenheit'
#view = vc.findViewWithAttribute('uniqueId', uniqueId);
#print view.getCoords()

#traffic = vc.findViewWithText('Traffic')
#if traffic:
#   traffic.touch()
#
#MonkeyRunner.sleep(5)

#ld = vc.findViewWithText('List dialog')
#if ld:
#   ld.touch()
#   MonkeyRunner.sleep(10)
#   # windows changed, request a new dump
#   vc.dump()
#   c3 = vc.findViewWithText('Command three')
#   if c3:
#      c3.touch()
#      MonkeyRunner.sleep(10)
#      device.press('KEYCODE_BACK', MonkeyDevice.DOWN_AND_UP)
#
#ok = vc.findViewWithText('OK')
#if ok:
#   ok.touch()
