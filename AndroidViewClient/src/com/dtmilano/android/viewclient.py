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
from com.android.monkeyrunner import MonkeyDevice, MonkeyRunner

DEBUG = False
DEBUG_RECEIVED = DEBUG and True
DEBUG_TREE = DEBUG and True
DEBUG_GETATTR = DEBUG and False
DEBUG_COORDS = DEBUG and True
DEBUG_TOUCH = DEBUG and True
DEBUG_STATUSBAR = DEBUG and True

ANDROID_HOME = os.environ['ANDROID_HOME'] if os.environ.has_key('ANDROID_HOME') else '/opt/android-sdk'
''' This environment variable is used to locate the I{Android SDK} components needed.
    Set C{ANDROID_HOME} in the process environment to point to the I{Android SDK} installation. '''
VIEW_SERVER_HOST = 'localhost'
VIEW_SERVER_PORT = 4939

# this is probably the only reliable way of determining the OS in monkeyrunner
os_name = java.lang.System.getProperty('os.name')
if os_name.startswith('Windows'):
    ADB = 'adb.exe'
else:
    ADB = 'adb'

OFFSET = 25
''' This assumes the smallest touchable view on the screen is approximately 50px x 50px
    and touches it at M{(x+OFFSET, y+OFFSET)} '''

# some constants for the attributes
TEXT_PROPERTY = 'text:mText'
WS = "\xfe" # the whitespace replacement char for TEXT_PROPERTY
GET_VISIBILITY_PROPERTY = 'getVisibility()'
LAYOUT_TOP_MARGIN_PROPERTY = 'layout:layout_topMargin'

def __nd(name):
    '''
    @return: Returns a named decimal
    '''
    return '(?P<%s>\d+)' % name

def __nh(name):
    '''
    @return: Returns a named hex
    '''
    return '(?P<%s>[0-9a-f]+)' % name

def __ns(name):
    '''
    @return: Returns a named string (only non-whitespace characters allowed)
    '''
    return '(?P<%s>\S+)' % name


class Window:
    '''
    Window class
    '''

    def __init__(self, winId, activity, wvx, wvy, wvw, wvh, visibility):
        '''
        Constructor
        
        @type winId: str
        @param winId: the window ID
        @type activity: str
        @param activity: the activity (or sometimes other component) owning the window
        @type wvx: int
        @param wvx: window's virtual X
        @type wvy: int
        @param wvy: window's virtual Y
        @type wvw: int
        @param wvw: window's virtual width
        @type wvh: int
        @param wvh: window's virtual height
        @type visibility: int
        @param visibility: visibility of the window
        '''

        if DEBUG_COORDS: print >> sys.stderr, "Window(%s, %s, %d, %d, %d, %d, %d)" % \
                (winId, activity, wvx, wvy, wvw, wvh, visibility)
        self.winId = winId
        self.activity = activity
        self.wvx = wvx
        self.wvy = wvy
        self.wvw = wvw
        self.wvh = wvh
        self.visibility = visibility

    def __str__(self):
        return "Window(%s, %s, %d, %d, %d, %d, %d)" % \
                (self.winId, self.activity, self.wvx, self.wvy, self.wvw, self.wvh, self.visibility)


class View:
    '''
    View class
    '''

    @staticmethod
    def factory(attrs, device):
        '''
        View factory
        '''
        
        if attrs.has_key('class'):
            clazz = attrs['class']
            if clazz == 'android.widget.TextView':
                return TextView(attrs, device)
            elif clazz == 'android.widget.EditText':
                return EditText(attrs, device)
            else:
                return View(attrs, device)
        else:
            return View(attrs, device)
    
    def __init__(self, map, device):
        '''
        Constructor
        
        @type map: map
        @param map: the map containing the (attribute, value) pairs
        @type device: MonkeyDevice
        @param device: the device containing this View
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
        '''
        Gets the View class
        
        @return:  the View class or None if not defined
        '''
        
        try:
            return self.map['class']
        except:
            return None

    def getId(self):
        '''
        Gets the View Id
        
        @return: the View Id or None if not defined
        @see: L{getUniqueId()}
        '''
        
        try:
            return self.map['mID']
        except:
            return None

    def getText(self):
        '''
        Gets the text attribute
        
        @return: the text attribute or None if not defined
        '''
        
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
        '''
        Gets the unique Id of this View.
        
        @see: L{ViewClient.__splitAttrs()} for a discussion on B{Unique Ids}
        '''
        
        try:
            return self.map['uniqueId']
        except:
            return None

    def getVisibility(self):
        '''
        Gets the View visibility
        '''
        
        try:
            if self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
                return 0x0
            elif self.map[GET_VISIBILITY_PROPERTY] == 'INVISIBLE':
                return 0x4
            elif self.map[GET_VISIBILITY_PROPERTY] == 'GONE':
                return 0x8
            else:
                return -2
        except:
            return -1

    def getX(self):
        '''
        Gets the View X coordinate
        '''
        
        if DEBUG_COORDS:
            print >>sys.stderr, "getX(%s %s ## %s)" % (self.getClass(), self.getId(), self.getUniqueId())
        x = 0
        if GET_VISIBILITY_PROPERTY in self.map and self.map[GET_VISIBILITY_PROPERTY] == 'VISIBLE':
            if DEBUG_COORDS: print >>sys.stderr, "   getX: VISIBLE adding %d" % int(self.map['layout:mLeft'])
            x += int(self.map['layout:mLeft'])
        if DEBUG_COORDS: print >>sys.stderr, "   getX: returning %d" % (x)
        return x
    
    def getY(self):
        '''
        Gets the View Y coordinate
        '''
        
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
        Returns the I{screen} coordinates of this C{View}.
        
        @return: The I{screen} coordinates of this C{View}
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
                if DEBUG_COORDS: print >> sys.stderr, "   getXY: skipping %s %s (%d,%d)" % (parent.getClass(), parent.getId(), parent.getX(), parent.getY())
                parent = parent.parent
                continue
            if DEBUG_COORDS: print >> sys.stderr, "   getXY: parent=%s x=%d hx=%d y=%d hy=%d" % (parent.getId(), x, hx, y, hy)
            hx += parent.getX()
            hy += parent.getY()
            parent = parent.parent

        (wvx, wvy) = self.__dumpWindowsInformation()
        if DEBUG_COORDS:
            print >>sys.stderr, "   getXY: wv=(%d, %d)" % (wvx, wvy)
            print >>sys.stderr, "   getXY: returning (%d, %d) ***" % (x+hx+wvx, y+hy+wvy)
        statusBarOffset = 0
        try:
            fw = self.windows[self.currentFocus]
            if DEBUG_STATUSBAR:
                print "focused window=", fw
                print "deciding whether to consider statusbar offset because current focused windows is at", (fw.wvx, fw.wvy)
        except KeyError:
            fw = None
        (sbw, sbh) = self.__obtainStatusBarDimensionsIfVisible()
        if fw and fw.wvy <= sbh:
            if DEBUG_STATUSBAR: print "considering offset=", sbh
            statusBarOffset = sbh
        return (x+hx+wvx, y+hy+wvy-statusBarOffset)

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

    def __obtainStatusBarDimensionsIfVisible(self):
        sbw = 0
        sbh = 0
        for winId in self.windows:
            w = self.windows[winId]
            if w.activity == 'StatusBar':
                if w.wvy == 0 and w.visibility == 0:
                    if DEBUG_COORDS: print >> sys.stderr, "      __obtainStatusBarDimensionsIfVisible: statusBar=", (w.wvw, w.wvh)
                    sbw = w.wvw
                    sbh = w.wvh
                break

        return (sbw, sbh)

    def __obtainVxVy(self, m):
        wvx = int(m.group('vx'))
        wvy = int(m.group('vy'))
        return wvx, wvy

    def __obtainVwVh(self, m):
        (wvx, wvy) = self.__obtainVxVy(m)
        wvx1 = int(m.group('vx1'))
        wvy1 = int(m.group('vy1'))
        return (wvx1-wvx, wvy1-wvy)

    def __dumpWindowsInformation(self):
        self.windows = {}
        self.currentFocus = None
        lines = self.device.shell('dumpsys window windows').split('\n')
        widRE = re.compile('^ *Window #%s Window{%s %s.*}:' %
                            (__nd('num'), __nh('winId'), __ns('activity')))
        currentFocusRE = re.compile('^  mCurrentFocus=Window{%s .*' % __nh('winId'))
        viewVisibilityRE = re.compile(' mViewVisibility=0x%s ' % __nh('visibility'))
        # This is for 4.0.4 API-15
        contentFrameRE = re.compile('^   *mContentFrame=\[%s,%s\]\[%s,%s\] mVisibleFrame=\[%s,%s\]\[%s,%s\]' %
                             (__nd('x'), __nd('y'), __nd('w'), __nd('h'), __nd('vx'), __nd('vy'), __nd('vx1'), __nd('vy1')))
        # This is for 4.1 API-16
        framesRE = re.compile('^   *Frames:')
        contentRE = re.compile('^     *content=\[%s,%s\]\[%s,%s\] visible=\[%s,%s\]\[%s,%s\]' % 
                               (__nd('x'), __nd('y'), __nd('w'), __nd('h'), __nd('vx'), __nd('vy'), __nd('vx1'), __nd('vy1')))
        
        for l in range(len(lines)):
            m = widRE.search(lines[l])
            if m:
                num = int(m.group('num'))
                winId = m.group('winId')
                activity = m.group('activity')
                wvx = 0
                wvy = 0
                wvw = 0
                wvh = 0
                visibility = -1
                for l2 in range(l+1, len(lines)):
                    m = widRE.search(lines[l2])
                    if m:
                        l += (l2-1)
                        break
                    m = viewVisibilityRE.search(lines[l2])
                    if m:
                        visibility = int(m.group('visibility'))
                        if DEBUG_COORDS: print >> sys.stderr, "__dumpWindowsInformation: visibility=", visibility
                    m = framesRE.search(lines[l2])
                    if m:
                        m = contentRE.search(lines[l2+1])
                        if m:
                            wvx, wvy = self.__obtainVxVy(m)
                            wvw, wvh = self.__obtainVwVh(m)
                    else:
                        m = contentFrameRE.search(lines[l2])
                        if m:
                            wvx, wvy = self.__obtainVxVy(m)
                            wvw, wvh = self.__obtainVwVh(m)
                self.windows[winId] = Window(winId, activity, wvx, wvy, wvw, wvh, visibility)
            else:
                m = currentFocusRE.search(lines[l])
                if m:
                    self.currentFocus = m.group('winId')
        
        if self.currentFocus in self.windows and self.windows[self.currentFocus].visibility == 0:
            if DEBUG_COORDS:
                print >> sys.stderr, "__dumpWindowsInformation: focus=", self.currentFocus
                print >> sys.stderr, "__dumpWindowsInformation:", self.windows[self.currentFocus]
            w = self.windows[self.currentFocus]
            return (w.wvx, w.wvy)
        else:
            if DEBUG_COORDS: print >> sys.stderr, "__dumpWindowsInformation: (0,0)"
            return (0,0)
    
    def touch(self, type=MonkeyDevice.DOWN_AND_UP):
        '''
        Touches this C{View}
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
        '''
        Adds a child
        
        @type child: View
        @param child: The child to add
        '''
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

class TextView(View):
    '''
    TextView class.
    '''
    
    pass

class EditText(TextView):
    '''
    EditText class.
    '''
    
    pass

class ViewClient:
    '''
    ViewClient is a I{ViewServer} client.
    
    If not running the ViewServer is started on the target device or emulator and then the port
    mapping is created.
    '''

    def __init__(self, device, adb=os.path.join(ANDROID_HOME, 'platform-tools', ADB), autodump=True, serialno='emulator-5554'):
        '''
        Constructor
        
        @type device: MonkeyDevice
        @param device: The device running the C{View server} to which this client will connect
        @type adb: str
        @param adb: the path of the C{adb} executable
        @type autodump: boolean
        @param autodump: whether an automatic dump is performed at the end of this constructor
        @type serialno: str
        @param serialno: the serial number of the device or emulator to connect to
        '''
        
        if not device:
            raise Exception('Device is not connected')
        if not os.access(adb, os.X_OK):
            raise Exception('adb="%s" is not executable. Did you forget to set ANDROID_HOME in the environment?' % adb)
        if not self.serviceResponse(device.shell('service call window 3')):
            try:
                self.assertServiceResponse(device.shell('service call window 1 i32 %d' %
                                                        VIEW_SERVER_PORT))
            except:
                raise Exception('Cannot start View server.\n'
                                'This only works on emulator and devices running developer versions.\n'
                                'Does hierarchyviewer work on your device ?')

        # FIXME: it seems there's no way of obtaining the serialno from the MonkeyDevice
        subprocess.check_call([adb, '-s', serialno, 'forward', 'tcp:%d' % VIEW_SERVER_PORT,
                               'tcp:%d' % VIEW_SERVER_PORT])

        self.device = device
        ''' The C{MonkeyDevice} device instance '''
        self.root = None
        ''' The root node '''
        self.viewsById = {}
        ''' The map containing all the L{View}s indexed by their L{uniqueId} '''
        self.display = {}
        ''' The map containing the device's display properties: width, height and density '''
        for prop in [ 'width', 'height', 'density' ]:
            try:
                self.display[prop] = device.getProperty(prop)
            except:
                self.display[prop] = -1

        if autodump:
            self.dump()
    
    @staticmethod
    def connectToDeviceOrExit(timeout=60):
        '''
        Connects to a device which serial number is obtained from the script arguments if available
        or using the default C{emulator-5554}.
        
        If the connection is not successful the script exits.
        L{MonkeyRunner.waitForConnection()} returns a L{MonkeyDevice} even if the connection failed.
        Then, to detect this situation, C{device.wake()} is attempted and if it fails then it is
        assumed the previous connection failed.
        
        @type timeout: int
        @param timeout: timeout for the connection
        @return: the device and serialno used for the connection
        '''
        
        serialno = sys.argv[1] if len(sys.argv) > 1 else 'emulator-5554'
        device = MonkeyRunner.waitForConnection(timeout, serialno)
        try:
            device.wake()
        except java.lang.NullPointerException, e:
            print >> sys.stderr, "%s: ERROR: Couldn't connect to %s: %s" % (os.path.basename(sys.argv[0]), serialno, e)
            sys.exit(1)
        return device, serialno
        
    @staticmethod
    def traverseShowClassIdAndText(view):
        '''
        Shows the View class, id and text if available.
        This function can be used as a transform function to L{ViewClient.traverse()}
        
        @type view: I{View}
        @param view: the View
        @return: the string containing class, id, and text if available 
        '''
        
        try:
            return "%s %s %s" % (view.getClass(), view.getId(), view.getText())
        except Exception, e:
            return "Exception in view=%s: %s" % (view.__smallStr__(), e)
        
    # methods that can be used to transform ViewClient.traverse output
    TRAVERSE_CIT = traverseShowClassIdAndText
    ''' An alias for L{traverseShowClassIdAndText(view)} '''
    
    def assertServiceResponse(self, response):
        if not self.serviceResponse(response):
            raise Exception('Invalid response received from service.')

    def serviceResponse(self, response):
        '''
        Checks the response received from the I{ViewServer}.
        
        @return: C{True} if the response received matches L{PARCEL_TRUE}, C{False} otherwise
        '''
        
        PARCEL_TRUE = "Result: Parcel(00000000 00000001   '........')\r\n"
        if DEBUG:
            print >>sys.stderr, "serviceResponse: comparing '%s' vs Parcel(%s)" % (response, PARCEL_TRUE)
        return response == PARCEL_TRUE

    def setViews(self, received):
        '''
        Sets C{self.views} to the received value splitting it into lines.
        
        @type received: str
        @param received: the string received from the I{View server}
        '''
        
        self.views = received.split("\n")
        if DEBUG:
            print >>sys.stderr, "there are %d views in this dump" % len(self.views)

    def __splitAttrs(self, strArgs, addViewToViewsById=False):
        '''
        Splits the C{View} attributes in C{strArgs} and optionally adds the view id to the C{viewsById} list.
        
        Unique Ids
        ==========
        It is very common to find C{View}s having B{NO_ID} as the Id. This turns very difficult to 
        use L{self.findViewById()}. To help in this situation this method assigns B{unique Ids} if
        C{addViewToViewsById} is C{True}.
        
        The B{unique Ids} are generated using the pattern C{id/no_id/<number>} with C{<number>} starting
        at 1.
        
        @type strArgs: str
        @param strArgs: the string containing the raw list of attributes and values
        @type addViewToViewsById: boolean
        @param addViewToViewsById: whether to add the parsed list of attributes and values to the
                                   map C{self.viewsById}
        
        @return: Returns the attributes map.
        '''
        
        # replace the spaces in text:mText to preserve them in later split
        # they are translated back after the attribute matches
        textRE = re.compile('%s=%s,' % (TEXT_PROPERTY, __nd('len')))
        m = textRE.search(strArgs)
        if m:
            s1 = strArgs[m.start():m.end()+int(m.group('len'))]
            s2 = s1.replace(' ', WS)
            strArgs = strArgs.replace(s1, s2, 1)

        idRE = re.compile("(?P<viewId>id/\S+)")
        attrRE = re.compile('%s(\(\))?=\d+,%s' % (__ns('attr'), __ns('val')))
        hashRE = re.compile('%s@%s' % (__ns('class'), __nh('oid')))
        
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
                self.root = View.factory(attrs, self.device) #View(attrs, self.device)
                treeLevel = 0
                newLevel = 0
                lastView = self.root
                parent = self.root
                parents.append(parent)
            else:
                newLevel = (len(v) - len(v.lstrip()))
                if newLevel == 0:
                    raise "newLevel==0 but tree can have only one root, v=", v
                child = View.factory(attrs, self.device) #View(attrs, self.device)
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
        '''
        Gets the root node of the C{View} tree
        
        @return: the root node of the C{View} tree
        '''
        return self.root

    def traverse(self, root="ROOT", indent="", transform=View.__str__):
        '''
        Traverses the C{View} tree and prints its nodes.
        
        The nodes are printed converting them to string but other transformations can be specified
        by providing a method name as the C{transform} parameter.
        
        @type root: L{View}
        @param root: the root node from where the traverse starts
        @type indent: str
        @param indent: the indentation string to use to print the nodes
        @type transform: method
        @param transform: a method to use to transform the node before is printed  
        '''
        if not root:
            return

        if root == "ROOT":
            root = self.root

        s = transform(root)
        if s:
            print "%s%s" % (indent, s)
        
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


