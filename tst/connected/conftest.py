import os

import pytest

from com.dtmilano.android.uiautomator.uiautomatorhelper import UiAutomatorHelper
from com.dtmilano.android.viewclient import ViewClient

DEBUG = False


@pytest.fixture(scope='module')
def avc():
    assert os.environ['SERIALNO']
    return ViewClient.connectToDeviceOrExit(serialno=os.environ['SERIALNO'])


@pytest.fixture(scope='module')
def helper(avc) -> UiAutomatorHelper:
    return ViewClient(*avc, useuiautomatorhelper=True).uiAutomatorHelper


@pytest.fixture(scope='function')
def calculator(avc, helper):
    if DEBUG:
        print('\nFixture: Starting Calculator')
    pkg = 'com.google.android.calculator'
    helper.target_context.start_activity(pkg, 'com.android.calculator2.Calculator')
    helper.ui_device.wait_for_idle()
    yield 'started'
    if DEBUG:
        print('\nfixture: Stopping Calculator')
    avc[0].forceStop(pkg)


@pytest.fixture(scope='function')
def oid_digit(helper, calculator):
    response = helper.ui_device.find_object(ui_selector='res@com.google.android.calculator:id/digit_9')
    assert response is not None
    assert response.oid > 0
    return response.oid


@pytest.fixture(scope='function')
def oid_group(helper, calculator):
    response = helper.ui_device.find_object(ui_selector='res@com.google.android.calculator:id/main_calculator')
    assert response is not None
    assert response.oid > 0
    return response.oid
