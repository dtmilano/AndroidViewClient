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

__version__ = '22.3.0'

import os
import platform
import re
import subprocess
import sys
import threading
import time
import warnings
from abc import ABC
from datetime import datetime
from typing import Optional, List, Tuple

import culebratester_client
from culebratester_client import Text, ObjectRef, DefaultApi, Point, PerformTwoPointerGestureBody, \
    BooleanResponse, NumberResponse, StatusResponse

from com.dtmilano.android.adb.adbclient import AdbClient
from com.dtmilano.android.common import obtainAdbPath

__author__ = 'diego'

from com.dtmilano.android.kato import kato

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


def check_response(response: StatusResponse) -> None:
    """
    Checks if the status response is OK. Otherwise, it raises an exception.

    :param response: the response
    :return: None
    """
    if response.status != 'OK':
        raise RuntimeError(response)


class UiAutomatorHelper:
    """
    UiAutomatorHelper is a backend for AndroidViewClient.
    """
    PACKAGE = 'com.dtmilano.android.culebratester2'
    TEST_CLASS = PACKAGE + '.test'
    TEST_RUNNER = 'com.dtmilano.android.culebratester2.UiAutomatorHelper'

    def __init__(self, adbclient, adb=None, localport=9987, remoteport=9987, hostname='localhost', api_version='v2'):
        """
        UiAutomatorHelper constructor used when the backend selected is **CulebraTester2-public**.
        This class holds references to the different API's:
         - Device
         - TargetContext
         - ObjectStore
         - UiDevice
         - UiObject
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
        ''' Is it macOS? '''
        self.hostname = hostname
        ''' The hostname we are connecting to. '''

        print(
            f'⚠️  CulebraTester2 server should have been started and localport {localport} redirected to remote port {remoteport}.',
            file=sys.stderr)
        configuration = culebratester_client.Configuration()
        configuration.host = f'http://{hostname}:{localport}/{api_version}'
        self.api_instance: DefaultApi = culebratester_client.DefaultApi(culebratester_client.ApiClient(configuration))
        self.device: UiAutomatorHelper.Device = UiAutomatorHelper.Device(self)
        self.target_context: UiAutomatorHelper.TargetContext = UiAutomatorHelper.TargetContext(self)
        self.object_store: UiAutomatorHelper.ObjectStore = UiAutomatorHelper.ObjectStore(self)
        self.ui_device: UiAutomatorHelper.UiDevice = UiAutomatorHelper.UiDevice(self)
        self.ui_object: UiAutomatorHelper.UiObject = UiAutomatorHelper.UiObject(self)
        self.ui_object2: UiAutomatorHelper.UiObject2 = UiAutomatorHelper.UiObject2(self)
        self.until: UiAutomatorHelper.Until = UiAutomatorHelper.Until(self)
        self.kato = kato.Kato()

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

    @staticmethod
    def timestamp() -> str:
        """
        Timestamp in ISO format.

        WARNING: may not be suitable to include in filenames on some platforms as it may include invalid path chars
        (i.e. `:`).

        :return: the timestamps
        """
        return datetime.now().isoformat()

    #
    # UiAutomatorHelper internal commands
    #
    def quit(self):
        pass

    #
    # API Base
    #
    class ApiBase(ABC):
        """
        Abstract class to serve as a base for API implementations.
        """

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__()
            self.uiAutomatorHelper = uiAutomatorHelper

        @staticmethod
        def intersection(l1: list, l2: list) -> list:
            """
            Obtains the intersection between the two lists.

            :param l1: list 1
            :type l1: list
            :param l2: list 2
            :type l2: list
            :return: the list containing the intersection
            :rtype: list
            """
            return list(set(l1) & set(l2))

        def some(self, l1: list, l2: list) -> bool:
            """
            Some elements are in both lists.

            :param l1: list 1
            :type l1: list
            :param l2: list 2
            :type l2: list
            :return: whether some elements are in both lists
            :rtype: bool
            """
            return len(self.intersection(l1, l2)) > 0

        def all(self, l1: list, l2: list) -> bool:
            """
            All the elements are in both lists.

            :param l1: list 1
            :type l1: list
            :param l2: list 2
            :type l2: list
            :return: whether all elements are in both lists
            :rtype: bool
            """
            li = len(self.intersection(l1, l2))
            return li == len(l1) and li == len(l2)

    #
    # Device
    #
    class Device(ApiBase):
        """
        Device
        :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
        """

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def display_real_size(self):
            """
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return: the display real size
            """
            return self.uiAutomatorHelper.api_instance.device_display_real_size_get()

        def dumpsys(self, service, **kwargs) -> str:
            """
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml

            :param service: the service
            :return: the dumpsys output
            """
            return self.uiAutomatorHelper.api_instance.device_dumpsys_get(service=service, _preload_content=False,
                                                                          **kwargs).read().decode('UTF-8')

        def get_top_activity_name_and_pid(self) -> Optional[str]:
            dat = self.dumpsys('activity', arg1='top')
            activityRE = re.compile(r'\s*ACTIVITY ([A-Za-z0-9_.]+)/([A-Za-z0-9_.\$]+) \w+ pid=(\d+)')
            m = activityRE.findall(dat)
            if len(m) > 0:
                return m[-1]
            else:
                warnings.warn("NO MATCH:" + dat)
                return None

        def get_top_activity_name(self) -> Optional[str]:
            tanp = self.get_top_activity_name_and_pid()
            if tanp:
                return tanp[0] + '/' + tanp[1]
            else:
                return None

        def get_top_activity_uri(self) -> Optional[str]:
            tan = self.get_top_activity_name()
            dat = self.dumpsys('activity')
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

        def wait_for_new_toast(self, timeout=10000):
            """
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml

            :return: the text in the Toast if found
            """
            return self.uiAutomatorHelper.api_instance.device_wait_for_new_toast_get(timeout=timeout)

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
            :rtype: list
            """
            return self.uiAutomatorHelper.api_instance.object_store_list_get()

        def remove(self, oid: int):
            """
            Removes an object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml

            :param oid: the object id
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

        def click(self, x: int, y: int):
            """
            Clicks on the specified coordinates.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return:
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_device_click_get(x=x, y=y))

        def dump_window_hierarchy(self, _format='JSON'):
            """
            Dumps the window hierarchy.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param _format: the format (e.g.: JSON, XML)
            :return: the window hierarchy
            """
            return self.uiAutomatorHelper.api_instance.ui_device_dump_window_hierarchy_get(format=_format)

        @kato.kato
        def find_object(self, **kwargs):
            """
            Finds an object.
            Invokes GET or POST method depending on the arguments passed.

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

        # @kato.kato
        def find_objects(self, **kwargs):
            """
            Finds objects.
            Invokes GET or POST method depending on the arguments passed.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return:
            """
            if 'body' in kwargs:
                return self.uiAutomatorHelper.api_instance.ui_device_find_objects_post(**kwargs)
            if 'by_selector' in kwargs:
                return self.uiAutomatorHelper.api_instance.ui_device_find_objects_get(**kwargs)
            body = culebratester_client.Selector(**kwargs)
            return self.uiAutomatorHelper.api_instance.ui_device_find_objects_post(body=body)

        # @kato.kato
        def has_object(self, **kwargs) -> bool:
            """
            Has an object.
            Invokes GET or POST method depending on the arguments passed.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return: True or False
            """
            if 'body' in kwargs:
                return self.uiAutomatorHelper.api_instance.ui_device_has_object_post(**kwargs).value
            if self.some(['resource_id', 'ui_selector', 'by_selector'], kwargs):
                return self.uiAutomatorHelper.api_instance.ui_device_has_object_get(**kwargs).value
            body = culebratester_client.Selector(**kwargs)
            return self.uiAutomatorHelper.api_instance.ui_device_has_object_post(body=body).value

        def press_back(self) -> None:
            """
            Presses BACK.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return:
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_device_press_back_get())

        def press_enter(self) -> None:
            """
            Presses ENTER.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return:
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_device_press_enter_get())

        def press_home(self) -> None:
            """
            Presses HOME.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return:
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_device_press_home_get())

        def press_recent_apps(self) -> None:
            """
            Press recent apps.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :return:
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_device_press_recent_apps_get())

        def press_key_code(self, key_code: int, meta_state: int = 0) -> None:
            """
            Presses a key code.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param key_code:
            :param meta_state:
            :return:
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_device_press_key_code_get(key_code=key_code,
                                                                                            meta_state=meta_state))

        def swipe(self, **kwargs) -> None:
            """
            Swipes.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return:
            """
            if self.all(['start_x', 'start_y', 'end_x', 'end_y', 'steps'], kwargs):
                check_response(self.uiAutomatorHelper.api_instance.ui_device_swipe_get(**kwargs))
                return
            if 'segments' in kwargs:
                # noinspection PyBroadException
                try:
                    segments = kwargs['segments']
                    if isinstance(segments, list):
                        if all(isinstance(e, tuple) for e in segments):
                            kwargs['segments'] = list(map(lambda e: Point(*e), segments))
                except Exception:
                    pass
            body = culebratester_client.SwipeBody(**kwargs)
            check_response(self.uiAutomatorHelper.api_instance.ui_device_swipe_post(body=body))

        def take_screenshot(self, scale=1.0, quality=90, filename=None, **kwargs):
            """
            Takes screenshot.
            Eventually save it in a file specified by filename.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param scale: the scale
            :param quality: the quality
            :param filename: if specified the image will be saved in filename
            :param kwargs: optional arguments
            :return: the response containing the image binary if the filename was not specified
            """
            if filename:
                img = self.uiAutomatorHelper.api_instance.ui_device_screenshot_get(scale=scale,
                                                                                   quality=quality,
                                                                                   _preload_content=False,
                                                                                   **kwargs).read()
                with open(filename, 'wb') as file:
                    file.write(img)
                return
            return self.uiAutomatorHelper.api_instance.ui_device_screenshot_get(scale=scale,
                                                                                quality=quality,
                                                                                _preload_content=False,
                                                                                **kwargs)

        def wait(self, oid: int, timeout=10000):
            """
            Waits for a search condition.

            :param oid: the search condition ref (oid)
            :param timeout: the timeout in ms
            :return: The final result returned by the condition, or null if the condition was not met before the timeout.
            """
            return self.uiAutomatorHelper.api_instance.ui_device_wait_get(oid=oid,
                                                                          timeout=timeout)

        def wait_for_idle(self, **kwargs) -> None:
            """
            Waits for idle.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param kwargs:
            :return:
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_device_wait_for_idle_get(**kwargs))

        def wait_for_window_update(self, timeout=5000, **kwargs) -> None:
            """
            Waits for window update.

            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param timeout: the timeout
            :param kwargs:
            :return:
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_device_wait_for_window_update_get(timeout, **kwargs))

    #
    # UiObject
    #
    class UiObject(ApiBase):
        """
        Inner UiObject class.

        Notice that this class does not require an OID in its constructor.
        """

        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def dump(self, oid: int):
            """

            :param oid:
            :return:
            """
            return self.uiAutomatorHelper.api_instance.ui_object_oid_dump_get(oid=oid)

        def exists(self, oid: int) -> bool:
            """
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid:
            :return:
            """
            response: BooleanResponse = self.uiAutomatorHelper.api_instance.ui_object_oid_exists_get(oid=oid)
            return response.value

        def get_child_count(self, oid: int) -> int:
            """
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid:
            :return:
            """
            response: NumberResponse = self.uiAutomatorHelper.api_instance.ui_object_oid_get_child_count_get(oid=oid)
            return int(response.value)

        def perform_two_pointer_gesture(self, oid: int, startPoint1: Tuple[int, int], startPoint2: Tuple[int, int],
                                        endPoint1: Tuple[int, int], endPoint2: Tuple[int, int], steps: int) -> None:
            """
            Generates a two-pointer gesture with arbitrary starting and ending points.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :param startPoint1:
            :param startPoint2:
            :param endPoint1:
            :param endPoint2:
            :param steps:
            :return: the result of the operation
            """
            body = PerformTwoPointerGestureBody(Point(startPoint1[0], startPoint1[1]),
                                                Point(startPoint2[0], startPoint2[1]),
                                                Point(endPoint1[0], endPoint1[1]),
                                                Point(endPoint2[0], endPoint2[1]),
                                                steps)
            response = self.uiAutomatorHelper.api_instance.ui_object_oid_perform_two_pointer_gesture_post(oid=oid,
                                                                                                          body=body)
            check_response(response)

        def pinch_in(self, oid: int, percentage: int, steps: int = 50) -> None:
            """
            Performs a two-pointer gesture, where each pointer moves diagonally toward the other, from the edges to the
            center of this UiObject.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :param percentage: percentage of the object's diagonal length for the pinch gesture
            :param steps: the number of steps for the gesture. Steps are injected about 5 milliseconds apart, so 100
            steps may take around 0.5 seconds to complete.
            :return: the result of the operation
            """
            response = self.uiAutomatorHelper.api_instance.ui_object_oid_pinch_in_get(oid=oid, percentage=percentage,
                                                                                      steps=steps)
            check_response(response)

        def pinch_out(self, oid: int, percentage: int, steps: int = 50) -> None:
            """
            Performs a two-pointer gesture, where each pointer moves diagonally opposite across the other, from the
            center out towards the edges of the UiObject.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :param percentage: percentage of the object's diagonal length for the pinch gesture
            :param steps: the number of steps for the gesture. Steps are injected about 5 milliseconds apart, so 100
            steps may take around 0.5 seconds to complete.
            :return: the result of the operation
            """
            response = self.uiAutomatorHelper.api_instance.ui_object_oid_pinch_out_get(oid=oid, percentage=percentage,
                                                                                       steps=steps)

            check_response(response)

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

        def clear(self, oid: int) -> None:
            """
            Clears the text content if this object is an editable field.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the result of the operation
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_object2_clear_get(oid=oid))

        def click(self, oid: int) -> None:
            """
            Clicks on this object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the result of the operation
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_object2_oid_click_get(oid=oid))

        def click_and_wait(self, oid: int, event_condition_ref, timeout=10000) -> None:
            """
            Clicks and wait.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :param event_condition_ref: the event condition
            :param timeout: the timeout
            :return: the status response
            """
            check_response(
                self.uiAutomatorHelper.api_instance.ui_object2_oid_click_and_wait_get(oid, event_condition_ref,
                                                                                      timeout=timeout))

        def dump(self, oid):
            """
            Dumps the content of an object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the content
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_oid_dump_get(oid=oid)

        def get_content_description(self, oid: int) -> str:
            """
            Returns the content description for this object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the text
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_oid_get_content_description_get(oid=oid)

        def get_text(self, oid: int) -> str:
            """
            Returns the text value for this object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the text
            """
            return self.uiAutomatorHelper.api_instance.ui_object2_oid_get_text_get(oid=oid)

        def long_click(self, oid: int) -> None:
            """
            Performs a long click on this object.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :return: the result of the operation
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_object2_oid_long_click_get(oid=oid))

        def set_text(self, oid: int, text: str):
            """
            Sets the text content if this object is an editable field.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml
            :param oid: the oid
            :param text: the text
            :return: the result of the operation
            """
            check_response(self.uiAutomatorHelper.api_instance.ui_object2_oid_set_text_post(oid=oid, body=Text(text)))

    #
    # Until
    #
    class Until(ApiBase):
        def __init__(self, uiAutomatorHelper) -> None:
            super().__init__(uiAutomatorHelper)

        def find_object(self, **kwargs) -> ObjectRef:
            """
            Returns a SearchCondition that is satisfied when at least one element matching the selector can be found.
            The condition will return the first matching element.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml

            :param kwargs: the arguments
            :return: the search condition reference
            """
            if 'body' in kwargs:
                return self.uiAutomatorHelper.api_instance.until_find_object_post(**kwargs)
            if 'by_selector' in kwargs:
                return self.uiAutomatorHelper.api_instance.until_find_object_get(**kwargs)
            body = culebratester_client.Selector(**kwargs)
            return self.uiAutomatorHelper.api_instance.until_find_object_post(body=body)

        def find_objects(self, **kwargs) -> List[ObjectRef]:
            """
            Returns a ``SearchCondition`` that is satisfied when at least one element matching the selector can be found.
            The condition will return the first matching element.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml

            :param kwargs: the arguments
            :return: the search condition object reference
            """
            if 'body' in kwargs:
                return self.uiAutomatorHelper.api_instance.until_find_objects_post(**kwargs)
            if 'by_selector' in kwargs:
                return self.uiAutomatorHelper.api_instance.until_find_objects_get(**kwargs)
            body = culebratester_client.Selector(**kwargs)
            return self.uiAutomatorHelper.api_instance.until_find_objects_post(body=body)

        def new_window(self) -> ObjectRef:
            """
            Returns a condition that depends on a new window having appeared.
            :see https://github.com/dtmilano/CulebraTester2-public/blob/master/openapi.yaml

            :return: the event condition reference
            :rtype: Until object reference
            """
            return self.uiAutomatorHelper.api_instance.until_new_window_get()
