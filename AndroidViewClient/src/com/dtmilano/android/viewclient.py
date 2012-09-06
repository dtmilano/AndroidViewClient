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
import types
from com.android.monkeyrunner import MonkeyDevice

DEBUG = False
DEBUG_RECEIVED = DEBUG and True
DEBUG_TREE = DEBUG and True
DEBUG_GETATTR = DEBUG and False
DEBUG_COORDS = DEBUG and True
DEBUG_TOUCH = DEBUG and False

ANDROID_HOME = os.environ['ANDROID_HOME'] if os.environ.has_key('ANDROID_HOME') else '/opt/android-sdk'
VIEW_SERVER_HOST = 'localhost'
VIEW_SERVER_PORT = 4939

# this is probably the only reliable way of determining the OS in monkeyrunner
os_name = java.lang.System.getProperty('os.name')
if os_name.startswith('Windows'):
    ADB = 'adb.exe'
else:
    ADB = 'adb'

# This assumes the smallest touchable view on the screen is approximately 50px x 50px
# and touches it at (x+OFFSET, y+OFFSET)
OFFSET = 25

# some constants for the attributes
TEXT_PROPERTY = 'text:mText'
WS = "\xfe" # the whitespace replacement char for TEXT_PROPERTY
GET_VISIBILITY_PROPERTY = 'getVisibility()'
LAYOUT_TOP_MARGIN_PROPERTY = 'layout:layout_topMargin'

def __nd(name):
    '''
    Returns a named decimal
    '''
    return '(?P<%s>\d+)' % name

def __nh(name):
    '''
    Returns a named hexa
    '''
    return '(?P<%s>[0-9a-f]+)' % name


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
        self.children = []
        self.parent = None
        self.windows = {}
        self.currentFocus = None
        
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
            
    def getClass(self):
        try:
            return self.map['class']
        except:
            return None

    def getId(self):
        try:
            return self.map['mID']
        except:
            return None

    def getText(self):
        try:
            return self.map[TEXT_PROPERTY]
        except Exception:
            return None

    def getHeight(self):
        try:
            return int(self.map['layout:getHeight()'])
        except:
            return 0

    def getWidth(self):
        try:
            return int(self.map['layout:getWidth()'])
        except:
            return 0

    def getUniqueId(self):
        try:
            return self.map['uniqueId']
        except:
            return None

    def getX(self):
        if DEBUG_COORDS:
            print >>sys.stderr, "getX(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())
        x = 0
        if GET_VISIBILITY_PROPERTY in self.map and self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
            if DEBUG_COORDS: print >>sys.stderr, "   getX: VISIBLE adding %d" % int(self.map['layout:mLeft'])
            x += int(self.map['layout:mLeft'])
        if DEBUG_COORDS: print >>sys.stderr, "   getX: returning %d" % (x)
        return x
    
    def getY(self):
        if DEBUG_COORDS:
            print >>sys.stderr, "getY(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())
        y = 0
        if GET_VISIBILITY_PROPERTY in self.map and self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
            if DEBUG_COORDS: print >>sys.stderr, "   getY: VISIBLE adding %d" % int(self.map['layout:mTop'])
            y += int(self.map['layout:mTop'])

        if DEBUG_COORDS: print >>sys.stderr, "   getY: returning %d" % (y)
        return y
    
    def getXY(self):
        '''
        Returns the "screen" coordinates of this View.
        '''
        
        if DEBUG_COORDS:
            print >> sys.stderr, "getXY(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())

        x = self.getX()
        y = self.getY()
        parent = self.parent
        if DEBUG_COORDS: print >> sys.stderr, "   getXY: x=%s y=%s parent=%s" % (x, y, parent.getId() if parent else "None")
        hx = 0
        hy = 0
        while parent != None:
            if DEBUG_COORDS: print >> sys.stderr, "      getXY: parent: %s %s <<<<" % (parent.getClass(), parent.getId())
            if parent.getClass() in [ 'com.android.internal.widget.ActionBarView',
                                       'com.android.internal.widget.ActionBarContextView',
                                       'com.android.internal.view.menu.ActionMenuView',
                                       'com.android.internal.policy.impl.PhoneWindow$DecorView' ]:
                if DEBUG_COORDS: print >> sys.stderr, "   getXY: skipping %s %s" % (parent.getClass(), parent.getId())
                parent = parent.parent
                continue
            if DEBUG_COORDS: print >> sys.stderr, "   getXY: parent=%s x=%d hx=%d y=%d hy=%d" % (parent.getId(), x, hx, y, hy)
            hx += parent.getX()
            hy += parent.getY()
            parent = parent.parent

        (wvx, wvy) = self.__dumpWindowsInformation()
        if DEBUG_COORDS: print >>sys.stderr, "   getXY: wv=(%d, %d)" % (wvx, wvy)
        if DEBUG_COORDS: print >>sys.stderr, "   getXY: returning (%d, %d) ***" % (x+hx+wvx, y+hy+wvy)
        return (x+hx+wvx, y+hy+wvy)

    def getCoords(self):
        '''
        Gets the coords of the View
        '''
        if DEBUG_COORDS:
            print >>sys.stderr, "getCoords(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())

        (x, y) = self.getXY();
        w = self.getWidth()
        h = self.getHeight()
        return ((x, y), (x+w, y+h))

    def __obtainVxVy(self, m):
        wvx = int(m.group('vx'))
        wvy = int(m.group('vy'))
        return wvx, wvy

    def __dumpWindowsInformation(self):
        self.windows = {}
        self.currentFocus = None
        lines = self.device.shell('dumpsys window windows').split('\n')
        widRE = re.compile('^ *Window #%s Window{%s (?P<activity>\S+).*}:' %
                            (__nd('num'), __nh('winId')))
        currentFocusRE = re.compile('^  mCurrentFocus=Window{%s .*' % __nh('winId'))
        # This is for 4.0.4 API-15
        contentFrameRE = re.compile('^   *mContentFrame=\[%s,%s\]\[%s,%s\] mVisibleFrame=\[%s,%s\]' %
                            (__nd('x'), __nd('y'), __nd('w'), __nd('h'), __nd('vx'), __nd('vy')))
        # This is for 4.1 API-16
        framesRE = re.compile('^   *Frames:')
        contentRE = re.compile('^     *content=\[%s,%s\]\[%s,%s\] visible=\[%s,%s\]' % 
                            (__nd('x'), __nd('y'), __nd('w'), __nd('h'), __nd('vx'), __nd('vy')))
        
        for l in range(len(lines)):
            m = widRE.search(lines[l])
            if m:
                num = int(m.group('num'))
                winId = m.group('winId')
                activity = m.group('activity')
                wvx = 0
                wvy = 0
                for l2 in range(l+1, len(lines)):
                    m = widRE.search(lines[l2])
                    if m:
                        l += (l2-1)
                        break
                    m = framesRE.search(lines[l2])
                    if m:
                        m = contentRE.search(lines[l2+1])
                        if m:
                            wvx, wvy = self.__obtainVxVy(m)
                    else:
                        m = contentFrameRE.search(lines[l2])
                        if m:
                            wvx, wvy = self.__obtainVxVy(m)
                self.windows[winId] = (wvx, wvy)
            else:
                m = currentFocusRE.search(lines[l])
                if m:
                    self.currentFocus = m.group('winId')
        
        if self.currentFocus in self.windows:
            return self.windows[self.currentFocus]
        else:
            return (0,0)
    
    def touch(self, type=MonkeyDevice.DOWN_AND_UP):
        '''
        Touches this View
        '''
        
        (x, y) = self.getXY()
        if DEBUG_TOUCH:
            print >>sys.stderr, "should touch @ (%d, %d)" % (x+OFFSET, y+OFFSET)
        self.device.touch(x+OFFSET, y+OFFSET, type)
    
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
        __str = "View["
        if "class" in self.map:
            __str += " class=" + self.map['class']
        __str += " id=%s" % self.getId()
        __str += " ]   parent="
        if self.parent and "class" in self.parent.map:
            __str += "%s" % self.parent.map["class"]
        else:
            __str += "None"

        return __str
            
    def __tinyStr__(self):
        __str = "View["
        if "class" in self.map:
            __str += " class=" + re.sub('.*\.', '', self.map['class'])
        __str += " id=%s" % self.getId()
        __str += " ]"
        #__str += "parent="
        #if self.parent and "class" in self.parent.map:
        #    __str += "%s" % re.sub('.*\.', '', self.parent.map["class"])
        #else:
        #    __str += "None"

        return __str
            
    def __str__(self):
        __str = "View["
        if "class" in self.map:
            __str += " class=" + self.map["class"] + " "
        for a in self.map:
            __str += a + "=" + self.map[a] + " "
        __str += "]   parent="
        if self.parent and "class" in self.parent.map:
            __str += "%s" % self.parent.map["class"]
        else:
            __str += "None"

        return __str

 
class ViewClient:
    '''
    ViewClient is a ViewServer client.
    
    If not running the ViewServer is started on the target device or emulator and then the port
    mapping is created.
    '''

    def __init__(self, device, adb=os.path.join(ANDROID_HOME, 'platform-tools', ADB), autodump=True):
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
        self.display = {}
        for prop in [ 'width', 'height', 'density' ]:
            try:
                self.display[prop] = device.getProperty(prop)
            except:
                self.display[prop] = -1

        if autodump:
            self.dump()
    
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

    def __splitAttrs(self, strArgs, addViewToViewsById=False):
        '''
        Splits the view attributes in strArgs and optionally adds the view id to the viewsById list.
        Returns the attributes map.
        '''
        
        # replace the spaces in text:mText to preserve them in later split
        # they are translated back after the attribute matches
        textRE = re.compile(TEXT_PROPERTY + "=(?P<len>\d+),")
        m = textRE.search(strArgs)
        if m:
            s1 = strArgs[m.start():m.end()+int(m.group('len'))]
            s2 = s1.replace(' ', WS)
            strArgs = strArgs.replace(s1, s2, 1)

        idRE = re.compile("(?P<viewId>id/\S+)")
        attrRE = re.compile("(?P<attr>\S+)(\(\))?=\d+,(?P<val>\S+)")
        hashRE = re.compile("(?P<class>\S+)@(?P<oid>[0-9a-f]+)")
        
        attrs = {}
        viewId = None
        m = idRE.search(strArgs)
        if m:
            viewId = m.group('viewId')
            if DEBUG:
                print >>sys.stderr, "found %s" % viewId

        for attr in strArgs.split():
            m = attrRE.match(attr)
            if m:
                attr = m.group('attr')
                val = m.group('val')
                if attr == TEXT_PROPERTY:
                    # restore spaces that have been replaced
                    val = val.replace(WS, ' ')
                attrs[attr] = val
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
                # immediately incremented if another view with no id was found before to generate
                # a unique id
                viewId = "id/no_id/1"
            if viewId in self.viewsById:
                # sometimes the view ids are not unique, so let's generate a unique id here
                i = 1
                while True:
                    newId = re.sub('/\d+$', '', viewId) + '/%d' % i
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
    
    def parseTree(self, treeStr):
        self.root = None
        parent = None
        parents = []
        treeLevel = -1
        newLevel = -1
        lastView = None
        for v in self.views:
            if v == 'DONE' or v == 'DONE.':
                break
            attrs = self.__splitAttrs(v, addViewToViewsById=True)
            if not self.root:
                if v[0] == ' ':
                    raise "Unexpected root element starting with ' '."
                self.root = View(attrs, self.device)
                treeLevel = 0
                newLevel = 0
                lastView = self.root
                parent = self.root
                parents.append(parent)
            else:
                newLevel = (len(v) - len(v.lstrip()))
                if newLevel == 0:
                    raise "newLevel==0 but tree can have only one root, v=", v
                child = View(attrs, self.device)
                if newLevel == treeLevel:
                    parent.add(child)
                    lastView = child
                elif newLevel > treeLevel:
                    if (newLevel - treeLevel) != 1:
                        raise "newLevel jumps %d levels, v=%s" % ((newLevel-treeLevel), v)
                    parent = lastView
                    parents.append(parent)
                    parent.add(child)
                    lastView = child
                    treeLevel = newLevel
                else: # newLevel < treeLevel
                    for i in range(treeLevel - newLevel):
                        parents.pop()
                    parent = parents.pop()
                    parents.append(parent)
                    parent.add(child)
                    treeLevel = newLevel
                    lastView = child
     

    def getRoot(self):
        return self.root

    def traverse(self, root, indent="", transform=View.__str__):
        if not root:
            return

        print "%s%s" % (indent, transform(root))
        
        for ch in root.children:
            self.traverse(ch, indent=indent+"   ", transform=transform)
                
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

    def findViewById(self, viewId, root="ROOT"):
        '''
        Finds the View with the specified viewId.
        '''

        if not root:
            return None

        if type(root) == types.StringType and root == "ROOT":
            return self.findViewById(viewId, self.root)

        if root.getId() == viewId:
            return root

        if re.match('^id/no_id', viewId):
            if root.getUniqueId() == viewId:
                return root;
        
        for ch in root.children:
            foundView = self.findViewById(viewId, ch)
            if foundView:
                return foundView

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
         
    def __findViewWithAttributeInTreeThatMatches(self, attr, regex, root, rlist=[]):
        if not self.root:
            print >>sys.stderr, "ERROR: no root, did you forget to call dump()?"
            return None

        if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTreeThatMatches: checking if root=%s attr=%s matches %s" % (root.__smallStr__(), attr, regex)
        
        if root and attr in root.map and regex.match(root.map[attr]):
            if DEBUG: print >>sys.stderr, "__findViewWithAttributeInTreeThatMatches:  FOUND: %s" % root.__smallStr__()
            return root
            #print >>sys.stderr, "appending root=%s to rlist=%s" % (root.__smallStr__(), rlist)
            #return rlist.append(root)
        else:
            for ch in root.children:
                v = self.__findViewWithAttributeInTreeThatMatches(attr, regex, ch, rlist)
                if v:
                    return v
                    #print >>sys.stderr, "appending v=%s to rlist=%s" % (v.__smallStr__(), rlist)
                    #return rlist.append(v)
        
        return None
        #return rlist

    def findViewWithAttribute(self, attr, val):
        '''
        Finds the View with the specified attribute and value
        '''
        
        return self.__findViewWithAttributeInTree(attr, val, self.root)
        
    def findViewWithAttributeThatMatches(self, attr, regex):
        '''
        Finds the list of Views with the specified attribute matching
        regex
        '''
        
        return self.__findViewWithAttributeInTreeThatMatches(attr, regex, self.root)
        
    def findViewWithText(self, text):
        if type(text).__name__ == 'PatternObject':
            return self.findViewWithAttributeThatMatches(TEXT_PROPERTY, text)
            #l = self.findViewWithAttributeThatMatches(TEXT_PROPERTY, text)
            #ll = len(l)
            #if ll == 0:
            #    return None
            #elif ll == 1:
            #    return l[0]
            #else:
            #    print >>sys.stderr, "WARNING: findViewWithAttributeThatMatches invoked by findViewWithText returns %d items." % ll
            #    return l
        else:
            return self.findViewWithAttribute(TEXT_PROPERTY, text)

    def getViewIds(self):
        '''
        Returns the Views map.
        '''

        return self.viewsById
    
    def __getFocusedWindowPosition(self):
        focusedWindowId = self.__getFocusedWindowId()


if __name__ == "__main__":
    try:
        vc = ViewClient(None)
    except:
        print "%s: Don't expect this to do anything" % __file__


