'''
Copyright (C) 2012-2013  Diego Torres Milano
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

__version__ = '4.4.3'

import sys
import warnings
if sys.executable:
    if 'monkeyrunner' in sys.executable:
        warnings.warn(
    '''

    You should use a 'python' interpreter, not 'monkeyrunner' for this module

    ''', RuntimeWarning)
import socket
import time
import re
import signal
import os
import types
import platform

DEBUG = False

HOSTNAME = 'localhost'
PORT = 5037

OKAY = 'OKAY'
FAIL = 'FAIL'

UP = 0
DOWN = 1
DOWN_AND_UP = 2

TIMEOUT = 15

class Device:
    @staticmethod
    def factory(_str):
        if DEBUG:
            print >> sys.stderr, "Device.factory(", _str, ")"
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


class AdbClient:

    def __init__(self, serialno, hostname=HOSTNAME, port=PORT, settransport=True, reconnect=True):
        if not serialno:
            raise ValueError("serialno must not be empty or None")
        self.serialno = serialno
        self.hostname = hostname
        self.port = port

        self.reconnect = reconnect
        self.__connect()

        self.checkVersion()
        self.isTransportSet = False
        if settransport:
            self.__setTransport()

    @staticmethod
    def setAlarm(timeout):
        osName = platform.system()
        if osName.startswith('Windows'): # alarm is not implemented in Windows
            return
        if DEBUG:
            print >> sys.stderr, "setAlarm(%d)" % timeout
        signal.alarm(timeout)

    def setReconnect(self, val):
        self.reconnect = val

    def __connect(self):
        if DEBUG:
            print >> sys.stderr, "__connect()"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(TIMEOUT)
        try:
            self.socket.connect((self.hostname, self.port))
        except socket.error, ex:
            raise RuntimeError("ERROR: Connecting to %s:%d: %s" % (self.socket, self.port, ex))

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
            self.__connect()
            self.__setTransport()

    def __receive(self, nob=None):
        if DEBUG:
            print >> sys.stderr, "__receive()"
        self.checkConnected()
        if nob is None:
            nob = int(self.socket.recv(4), 16)
        if DEBUG:
            print >> sys.stderr, "    __receive: receiving", nob, "bytes"
        recv = bytearray()
        nr = 0
        while nr < nob:
            chunk = self.socket.recv(min((nob-nr), 4096))
            recv.extend(chunk)
            nr += len(chunk)
        if DEBUG:
            print >> sys.stderr, "    __receive: returning len=", len(recv)
        return str(recv)

    def __checkOk(self):
        if DEBUG:
            print >> sys.stderr, "__checkOk()"
        self.checkConnected()
        self.setAlarm(TIMEOUT)
        recv = self.socket.recv(4)
        if DEBUG:
            print >> sys.stderr, "    __checkOk: recv=", repr(recv)
        if recv != OKAY:
            error = self.socket.recv(1024)
            raise RuntimeError("ERROR: %s %s" % (repr(recv), error))
        self.setAlarm(0)
        if DEBUG:
            print >> sys.stderr, "    __checkOk: returning True"
        return True

    def checkConnected(self):
        if DEBUG:
            print >> sys.stderr, "checkConnected()"
        if not self.socket:
            raise RuntimeError("ERROR: Not connected")
        if DEBUG:
            print >> sys.stderr, "    checkConnected: returning True"
        return True

    def checkVersion(self, reconnect=True):
        if DEBUG:
            print >> sys.stderr, "checkVersion(reconnect=%s)" % reconnect
        self.__send('host:version', reconnect=False)
        version = self.socket.recv(8)
        VERSION='0004001f'
        if version != VERSION:
            raise RuntimeError("ERROR: Incorrect ADB server version %s (expecting %s)" % (version, VERSION))
        if reconnect:
            self.__connect()

    def __setTransport(self):
        if DEBUG:
            print >> sys.stderr, "__setTransport()"
        self.checkConnected()
        serialnoRE = re.compile(self.serialno)
        found = False
        for device in self.getDevices():
            if serialnoRE.match(device.serialno):
                found = True
                break
        if not found:
            raise RuntimeError("ERROR: couldn't find device that matches '%s'" % self.serialno)
        self.serialno = device.serialno
        msg = 'host:transport:%s' % self.serialno
        if DEBUG:
            print >> sys.stderr, "    __setTransport: msg=", msg
        self.__send(msg, reconnect=False)
        self.isTransportSet = True

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
        self.__connect()
        return devices

    def shell(self, cmd=None):
        if DEBUG:
            print >> sys.stderr, "shell(cmd=%s)" % cmd
        if cmd:
            self.__send('shell:%s' % cmd, checkok=True, reconnect=False)
            out = ''
            while True:
                _str = None
                try:
                    _str = self.socket.recv(4096)
                except Exception, ex:
                    print >> sys.stderr, "ERROR:", ex
                if not _str:
                    break
                out += _str
            if self.reconnect:
                if DEBUG:
                    print >> sys.stderr, "Reconnecting..."
                self.close()
                self.__connect()
                self.__setTransport()
            return out
        else:
            self.__send('shell:')
            #sin = self.socket.makefile("rw")
            #sout = self.socket.makefile("r")
            #return (sin, sin)
            sout = adbClient.socket.makefile("r")
            return sout

    def __getRestrictedScreen(self):
        ''' Gets C{mRestrictedScreen} values from dumpsys. This is a method to obtain display dimensions '''

        rsRE = re.compile('\s*mRestrictedScreen=\((?P<x>\d+),(?P<y>\d+)\) (?P<w>\d+)x(?P<h>\d+)')
        for line in self.shell('dumpsys window').splitlines():
            m = rsRE.match(line)
            if m:
                return m.groups()
        raise RuntimeError("Couldn't find mRestrictedScreen in dumpsys")

    def __getProp(self, key, strip=True):
        prop = self.shell('getprop %s' % key)
        if strip:
            prop = prop.rstrip('\r\n')
        return prop

    def __getDisplayWidth(self, key, strip=True):
        (x, y, w, h) = self.__getRestrictedScreen()
        return int(w)

    def __getDisplayHeight(self, key, strip=True):
        (x, y, w, h) = self.__getRestrictedScreen()
        return int(h)

    def getSystemProperty(self, key, strip=True):
        return self.getProperty(key, strip)

    def getProperty(self, key, strip=True):
        ''' Gets the property value for key '''

        import collections
        MAP_KEYS = collections.OrderedDict([
                          (re.compile('display.width'), self.__getDisplayWidth),
                          (re.compile('display.height'), self.__getDisplayHeight),
                          (re.compile('.*'), self.__getProp),
                          ])
        '''Maps properties key values (as regexps) to instance methods to obtain its values.'''

        for kre in MAP_KEYS.keys():
            if kre.match(key):
                return MAP_KEYS[kre](key=key, strip=strip)
        raise ValueError("key='%s' does not match any map entry")

    def press(self, name, eventType=DOWN_AND_UP):
        cmd = 'input keyevent %s' % name
        if DEBUG:
            print >>sys.stderr, "press(%s)" % cmd
        self.shell(cmd)

    def startActivity(self, component=None, flags=None, uri=None):
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
        if re.search(r"(Error type)|(Error: )|(Cannot find 'App')", out, re.IGNORECASE|re.MULTILINE):
            raise RuntimeError(out)

    def takeSnapshot(self, reconnect=False):
        '''
        Takes a snapshot of the device and return it as a PIL Image.
        '''

        try:
            from PIL import Image
        except:
            raise Exception("You have to install PIL to use takeSnapshot()")
        self.__send('framebuffer:', checkok=True, reconnect=False)
        import struct
        #case 1: // version
        #           return 12; // bpp, size, width, height, 4*(length, offset)
        received = self.__receive(1 * 4 + 12 * 4)
        (version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, glen, aoffset, alen) = struct.unpack('<' + 'L' * 13, received)
        if DEBUG:
            print >> sys.stderr, "    takeSnapshot:", (version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, glen, aoffset, alen)
        offsets = {roffset:'R', goffset:'G', boffset:'B'}
        if bpp == 32:
            offsets[aoffset] = 'A'
        argMode = ''.join([offsets[o] for o in sorted(offsets)])
        if DEBUG:
            print >> sys.stderr, "    takeSnapshot:", (version, bpp, size, width, height, roffset, rlen, boffset, blen, goffset, blen, aoffset, alen, argMode)
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
            self.__connect()
            self.__setTransport()
        if DEBUG:
            print >> sys.stderr, "    takeSnapshot: Image.frombuffer(%s, %s, %s, %s, %s, %s, %s)" % (mode, (width, height), 'data', 'raw', argMode, 0, 1)
        return Image.frombuffer(mode, (width, height), received, 'raw', argMode, 0, 1)

    def touch(self, x, y, eventType=DOWN_AND_UP):
        self.shell('input tap %d %d' % (x, y))

    def drag(self, (x0, y0), (x1, y1), duration, steps):
        self.shell('input swipe %d %d %d %d %d' % (x0, y0, x1, y1, duration*1000))

    def type(self, text):
        self.shell(u'input text "%s"' % text)

    def wake(self):
        self.shell('input keyevent 26')

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
            sout.readline(4096) # eat first line, which is the command
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
