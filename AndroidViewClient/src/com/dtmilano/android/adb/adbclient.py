'''
Created on Dec 1, 2012

@author: diego
'''
import sys
import socket
import time
import re
import signal
import os
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
        self.socket.send('%04x%s' % (len(msg), msg))
        if checkok:
            self.__checkOk()
        if reconnect:
            if DEBUG:
                print >> sys.stderr, "    __send: reconnecting"
            self.__connect()
            self.__setTransport()
    
    def __receive(self):
        if DEBUG:
            print >> sys.stderr, "__receive()"
        self.checkConnected()
        n = int(self.socket.recv(4), 16)
        recv = self.socket.recv(n)
        return recv
        
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
        if version != '0004001f':
            raise RuntimeError("ERROR: Incorrect version %s" % (version))
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
    
    def getSystemProperty(self, key, strip=True):
        return self.getProperty(key, strip)
    
    def getProperty(self, key, strip=True):
        prop = self.shell('getprop %s' % key)
        if strip:
            prop = prop.rstrip('\r\n')
        return prop
    
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
        self.shell(cmd)
    
    def touch(self, x, y, eventType=DOWN_AND_UP):
        self.shell('input tap %d %d' % (x, y))
    
    def type(self, text):
        self.shell('input text "%s"' % text)
        
    def wake(self):
        self.shell('input keyevent 26')
        
    
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