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

__version__ = '10.8.1'

import os
import subprocess
import sys
import platform
import threading
import re
try:
    import requests
    REQUESTS_AVAILABLE = True
except:
    REQUESTS_AVAILABLE = False
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
        self.pkg = re.sub('\.test$', '', self.testClass)

    def run(self):
        if DEBUG:
            print >> sys.stderr, "RunTestsThread: Acquiring lock"
        lock.acquire()
        if DEBUG:
            print >> sys.stderr, "RunTestsThread: Lock acquired"
        self.forceStop()
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

    def forceStop(self):
        if DEBUG:
            print >> sys.stderr, "Cleaning up before start. Stopping '%s'" % self.pkg
        self.adbClient.shell('am force-stop ' + self.pkg)


class UiAutomatorHelper:
    PACKAGE = 'com.dtmilano.android.uiautomatorhelper'
    TEST_CLASS = PACKAGE + '.test'
    TEST_RUNNER = PACKAGE + '.UiAutomatorHelperTestRunner'

    def __init__(self, adbclient, adb=None, localport=9999, remoteport=9999, hostname='localhost'):
        if not REQUESTS_AVAILABLE:
            raise Exception('''Python Requests is needed for UiAutomatorHelper to work.

On Ubuntu install

   $ sudo apt-get install python-requests

On OSX install

   $ easy_install requests
''')

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
        self.baseUrl = 'http://%s:%d' % (hostname, localport)
        try:
            self.session = self.__connectSession()
        except RuntimeError, ex:
            self.thread.forceStop()
            raise ex


    def __connectSession(self):
        if DEBUG:
            print >> sys.stderr, "UiAutomatorHelper: Acquiring lock"
        lock.acquire()
        if DEBUG:
            print >> sys.stderr, "UiAutomatorHelper: Lock acquired"
            print >> sys.stderr, "UiAutomatorHelper: Connecting session"
        session = requests.Session()
        if not session:
            raise RuntimeError("Cannot create session")
        tries = 10
        while tries > 0:
            time.sleep(0.5)
            if DEBUG:
                print >> sys.stderr, "UiAutomatorHelper: Attempting to connect to", self.baseUrl, '(tries=%s)' % tries
            try:
                response = session.head(self.baseUrl)
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError, ex:
                tries -= 1
        lock.release()
        if tries == 0:
            raise RuntimeError("Cannot connect to " + self.baseUrl)
        if DEBUG:
            print >> sys.stderr, "UiAutomatorHelper: HEAD", response
            print >> sys.stderr, "UiAutomatorHelper: Releasing lock"
        #lock.release()
        return session

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


    def __httpCommand(self, url, params=None, method='GET'):
        if method == 'GET':
            if params:
                response = self.session.get(self.baseUrl + url, params=params)
            else:
                response = self.session.get(self.baseUrl + url)
        elif method == 'PUT':
            response = self.session.put(self.baseUrl + url, params=params)
        else:
            raise RuntimeError("method not supported: " + method)
        return response.content

    #
    # UiAutomatorHelper internal commands
    #
    def quit(self):
        try:
            self.__httpCommand('/UiAutomatorHelper/quit')
        except:
            pass
        self.session.close()

    #
    # UiDevice
    #
    def findObject(self, resourceId):
        if not resourceId:
            raise RuntimeError('findObject: resourceId must have a value')
        params = {'resourceId': resourceId}
        response = self.__httpCommand('/UiDevice/findObject', params)
        # <response><object oid="0x1234" className="android.widget.EditText"/></response>
        m = re.search('oid="0x([0-9a-f]+)"', response)
        if m:
            return int("0x" + m.group(1), 16)
        raise RuntimeError("Invalid response: " + response)

    def takeScreenshot(self, scale=1.0, quality=90):
        params = {'scale': scale, 'quality': quality}
        return self.__httpCommand('/UiDevice/takeScreenshot', params)

    def click(self, x, y):
        params = {'x': x, 'y': y}
        return self.__httpCommand('/UiDevice/click', params)

    def swipe(self, (x0, y0), (x1, y1), steps):
        params = {'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'steps': steps}
        return self.__httpCommand('/UiDevice/swipe', params)

    def dumpWindowHierarchy(self):
        dump = self.__httpCommand('/UiDevice/dumpWindowHierarchy').decode(encoding='UTF-8', errors='replace')
        if DEBUG:
            print >> sys.stderr, "DUMP: ", dump
        return dump

    #
    # UiObject
    #
    def setText(self, uiObject, text):
        params = {'text': text}
        return self.__httpCommand('/UiObject/0x%x/setText' % (uiObject), params)
