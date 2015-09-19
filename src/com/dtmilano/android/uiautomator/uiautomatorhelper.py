# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2015  Diego Torres Milano
Created on Feb 2, 2015

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

__version__ = '10.7.5'

import httplib
from httplib import HTTPConnection
import os
import subprocess
import sys
import platform
import threading
import re
import urllib
import time
from com.dtmilano.android.adb.adbclient import AdbClient
from com.dtmilano.android.common import obtainAdbPath

__author__ = 'diego'


DEBUG = False

lock = threading.Lock()

class RunTestsThread(threading.Thread):
    """
    Runs the instrumentation for the specified package in a new thread.
    """
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None, adbClient=None, testClass=None, testRunner=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, verbose=verbose)
        self.adbClient = adbClient
        self.testClass = testClass
        self.testRunner = testRunner

    def run(self):
        if DEBUG:
            print >> sys.stderr, "RunTestsThread: Acquiring lock"
        lock.acquire()
        pkg = re.sub('\.test$', '', self.testClass)
        if DEBUG:
            print >> sys.stderr, "Cleaning up before start. Stopping '%s'" % pkg
        self.adbClient.shell('am force-stop ' + pkg)
        time.sleep(3)
        if DEBUG:
            print >> sys.stderr, "Starting test..."
            print >> sys.stderr, "RunTestsThread: Releasing lock"
        lock.release()
        out = self.adbClient.shell('am instrument -w ' + self.testClass + '/' + self.testRunner + '; echo "ERROR: $?"')
        if DEBUG:
            print >> sys.stderr, "\nFinished test."
        errmsg = out.splitlines()[-1]
        m = re.match('ERROR: (\d+)', errmsg)
        if m:
            exitval = int(m.group(1))
            if exitval != 0:
                raise RuntimeError('Cannot start test on device: ' + out)
        else:
            raise RuntimeError('Unknown message')

class UiAutomatorHelper:
    REUSE_CONNECTION = False
    PACKAGE = 'com.dtmilano.android.uiautomatorhelper'
    TEST_CLASS = PACKAGE + '.test'
    TEST_RUNNER = PACKAGE + '.UiAutomatorHelperTestRunner'

    def __init__(self, adbclient, adb=None, localport=9999, remoteport=9999, hostname='localhost'):
        self.adbClient = adbclient
        ''' The adb client (a.k.a. device) '''
        instrumentation = self.adbClient.shell('pm list instrumentation %s' % self.PACKAGE)
        if not re.match('instrumentation:%s/%s \(target=%s\)' % (self.TEST_CLASS, self.TEST_RUNNER, self.PACKAGE), instrumentation):
            raise RuntimeError('The target device does not contain the instrumentation for %s' % self.PACKAGE)
        self.adb = self.__whichAdb(adb)
        ''' The adb command '''
        self.osName = platform.system()
        ''' The OS name. We sometimes need specific behavior. '''
        self.isDarwin = (self.osName == 'Darwin')
        ''' Is it Mac OSX? '''
        self.hostname = hostname
        ''' The hostname we are connecting to. '''
        if hostname in ['localhost', '127.0.0.1']:
            self.__redirectPort(localport, remoteport)
        self.__runTests()
        self.conn = None
        if not self.REUSE_CONNECTION:
            self.__connectToServer(hostname, localport)

    def __connectToServer(self, hostname, port):
        if DEBUG:
            print >> sys.stderr, "UiAutomatorHelper: Acquiring lock"
        lock.acquire()
        self.conn = httplib.HTTPConnection(hostname, port)
        if not self.conn:
            raise RuntimeError("Cannot connect to %s:%d" % (hostname, port))
        #self.conn.connect();
        if DEBUG:
            print >> sys.stderr, "UiAutomatorHelper: Releasing lock"
        lock.release()

    def __whichAdb(self, adb):
        if adb:
            if not os.access(adb, os.X_OK):
                raise Exception('adb="%s" is not executable' % adb)
        else:
            # Using adbclient we don't need adb executable yet (maybe it's needed if we want to
            # start adb if not running) or to redirect ports
            adb = obtainAdbPath()

        return adb

    def __redirectPort(self, localport, remoteport):
        self.localPort = localport
        self.remotePort = remoteport
        subprocess.check_call([self.adb, '-s', self.adbClient.serialno, 'forward', 'tcp:%d' % self.localPort,
                               'tcp:%d' % self.remotePort])

    def __runTests(self):
        if DEBUG:
            print >> sys.stderr, "__runTests: start"
        # We need a new AdbClient instance with timeout=None (means, no timeout) for the long running test service
        newAdbClient = AdbClient(self.adbClient.serialno, self.adbClient.hostname, self.adbClient.port, timeout=None)
        self.thread = RunTestsThread(adbClient=newAdbClient, testClass=self.TEST_CLASS, testRunner=self.TEST_RUNNER)
        if DEBUG:
            print >> sys.stderr, "__runTests: starting thread"
        self.thread.start()
        if DEBUG:
            print >> sys.stderr, "__runTests: end"


    def __httpCommand(self, url, method='GET'):
        if self.isDarwin or not self.REUSE_CONNECTION:
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # !! The connection cannot be resued in OSX, it gives:
            # !!     response = conn.getresponse()
            # !! File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/httplib.py", line 1045, in getresponse
            # !!     response.begin()
            # !!   File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/httplib.py", line 409, in begin
            # !!     version, status, reason = self._read_status()
            # !!   File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/httplib.py", line 373, in _read_status
            # !!     raise BadStatusLine(line)
            # !! httplib.BadStatusLine: ''
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            if self.conn:
                self.conn.close()
            self.__connectToServer(self.hostname, self.localPort)
            time.sleep(0.9)
        self.conn.request(method, url)
        try:
            response = self.conn.getresponse()
            if response.status == 200:
                return response.read()
            raise RuntimeError(response.status + " " + response.reason + " while " + method + " " + url)
        except httplib.BadStatusLine, ex:
            if DEBUG:
                print >> sys.stderr, 'ERROR: BadStatusLine', ex
            return u''
        except Exception, ex:
            print >> sys.stderr, 'ERROR:', ex
            return u''
        finally:
            if self.isDarwin or not self.REUSE_CONNECTION:
                self.conn.close()

    #
    # UiAutomatorHelper internal commands
    #
    def quit(self):
        self.__httpCommand('/UiAutomatorHelper/quit')

    #
    # UiDevice
    #
    def findObject(self, resourceId):
        if not resourceId:
            raise RuntimeError('findObject: resourceId must have a value')
        response = self.__httpCommand('/UiDevice/findObject?resourceId=%s' % (resourceId))
        # <response><object oid="0x1234" className="android.widget.EditText"/></response>
        m = re.search('oid="0x([0-9a-f]+)"', response)
        if m:
            return int("0x" + m.group(1), 16)
        raise RuntimeError("Invalid response: " + response)

    def takeScreenshot(self, scale=1.0, quality=90):
        return self.__httpCommand('/UiDevice/takeScreenshot?scale=%f&quality=%d' % (scale, quality))

    def click(self, x, y):
        return self.__httpCommand('/UiDevice/click?x=%d&y=%d' % (x, y))

    def swipe(self, (x0, y0), (x1, y1), steps):
        return self.__httpCommand('/UiDevice/swipe?x0=%d&y0=%d&x1=%d&y1=%d&steps=%d' % (x0, y0, x1, y1, steps))

    def dumpWindowHierarchy(self):
        dump = self.__httpCommand('/UiDevice/dumpWindowHierarchy').decode(encoding='UTF-8', errors='replace')
        if DEBUG:
            print >> sys.stderr, "DUMP: ", dump
        return dump

    #
    # UiObject
    #
    def setText(self, uiObject, text):
        return self.__httpCommand('/UiObject/0x%x/setText?text=%s' % (uiObject, urllib.quote_plus(text)))
