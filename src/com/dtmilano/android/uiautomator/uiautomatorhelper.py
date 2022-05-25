# -*- coding: utf-8 -*-
"""
Copyright (C) 2012-2022  Diego Torres Milano
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
"""

from __future__ import print_function

__version__ = '21.4.3'

import json
import os
import platform
import re
import subprocess
import sys
import threading
import time
from abc import ABC

import culebratester_client
from culebratester_client import Text, ObjectRef, StatusResponse

from com.dtmilano.android.adb.adbclient import AdbClient
from com.dtmilano.android.common import obtainAdbPath

__author__ = 'diego'

DEBUG = False

lock = threading.Lock()


class RunTestsThread(threading.Thread):
    """
    Runs the instrumentation for the specified package in a new thread.
    """

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None, adbClient=None,
                 testClass=None, testRunner=None):
        threading.Thread.__init__(self, group=group, target=target, name=name)
        self.adbClient = adbClient
        self.testClass = testClass
        self.testRunner = testRunner
        self.pkg = re.sub('\\.test$', '', self.testClass)

    def run(self):
        if DEBUG:
            print("RunTestsThread: Acquiring lock", file=sys.stderr)
        lock.acquire()
        if DEBUG:
            print("RunTestsThread: Lock acquired", file=sys.stderr)
        self.forceStop()
        time.sleep(3)
        if DEBUG:
            print("Starting test...", file=sys.stderr)
            print("RunTestsThread: Releasing lock", file=sys.stderr)
        lock.release()
        out = self.adbClient.shell('am instrument -w ' + self.testClass + '/' + self.testRunner + '; echo "ERROR: $?"')
        if DEBUG:
            print("\nFinished test.", file=sys.stderr)
        errmsg = out.splitlines()[-1]
        m = re.match('ERROR: (\\d+)', errmsg)
        if m:
            exitval = int(m.group(1))
            if exitval != 0:
                raise RuntimeError('Cannot start test on device: ' + out)
        else:
            raise RuntimeError('Unknown message')

    def forceStop(self):
        if DEBUG:
            print("Cleaning up before start. Stopping '%s'" % self.pkg, file=sys.stderr)
        self.adbClient.shell('am force-stop ' + self.pkg)


class UiAutomatorHelper:
    PACKAGE = 'com.dtmilano.android.culebratester'
    TEST_CLASS = PACKAGE + '.test'
    TEST_RUNNER = 'com.dtmilano.android.uiautomatorhelper.UiAutomatorHelperTestRunner'

    def __init__(self, adbclient, adb=None, localport=9987, remoteport=9987, hostname='localhost', api_version='v2'):
        """
        UiAutomatorHelper constructor used when the backend selected is **CulebraTester2-public**.
        This class holds references to the different API's:
         - Device
         - TargetContext
         - ObjectStore
         - UiDevice
         - UiObject2
         - Until

        :param adbclient: the adb client
        :param adb: adb if known
        :param localport: the local port used in CulebraTester2-public port forwarding
        :param remoteport: the remote port used in CulebraTester2-public port forwarding
        :param hostname: the hostname used by CulebraTester2-public
        :param api_version: the api version
        """
        self.adbClient = adbclient
        ''' The adb client (a.k.a. device) '''
        self.adb = self.__whichAdb(adb)
        ''' The adb command '''
        self.osName = platform.system()
        ''' The OS name. We sometimes need specific behavior. '''
        self.isDarwin = (self.osName == 'Darwin')
        ''' Is it Mac OSX? '''
        self.hostname = hostname
        ''' The hostname we are connecting to. '''

        print(
            f'⚠️  CulebraTester2 server should have been started and localport {localport} redirected to remote port {remoteport}.',
            file=sys.stderr)
        configuration = culebratester_client.Configuration()
        configuration.host = f'http://{hostname}:{localport}/{api_version}'
        self.api_instance = culebratester_client.DefaultApi(culebratester_client.ApiClient(configuration))
        self.device: UiAutomatorHelper.Device = UiAutomatorHelper.Device(self)
        self.target_context: UiAutomatorHelper.TargetContext = UiAutomatorHelper.TargetContext(self)
        self.object_store: UiAutomatorHelper.ObjectStore = UiAutomatorHelper.ObjectStore(self)
        self.ui_device: UiAutomatorHelper.UiDevice = UiAutomatorHelper.UiDevice(self)
        self.ui_object2: UiAutomatorHelper.UiObject2 = UiAutomatorHelper.UiObject2(self)
        self.until: UiAutomatorHelper.Until = UiAutomatorHelper.Until(self)

    def __connectSession(self):
        if DEBUG:
            print("UiAutomatorHelper: Acquiring lock", file=sys.stderr)
        lock.acquire()
        if DEBUG:
            print("UiAutomatorHelper: Lock acquired", file=sys.stderr)
            print("UiAutomatorHelper: Connecting session", file=sys.stderr)
        session = None  # requests.Session()
        if not session:
            raise RuntimeError("Cannot create session")
        tries = 10
        while tries > 0:
            time.sleep(0.5)
            if DEBUG:
                print("UiAutomatorHelper: Attempting to connect to", self.baseUrl, '(tries=%s)' % tries,
                      file=sys.stderr)
            try:
                response = session.head(self.baseUrl)
                if response.status_code == 200:
                    break
            except:  # requests.exceptions.ConnectionError as ex:
                tries -= 1
        lock.release()
        if tries == 0:
            raise RuntimeError("Cannot connect to " + self.baseUrl)
        if DEBUG:
            print("UiAutomatorHelper: HEAD", response, file=sys.stderr)
            print("UiAutomatorHelper: Releasing lock", file=sys.stderr)
        # lock.release()
        return session

    @staticmethod
    def __whichAdb(adb):
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
            print("__runTests: start", file=sys.stderr)
        # We need a new AdbClient instance with timeout=None (means, no timeout) for the long running test service
        newAdbClient = AdbClient(self.adbClient.serialno, self.adbClient.hostname, self.adbClient.port, timeout=None)
        self.thread = RunTestsThread(adbClient=newAdbClient, testClass=self.TEST_CLASS, testRunner=self.TEST_RUNNER)
        if DEBUG:
            print("__runTests: starting thread", file=sys.stderr)
        self.thread.start()
        if DEBUG:
            print("__runTests: end", file=sys.stderr)

    def __httpCommand(self, url, params=None, method='GET'):
        raise RuntimeError(f"this method should not be used: url={url} params={params} method={method}")

    #
    # UiAutomatorHelper internal commands
    #
    def quit(self):
        # try:
        #     self.__httpCommand('/UiAutomatorHelper/quit')
        # except:
        #     pass
        # self.session.close()
        pass

    #
    # API Base
    #
    class ApiBase(ABC):

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__()
            self.uiAutomatorHelper = uiAutomatorHelper

        @staticmethod
        def intersection(l1, l2):
            return list(set(l1) & set(l2))

        def some(self, l1, l2):
            return len(self.intersection(l1, l2)) > 0

        def all(self, l1, l2):
            li = len(self.intersection(l1, l2))
            return li == len(l1) and li == len(l2)

    #
    # Device
    #
    class Device(ApiBase):
        """
        Device
        """

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def display_real_size(self):
            """
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return: the display real size
            """
            return self.uiAutomatorHelper.api_instance.device_display_real_size_get()

        def wait_for_new_toast(self, timeout=10000):
            """
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return: the text in the Toast if found
            """
            return self.uiAutomatorHelper.api_instance.device_wait_for_new_toast_get(timeout=timeout)

    def getDisplayRealSize(self):
        """
        :deprecated: use uiAutomatorHelper.device.display_real_size()
        :return: the display real size
        """
        return self.api_instance.device_display_real_size_get()

    #
    # TargetContext
    #
    class TargetContext(ApiBase):
        """
        Target Context.
        """

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def start_activity(self, pkg, cls, **kwargs):
            """
            Starts an activity.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param pkg: the package
            :param cls: the Activity class
            :param kwargs: uri: the optional URI
            :return: the api response
            """
            return self.uiAutomatorHelper.api_instance.target_context_start_activity_get(pkg, cls, **kwargs)

    #
    # ObjectStore
    #
    class ObjectStore(ApiBase):
        """
        Object Store.
        """

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def clear(self):
            """
            Clears all the objects.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return: the status
            """
            return self.uiAutomatorHelper.api_instance.object_store_clear_get()

        def list(self):
            """
            List the objects.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return: the list of objects
            """
            return self.uiAutomatorHelper.api_instance.object_store_list_get()

        def remove(self, oid: int):
            """
            Removes an object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return: the status
            """
            return self.uiAutomatorHelper.api_instance.object_store_remove_get(oid)

    #
    # UiDevice
    #
    class UiDevice(ApiBase):
        """
        UI Device.
        """

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def click(self, **kwargs):
            """
            Clicks.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return:
            """
            if self.all(['x', 'y'], kwargs):
                x = int(kwargs['x'])
                y = int(kwargs['y'])
                return self.uiAutomatorHelper.api_instance.ui_device_click_get(x=x, y=y)
            else:
                raise ValueError('click: (x, y) must have a value')

        def dump_window_hierarchy(self, _format='JSON'):
            """
            Dumps the window hierarchy.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param _format:
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_dump_window_hierarchy_get(format=_format)

        def find_object(self, **kwargs):
            """
            Finds an object.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return:
            """
            if 'body' in kwargs:
                return self.uiAutomatorHelper.api_instance.ui_device_find_object_post(**kwargs)
            if self.some(['resource_id', 'ui_selector', 'by_selector'], kwargs):
                return self.uiAutomatorHelper.api_instance.ui_device_find_object_get(**kwargs)
            body = culebratester_client.Selector(**kwargs)
            return self.uiAutomatorHelper.api_instance.ui_device_find_object_post(body=body)

        def find_objects(self, **kwargs):
            """
            Finds objects.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_find_objects_get(**kwargs)

        def press_back(self):
            """
            Presses BACK.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_press_back_get()

        def press_enter(self):
            """
            Presses ENTER.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_press_enter_get()

        def press_home(self):
            """
            Presses HOME.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_press_home_get()

        def press_key_code(self, key_code, meta_state=0):
            """
            Presses a key code.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param key_code:
            :param meta_state:
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_press_key_code_get(key_code=key_code,
                                                                                    meta_state=meta_state)

        def swipe(self, **kwargs):
            """
            Swipes.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return:
            """
            if self.all(['start_x', 'start_y', 'end_x', 'end_y', 'steps'], kwargs):
                return self.uiAutomatorHelper.api_instance.ui_device_swipe_get(**kwargs)
            body = culebratester_client.SwipeBody(**kwargs)
            return self.uiAutomatorHelper.api_instance.ui_device_swipe_post(body=body)

        def take_screenshot(self, scale=1.0, quality=90, **kwargs):
            """
            Takes screenshot.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param scale:
            :param quality:
            :param kwargs:
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_screenshot_get(scale=scale, quality=quality,
                                                                                _preload_content=False, **kwargs)

        def wait(self, search_condition_ref: int, timeout=10000):
            """

            :param search_condition_ref: the search condition ref (oid)
            :param timeout: the timeout in ms
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_wait_get(search_condition_ref=search_condition_ref,
                                                                          timeout=timeout)

        def wait_for_idle(self, **kwargs):
            """
            Waits for idle.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_wait_for_idle_get(**kwargs)

        def wait_for_window_update(self, timeout=5000, **kwargs):
            """
            Waits for window update.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param timeout: the timeout
            :param kwargs:
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_device_wait_for_window_update_get(timeout, **kwargs)

    #
    # UiObject2
    #
    class UiObject2(ApiBase):
        """
        Inner UiObject2 class.

        Notice that this class does not require an OID in its constructor.
        """

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def clear(self, oid):
            """
            Clears the text content if this object is an editable field.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the result of the operation
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_clear_get(oid=oid)

        def click(self, oid):
            """
            Clicks on this object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the result of the operation
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_oid_click_get(oid=oid)

        def click_and_wait(self, oid: int, event_condition_ref, timeout=10000) -> StatusResponse:
            """
            Clicks and wait.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :param event_condition_ref: the event condition
            :param timeout: the timeout
            :return: the status response
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_oid_click_and_wait_get(oid, event_condition_ref,
                                                                                         timeout=timeout)

        def dump(self, oid):
            """
            Dumps the content of an object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the content
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_dump_get(oid=oid)

        def get_text(self, oid):
            """
            Returns the text value for this object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the text
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_oid_get_text_get(oid=oid)

        def long_click(self, oid):
            """
            Performs a long click on this object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the result of the operation
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_oid_long_click_get(oid=oid)

        def set_text(self, oid, text):
            """
            Sets the text content if this object is an editable field.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :param text: the text
            :return: the result of the operation
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_oid_set_text_post(oid=oid, body=Text(text))

    #
    # Until
    #
    class Until(ApiBase):
        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def find_object(self, by_selector: str) -> ObjectRef:
            """
            Returns a SearchCondition that is satisfied when at least one element matching the selector can be found.
            The condition will return the first matching element.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param by_selector: the selector
            :return: the search condition reference
            """
            return self.uiAutomatorHelper.api_instance.until_find_object_get(by_selector=by_selector)

        def new_window(self) -> ObjectRef:
            """
            Returns a condition that depends on a new window having appeared.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return: the event condition reference
            """
            return self.uiAutomatorHelper.api_instance.until_new_window_get()

    def click(self, **kwargs):
        """
        :deprecated:
        :param kwargs:
        :return:
        """
        params = kwargs
        if not (('x' in params and 'y' in params) or 'oid' in params):
            raise RuntimeError('click: (x, y) or oid must have a value')
        if 'oid' in params:
            oid = int(params['oid'])
            return self.api_instance.ui_object2_oid_click_get(oid)
        else:
            x = int(params['x'])
            y = int(params['y'])
            return self.api_instance.ui_device_click_get(x=x, y=y)

    def dumpWindowHierarchy(self):
        """
        :deprecated:
        """
        return self.api_instance.ui_device_dump_window_hierarchy_get(format='JSON')

    def findObject(self, **kwargs):
        """
        :deprecated:
        """
        return self.api_instance.ui_device_find_object_get(**kwargs)

    def findObjects(self, **kwargs):
        """
        :deprecated:
        """
        return self.api_instance.ui_device_find_objects_get(**kwargs)

    def longClick(self, **kwargs):
        """
        :deprecated:
        """
        params = kwargs
        if not (('x' in params and 'y' in params) or 'oid' in params):
            raise RuntimeError('longClick: (x, y) or oid must have a value')
        if 'oid' in params:
            oid = int(params['oid'])
            return self.api_instance.ui_object2_oid_long_click_get(oid)
        else:
            return self.__httpCommand('/UiDevice/longClick', params)

    def openNotification(self):
        """
        :deprecated:
        """
        return self.__httpCommand('/UiDevice/openNotification')

    def openQuickSettings(self):
        """
        :deprecated:
        """
        return self.__httpCommand('/UiDevice/openQuickSettings')

    def pressBack(self):
        """
        :deprecated:
        """
        return self.api_instance.ui_device_press_back_get()

    def pressHome(self):
        """
        :deprecated:
        """
        return self.api_instance.ui_device_press_home_get()

    def pressKeyCode(self, keyCode, metaState=0):
        """
        :deprecated:
        """
        return self.api_instance.ui_device_press_key_code_get(key_code=keyCode, meta_state=metaState)

    def pressRecentApps(self):
        """
        :deprecated:
        """
        return self.__httpCommand('/UiDevice/pressRecentApps')

    def swipe(self, startX=-1, startY=-1, endX=-1, endY=-1, steps=10, segments=None, segmentSteps=5):
        """
        :deprecated:
        """
        if segments is None:
            segments = []
        if startX != -1 and startY != -1:
            params = {'startX': startX, 'startY': startY, 'endX': endX, 'endY': endY, 'steps': steps}
        elif segments:
            params = {'segments': ','.join(str(p) for p in segments), "segmentSteps": segmentSteps}
        else:
            raise RuntimeError(
                "Cannot determine method invocation from provided parameters. startX and startY or segments must be "
                "provided.")
        return self.__httpCommand('/UiDevice/swipe', params)

    def takeScreenshot(self, scale=1.0, quality=90, **kwargs):
        """
        :deprecated:
        """
        return self.api_instance.ui_device_screenshot_get(scale=scale, quality=quality, **kwargs)

    def waitForIdle(self, timeout):
        """
        :deprecated:
        """
        params = {'timeout': timeout}
        return self.api_instance.ui_device_wait_for_idle_get(**params)

    #
    # UiObject2
    #
    def setText(self, oid, text):
        """
        :deprecated:
        """
        body = {'text': text}
        return self.api_instance.ui_object2_oid_set_text_post(body, oid)

    def clickAndWait(self, uiObject2, eventCondition, timeout):
        """

        :deprecated:
        :param uiObject2:
        :param eventCondition:
        :param timeout:
        :return:
        """
        params = {'eventCondition': eventCondition, 'timeout': timeout}
        return self.__httpCommand('/UiObject2/%d/clickAndWait' % uiObject2.oid, params)

    def getText(self, oid):
        return self.api_instance.ui_object2_oid_get_text_get(oid)

    def isChecked(self, uiObject=None):
        """

        :deprecated:
        :param uiObject:
        :return:
        """
        # This path works for UiObject and UiObject2, so there's no need to handle both cases differently
        path = '/UiObject/%d/isChecked' % uiObject.oid
        response = self.__httpCommand(path, None)
        r = json.loads(response)
        if r['status'] == 'OK':
            return r['checked']
        raise RuntimeError("Error: " + response)

    #
    # UiScrollable
    #
    def uiScrollable(self, path, params=None):
        response = self.__httpCommand('/UiScrollable/' + path, params)
        if DEBUG:
            print("UiAutomatorHelper: uiScrollable: response=", response, file=sys.stderr)
        r = None
        try:
            r = json.loads(response)
        except:
            print("====================================", file=sys.stderr)
            print("Invalid JSON RESPONSE: ", response, file=sys.stderr)
        if r['status'] == 'OK':
            if 'oid' in r:
                if DEBUG:
                    print("UiAutomatorHelper: uiScrollable: returning", int(r['oid']), file=sys.stderr)
                return int(r['oid']), r
            else:
                return r
        if DEBUG:
            print("RESPONSE: ", response, file=sys.stderr)
            print("r=", r, file=sys.stderr)
        raise RuntimeError("Error: " + response)


class UiObject:
    """
    A UiObject is a representation of a view.
    """

    def __init__(self, uiAutomatorHelper, oid, response):
        self.uiAutomatorHelper = uiAutomatorHelper
        self.oid = oid
        self.className = response['className']

    def getOid(self):
        return self.oid

    def getClassName(self):
        return self.className

    def click(self):
        self.uiAutomatorHelper.click(oid=self.oid)

    def longClick(self):
        self.uiAutomatorHelper.longClick(oid=self.oid)

    def getText(self):
        return self.uiAutomatorHelper.getText(uiObject=self)

    def setText(self, text):
        self.uiAutomatorHelper.setText(uiObject=self, text=text)


class UiObject2:
    """
    A UiObject2 represents a UI element. Unlike UiObject, it is bound to a particular view instance and can become
    stale.
    """

    def __init__(self, uiAutomatorHelper: UiAutomatorHelper, class_name: str, oid: int):
        """
        Constructor.

        :param uiAutomatorHelper: the uiAutomatorHelper instance.
        :param class_name: the class name of the UI object
        :param oid: the object id
        """
        self.uiAutomatorHelper = uiAutomatorHelper
        self.class_name = class_name
        self.oid = oid

    def clear(self):
        """
        Clears the text content if this object is an editable field.
        :return: the result of the operation
        """
        return self.uiAutomatorHelper.ui_object2.clear(oid=self.oid)

    def click(self):
        """
        Clicks on this object.
        :return: the result of the operation
        """
        return self.uiAutomatorHelper.ui_object2.click(oid=self.oid)

    def dump(self):
        """
        Dumps the content of the object/
        :return: the content of the object
        """
        return self.uiAutomatorHelper.ui_object2.dump(oid=self.oid)

    def get_text(self):
        """
        Returns the text value for this object.
        :return: the text
        """
        return self.uiAutomatorHelper.ui_object2.get_text(oid=self.oid)

    def long_click(self):
        """
        Performs a long click on this object.
        :return: the result of the operation
        """
        return self.uiAutomatorHelper.ui_object2.long_click(oid=self.oid)

    def set_text(self, text):
        """
        Sets the text content if this object is an editable field.
        :param text: the text
        :return: the result of the operation
        """
        return self.uiAutomatorHelper.ui_object2.set_text(oid=self.oid, text=text)

    def clickAndWait(self, eventCondition, timeout):
        """
        :deprecated:
        :param eventCondition:
        :param timeout:
        :return:
        """
        self.uiAutomatorHelper.clickAndWait(uiObject2=self, eventCondition=eventCondition, timeout=timeout)

    def isChecked(self):
        """

        :deprecated:
        :rtype: bool
        """
        return self.uiAutomatorHelper.isChecked(uiObject=self)

    def longClick(self):
        """

        :deprecated:
        """
        self.uiAutomatorHelper.longClick(oid=self.oid)

    def getText(self):
        """

        :deprecated:
        :return:
        """
        # NOTICE: even if this is an uiObject2 we are invoking the only "getText" method in UiAutomatorHelper
        # passing the uiObject2 as uiObject
        return self.uiAutomatorHelper.getText(uiObject=self)

    def setText(self, text):
        """

        :deprecated:
        :param text:
        """
        # NOTICE: even if this is an uiObject2 we are invoking the only "setText" method in UiAutomatorHelper
        # passing the uiObject2 as uiObject
        self.uiAutomatorHelper.setText(uiObject=self, text=text)


class UiScrollable:
    def __init__(self, uiAutomatorHelper, uiSelector):
        self.uiAutomatorHelper = uiAutomatorHelper
        self.uiSelector = uiSelector
        self.oid, self.response = self.__createUiScrollable()

    def __createUiScrollable(self):
        return self.uiAutomatorHelper.uiScrollable('new', {'uiSelector': self.uiSelector})

    def flingBackward(self):
        return self.uiAutomatorHelper.uiScrollable(str(self.oid) + '/flingBackward')

    def flingForward(self):
        return self.uiAutomatorHelper.uiScrollable(str(self.oid) + '/flingForward')

    def flingToBeginning(self, maxSwipes=20):
        return self.uiAutomatorHelper.uiScrollable(str(self.oid) + '/flingToBeginning', {'maxSwipes': maxSwipes})

    def flingToEnd(self, maxSwipes=20):
        return self.uiAutomatorHelper.uiScrollable(str(self.oid) + '/flingToEnd', {'maxSwipes': maxSwipes})

    def getChildByDescription(self, uiSelector, description, allowScrollSearch):
        oid, response = self.uiAutomatorHelper.uiScrollable(str(self.oid) + '/getChildByDescription',
                                                            {'uiSelector': uiSelector,
                                                             'contentDescription': description,
                                                             'allowScrollSearch': allowScrollSearch})
        return UiObject(self.uiAutomatorHelper, oid, response)

    def getChildByText(self, uiSelector, text, allowScrollSearch):
        oid, response = self.uiAutomatorHelper.uiScrollable(str(self.oid) + '/getChildByText',
                                                            {'uiSelector': uiSelector, 'text': text,
                                                             'allowScrollSearch': allowScrollSearch})
        return UiObject(self.uiAutomatorHelper, oid, response)

    def setAsHorizontalList(self):
        self.uiAutomatorHelper.uiScrollable(str(self.oid) + '/setAsHorizontalList')
        return self

    def setAsVerticalList(self):
        self.uiAutomatorHelper.uiScrollable(str(self.oid) + '/setAsVerticalList')
        return self
