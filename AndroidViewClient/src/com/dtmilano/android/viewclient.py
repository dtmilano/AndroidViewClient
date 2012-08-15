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
import java
from com.android.monkeyrunner import MonkeyDevice

DEBUG = False
DEBUG_RECEIVED = DEBUG and True
DEBUG_TREE = DEBUG and True
DEBUG_GETATTR = DEBUG and False

ANDROID_HOME = os.environ['ANDROID_HOME'] if os.environ.has_key('ANDROID_HOME') else '/opt/android-sdk'
VIEW_SERVER_HOST = 'localhost'
VIEW_SERVER_PORT = 4939

# this is probably the only reliable way of determining the OS in monkeyrunner
os_name = java.lang.System.getProperty('os.name')
if os_name.startswith('Windows'):
    ADB = 'adb.exe'
else:
    ADB = 'adb'

OFFSET = 50

class View:
    '''
    View class
    '''

    GET_VISIBILITY_PROPERTY = 'getVisibility()'
    LAYOUT_TOP_MARGIN_PROPERTY = 'layout:layout_topMargin'

    def __init__(self, map, device):
        '''
        Constructor
        '''
        
        self.map = map
        self.device = device
        self.children = []
        self.parent = None
        
    def __getitem__(self, key):
        return self.map[key]
        
    def __getattr__(self, name):
        if DEBUG_GETATTR:
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
            print >>sys.stderr, "__call__(%s)" % (args if args else None)
            
    def getX(self):
        x = 0
        if self.GET_VISIBILITY_PROPERTY in self.map and self.map[self.GET_VISIBILITY_PROPERTY] == 'VISIBLE':
            x += int(self.map['layout:mLeft'])
        #x += OFFSET/2
        return x
    
    def getY(self):
        y = 0
        if self.GET_VISIBILITY_PROPERTY in self.map and self.map[self.GET_VISIBILITY_PROPERTY] == 'VISIBLE':
            y += int(self.map['layout:mTop'])

        #if self.LAYOUT_TOP_MARGIN_PROPERTY in self.map:
        #    if DEBUG:
        #        print >>sys.stderr, "   adding top margin=%d" % int(self.map[self.LAYOUT_TOP_MARGIN_PROPERTY])
        #    y += int(self.map[self.LAYOUT_TOP_MARGIN_PROPERTY])
        return y
    
    def getXY(self):
        '''
        Returns the coordinates of this View
        '''
        
        # FIXME: this usually doesn't return the real coordinates of the View but the coordinates
        #        relative to its parent, so to obtain the real coordinates the View root should
        #        have to be traversed to the root adding the coordinates for every child
        x = self.getX()
        y = self.getY()
        parent = self.parent
        hy = 0
        while parent != None:
            if parent.map['class'] in [ 'com.android.internal.widget.ActionBarView', 
                                       'com.android.internal.widget.ActionBarContainer',
                                       'com.android.internal.widget.ActionBarContextView',
                                       'com.android.internal.view.menu.ActionMenuView' ]:
                parent = parent.parent
                continue
            if DEBUG: print >>sys.stderr, "$$$ parent=%s y=%d py=%d hy=%d" % (parent.__smallStr__(), y, parent.getY(), hy)
            hy += parent.getY()
            parent = parent.parent
            if parent and parent['mID'] == 'id/action_bar_title':
                break
        return (x, y+hy)

    def getCoords(self):
        '''
        Gets the coords of the View
        '''
        (x, y) = self.getXY();
        w = int(self.map['layout:getWidth()'])
        h = int(self.map['layout:getHeight()'])
        return ((x, y), (x+w, y+h))

    def touch(self, type=MonkeyDevice.DOWN_AND_UP):
        '''
        Touches this View
        '''
        
        (x, y) = self.getXY()
        if DEBUG:
            print >>sys.stderr, "should touch @ (%d, %d)" % (x+OFFSET/2, y+OFFSET/2)
        self.device.touch(x+OFFSET/2, y+OFFSET/2, type)
        
    def allPossibleNamesWithColon(self, name):
        l = []
        for i in range(name.count("_")):
            name = name.replace("_", ":", 1)
            l.append(name)
        return l

    def intersection(self, l1, l2):
        return list(set(l1) & set(l2))
    
    def add(self, child):
        child.parent = self
        self.children.append(child)
        
    def __smallStr__(self):
        str = "View["
        if "class" in self.map:
            str += " class=" + self.map['class']
        str += " id=" + self.map['mID']
        str += " ]   parent="
        if self.parent and "class" in self.parent.map:
            str += "%s" % self.parent.map["class"]
        else:
            str += "None"
        return str
            
    def __str__(self):
        str = "View["
        if "class" in self.map:
            str += " class=" + self.map["class"] + " "
        for a in self.map:
            str += a + "=" + self.map[a] + " "
        str += "]   parent="
        if self.parent and "class" in self.parent.map:
            str += "%s" % self.parent.map["class"]
        else:
            str += "None"

        return str

 
class ViewClient:
    '''
    ViewClient is a ViewServer client.
    
    If not running the ViewServer is started on the target device or emulator and then the port
    mapping is created.
    '''

    def __init__(self, device, adb=os.path.join(ANDROID_HOME, 'platform-tools', ADB)):
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

        # FIXME: if there are more than one device this command will fail
        # -s <serialno> should be included in next command but it seems there's
        # no way of obtaining the serialno from the MonkeyDevice
        subprocess.check_call([adb, 'forward', 'tcp:%d' % VIEW_SERVER_PORT,
                               'tcp:%d' % VIEW_SERVER_PORT])

        self.device = device
        self.root = None
        self.viewsById = {}
    
    def assertServiceResponse(self, response):
        if not self.serviceResponse(response):
            raise Exception('Invalid response received from service.')

    def serviceResponse(self, response):
        PARCEL_TRUE = "Result: Parcel(00000000 00000001   '........')\r\n"
        if DEBUG:
            print >>sys.stderr, "serviceResponse: comparing '%s' vs Parcel(%s)" % (response, PARCEL_TRUE)
        return response == PARCEL_TRUE

    def setViews(self, received):
        self.views = received.split("\n")
        if DEBUG:
            print >>sys.stderr, "there are %d views in this dump" % len(self.views)

    def __splitAttrs(self, str, addViewToViewsById=False):
        '''
        Splits the view attributes in str and optionally adds the view id to the viewsById list.
        Returns the attributes map.
        '''
        
        idRE = re.compile("(?P<viewId>id/\S+)")
        # FIXME: this split is incorrect if for example a text:mText contains spaces
        # maybe something like this should be used and the count the chars specified
        # and cut it
        #textRE = re.compile("(?P<attr>\S+)(\(\))?=\d+,(?P<text>.+)")
        attrRE = re.compile("(?P<attr>\S+)(\(\))?=\d+,(?P<val>\S+)")
        hashRE = re.compile("(?P<class>\S+)@(?P<oid>[0-9a-f]+)")
        
        attrs = {}
        viewId = None
        m = idRE.search(str)
        if m:
            viewId = m.group('viewId')
            if DEBUG:
                print >>sys.stderr, "found %s" % viewId

        # FIXME: this split is incorrect if for example a text:mText contains spaces
        for attr in str.split():
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
                        print >>sys.stderr, attr, "doesn't match"
        
        if addViewToViewsById:
            if not viewId:
                # If the view has NO_ID we are assigning a default id here (id/no_id) which is
                # immediatelly incremented if another view with no id was found before to generate
                # a unique id
                viewId = "id/no_id"
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
                    print >>sys.stderr, "adding viewById %s" % viewId
            # We are assigning a new attribute to keep the original id preserved, which could have
            # been NO_ID repeated multiple times
            attrs['uniqueId'] = viewId
            self.viewsById[viewId] = attrs
                          
        return attrs
    
    def parseTree(self, str):
        self.root = None
        parent = None
        treeLevel = 0
        lastView = None
        for v in self.views:
            if v == 'DONE':
                break
            attrs = self.__splitAttrs(v, addViewToViewsById=True)
            if not self.root:
                if v[0] == ' ':
                    raise "Unexpected ' '."
                self.root = View(attrs, self.device)
                parent = self.root
                lastView = self.root
            else:
                newLevel = (len(v) - len(v.lstrip()))
                if treeLevel != newLevel:
                    parent = lastView
                    treeLevel = newLevel
                lastView = View(attrs, self.device)
                parent.add(lastView)
                    
    
    def getRoot(self):
        return self.root

    def traverse(self, root, indent=""):
        if not root:
            return

        print >>sys.stderr, "%s%s" % (indent, root)
        
        for ch in root.children:
            self.traverse(ch, indent=indent+"   ")
                
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
        if DEBUG_RECEIVED:
            print >>sys.stderr
            print >>sys.stderr, received
            print >>sys.stderr
        self.setViews(received)
        self.parseTree(self.views)

        if DEBUG_TREE:
            self.traverse(self.root)
            
        return self.views

    def findViewById(self, viewId):
        '''
        Finds the View with the specified viewId.
        '''
        return View(self.viewsById[viewId], self.device)

    def findViewByTag(self, tag):
        '''
        Finds the View with the specified tag
        '''
        
        return self.findViewWithAttribute('getTag()', tag)
    
    def __findViewWithAttributeInTree(self, attr, val, root):
        if not self.root:
           print >>sys.stderr, "ERROR: no root, did you forget to call dump()?"
           return None

        if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTree: checking if root=%s has attr=%s == %s" % (root.__smallStr__(), attr, val)
        
        if root and attr in root.map and root.map[attr] == val:
            if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTree:  FOUND: %s" % root.__smallStr__()
            return root
        else:
            for ch in root.children:
                v = self.__findViewWithAttributeInTree(attr, val, ch)
                if v:
                    return v
        
        return None
         
    def findViewWithAttribute(self, attr, val):
        '''
        Finds the View with the specified attribute and value
        '''
        
        return self.__findViewWithAttributeInTree(attr, val, self.root)
        
    def findViewWithText(self, text):
        return self.findViewWithAttribute('text:mText', text)

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


