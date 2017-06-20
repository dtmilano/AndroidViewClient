'''
Copyright (C) 2012-2017  Diego Torres Milano
Created on Dec 1, 2012

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@author: Diego Torres Milano
'''
import subprocess
import threading

from com.dtmilano.android.adb.dumpsys import Dumpsys

__version__ = '13.4.0'

import sys
import warnings

if sys.executable:
    if 'monkeyrunner' in sys.executable:
        warnings.warn(
            '''

            You should use a 'python' interpreter, not 'monkeyrunner' for this module

            ''', RuntimeWarning)
import string
import datetime
import struct
import cStringIO as StringIO
import socket
import time
import re
import os
import platform

from com.dtmilano.android.window import Window
from com.dtmilano.android.common import _nd, _nh, _ns, obtainPxPy, obtainVxVy, \
    obtainVwVh, profileStart, profileEnd
from com.dtmilano.android.adb.androidkeymap import KEY_MAP

DEBUG = False
DEBUG_SHELL = DEBUG and False
DEBUG_TOUCH = DEBUG and False
DEBUG_LOG = DEBUG and False
DEBUG_WINDOWS = DEBUG and False
DEBUG_COORDS = DEBUG and False
DEBUG_IMAGE_ROTATION = DEBUG and False

PIL_AVAILABLE = False
PROFILE = False

try:
    HOSTNAME = os.environ['ANDROID_ADB_SERVER_HOST']
except:
    HOSTNAME = 'localhost'

try:
    PORT = int(os.environ['ANDROID_ADB_SERVER_PORT'])
except KeyError:
    PORT = 5037

OKAY = 'OKAY'
FAIL = 'FAIL'

UP = 0
DOWN = 1
DOWN_AND_UP = 2

TIMEOUT = 15

WIFI_SERVICE = 'wifi'

# some device properties
VERSION_SDK_PROPERTY = 'ro.build.version.sdk'
VERSION_RELEASE_PROPERTY = 'ro.build.version.release'


class Device:
    @staticmethod
    def factory(_str):
        if DEBUG:
            print >> sys.stderr, "Device.factory(", _str, ")"
            print >> sys.stderr, "   _str=", repr(_str)
            print >> sys.stderr, "   _str=", _str.replace(' ', '_')
        values = _str.split(None, 2)
        if DEBUG:
            print >> sys.stderr, "values=", values
        return Device(*values)

    def __init__(self, serialno, status, qualifiers=None):
        self.serialno = serialno
        self.status = status
        self.qualifiers = qualifiers

    def __str__(self):
        return "<<<" + self.serialno + ", " + self.status + ", %s>>>" % self.qualifiers


class WifiManager:
    '''
    Simulates Android WifiManager.

    @see: http://developer.android.com/reference/android/net/wifi/WifiManager.html
    '''

    WIFI_STATE_DISABLING = 0
    WIFI_STATE_DISABLED = 1
    WIFI_STATE_ENABLING = 2
    WIFI_STATE_ENABLED = 3
    WIFI_STATE_UNKNOWN = 4

    WIFI_IS_ENABLED_RE = re.compile('Wi-Fi is enabled')
    WIFI_IS_DISABLED_RE = re.compile('Wi-Fi is disabled')

    def __init__(self, device):
        self.device = device

    def getWifiState(self):
        '''
        Gets the Wi-Fi enabled state.

        @return: One of WIFI_STATE_DISABLED, WIFI_STATE_DISABLING, WIFI_STATE_ENABLED, WIFI_STATE_ENABLING, WIFI_STATE_UNKNOWN
        '''

        result = self.device.shell('dumpsys wifi')
        if result:
            state = result.splitlines()[0]
            if self.WIFI_IS_ENABLED_RE.match(state):
                return self.WIFI_STATE_ENABLED
            elif self.WIFI_IS_DISABLED_RE.match(state):
                return self.WIFI_STATE_DISABLED
        print >> sys.stderr, "UNKNOWN WIFI STATE:", state
        return self.WIFI_STATE_UNKNOWN


class Timer():
    def __init__(self, timeout, handler, args):
        self.timer = threading.Timer(timeout, handler, args)

    def start(self):
        self.timer.start()

    def cancel(self):
        self.timer.cancel()

    class TimeoutException(Exception):
        pass


class AdbClient:

    UP = UP
    DOWN = DOWN
    DOWN_AND_UP = DOWN_AND_UP

    def __init__(self, serialno=None, hostname=HOSTNAME, port=PORT, settransport=True, reconnect=True,
                 ignoreversioncheck=False, timeout=TIMEOUT):
        self.Log = AdbClient.__Log(self)

        self.serialno = serialno
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.timerId = -1
        self.timers = {}

        self.reconnect = reconnect
        self.socket = AdbClient.connect(self.hostname, self.port, self.timeout)

        self.checkVersion(ignoreversioncheck)

        self.build = {}
        ''' Build properties '''

        self.__displayInfo = None
        ''' Cached display info. Reset it to C{None} to force refetching display info '''

        self.display = {}
        ''' The map containing the device's physical display properties: width, height and density '''

        self.isTransportSet = False
        if settransport and serialno != None:
            self.__setTransport(timeout=timeout)
            self.build[VERSION_SDK_PROPERTY] = int(self.__getProp(VERSION_SDK_PROPERTY))
            self.initDisplayProperties()

    def timeoutHandler(self, timerId):
        print >> sys.stderr, "TIMEOUT HANDLER", timerId
        self.timers[timerId] = "EXPIRED"
        raise Timer.TimeoutException("Timer %d has expired" % timerId)

    def setTimer(self, timeout):
        """
        Sets a timer.

        :param timeout: timeout in seconds
        :return: the timerId
        """
        self.timerId += 1
        timer = Timer(timeout, self.timeoutHandler, [self.timerId])
        timer.start()
        self.timers[self.timerId] = timer
        return self.timerId

    def cancelTimer(self, timerId):
        if DEBUG:
            print >> sys.stderr, "Canceling timer with ID=%s" % timerId
        if timerId not in self.timers:
            print >> sys.stderr, "timers does not contain a timer with ID=%s" % timerId
            print >> sys.stderr, "available timers:"
            for t in self.timers:
                print >> sys.stderr, "   id=", t
        if self.timers[timerId] != "EXPIRED":
            self.timers[timerId].cancel()
        del self.timers[timerId]

    def setSerialno(self, serialno):
        if self.isTransportSet:
            raise ValueError("Transport is already set, serialno cannot be set once this is done.")
        self.serialno = serialno
        self.__setTransport()
        self.build[VERSION_SDK_PROPERTY] = int(self.__getProp(VERSION_SDK_PROPERTY))

    def setReconnect(self, val):
        self.reconnect = val

    @staticmethod
    def connect(hostname, port, timeout=TIMEOUT):
        if DEBUG:
            print >> sys.stderr, "AdbClient.connect(%s, %s, %s)" % (hostname, port, timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_LINGER: Idea proposed by kysersozelee (#173)
        l_onoff = 1
        l_linger = 0
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                     struct.pack('ii', l_onoff, l_linger))
        s.settimeout(timeout)
        try:
            s.connect((hostname, port))
        except socket.error, ex:
            raise RuntimeError("ERROR: Connecting to %s:%d: %s.\nIs adb running on your computer?" % (s, port, ex))
        return s

    def close(self):
        if DEBUG:
            print >> sys.stderr, "Closing socket...", self.socket
        if self.socket:
            self.socket.close()

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def __send(self, msg, checkok=True, reconnect=False):
        if DEBUG:
            print >> sys.stderr, "__send(%s, checkok=%s, reconnect=%s)" % (msg, checkok, reconnect)
        if not re.search('^host:', msg):
            if not self.isTransportSet:
                self.__setTransport()
        else:
            self.checkConnected()
        b = bytearray(msg, 'utf-8')
        self.socket.send('%04X%s' % (len(b), b))
        if checkok:
            self.__checkOk()
        if reconnect:
            if DEBUG:
                print >> sys.stderr, "    __send: reconnecting"
            self.socket = AdbClient.connect(self.hostname, self.port, self.timeout)
            self.__setTransport()

    def __receive(self, nob=None, sock=None):
        if DEBUG:
            print >> sys.stderr, "__receive(nob=%s)" % (nob)
        if not sock:
            sock = self.socket
        self.checkConnected(sock)
        if nob is None:
            nob = int(sock.recv(4), 16)
        if DEBUG:
            print >> sys.stderr, "    __receive: receiving", nob, "bytes"
        recv = bytearray(nob)
        view = memoryview(recv)
        nr = 0
        timerId = self.setTimer(timeout=self.timeout)
        try:
            while nr < nob:
                l = sock.recv_into(view, len(view))
                if DEBUG:
                    print >> sys.stderr, "l=", l, "nr=", nr
                    print >> sys.stderr, "timer=", self.timers[timerId]
                view = view[l:]
                nr += l
                if self.timers[timerId] == 'EXPIRED':
                    raise Timer.TimeoutException('%d EXPIRED' % timerId)
        except Timer.TimeoutException, ex:
                if self.timers[timerId] == 'EXPIRED':
                    raise RuntimeError("Timeout receiving %d bytes (%d received)" % (nob, nr))
        finally:
            self.cancelTimer(timerId)
        if DEBUG:
            print >> sys.stderr, "    __receive: returning len=", len(recv)
        return str(recv)

    def __checkOk(self, sock=None):
        if DEBUG:
            print >> sys.stderr, "__checkOk()"
        if not sock:
            sock = self.socket
        self.checkConnected(sock=sock)
        timerId = self.setTimer(timeout=self.timeout)
        recv = sock.recv(4)
        if DEBUG:
            print >> sys.stderr, "    __checkOk: recv=", repr(recv)
        try:
            if recv != OKAY:
                error = sock.recv(1024)
                if error.startswith('0049'):
                    raise RuntimeError(
                        "ERROR: This computer is unauthorized. Please check the confirmation dialog on your device.")
                else:
                    raise RuntimeError("ERROR: %s %s" % (repr(recv), error))
        finally:
            self.cancelTimer(timerId)
        if DEBUG:
            print >> sys.stderr, "    __checkOk: returning True"
        return True

    def checkConnected(self, sock=None):
        if DEBUG:
            print >> sys.stderr, "checkConnected()"
        if not sock:
            sock = self.socket
        if not sock:
            raise RuntimeError("ERROR: Not connected")
        if DEBUG:
            print >> sys.stderr, "    checkConnected: returning True"
        return True

    def checkVersion(self, ignoreversioncheck=False, reconnect=True):
        if DEBUG:
            print >> sys.stderr, "checkVersion(reconnect=%s)   ignoreversioncheck=%s" % (reconnect, ignoreversioncheck)
        self.__send('host:version', reconnect=False)
        # HACK: MSG_WAITALL not available on windows
        # version = self.socket.recv(8, socket.MSG_WAITALL)
        version = self.__readExactly(self.socket, 8)

        VALID_ADB_VERSIONS = ["00040027", "00040024", "00040023", "00040020", "0004001f"]

        if not (version in VALID_ADB_VERSIONS) and not ignoreversioncheck:
            raise RuntimeError(
                "ERROR: Incorrect ADB server version %s (expecting one of %s)" % (version, VALID_ADB_VERSIONS))
        if reconnect:
            self.socket = AdbClient.connect(self.hostname, self.port, self.timeout)

    def __setTransport(self, timeout=60):
        if DEBUG:
            print >> sys.stderr, "__setTransport()"
        if not self.serialno:
            raise ValueError("serialno not set, empty or None")
        self.checkConnected()
        serialnoRE = re.compile(self.serialno)
        found = False
        devices = self.getDevices()
        if len(devices) == 0 and timeout > 0:
            print >> sys.stderr, "Empty device list, will wait %s secs for devices to appear" % self.timeout
            # Sets the timeout to 5 to be able to loop while trying to receive new devices being added
            _s = AdbClient.connect(self.hostname, self.port, timeout=5)
            msg = 'host:track-devices'
            b = bytearray(msg, 'utf-8')
            try:
                timerId = self.setTimer(timeout=timeout)
                _s.send('%04X%s' % (len(b), b))
                self.__checkOk(sock=_s)
                # eat '0000'
                _s.recv(4)
                found = False
                while not found:
                    sys.stderr.write(".")
                    sys.stderr.flush()
                    try:
                        for line in _s.recv(1024).splitlines():
                            # skip first 4 bytes containing the response size
                            device = Device.factory(line[4:])
                            if device.status == 'device':
                                devices.append(device)
                                found = True
                                break
                        if found:
                            break
                    except socket.timeout as ex:
                        # we continue trying until timer times out
                        pass
                    finally:
                        time.sleep(3)
                    if self.timers[timerId] == "EXPIRED":
                        break
                self.cancelTimer(timerId)
            except Timer.TimeoutException as ex:
                print >> sys.stderr, "EXCEPTION", ex
                pass
            finally:
                _s.close()
                sys.stderr.write("\n")
                sys.stderr.flush()
        if len(devices) == 0:
            raise RuntimeError("ERROR: There are no connected devices")
        for device in devices:
            if serialnoRE.match(device.serialno):
                found = True
                break
        if not found:
            raise RuntimeError("ERROR: couldn't find device that matches '%s' in %s" % (self.serialno, devices))
        self.serialno = device.serialno
        msg = 'host:transport:%s' % self.serialno
        if DEBUG:
            print >> sys.stderr, "    __setTransport: msg=", msg
        self.__send(msg, reconnect=False)
        self.isTransportSet = True

    def __checkTransport(self):
        if not self.isTransportSet:
            raise RuntimeError("ERROR: Transport is not set")

    def __readExactly(self, sock, size):
        if DEBUG:
            print >> sys.stderr, "__readExactly(socket=%s, size=%d)" % (sock, size)
        _buffer = bytearray(size)
        view = memoryview(_buffer)
        nb = 0
        while nb < size:
            l = sock.recv_into(view, len(view))
            view = view[l:]
            nb += l
        return str(_buffer)

    def getDevices(self):
        if DEBUG:
            print >> sys.stderr, "getDevices()"
        self.__send('host:devices-l', checkok=False)
        try:
            self.__checkOk()
        except RuntimeError, ex:
            print >> sys.stderr, "**ERROR:", ex
            return None
        devices = []
        for line in self.__receive().splitlines():
            devices.append(Device.factory(line))
        self.socket = AdbClient.connect(self.hostname, self.port, self.timeout)
        return devices

    def shell(self, cmd=None):
        if DEBUG_SHELL:
            print >> sys.stderr, "shell(cmd=%s)" % cmd
        self.__checkTransport()
        if cmd:
            self.__send('shell:%s' % cmd, checkok=True, reconnect=False)
            chunks = []
            while True:
                chunk = None
                try:
                    chunk = self.socket.recv(4096)
                except Exception, ex:
                    print >> sys.stderr, "ERROR:", ex
                if not chunk:
                    break
                chunks.append(chunk)
            if self.reconnect:
                if DEBUG:
                    print >> sys.stderr, "Reconnecting..."
                self.close()
                self.socket = AdbClient.connect(self.hostname, self.port, self.timeout)
                self.__setTransport()
            return ''.join(chunks)
        else:
            self.__send('shell:')
            # sin = self.socket.makefile("rw")
            # sout = self.socket.makefile("r")
            # return (sin, sin)
            sout = adbClient.socket.makefile("r")
            return sout

    def getRestrictedScreen(self):
        ''' Gets C{mRestrictedScreen} values from dumpsys. This is a method to obtain display dimensions '''

        rsRE = re.compile('\s*mRestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<w>\d+)x(?P<h>\d+)')
        for line in self.shell('dumpsys window').splitlines():
            m = rsRE.match(line)
            if m:
                return m.groups()
        raise RuntimeError("Couldn't find mRestrictedScreen in 'dumpsys window'")

    def getDisplayInfo(self):
        self.__checkTransport()
        displayInfo = self.getLogicalDisplayInfo()
        if displayInfo:
            return displayInfo
        displayInfo = self.getPhysicalDisplayInfo()
        if displayInfo:
            return displayInfo
        raise RuntimeError("Couldn't find display info in 'wm size', 'dumpsys display' or 'dumpsys window'")

    def getLogicalDisplayInfo(self):
        '''
        Gets C{mDefaultViewport} and then C{deviceWidth} and C{deviceHeight} values from dumpsys.
        This is a method to obtain display logical dimensions and density
        '''

        self.__checkTransport()
        logicalDisplayRE = re.compile(
            '.*DisplayViewport\{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')
        for line in self.shell('dumpsys display').splitlines():
            m = logicalDisplayRE.search(line, 0)
            if m:
                self.__displayInfo = {}
                for prop in ['width', 'height', 'orientation']:
                    self.__displayInfo[prop] = int(m.group(prop))
                for prop in ['density']:
                    d = self.__getDisplayDensity(None, strip=True, invokeGetPhysicalDisplayIfNotFound=True)
                    if d:
                        self.__displayInfo[prop] = d
                    else:
                        # No available density information
                        self.__displayInfo[prop] = -1.0
                return self.__displayInfo
        return None

    def getPhysicalDisplayInfo(self):
        ''' Gets C{mPhysicalDisplayInfo} values from dumpsys. This is a method to obtain display dimensions and density'''

        self.__checkTransport()
        phyDispRE = re.compile('Physical size: (?P<width>\d+)x(?P<height>\d+).*Physical density: (?P<density>\d+)', re.DOTALL)
        m = phyDispRE.search(self.shell('wm size; wm density'))
        if m:
            displayInfo = {}
            for prop in ['width', 'height']:
                displayInfo[prop] = int(m.group(prop))
            for prop in ['density']:
                displayInfo[prop] = float(m.group(prop))
            return displayInfo

        phyDispRE = re.compile(
            '.*PhysicalDisplayInfo{(?P<width>\d+) x (?P<height>\d+), .*, density (?P<density>[\d.]+).*')
        for line in self.shell('dumpsys display').splitlines():
            m = phyDispRE.search(line, 0)
            if m:
                displayInfo = {}
                for prop in ['width', 'height']:
                    displayInfo[prop] = int(m.group(prop))
                for prop in ['density']:
                    # In mPhysicalDisplayInfo density is already a factor, no need to calculate
                    displayInfo[prop] = float(m.group(prop))
                return displayInfo

        # This could also be mSystem or mOverscanScreen
        phyDispRE = re.compile('\s*mUnrestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<width>\d+)x(?P<height>\d+)')
        # This is known to work on older versions (i.e. API 10) where mrestrictedScreen is not available
        dispWHRE = re.compile('\s*DisplayWidth=(?P<width>\d+) *DisplayHeight=(?P<height>\d+)')
        for line in self.shell('dumpsys window').splitlines():
            m = phyDispRE.search(line, 0)
            if not m:
                m = dispWHRE.search(line, 0)
            if m:
                displayInfo = {}
                for prop in ['width', 'height']:
                    displayInfo[prop] = int(m.group(prop))
                for prop in ['density']:
                    d = self.__getDisplayDensity(None, strip=True, invokeGetPhysicalDisplayIfNotFound=False)
                    if d:
                        displayInfo[prop] = d
                    else:
                        # No available density information
                        displayInfo[prop] = -1.0
                return displayInfo

    def __getProp(self, key, strip=True):
        if DEBUG:
            print >> sys.stderr, "__getProp(%s, %s)" % (key, strip)
        prop = self.shell('getprop %s' % key)
        if strip:
            prop = prop.rstrip('\r\n')
        if DEBUG:
            print >> sys.stderr, "    __getProp: returning '%s'" % prop
        return prop

    def __getDisplayWidth(self, key, strip=True):
        if self.__displayInfo and 'width' in self.__displayInfo:
            return self.__displayInfo['width']
        return self.getDisplayInfo()['width']

    def __getDisplayHeight(self, key, strip=True):
        if self.__displayInfo and 'height' in self.__displayInfo:
            return self.__displayInfo['height']
        return self.getDisplayInfo()['height']

    def __getDisplayOrientation(self, key, strip=True):
        if self.__displayInfo and 'orientation' in self.__displayInfo:
            return self.__displayInfo['orientation']
        displayInfo = self.getDisplayInfo()
        if 'orientation' in displayInfo:
            return displayInfo['orientation']
        # Fallback method to obtain the orientation
        # See https://github.com/dtmilano/AndroidViewClient/issues/128
        surfaceOrientationRE = re.compile('SurfaceOrientation:\s+(\d+)')
        output = self.shell('dumpsys input')
        m = surfaceOrientationRE.search(output)
        if m:
            return int(m.group(1))
        # We couldn't obtain the orientation
        return -1

    def __getDisplayDensity(self, key, strip=True, invokeGetPhysicalDisplayIfNotFound=True):
        if self.__displayInfo and 'density' in self.__displayInfo:  # and self.__displayInfo['density'] != -1: # FIXME: need more testing
            return self.__displayInfo['density']
        BASE_DPI = 160.0
        d = self.getProperty('ro.sf.lcd_density', strip)
        if d:
            return float(d) / BASE_DPI
        d = self.getProperty('qemu.sf.lcd_density', strip)
        if d:
            return float(d) / BASE_DPI
        if invokeGetPhysicalDisplayIfNotFound:
            return self.getPhysicalDisplayInfo()['density']
        return -1.0

    def getSystemProperty(self, key, strip=True):
        self.__checkTransport()
        return self.getProperty(key, strip)

    def getProperty(self, key, strip=True):
        ''' Gets the property value for key '''

        self.__checkTransport()
        import collections
        MAP_PROPS = collections.OrderedDict([
            (re.compile('display.width'), self.__getDisplayWidth),
            (re.compile('display.height'), self.__getDisplayHeight),
            (re.compile('display.density'), self.__getDisplayDensity),
            (re.compile('display.orientation'), self.__getDisplayOrientation),
            (re.compile('.*'), self.__getProp),
        ])
        '''Maps properties key values (as regexps) to instance methods to obtain its values.'''

        for kre in MAP_PROPS.keys():
            if kre.match(key):
                return MAP_PROPS[kre](key=key, strip=strip)
        raise ValueError("key='%s' does not match any map entry")

    def getSdkVersion(self):
        '''
        Gets the SDK version.
        '''

        self.__checkTransport()
        return self.build[VERSION_SDK_PROPERTY]

    def press(self, name, eventType=DOWN_AND_UP):
        self.__checkTransport()
        if isinstance(name, unicode):
            name = name.decode('ascii', errors='replace')
        cmd = 'input keyevent %s' % name
        if DEBUG:
            print >> sys.stderr, "press(%s)" % cmd
        self.shell(cmd)

    def longPress(self, name, duration=0.5, dev='/dev/input/event0', scancode=0, repeat=1):
        self.__checkTransport()
        # WORKAROUND:
        # Using 'input keyevent --longpress POWER' does not work correctly in
        # KitKat (API 19), it sends a short instead of a long press.
        # This uses the events instead, but it may vary from device to device.
        # The events sent are device dependent and may not work on other devices.
        # If this does not work on your device please do:
        #     $ adb shell getevent -l
        # and post the output to https://github.com/dtmilano/AndroidViewClient/issues
        # specifying the device and API level.
        if name[0:4] == 'KEY_':
            name = name[4:]
        # FIXME:
        # Most of the keycodes are in KEY_MAP so it's very unlikely that the longpress event
        # is sent via `input keyevent ...` (look next if)
        if name in KEY_MAP:
            self.shell('sendevent %s 1 %d 1' % (dev, KEY_MAP[name]))
            self.shell('sendevent %s 0 0 0' % dev)
            for _ in range(repeat):
                self.shell('sendevent %s 4 4 %d' % (dev, scancode))
                self.shell('sendevent %s 0 0 0' % dev)
            time.sleep(duration)
            self.shell('sendevent %s 1 %d 0' % (dev, KEY_MAP[name]))
            self.shell('sendevent %s 0 0 0' % dev)
            return

        version = self.getSdkVersion()
        if version >= 19:
            cmd = 'input keyevent --longpress %s' % name
            if DEBUG:
                print >> sys.stderr, "longPress(%s)" % cmd
            self.shell(cmd)
        else:
            raise RuntimeError("longpress: not supported for API < 19 (version=%d)" % version)

    def startActivity(self, component=None, flags=None, uri=None):
        self.__checkTransport()
        cmd = 'am start'
        if component:
            cmd += ' -n %s' % component
        if flags:
            cmd += ' -f %s' % flags
        if uri:
            cmd += ' %s' % uri
        if DEBUG:
            print >> sys.stderr, "Starting activity: %s" % cmd
        out = self.shell(cmd)
        if re.search(r"(Error type)|(Error: )|(Cannot find 'App')", out, re.IGNORECASE | re.MULTILINE):
            raise RuntimeError(out)

    def takeSnapshot(self, reconnect=False):
        '''
        Takes a snapshot of the device and return it as a PIL Image.
        '''

        if PROFILE:
            profileStart()

        global PIL_AVAILABLE
        if not PIL_AVAILABLE:
            try:
                global Image
                from PIL import Image
                PIL_AVAILABLE = True
            except:
                raise Exception("You have to install PIL to use takeSnapshot()")

        sdk_version = self.getSdkVersion()
        USE_ADB_FRAMEBUFFER_METHOD = (sdk_version < 14 or sdk_version >= 23)
        if USE_ADB_FRAMEBUFFER_METHOD:
            self.__checkTransport()

            self.__send('framebuffer:', checkok=True, reconnect=False)
            # case 1: // version
            #           return 12; // bpp, size, width, height, 4*(length, offset)
            received = self.__receive(1 * 4 + 12 * 4)
            (version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, glen, aoffset,
             alen) = struct.unpack(
                '<' + 'L' * 13, received)
            if DEBUG:
                print >> sys.stderr, "    takeSnapshot:", (
                    version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, glen, aoffset, alen)
            offsets = {roffset: 'R', goffset: 'G', boffset: 'B'}
            if bpp == 32:
                if alen != 0:
                    offsets[aoffset] = 'A'
                else:
                    warnings.warn('''framebuffer is specified as 32bpp but alpha length is 0''')
            argMode = ''.join([offsets[o] for o in sorted(offsets)])
            if DEBUG:
                print >> sys.stderr, "    takeSnapshot:", (
                    version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, blen, aoffset, alen,
                    argMode)
            if argMode == 'BGRA':
                argMode = 'RGBA'
            if bpp == 16:
                mode = 'RGB'
                argMode += ';16'
            else:
                mode = argMode
            self.__send('\0', checkok=False, reconnect=False)
            if DEBUG:
                print >> sys.stderr, "    takeSnapshot: reading %d bytes" % (size)
            received = self.__receive(size)
            if reconnect:
                self.socket = AdbClient.connect(self.hostname, self.port, self.timeout)
                self.__setTransport()
            if DEBUG:
                print >> sys.stderr, "    takeSnapshot: Image.frombuffer(%s, %s, %s, %s, %s, %s, %s)" % (
                    mode, (width, height), 'data', 'raw', argMode, 0, 1)
            image = Image.frombuffer(mode, (width, height), received, 'raw', argMode, 0, 1)
        else:
            # ALTERNATIVE_METHOD: screencap
            received = self.shell('/system/bin/screencap -p').replace("\r\n", "\n")
            if not received:
                raise RuntimeError('"/system/bin/screencap -p" result was empty')
            stream = StringIO.StringIO(received)
            try:
                image = Image.open(stream)
            except IOError, ex:
                print >> sys.stderr, ex
                print >> sys.stderr, repr(stream)
                print >> sys.stderr, repr(received)
                raise RuntimeError('Cannot convert stream to image: ' + ex.message)

        # Just in case let's get the real image size
        (w, h) = image.size
        if w == self.display['height'] and h == self.display['width']:
            # FIXME: We are not catching the 180 degrees rotation here
            if 'orientation' in self.display:
                r = (0, 90, 180, -90)[self.display['orientation']]
            else:
                r = 90
            image = image.rotate(r, expand=1).resize((h, w))

        if PROFILE:
            profileEnd()
        return image

    def __transformPointByOrientation(self, (x, y), orientationOrig, orientationDest):
        if orientationOrig != orientationDest:
            if orientationDest == 1:
                _x = x
                x = self.display['width'] - y
                y = _x
            elif orientationDest == 3:
                _x = x
                x = y
                y = self.display['height'] - _x
        return (x, y)

    def touch(self, x, y, orientation=-1, eventType=DOWN_AND_UP):
        if DEBUG_TOUCH:
            print >> sys.stderr, "touch(x=", x, ", y=", y, ", orientation=", orientation, ", eventType=", eventType, ")"
        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        self.shell(
            'input tap %d %d' % self.__transformPointByOrientation((x, y), orientation, self.display['orientation']))

    def touchDip(self, x, y, orientation=-1, eventType=DOWN_AND_UP):
        if DEBUG_TOUCH:
            print >> sys.stderr, "touchDip(x=", x, ", y=", y, ", orientation=", orientation, ", eventType=", eventType, ")"
        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        x = x * self.display['density']
        y = y * self.display['density']
        self.touch(x, y, orientation, eventType)

    def longTouch(self, x, y, duration=2000, orientation=-1):
        '''
        Long touches at (x, y)

        @param duration: duration in ms
        @param orientation: the orientation (-1: undefined)

        This workaround was suggested by U{HaMi<http://stackoverflow.com/users/2571957/hami>}
        '''

        self.__checkTransport()
        self.drag((x, y), (x, y), duration, orientation)

    def drag(self, (x0, y0), (x1, y1), duration, steps=1, orientation=-1):
        '''
        Sends drag event in PX (actually it's using C{input swipe} command).

        @param (x0, y0): starting point in PX
        @param (x1, y1): ending point in PX
        @param duration: duration of the event in ms
        @param steps: number of steps (currently ignored by @{input swipe})
        @param orientation: the orientation (-1: undefined)
        '''

        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        (x0, y0) = self.__transformPointByOrientation((x0, y0), orientation, self.display['orientation'])
        (x1, y1) = self.__transformPointByOrientation((x1, y1), orientation, self.display['orientation'])

        version = self.getSdkVersion()
        if version <= 15:
            raise RuntimeError('drag: API <= 15 not supported (version=%d)' % version)
        elif version <= 17:
            self.shell('input swipe %d %d %d %d' % (x0, y0, x1, y1))
        else:
            self.shell('input touchscreen swipe %d %d %d %d %d' % (x0, y0, x1, y1, duration))

    def dragDip(self, (x0, y0), (x1, y1), duration, steps=1, orientation=-1):
        '''
        Sends drag event in DIP (actually it's using C{input swipe} command.

        @param (x0, y0): starting point in DIP
        @param (x1, y1): ending point in DIP
        @param duration: duration of the event in ms
        @param steps: number of steps (currently ignored by @{input swipe}
        '''

        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        density = self.display['density'] if self.display['density'] > 0 else 1
        x0 = x0 * density
        y0 = y0 * density
        x1 = x1 * density
        y1 = y1 * density
        self.drag((x0, y0), (x1, y1), duration, steps, orientation)

    def type(self, text):
        self.__checkTransport()
        if type(text) is str:
            escaped = text.replace('%s', '\\%s')
            encoded = escaped.replace(' ', '%s')
        else:
            encoded = str(text);
        #FIXME find out which characters can be dangerous,
        # for exmaple not worst idea to escape " 
        self.shell(u'input text "%s"' % encoded)

    def wake(self):
        self.__checkTransport()
        if not self.isScreenOn():
            self.shell('input keyevent POWER')

    def isLocked(self):
        '''
        Checks if the device screen is locked.

        @return True if the device screen is locked
        '''

        self.__checkTransport()
        lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        m = lockScreenRE.search(self.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise RuntimeError("Couldn't determine screen lock state")

    def isScreenOn(self):
        '''
        Checks if the screen is ON.

        @return True if the device screen is ON
        '''

        self.__checkTransport()
        screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = screenOnRE.search(self.shell('dumpsys window policy'))
        if m:
            return (m.group(1) == 'true')
        raise RuntimeError("Couldn't determine screen ON state")

    def unlock(self):
        '''
        Unlocks the screen of the device.
        '''

        self.__checkTransport()
        self.shell('input keyevent MENU')
        self.shell('input keyevent BACK')

    @staticmethod
    def percentSame(image1, image2):
        '''
        Returns the percent of pixels that are equal

        @author: catshoes
        '''

        # If the images differ in size, return 0% same.
        size_x1, size_y1 = image1.size
        size_x2, size_y2 = image2.size
        if (size_x1 != size_x2 or
                    size_y1 != size_y2):
            return 0

        # Images are the same size
        # Return the percent of pixels that are equal.
        numPixelsSame = 0
        numPixelsTotal = size_x1 * size_y1
        image1Pixels = image1.load()
        image2Pixels = image2.load()

        # Loop over all pixels, comparing pixel in image1 to image2
        for x in range(size_x1):
            for y in range(size_y1):
                if (image1Pixels[x, y] == image2Pixels[x, y]):
                    numPixelsSame += 1

        return numPixelsSame / float(numPixelsTotal)

    @staticmethod
    def sameAs(image1, image2, percent=1.0):
        '''
        Compares 2 images

        @author: catshoes
        '''

        return (AdbClient.percentSame(image1, image2) >= percent)

    @staticmethod
    def imageInScreen(screen, image):
        '''
        Checks if image is on the screen

        :param screen: the screen image
        :param image: the partial image to look for
        :return: True or False

        @author: Perry Tsai <ripple0129@gmail.com>
        '''

        # To make sure image smaller than screen.
        size_x1, size_y1 = screen.size
        size_x2, size_y2 = image.size
        if size_x1 <= size_x2 or size_y1 <= size_y2:
            return 0

        # Load pixels.
        screenPixels = screen.load()
        imagePixels = image.load()

        # Loop over all pixels, if pixel image[0,0] same as pixel screen[x,y] do crop and compare
        for x in range(size_x1 - size_x2):
            for y in range(size_y1 - size_y2):
                if imagePixels[0, 0] == screenPixels[x, y]:
                    croppedScreen = screen.crop((x, y, x + size_x2, y + size_y2))
                    size_x3, size_y3 = croppedScreen.size
                    croppedPixels = croppedScreen.load()
                    for x in range(size_x3):
                        for y in range(size_y3):
                            if imagePixels[x, y] == croppedPixels[x, y]:
                                return True


    @staticmethod
    def compare(image1, image2, imageResult):
        COMPARE = '/usr/bin/compare'
        if os.path.isfile(COMPARE) and os.access(COMPARE, os.X_OK):
            result = subprocess.call([COMPARE, image1, image2, imageResult])
            if result != 2:
                return result == 0
            else:
                raise RuntimeError("ERROR running ImageMaigck's compare")
        else:
            raise RuntimeError("This method requires ImageMagick's compare to be installed.")

    def isKeyboardShown(self):
        '''
        Whether the keyboard is displayed.
        '''

        self.__checkTransport()
        dim = self.shell('dumpsys input_method')
        if dim:
            # FIXME: API >= 15 ?
            return "mInputShown=true" in dim
        return False

    def initDisplayProperties(self):
        self.__checkTransport()
        self.__displayInfo = None
        self.display['width'] = self.getProperty('display.width')
        self.display['height'] = self.getProperty('display.height')
        self.display['density'] = self.getProperty('display.density')
        self.display['orientation'] = self.getProperty('display.orientation')

    def log(self, tag, message, priority='D', verbose=False):
        if DEBUG_LOG:
            print >> sys.stderr, "log(tag=%s, message=%s, priority=%s, verbose=%s)" % (tag, message, priority, verbose)
        self.__checkTransport()
        message = self.substituteDeviceTemplate(message)
        if verbose or priority == 'V':
            print >> sys.stderr, tag + ':', message
        self.shell('log -p %c -t "%s" %s' % (priority, tag, message))

    class __Log():
        '''
        Log class to simulate C{android.util.Log}
        '''

        def __init__(self, adbClient):
            self.adbClient = adbClient

        def __getattr__(self, attr):
            '''
            Returns the corresponding log method or @C{AttributeError}.
            '''

            if attr in ['v', 'd', 'i', 'w', 'e']:
                return lambda tag, message, verbose: self.adbClient.log(tag, message, priority=attr.upper(),
                                                                        verbose=verbose)
            raise AttributeError(self.__class__.__name__ + ' has no attribute "%s"' % attr)

    def getSystemService(self, name):
        if name == WIFI_SERVICE:
            return WifiManager(self)

    def getWindows(self):
        self.__checkTransport()
        windows = {}
        dww = self.shell('dumpsys window windows')
        if DEBUG_WINDOWS: print >> sys.stderr, dww
        lines = dww.splitlines()
        widRE = re.compile('^ *Window #%s Window\{%s (u\d+ )?%s?.*\}:' %
                           (_nd('num'), _nh('winId'), _ns('activity', greedy=True)))
        currentFocusRE = re.compile('^  mCurrentFocus=Window\{%s .*' % _nh('winId'))
        viewVisibilityRE = re.compile(' mViewVisibility=0x%s ' % _nh('visibility'))
        # This is for 4.0.4 API-15
        containingFrameRE = re.compile('^   *mContainingFrame=\[%s,%s\]\[%s,%s\] mParentFrame=\[%s,%s\]\[%s,%s\]' %
                                       (_nd('cx'), _nd('cy'), _nd('cw'), _nd('ch'), _nd('px'), _nd('py'), _nd('pw'),
                                        _nd('ph')))
        contentFrameRE = re.compile('^   *mContentFrame=\[%s,%s\]\[%s,%s\] mVisibleFrame=\[%s,%s\]\[%s,%s\]' %
                                    (_nd('x'), _nd('y'), _nd('w'), _nd('h'), _nd('vx'), _nd('vy'), _nd('vx1'),
                                     _nd('vy1')))
        # This is for 4.1 API-16
        framesRE = re.compile('^   *Frames: containing=\[%s,%s\]\[%s,%s\] parent=\[%s,%s\]\[%s,%s\]' %
                              (_nd('cx'), _nd('cy'), _nd('cw'), _nd('ch'), _nd('px'), _nd('py'), _nd('pw'), _nd('ph')))
        contentRE = re.compile('^     *content=\[%s,%s\]\[%s,%s\] visible=\[%s,%s\]\[%s,%s\]' %
                               (_nd('x'), _nd('y'), _nd('w'), _nd('h'), _nd('vx'), _nd('vy'), _nd('vx1'), _nd('vy1')))
        policyVisibilityRE = re.compile('mPolicyVisibility=%s ' % _ns('policyVisibility', greedy=True))

        currentFocus = None

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
                px = 0
                py = 0
                visibility = -1
                policyVisibility = 0x0

                for l2 in range(l + 1, len(lines)):
                    m = widRE.search(lines[l2])
                    if m:
                        l += (l2 - 1)
                        break
                    m = viewVisibilityRE.search(lines[l2])
                    if m:
                        visibility = int(m.group('visibility'))
                        if DEBUG_COORDS: print >> sys.stderr, "getWindows: visibility=", visibility
                    if self.build[VERSION_SDK_PROPERTY] >= 17:
                        wvx, wvy = (0, 0)
                        wvw, wvh = (0, 0)
                    if self.build[VERSION_SDK_PROPERTY] >= 16:
                        m = framesRE.search(lines[l2])
                        if m:
                            px, py = obtainPxPy(m)
                            m = contentRE.search(lines[l2 + 1])
                            if m:
                                # FIXME: the information provided by 'dumpsys window windows' in 4.2.1 (API 16)
                                # when there's a system dialog may not be correct and causes the View coordinates
                                # be offset by this amount, see
                                # https://github.com/dtmilano/AndroidViewClient/issues/29
                                wvx, wvy = obtainVxVy(m)
                                wvw, wvh = obtainVwVh(m)
                    elif self.build[VERSION_SDK_PROPERTY] == 15:
                        m = containingFrameRE.search(lines[l2])
                        if m:
                            px, py = obtainPxPy(m)
                            m = contentFrameRE.search(lines[l2 + 1])
                            if m:
                                wvx, wvy = obtainVxVy(m)
                                wvw, wvh = obtainVwVh(m)
                    elif self.build[VERSION_SDK_PROPERTY] == 10:
                        m = containingFrameRE.search(lines[l2])
                        if m:
                            px, py = obtainPxPy(m)
                            m = contentFrameRE.search(lines[l2 + 1])
                            if m:
                                wvx, wvy = obtainVxVy(m)
                                wvw, wvh = obtainVwVh(m)
                    else:
                        warnings.warn("Unsupported Android version %d" % self.build[VERSION_SDK_PROPERTY])

                    # print >> sys.stderr, "Searching policyVisibility in", lines[l2]
                    m = policyVisibilityRE.search(lines[l2])
                    if m:
                        policyVisibility = 0x0 if m.group('policyVisibility') == 'true' else 0x8

                windows[winId] = Window(num, winId, activity, wvx, wvy, wvw, wvh, px, py, visibility + policyVisibility)
            else:
                m = currentFocusRE.search(lines[l])
                if m:
                    currentFocus = m.group('winId')

        if currentFocus in windows and windows[currentFocus].visibility == 0:
            if DEBUG_COORDS:
                print >> sys.stderr, "getWindows: focus=", currentFocus
                print >> sys.stderr, "getWindows:", windows[currentFocus]
            windows[currentFocus].focused = True

        return windows

    def getFocusedWindow(self):
        '''
        Gets the focused window.

        @return: The focused L{Window}.
        '''

        for window in self.getWindows().values():
            if window.focused:
                return window
        return None

    def getFocusedWindowName(self):
        '''
        Gets the focused window name.

        This is much like monkeyRunner's C{HierarchyView.getWindowName()}

        @return: The focused window name
        '''

        window = self.getFocusedWindow()
        if window:
            return window.activity
        return None

    def getTopActivityNameAndPid(self):
        dat = self.shell('dumpsys activity top')
        lines = dat.splitlines()
        activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.]+) \w+ pid=(\d+)')
        m = activityRE.search(lines[1])
        if m:
            return (m.group(1), m.group(2), m.group(3))
        else:
            warnings.warn("NO MATCH:" + lines[1])
            return None

    def getTopActivityName(self):
        tanp = self.getTopActivityNameAndPid()
        if tanp:
            return tanp[0] + '/' + tanp[1]
        else:
            return None

    def substituteDeviceTemplate(self, template):
        serialno = self.serialno.replace('.', '_').replace(':', '-')
        focusedWindowName = self.getFocusedWindowName().replace('/', '-').replace('.', '_')
        timestamp = datetime.datetime.now().isoformat()
        osName = platform.system()
        if osName.startswith('Windows'):  # ':' not supported in filenames
            timestamp.replace(':', '_')
        _map = {
            'serialno': serialno,
            'focusedwindowname': focusedWindowName,
            'timestamp': timestamp
        }
        return string.Template(template).substitute(_map)

    def dumpsys(self, subcommand, args):
        return Dumpsys(self, subcommand, args)


if __name__ == '__main__':
    adbClient = AdbClient(os.environ['ANDROID_SERIAL'])
    INTERACTIVE = False
    if INTERACTIVE:
        sout = adbClient.shell()
        prompt = re.compile(".+@android:(.*) [$#] \r\r\n")
        while True:
            try:
                cmd = raw_input('adb $ ')
            except EOFError:
                break
            if cmd == 'exit':
                break
            adbClient.socket.__send(cmd + "\r\n")
            sout.readline(4096)  # eat first line, which is the command
            while True:
                line = sout.readline(4096)
                if prompt.match(line):
                    break
                print line,
                if not line:
                    break

        print "\nBye"
    else:
        print 'date:', adbClient.shell('date')
