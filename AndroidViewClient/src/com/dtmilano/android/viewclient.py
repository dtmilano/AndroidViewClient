'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 2, 2012

@author: diego
'''

import sys
import subprocess
import re
import socket
import os

DEBUG = False

ANDROID_HOME = os.environ['ANDROID_HOME'] if os.environ.has_key('ANDROID_HOME') else '/opt/android-sdk'
VIEW_SERVER_HOST = 'localhost'
VIEW_SERVER_PORT = 4939

STATUS_BAR = 38
TITLE = 40
CHECK_BOX = 50 # FIXME: this is not just for CheckBox

class View:
    '''
    View class
    '''
    
    def __init__(self, map, device):
        '''
        Constructor
        '''
        
        self.map = map
        self.device = device
        
    def __getitem__(self, key):
        return self.map[key]
        
    def __getattr__(self, name):
        if DEBUG:
            print >>sys.stderr, "__getattr__(%s)" % (name)
        
        # I should try to see if 'name' is a defined method
        # but it seems that if I call locals() here an infinite loop is entered
        
        if self.map.has_key(name):
            r = self.map[name]
        elif self.map.has_key(name + '()'):
            # the method names are stored in the map with their trailing '()'
            r = self.map[name + '()']
        elif name.count("_") > 0:
            mangledList = self.allPossibleNamesWithColon(name)
            mangledName = self.intersection(mangledList, self.map.keys())
            if len(mangledName) > 0:
                r = self.map[mangledName[0]]
            else:
                # Default behavior
                raise AttributeError, name
        else:
            # Default behavior
            raise AttributeError, name
        
        # if the method name starts with 'is' let's assume its return value is boolean
        if name[:2] == 'is':
            r = True if r == 'true' else False
        
        # this should not cached in some way
        def innerMethod():
            if DEBUG:
                print >>sys.stderr, "innerMethod: %s returning %s" % (innerMethod.__name__, r)
            return r
        
        innerMethod.__name__ = name
        
        # this should work, but then there's problems with the arguments of innerMethod 
        # even if innerMethod(self) is added
        #setattr(View, innerMethod.__name__, innerMethod)
        #setattr(self, innerMethod.__name__, innerMethod)
        
        return innerMethod
    
    def __call__(self, *args, **kwargs):
        if DEBUG:
            print "__call__(%s)" % (args if args else None)
            
    def getXY(self):
        '''
        Returns the coordinates of this View
        '''
        
        # FIXME: it's not always a CheckBox
        x = int(self.map['layout:mLeft']) + int(self.map['layout:layout_leftMargin']) + CHECK_BOX/2
        y = int(self.map['layout:mTop']) + int(self.map['layout:layout_topMargin']) + STATUS_BAR + TITLE + CHECK_BOX/2
        return (x, y)

    # FIXME: should be MonkeyDevice.DOWN_AND_UP
    def touch(self, type="DOWN_AND_UP"):
        '''
        Touches this View
        '''
        
        (x, y) = self.getXY()
        if DEBUG:
            print >>sys.stderr, "should click @ (%d, %d)" % (x, y)
        self.device.touch(x, y, type)
        
    def allPossibleNamesWithColon(self, name):
        l = []
        for i in range(name.count("_")):
            name = name.replace("_", ":", 1)
            l.append(name)
        return l

    def intersection(self, l1, l2):
        return list(set(l1) & set(l2))
    
    def __str__(self):
        str = "View[ "
        for a in self.map:
            str += a + "=" + self.map[a] + " "
        str += "]"
        return str

 
class ViewClient:
    '''
    ViewClient is a ViewServer client.
    
    If not running the ViewServer is started on the target device or emulator and then the port
    mapping is created.
    '''

    def __init__(self, device, adb=os.path.join(ANDROID_HOME, 'platform-tools', 'adb')):
        '''
        Constructor
        '''
        
        if not device:
            raise Exception('Device is not connected')
        if not os.access(adb, os.X_OK):
            raise Exception('adb="%s" is not executable' % adb)
        if not self.serviceResponse(device.shell('service call window 3')):
            try:
                self.assertServiceResponse(device.shell('service call window 1 i32 %d' %
                                                        VIEW_SERVER_PORT))
            except:
                raise Exception('Cannot start View server.\n'
                                'This only works on emulator and devices running developer versions.\n'
                                'Does hierarchyviewer work on your device ?')

        subprocess.check_call([adb, 'forward', 'tcp:%d' % VIEW_SERVER_PORT,
                               'tcp:%d' % VIEW_SERVER_PORT])

        self.device = device
        self.viewsById = {}
    
    def assertServiceResponse(self, response):
        if not self.serviceResponse(response):
            raise Exception('Invalid response received from service.')

    def serviceResponse(self, response):
        PARCEL_TRUE = "Result: Parcel(00000000 00000001   '........')\r\n"
        if DEBUG:
            print >>sys.stderr, "serviceResponse: comparing '%s' vs Parcel(%s)" % (response, PARCEL_TRUE)
        return response == PARCEL_TRUE

    def dump(self, windowId=-1):
        '''
        Dumps the window content
        '''
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((VIEW_SERVER_HOST, VIEW_SERVER_PORT))
        s.send('dump %d\r\n' % windowId)
        received = ""
        doneRE = re.compile("DONE")
        while True:
            received += s.recv(1024)
            if doneRE.search(received[-7:]):
                break

        s.close()
        self.views = received.split("\n")
        if DEBUG:
            print "there are %d views in this dump" % len(self.views)

        idRE = re.compile("(?P<viewId>id/\S+)")
        attrRE = re.compile("(?P<attr>\S+)(\(\))?=\d+,(?P<val>\S+)")
        hashRE = re.compile("(?P<class>\S+)@(?P<oid>[0-9a-f]+)")

        for v in self.views:
            attrs = {}
            m = idRE.search(v)
            if m:
                viewId = m.group('viewId')
                if DEBUG:
                    print "found %s" % viewId
                for attr in v.split():
                    m = attrRE.match(attr)
                    if m:
                        attrs[m.group('attr')] = m.group('val')                    
                    else:
                        m = hashRE.match(attr)
                        if m:
                            attrs['class'] = m.group('class')
                            attrs['oid'] = m.group('oid')
                        else:
                            if DEBUG:
                                print attr, "doesn't match"

                    
                if viewId in self.viewsById:
                    # sometimes the view ids are not unique, so let's generate a unique id here
                    i = 1
                    while True:
                        newId = viewId + '/%d' % i
                        if not newId in self.viewsById:
                            break
                        i += 1
                    viewId = newId
                if DEBUG:
                    print "adding viewById %s" % viewId
                self.viewsById[viewId] = attrs

        return self.views

    def findViewById(self, viewId):
        '''
        Finds the View with the specified viewId.
        '''
        return View(self.viewsById[viewId], self.device)

    def getViewIds(self):
        '''
        Returns the Views map.
        '''
        return self.viewsById


if __name__ == "__main__":
    try:
        vc = ViewClient(None)
    except:
        print "Don't expect this to do anything"

        