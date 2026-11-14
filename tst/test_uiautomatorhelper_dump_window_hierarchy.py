#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for UiAutomatorHelper.UiDevice.dump_window_hierarchy.

No device needed: the generated API client is replaced with a mock, so these
check only how the helper calls it and what it hands back.
"""

import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from com.dtmilano.android.uiautomator.uiautomatorhelper import UiAutomatorHelper

XML = "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><hierarchy rotation=\"0\"/>"


def _ui_device():
    helper = mock.Mock()
    return UiAutomatorHelper.UiDevice(helper), helper.api_instance.ui_device_dump_window_hierarchy_get


def test_xml_returns_the_document_without_deserializing():
    # The server sends XML as text/plain; deserializing it into the declared WindowHierarchy
    # model fails, so the helper must ask for the raw body and decode it.
    ui_device, call = _ui_device()
    call.return_value = mock.Mock(data=XML.encode('utf-8'))

    result = ui_device.dump_window_hierarchy(_format='XML')

    assert result == XML
    call.assert_called_once_with(format='XML', _preload_content=False)


def test_xml_format_is_case_insensitive():
    ui_device, call = _ui_device()
    call.return_value = mock.Mock(data=XML.encode('utf-8'))

    assert ui_device.dump_window_hierarchy(_format='xml') == XML


def test_json_is_still_deserialized():
    ui_device, call = _ui_device()
    sentinel = object()
    call.return_value = sentinel

    assert ui_device.dump_window_hierarchy() is sentinel
    call.assert_called_once_with(format='JSON')
