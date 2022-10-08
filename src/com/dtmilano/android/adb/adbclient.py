# coding=utf-8
'''
Copyright (C) 2012-2022  Diego Torres Milano
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

from __future__ import print_function

import subprocess
import threading
import unicodedata
from typing import Optional

from com.dtmilano.android.adb.dumpsys import Dumpsys

__version__ = '21.17.0'

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
import io as StringIO
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
except KeyError:
    HOSTNAME = 'localhost'

try:
    PORT = int(os.environ['ANDROID_ADB_SERVER_PORT'])
except KeyError:
    PORT = 5037

OKAY = b'OKAY'
FAIL = b'FAIL'

UP = 0
DOWN = 1
DOWN_AND_UP = 2

TIMEOUT = 15

WIFI_SERVICE = b'wifi'

# some device properties
VERSION_SDK_PROPERTY = 'ro.build.version.sdk'
VERSION_RELEASE_PROPERTY = 'ro.build.version.release'


class Device:
    @staticmethod
    def factory(_str):
        _str = _str.decode('utf-8')
        if DEBUG:
            print("Device.factory(", _str, ")", file=sys.stderr)
            print("   _str=", repr(_str), file=sys.stderr)
            print("   _str=", _str.replace(' ', '_'), file=sys.stderr)
        values = _str.split(None, 2)
        if DEBUG:
            print("values=", values, file=sys.stderr)
        return Device(*values)

    def __init__(self, serialno, status, qualifiers=None):
        self.serialno = serialno
        self.status = status
        self.qualifiers = qualifiers.split(None) if qualifiers else None

    def has_qualifier(self, qualifier):
        return self.qualifiers and qualifier in self.qualifiers

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
        print("UNKNOWN WIFI STATE:", state, file=sys.stderr)
        return self.WIFI_STATE_UNKNOWN


class Timer:
    def __init__(self, timeout, handler, args):
        self.timer = threading.Timer(timeout, handler, args)

    def start(self):
        self.timer.start()

    def cancel(self):
        self.timer.cancel()

    class TimeoutException(Exception):
        pass


def connect(hostname, port, timeout=TIMEOUT):
    """
    Connect to ADB server.
    :param hostname: the hostname
    :param port: the port
    :param timeout: the timeout in seconds
    :return:
    """

    if DEBUG:
        print("AdbClient.connect(%s, %s, %s)" % (hostname, port, timeout), file=sys.stderr)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_LINGER: Idea proposed by kysersozelee (#173)
    l_onoff = 1
    l_linger = 0
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                 struct.pack('ii', l_onoff, l_linger))
    s.settimeout(timeout)
    try:
        s.connect((hostname, port))
    except socket.error as ex:
        raise RuntimeError("ERROR: Connecting to %s:%d: %s.\nIs adb running on your computer?" % (s, port, ex))
    return s


class AdbClient:
    UP = UP
    DOWN = DOWN
    DOWN_AND_UP = DOWN_AND_UP

    def __init__(self, serialno=None, hostname=HOSTNAME, port=PORT, settransport=True, reconnect=True,
                 ignoreversioncheck=False, timeout=TIMEOUT, connect=connect):
        self.Log = AdbClient.__Log(self)

        self.serialno = serialno
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.__connect = connect
        self.timerId = -1
        self.timers = {}

        self.reconnect = reconnect
        self.socket = connect(self.hostname, self.port, self.timeout)

        self.lock = threading.RLock()

        self.checkVersion(ignoreversioncheck)

        self.build = {}
        ''' Build properties '''

        self.__displayInfo = None
        ''' Cached display info. Reset it to C{None} to force refetching display info '''

        self.display = {}
        ''' The map containing the device's physical display properties: width, height and density '''

        self.screenshot_number = 1
        ''' The screenshot number count '''

        self.isTransportSet = False
        if settransport and serialno is not None:
            self.__setTransport(timeout=timeout)
            self.build[VERSION_SDK_PROPERTY] = int(self.__getProp(VERSION_SDK_PROPERTY))
            self.initDisplayProperties()

    def __timeoutHandler(self, timerId, description=None):
        if DEBUG:
            print("\nTIMEOUT HANDLER", timerId, ':', description, file=sys.stderr)
        self.timers[timerId] = "EXPIRED"
        raise Timer.TimeoutException("Timer %s has expired" % description)

    def setTimer(self, timeout, description=None):
        """
        Sets a timer.

        :param description:
        :param timeout: timeout in seconds
        :return: the timerId
        """
        self.timerId += 1
        timer = Timer(timeout, self.__timeoutHandler, (self.timerId, description))
        timer.start()
        self.timers[self.timerId] = timer
        return self.timerId

    def cancelTimer(self, timerId):
        if DEBUG:
            print("Canceling timer with ID=%s" % timerId, file=sys.stderr)
        if timerId not in self.timers:
            print("timers does not contain a timer with ID=%s" % timerId, file=sys.stderr)
            print("available timers:", file=sys.stderr)
            for t in self.timers:
                print("   id=", t, file=sys.stderr)
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

    def close(self):
        if DEBUG:
            print("Closing socket...", self.socket, file=sys.stderr)
        if self.socket:
            self.socket.close()

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def __send(self, msg, checkok=True, reconnect=False):
        if DEBUG:
            print("__send(%s, checkok=%s, reconnect=%s)" % (msg, checkok, reconnect), file=sys.stderr)
        if not re.search('^host:', msg):
            if not self.isTransportSet:
                self.__setTransport()
        else:
            self.checkConnected()

        b = bytearray(msg, 'utf-8')
        timerId = self.setTimer(timeout=self.timeout, description="send")
        try:
            self.socket.send(b'%04X%s' % (len(b), b))
        except Exception as ex:
            raise RuntimeError("Error sending %d bytes" % len(b), ex)
        finally:
            self.cancelTimer(timerId)

        if checkok:
            self.__checkOk()

        if reconnect:
            if DEBUG:
                print("    __send: reconnecting", file=sys.stderr)
            self.socket = self.__connect(self.hostname, self.port, self.timeout)
            self.__setTransport()

    def __receive(self, nob=None, sock=None):
        if DEBUG:
            print("🟨 __receive(nob=%s)" % nob, file=sys.stderr)
        if not sock:
            sock = self.socket
        self.checkConnected(sock)
        timerId = self.setTimer(timeout=self.timeout, description="recv")
        try:
            if nob is None:
                nob = int(sock.recv(4), 16)
            if DEBUG:
                print("🟨    __receive: receiving", nob, "bytes", file=sys.stderr)
            recv = bytearray(nob)
            mview = memoryview(recv)
            nr = 0
            while nr < nob:
                l = sock.recv_into(mview, len(mview))
                if DEBUG:
                    print("🟨    __receive: recv_into(mview, %d):" % len(mview), file=sys.stderr)
                    print("🟨    __receive: l=", l, "nr=", nr, file=sys.stderr)
                    print("🟨    __receive: timer=", self.timers[timerId], file=sys.stderr)
                mview = mview[l:]
                nr += l
                if self.timers[timerId] == 'EXPIRED':
                    raise Timer.TimeoutException('%d EXPIRED' % timerId)
        finally:
            self.cancelTimer(timerId)
        if DEBUG:
            print("🟨    __receive: returning len=", len(recv), file=sys.stderr)
            print("🟨    __receive: '%s'" % repr(recv), file=sys.stderr)
        return recv

    def __checkOk(self, sock=None):
        if DEBUG:
            print("__checkOk()", file=sys.stderr)
        if not sock:
            sock = self.socket
        self.checkConnected(sock=sock)

        timerId = self.setTimer(timeout=self.timeout, description="checkOK")
        try:
            recv = sock.recv(4)
        finally:
            self.cancelTimer(timerId)

        if DEBUG:
            print("    __checkOk: recv(4)=", repr(recv), file=sys.stderr)

        timerId = self.setTimer(timeout=self.timeout, description="checkOK")
        try:
            if recv != OKAY:
                error = sock.recv(1024)
                if error.startswith(b'0049'):
                    raise RuntimeError(
                        "ERROR: This computer is unauthorized. Please check the confirmation dialog on your device.")
                else:
                    raise RuntimeError("ERROR: %s %s" % (repr(recv), error))
        finally:
            self.cancelTimer(timerId)
        if DEBUG:
            print("    __checkOk: returning True", file=sys.stderr)
        return True

    def checkConnected(self, sock=None):
        if DEBUG:
            print("checkConnected()", file=sys.stderr)
        if not sock:
            sock = self.socket
        if not sock:
            raise RuntimeError("ERROR: Not connected")
        if DEBUG:
            print("    checkConnected: returning True", file=sys.stderr)
        return True

    def checkVersion(self, ignoreversioncheck=False, reconnect=True):
        if DEBUG:
            print("checkVersion(reconnect=%s)   ignoreversioncheck=%s" % (reconnect, ignoreversioncheck),
                  file=sys.stderr)
        self.__send('host:version', reconnect=False)
        # HACK: MSG_WAITALL not available on windows
        # version = self.socket.recv(8, socket.MSG_WAITALL)
        version = self.__readExactly(self.socket, 8)

        VALID_ADB_VERSIONS = ["00040029", "00040028", "00040027", "00040024", "00040023", "00040020", "0004001f"]

        if not (version in VALID_ADB_VERSIONS) and not ignoreversioncheck:
            raise RuntimeError(
                "ERROR: Incorrect ADB server version %s (expecting one of %s)" % (version, VALID_ADB_VERSIONS))
        if reconnect:
            self.socket = self.__connect(self.hostname, self.port, self.timeout)

    def __setTransport(self, timeout=60):
        if DEBUG:
            print("__setTransport()", file=sys.stderr)
        if not self.serialno:
            raise ValueError("serialno not set, empty or None")
        self.checkConnected()
        serialnoRE = re.compile(self.serialno)
        found = False
        devices = self.getDevices()
        if len(devices) == 0 and timeout > 0:
            print("Empty device list, will wait %s secs for devices to appear" % self.timeout, file=sys.stderr)
            # Sets the timeout to 5 to be able to loop while trying to receive new devices being added
            _s = self.__connect(self.hostname, self.port, timeout=5)
            msg = 'host:track-devices'
            b = bytearray(msg, 'utf-8')
            timerId = self.setTimer(timeout=timeout, description="setTransport")
            try:
                _s.send(b'%04X%s' % (len(b), b))
                self.__checkOk(sock=_s)
                # eat '0000'
                _s.recv(4)
                found = False
                while not found:
                    sys.stderr.write("o")
                    sys.stderr.flush()
                    try:
                        for line in _s.recv(1024).splitlines():
                            # skip first 4 bytes containing the response size
                            device = Device.factory(line[4:])
                            if device.status == 'device':
                                devices.append(device)
                                # this looks like a bug, we skip serialno matching here
                                found = True
                                self.serialno = device.serialno
                                break
                        if found:
                            break
                    except socket.timeout as ex:
                        # we continue trying until timer times out
                        pass
                    finally:
                        time.sleep(3)
                    if DEBUG:
                        print("Checking if timer %d is EXPIRED:" % timerId, self.timers[timerId], file=sys.stderr)
                    if self.timers[timerId] == "EXPIRED":
                        break
            finally:
                self.cancelTimer(timerId)
                _s.close()
                sys.stderr.write("\n")
                sys.stderr.flush()
        if len(devices) == 0:
            raise RuntimeError("ERROR: There are no connected devices")
        for device in devices:
            if serialnoRE.match(device.serialno):
                found = True
                # self.serialno could've been a regexp, we can't feed that to adb as a transport
                self.serialno = device.serialno
                break
            if device.has_qualifier(self.serialno):
                # self.serialno is a proper transport value, it could be more specific than device.serialno
                # For instance devpath/usbpath specifies exactly one device, while serialno might be the same
                # for reflashed devices.
                # The only flipside here is that we fail to pick one (first/random) device from possibly many
                # having the same qualifier (product: model: or device:) if they have different serials.
                # This could be fixed by some custom logic or using host:transport-id: support in newer and.
                found = True
                break
        if not found:
            raise RuntimeError("ERROR: couldn't find device that matches '%s' in %s" % (self.serialno, devices))

        msg = 'host:transport:%s' % self.serialno
        if DEBUG:
            print("    __setTransport: msg=", msg, file=sys.stderr)
        self.__send(msg, reconnect=False)
        self.isTransportSet = True

    def __checkTransport(self):
        if DEBUG:
            print("__checkTransport()", file=sys.stderr)
        if not self.isTransportSet:
            raise RuntimeError("ERROR: Transport is not set")

    def __readExactly(self, sock, size):
        if DEBUG:
            print("__readExactly(socket=%s, size=%d)" % (sock, size), file=sys.stderr)
        _buffer = bytearray(size)
        view = memoryview(_buffer)
        nb = 0
        while nb < size:
            l = sock.recv_into(view, len(view))
            view = view[l:]
            nb += l

        return _buffer.decode('utf-8')

    def getDevices(self):
        if DEBUG:
            print("getDevices()", file=sys.stderr)
        self.__send('host:devices-l', checkok=False)
        try:
            self.__checkOk()
        except RuntimeError as ex:
            print("**ERROR:", ex, file=sys.stderr)
            return None

        devices = []
        for line in self.__receive().splitlines():
            devices.append(Device.factory(line))
        self.socket = self.__connect(self.hostname, self.port, self.timeout)
        return devices

    def shell(self, _cmd=None, _convertOutputToString=True):
        if DEBUG:
            print("shell(_cmd=%s)" % _cmd, file=sys.stderr)
        self.__checkTransport()
        #
        # synchronized
        #
        with self.lock:
            if _cmd:
                self.__send('shell:%s' % _cmd, checkok=True, reconnect=False)
                chunks = []
                while True:
                    chunk = None
                    try:
                        chunk = self.socket.recv(4096)
                        if DEBUG:
                            print('🟣 chunk=%s' % chunk)
                    except Exception as ex:
                        print("ERROR:", ex, file=sys.stderr)
                    if not chunk:
                        break
                    chunks.append(chunk)
                if self.reconnect:
                    if DEBUG:
                        print("Reconnecting...", file=sys.stderr)
                    self.close()
                    self.socket = self.__connect(self.hostname, self.port, self.timeout)
                    self.__setTransport()
                if _convertOutputToString:
                    return b''.join(chunks).decode('utf-8')
                else:
                    return b''.join(chunks)
            else:
                self.__send('shell:')
                # sin = self.socket.makefile("rw")
                # sout = self.socket.makefile("r")
                # return (sin, sin)
                return adbClient.socket.makefile("r")

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
        """
        Gets C{mDefaultViewport} and then C{deviceWidth} and C{deviceHeight} values from dumpsys.
        This is a method to obtain display logical dimensions and density.
        Obtains the rotation from dumpsys.
        """

        self.__checkTransport()
        logicalDisplayRE = re.compile(
            r'.*DisplayViewport\{.*valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), '
            r'deviceHeight=(?P<height>\d+).*')
        predictedRotationRE = re.compile(r'.*mPredictedRotation=(?P<rotation>\d).*')
        for _line in self.shell('dumpsys display').splitlines():
            m = logicalDisplayRE.search(_line, pos=0)
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

        for _line in self.shell('dumpsys window displays').splitlines():
            m = predictedRotationRE.search(_line, pos=0)
            if m:
                self.__displayInfo['rotation'] = int(m.group('rotation'))

        if self.__displayInfo:
            return self.__displayInfo
        return None

    def getPhysicalDisplayInfo(self):
        ''' Gets C{mPhysicalDisplayInfo} values from dumpsys. This is a method to obtain display dimensions and density'''

        self.__checkTransport()
        phyDispRE = re.compile('Physical size: (?P<width>\d+)x(?P<height>\d+).*Physical density: (?P<density>\d+)',
                               re.DOTALL)
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
            print("__getProp(%s, %s)" % (key, strip), file=sys.stderr)
        prop = self.shell('getprop %s' % key)
        if strip:
            prop = prop.rstrip('\r\n')
        if DEBUG:
            print("    __getProp: returning '%s'" % prop, file=sys.stderr)
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

        for kre in list(MAP_PROPS.keys()):
            if kre.match(key):
                return MAP_PROPS[kre](key=key, strip=strip)
        raise ValueError("key='%s' does not match any map entry")

    def getSdkVersion(self):
        '''
        Gets the SDK version.
        '''

        self.__checkTransport()
        return self.build[VERSION_SDK_PROPERTY]

    def press(self, name, eventType=DOWN_AND_UP, repeat=1):
        self.__checkTransport()

        cmd = 'input keyevent %s' % name
        for _ in range(1, repeat):
            cmd += ' %s' % name
        if DEBUG:
            print("press(%s)" % cmd, file=sys.stderr)
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
                print("longPress(%s)" % cmd, file=sys.stderr)
            self.shell(cmd)
        else:
            raise RuntimeError("longpress: not supported for API < 19 (version=%d)" % version)

    def resolveActivity(self, package):
        version = self.getSdkVersion()
        if version < 24:
            raise RuntimeError(f'resolve-activity: not supported for API < 24 (version={version})')
        cmd = f'cmd package resolve-activity --brief {package}'
        lines = self.shell(cmd).splitlines()
        if len(lines) != 2:
            raise RuntimeError(f'resolve-activity: cannot resolve activity for package {package}')
        return lines[1]

    def startActivity(self, component=None, flags=None, uri=None, package=None):
        """
        Starts an Activity.
        If package is specified instead of component the corresponding MAIN activity for the package
        will be resolved and used.
        """
        self.__checkTransport()
        cmd = 'am start'
        if package and not component:
            version = self.getSdkVersion()
            if version >= 24:
                component = self.resolveActivity(package)
            else:
                component = self.dumpsys(Dumpsys.PACKAGE, package).package['main-activity']
        if component:
            cmd += ' -n %s' % component
        if flags:
            cmd += ' -f %s' % flags
        if uri:
            cmd += ' %s' % uri
        if DEBUG:
            print("Starting activity: %s" % cmd, file=sys.stderr)
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
            # case 2: // version
            #           return 13; // bpp, colorSpace, size, width, height, 4*(length, offset)
            # let's assume version==1 and change later if it's not
            received = self.__receive(1 * 4 + 12 * 4)
            (version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, glen, aoffset, alen) = \
                struct.unpack('<' + 'L' * 13, received)
            if version == 2:
                # receive one more
                received += self.__receive(4)
                (version, bpp, colorspace, size, width, height, roffset, rlen, boffset, blen, goffset, glen, aoffset,
                 alen) = struct.unpack('<' + 'L' * 14, received)
            if DEBUG:
                if version == 1:
                    print("    takeSnapshot:", (
                        version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, glen, aoffset, alen),
                          file=sys.stderr)
                elif version == 2:
                    print("    takeSnapshot:", (
                        version, bpp, colorspace, width, height, roffset, rlen, boffset, blen, goffset, glen, aoffset,
                        alen), file=sys.stderr)
                else:
                    print("    takeSnapshot: unknown version", version, file=sys.stderr)

            offsets = {roffset: 'R', goffset: 'G', boffset: 'B'}
            if bpp == 32:
                if alen != 0:
                    offsets[aoffset] = 'A'
                else:
                    warnings.warn('''framebuffer is specified as 32bpp but alpha length is 0''')
            argMode = ''.join([offsets[o] for o in sorted(offsets)])
            if DEBUG:
                if version == 1:
                    print("    takeSnapshot:", (
                        version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, blen, aoffset, alen,
                        argMode), file=sys.stderr)
                elif version == 2:
                    print("    takeSnapshot:", (
                        version, bpp, colorspace, size, width, height, roffset, rlen, boffset, blen, goffset, blen,
                        aoffset, alen,
                        argMode), file=sys.stderr)

            if argMode == 'BGRA':
                argMode = 'RGBA'
            if bpp == 16:
                mode = 'RGB'
                argMode += ';16'
            else:
                mode = argMode
            self.__send('\0', checkok=False, reconnect=False)
            if DEBUG:
                print("    takeSnapshot: reading %d bytes" % size, file=sys.stderr)
            received = self.__receive(size)
            if reconnect:
                self.socket = self.__connect(self.hostname, self.port, self.timeout)
                self.__setTransport()
            if DEBUG:
                print("    takeSnapshot: Image.frombuffer(%s, %s, %s, %s, %s, %s, %s)" % (
                    mode, (width, height), 'data', 'raw', argMode, 0, 1), file=sys.stderr)
            image = Image.frombuffer(mode, (width, height), received, 'raw', argMode, 0, 1)
        else:
            # ALTERNATIVE_METHOD: screencap
            received = self.shell('/system/bin/screencap -p', False).replace(b'\r\n', b'\n')
            if not received:
                raise RuntimeError('"/system/bin/screencap -p" result was empty')
            stream = StringIO.BytesIO(received)
            try:
                image = Image.open(stream)
            except IOError as ex:
                print(ex, file=sys.stderr)
                print(repr(stream), file=sys.stderr)
                print(repr(received), file=sys.stderr)
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
        self.screenshot_number += 1
        return image

    def imageToData(self, image, output_type=None):
        """
        Helps in cases where the Views cannot be identified.
        Returns the text found in the image and its bounding box.
        :param image: the image (i.e. from takeScreenshot())
        :param output_type: the output type (defualt: pytessearct.Output.DICT)
        :return: the data from the image
        """
        try:
            import pytessearct
        except ImportError:
            raise Exception("You have to install pytesseract to use imageToData()")
        if not output_type:
            output_type = pytessearct.Output.DICT
        return pytessearct.image_to_data(image, output_type=output_type)

    def __transformPointByOrientation(self, xxx_todo_changeme, orientationOrig, orientationDest):
        (x, y) = xxx_todo_changeme
        if orientationOrig != orientationDest:
            if orientationDest == 1:
                _x = x
                x = self.display['width'] - y
                y = _x
            elif orientationDest == 3:
                _x = x
                x = y
                y = self.display['height'] - _x
        return x, y

    def touch(self, x, y, orientation=-1, eventType=DOWN_AND_UP):
        if DEBUG_TOUCH:
            print("touch(x=", x, ", y=", y, ", orientation=", orientation, ", eventType=", eventType, ")",
                  file=sys.stderr)
        self.__checkTransport()
        if orientation == -1:
            orientation = self.display['orientation']
        version = self.getSdkVersion()
        if version > 10:
            self.shell(
                'input tap %d %d' % self.__transformPointByOrientation((x, y), orientation,
                                                                       self.display['orientation']))
        else:
            raise RuntimeError('drag: API <= 10 not supported (version=%d)' % version)

    def touchDip(self, x, y, orientation=-1, eventType=DOWN_AND_UP):
        if DEBUG_TOUCH:
            print("touchDip(x=", x, ", y=", y, ", orientation=", orientation, ", eventType=", eventType, ")",
                  file=sys.stderr)
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

    def drag(self, xxx_todo_changeme1, xxx_todo_changeme2, duration, steps=1, orientation=-1):
        """
        Sends drag event in PX (actually it's using C{input swipe} command).

        @param (x0, y0): starting point in PX
        @param (x1, y1): ending point in PX
        @param duration: duration of the event in ms
        @param steps: number of steps (currently ignored by C{input swipe})
        @param orientation: the orientation (-1: undefined)
        """
        (x0, y0) = xxx_todo_changeme1
        (x1, y1) = xxx_todo_changeme2
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

    def dragDip(self, xxx_todo_changeme3, xxx_todo_changeme4, duration, steps=1, orientation=-1):
        """
        Sends drag event in DIP (actually it's using C{input swipe} command.

        @param (x0, y0): starting point in DIP
        @param (x1, y1): ending point in DIP
        @param duration: duration of the event in ms
        @param steps: number of steps (currently ignored by C{input swipe})
        """
        (x0, y0) = xxx_todo_changeme3
        (x1, y1) = xxx_todo_changeme4
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
        elif type(text) is str:
            warnings.warn("WARNING: 'input text' utility does not support unicode: %s" % text)
            normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
            encoded = normalized.replace(' ', '%s')
        else:
            encoded = text.decode('utf-8')
        # FIXME find out which characters can be dangerous,
        # for example not worst idea to escape "
        self.shell('input text "%s"' % encoded)

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
        dwp = self.shell('dumpsys window policy')
        m = lockScreenRE.search(dwp)
        if m:
            return m.group(1) == 'true'
        dreamingLockscreenRE = re.compile('mDreamingLockscreen=(true|false)')
        m = dreamingLockscreenRE.search(dwp)
        if m:
            return m.group(1) == 'true'
        raise RuntimeError("Couldn't determine screen lock state")

    def isScreenOn(self):
        """
        Checks if the screen is ON.

        @return: True if the device screen is ON
        """

        self.__checkTransport()
        window_policy = self.shell('dumpsys window policy')

        # Deprecated in API 20, removed in API 29
        screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = screenOnRE.search(window_policy)
        if m:
            return m.group(1) == 'true'

        # Added in API 20
        screenStateRE = re.compile('interactiveState=(INTERACTIVE_STATE_AWAKE|INTERACTIVE_STATE_SLEEP)')
        m = screenStateRE.search(window_policy)
        if m:
            return m.group(1) == 'INTERACTIVE_STATE_AWAKE'

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
                if image1Pixels[x, y] == image2Pixels[x, y]:
                    numPixelsSame += 1

        return numPixelsSame / float(numPixelsTotal)

    @staticmethod
    def sameAs(image1, image2, percent=1.0):
        '''
        Compares 2 images

        @author: catshoes
        '''

        return AdbClient.percentSame(image1, image2) >= percent

    @staticmethod
    def imageInScreen(screen, image):
        """
        Checks if image is on the screen

        @param screen: the screen image
        @param image: the partial image to look for
        @return: True or False

        @author: Perry Tsai <ripple0129@gmail.com>
        """

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
            print("log(tag=%s, message=%s, priority=%s, verbose=%s)" % (tag, message, priority, verbose),
                  file=sys.stderr)
        self.__checkTransport()
        message = self.substituteDeviceTemplate(message)
        if verbose or priority == 'V':
            print(tag + ':', message, file=sys.stderr)
        self.shell('log -p %c -t "%s" %s' % (priority, tag, message))

    class __Log:
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
            raise AttributeError('__Log: %s has not attribute "%s"' % (self.__class__.__name__, attr))

    def getSystemService(self, name):
        if name == WIFI_SERVICE:
            return WifiManager(self)

    def getWindows(self):
        self.__checkTransport()
        windows = {}
        dww = self.shell('dumpsys window windows')
        if DEBUG_WINDOWS: print(dww, file=sys.stderr)
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
                        if DEBUG_COORDS: print("getWindows: visibility=", visibility, file=sys.stderr)
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
                print("getWindows: focus=", currentFocus, file=sys.stderr)
                print("getWindows:", windows[currentFocus], file=sys.stderr)
            windows[currentFocus].focused = True

        return windows

    def getFocusedWindow(self):
        '''
        Gets the focused window.

        @return: The focused L{Window}.
        '''

        for window in list(self.getWindows().values()):
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
        activityRE = re.compile('\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.\$]+) \w+ pid=(\d+)')
        m = activityRE.findall(dat)
        if len(m) > 0:
            return m[-1]
        else:
            warnings.warn("NO MATCH:" + dat)
            return None

    def getTopActivityName(self):
        tanp = self.getTopActivityNameAndPid()
        if tanp:
            return tanp[0] + '/' + tanp[1]
        else:
            return None

    def getTopActivityUri(self) -> Optional[str]:
        tan = self.getTopActivityName()
        dat = self.shell('dumpsys activity')
        startActivityRE = re.compile(r'^\s*mStartActivity:')
        intentRE = re.compile(f'^\\s*Intent {{ act=(\\S+) dat=(\\S+) flg=(\\S+) cmp={tan} }}')
        lines = dat.splitlines()
        for n, _line in enumerate(lines):
            if startActivityRE.match(_line):
                for i in range(n, n + 6):
                    m = intentRE.match(lines[i])
                    if m:
                        return m.group(2)
        return None

    def substituteDeviceTemplate(self, template):
        serialno = self.serialno.replace('.', '_').replace(':', '-')
        pid = os.getpid()
        window_name = self.getFocusedWindowName() or 'no_name'
        focusedWindowName = window_name.replace('/', '-').replace('.', '_')
        timestamp = datetime.datetime.now().isoformat()
        osName = platform.system()
        if osName.startswith('Windows'):  # ':' not supported in filenames
            timestamp.replace(':', '_')
        _map = {
            'screenshot_number': f'{self.screenshot_number:04d}',
            'pid': pid,
            'serialno': serialno,
            'focusedwindowname': focusedWindowName,
            'timestamp': timestamp
        }
        return string.Template(template).substitute(_map)

    def dumpsys(self, subcommand, *args):
        return Dumpsys(self, subcommand, *args)


if __name__ == '__main__':
    adbClient = AdbClient(os.environ['ANDROID_SERIAL'])
    INTERACTIVE = False
    if INTERACTIVE:
        sout = adbClient.shell()
        prompt = re.compile(".+@android:(.*) [$#] \r\r\n")
        while True:
            try:
                cmd = input('adb $ ')
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
                print(line, end=' ')
                if not line:
                    break

        print("\nBye")
    else:
        print('date:', adbClient.shell('date'))
