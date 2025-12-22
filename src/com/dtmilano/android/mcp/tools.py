#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Tool Handlers for CulebraTester2

This module implements all MCP tool handlers that expose CulebraTester2
functionality through the Model Context Protocol.

Copyright (C) 2012-2024  Diego Torres Milano
Created on 2024-12-20 by Culebra

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import base64
import logging
from typing import Dict, Any

from culebratester_client.rest import ApiException
from com.dtmilano.android.mcp.server import mcp, client, objectStore

logger = logging.getLogger('culebratester2-mcp.tools')


@mcp.tool()
def getDeviceInfo() -> str:
    """
    Get device display information including screen dimensions and density.
    
    Returns:
        JSON string with display info (width, height, density, etc.)
    """
    logger.info("Tool called: getDeviceInfo")
    try:
        displayInfo = client.device_display_real_size_get()
        result = {
            "success": True,
            "data": {
                "width": displayInfo.x if hasattr(displayInfo, 'x') else None,
                "height": displayInfo.y if hasattr(displayInfo, 'y') else None,
                "device": displayInfo.device if hasattr(displayInfo, 'device') else None
            }
        }
        logger.debug("getDeviceInfo result: {}".format(result))
        return json.dumps(result)
    except Exception as e:
        logger.error("getDeviceInfo failed: {}".format(e))
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def dumpUiHierarchy() -> str:
    """
    Dump the current UI hierarchy as XML.
    
    Returns:
        JSON string with UI hierarchy XML
    """
    try:
        hierarchy = client.ui_device_dump_window_hierarchy_get()
        # Convert the WindowHierarchy object to a dictionary
        hierarchy_dict = hierarchy.to_dict() if hasattr(hierarchy, 'to_dict') else hierarchy
        return json.dumps({
            "success": True,
            "data": hierarchy_dict
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def findElementByText(text: str) -> str:
    """
    Find a UI element by its text content.
    
    Args:
        text: The text to search for
        
    Returns:
        JSON string with element info or error
    """
    logger.info("Tool called: findElementByText(text='{}')".format(text))
    try:
        # Use POST method with selector as body (not wrapped in "selector" key)
        selector = {"text": text}
        oid = client.ui_device_find_object_post(body=selector)
        
        if oid and hasattr(oid, 'oid'):
            # Store OID for later use
            elementId = "element_{}".format(oid.oid)
            objectStore.store(elementId, oid.oid)
            result = {
                "success": True,
                "elementId": elementId,
                "oid": oid.oid
            }
            logger.debug("findElementByText found element: {}".format(result))
            return json.dumps(result)
        else:
            logger.warning("findElementByText: Element not found")
            return json.dumps({
                "success": False,
                "error": "Element not found"
            })
    except ApiException as e:
        if e.status == 404:
            logger.info("findElementByText: Element with text '{}' not found (404)".format(text))
            return json.dumps({
                "success": False,
                "error": "Element not found with text: {}".format(text)
            })
        else:
            logger.error("findElementByText API error: {} - {}".format(e.status, e.reason))
            return json.dumps({
                "success": False,
                "error": "API error: {} - {}".format(e.status, e.reason)
            })
    except Exception as e:
        logger.error("findElementByText failed: {}".format(e))
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def findElementByResourceId(resourceId: str) -> str:
    """
    Find a UI element by its resource ID.
    
    Args:
        resourceId: The resource ID to search for (e.g., "com.example:id/button")
        
    Returns:
        JSON string with element info or error
    """
    logger.info("Tool called: findElementByResourceId(resourceId='{}')".format(resourceId))
    try:
        # Use POST method with selector as body (not wrapped in "selector" key)
        selector = {"res": resourceId}
        oid = client.ui_device_find_object_post(body=selector)
        
        if oid and hasattr(oid, 'oid'):
            # Store OID for later use
            elementId = "element_{}".format(oid.oid)
            objectStore.store(elementId, oid.oid)
            result = {
                "success": True,
                "elementId": elementId,
                "oid": oid.oid
            }
            logger.debug("findElementByResourceId found element: {}".format(result))
            return json.dumps(result)
        else:
            logger.warning("findElementByResourceId: Element not found")
            return json.dumps({
                "success": False,
                "error": "Element not found"
            })
    except ApiException as e:
        if e.status == 404:
            logger.info("findElementByResourceId: Element with resourceId '{}' not found (404)".format(resourceId))
            return json.dumps({
                "success": False,
                "error": "Element not found with resourceId: {}".format(resourceId)
            })
        else:
            logger.error("findElementByResourceId API error: {} - {}".format(e.status, e.reason))
            return json.dumps({
                "success": False,
                "error": "API error: {} - {}".format(e.status, e.reason)
            })
    except Exception as e:
        logger.error("findElementByResourceId failed: {}".format(e))
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def clickElement(elementId: str) -> str:
    """
    Click on a previously found UI element.
    
    Args:
        elementId: The ID of the element to click (from findElementByText or findElementByResourceId)
        
    Returns:
        JSON string with success status
    """
    logger.info("Tool called: clickElement(elementId='{}')".format(elementId))
    try:
        if not objectStore.exists(elementId):
            logger.warning("clickElement: Element not found in store")
            return json.dumps({
                "success": False,
                "error": "Element not found in store. Use findElementByText or findElementByResourceId first."
            })
        
        oid = objectStore.get(elementId)
        logger.debug("clickElement: Clicking OID {}".format(oid))
        result = client.ui_object2_oid_click_get(oid)
        logger.debug("clickElement: Success")
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        logger.error("clickElement failed: {}".format(e))
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def enterText(elementId: str, text: str) -> str:
    """
    Enter text into a UI element (e.g., EditText field).
    
    Args:
        elementId: The ID of the element to enter text into
        text: The text to enter
        
    Returns:
        JSON string with success status
    """
    try:
        if not objectStore.exists(elementId):
            return json.dumps({
                "success": False,
                "error": "Element not found in store. Use findElementByText or findElementByResourceId first."
            })
        
        oid = objectStore.get(elementId)
        result = client.ui_object2_oid_set_text_post(oid, body={"text": text})
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def pressBack() -> str:
    """
    Press the Android BACK button.
    
    Returns:
        JSON string with success status
    """
    try:
        result = client.ui_device_press_back_get()
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def pressHome() -> str:
    """
    Press the Android HOME button.
    
    Returns:
        JSON string with success status
    """
    try:
        result = client.ui_device_press_home_get()
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def takeScreenshot() -> str:
    """
    Take a screenshot of the current screen.
    
    Returns:
        JSON string with base64-encoded screenshot data
    """
    try:
        screenshot_data = client.ui_device_screenshot_get()
        
        # The API returns a string representation of bytes, convert it properly
        if isinstance(screenshot_data, str):
            # If it's a string starting with "b'", it's a string representation of bytes
            if screenshot_data.startswith("b'") or screenshot_data.startswith('b"'):
                # Use ast.literal_eval to safely convert string representation to bytes
                import ast
                screenshot_bytes = ast.literal_eval(screenshot_data)
            else:
                # It's already a base64 string or regular string
                screenshot_bytes = screenshot_data.encode('utf-8')
        else:
            # It's already bytes
            screenshot_bytes = screenshot_data
        
        # Convert bytes to base64 for JSON serialization
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        return json.dumps({
            "success": True,
            "data": screenshot_b64,
            "format": "base64"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def startApp(packageName: str, activityName: str = None) -> str:
    """
    Start an Android application.
    
    Args:
        packageName: The package name of the app (e.g., "com.example.app")
        activityName: Optional activity name to start (e.g., ".MainActivity")
        
    Returns:
        JSON string with success status
    """
    try:
        # Build component string
        if activityName:
            component = "{}/{}".format(packageName, activityName)
        else:
            component = packageName
        
        result = client.target_context_start_activity_get(component=component)
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def clickAtCoordinates(x: int, y: int) -> str:
    """
    Click at specific screen coordinates.
    
    Args:
        x: X coordinate (must be non-negative)
        y: Y coordinate (must be non-negative)
        
    Returns:
        JSON string with success status
    """
    try:
        # Validate coordinates
        if x < 0 or y < 0:
            return json.dumps({
                "success": False,
                "error": "Coordinates must be non-negative. Got x={}, y={}".format(x, y)
            })
        
        # Get display info to validate bounds
        displayInfo = client.device_display_real_size_get()
        width = displayInfo.x if hasattr(displayInfo, 'x') else 0
        height = displayInfo.y if hasattr(displayInfo, 'y') else 0
        
        if width > 0 and height > 0:
            if x >= width or y >= height:
                return json.dumps({
                    "success": False,
                    "error": "Coordinates out of bounds. Display is {}x{}, got ({}, {})".format(
                        width, height, x, y
                    )
                })
        
        result = client.ui_device_click_post(body={"x": x, "y": y})
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def longClickAtCoordinates(x: int, y: int) -> str:
    """
    Long click at specific screen coordinates.
    
    Args:
        x: X coordinate (must be non-negative)
        y: Y coordinate (must be non-negative)
        
    Returns:
        JSON string with success status
    """
    try:
        # Validate coordinates
        if x < 0 or y < 0:
            return json.dumps({
                "success": False,
                "error": "Coordinates must be non-negative. Got x={}, y={}".format(x, y)
            })
        
        # Get display info to validate bounds
        displayInfo = client.device_display_real_size_get()
        width = displayInfo.x if hasattr(displayInfo, 'x') else 0
        height = displayInfo.y if hasattr(displayInfo, 'y') else 0
        
        if width > 0 and height > 0:
            if x >= width or y >= height:
                return json.dumps({
                    "success": False,
                    "error": "Coordinates out of bounds. Display is {}x{}, got ({}, {})".format(
                        width, height, x, y
                    )
                })
        
        # Note: CulebraTester2 client doesn't have a direct long click at coordinates method
        # We'll use the drag method with same start/end coordinates and long duration
        result = client.ui_device_drag_get(start_x=x, start_y=y, end_x=x, end_y=y, steps=50)
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def swipeGesture(startX: int, startY: int, endX: int, endY: int, steps: int = 10) -> str:
    """
    Perform a swipe gesture from one coordinate to another.
    
    Args:
        startX: Starting X coordinate (must be non-negative)
        startY: Starting Y coordinate (must be non-negative)
        endX: Ending X coordinate (must be non-negative)
        endY: Ending Y coordinate (must be non-negative)
        steps: Number of steps for the swipe (default: 10, must be positive)
        
    Returns:
        JSON string with success status
    """
    try:
        # Validate coordinates
        if startX < 0 or startY < 0 or endX < 0 or endY < 0:
            return json.dumps({
                "success": False,
                "error": "Coordinates must be non-negative. Got start=({}, {}), end=({}, {})".format(
                    startX, startY, endX, endY
                )
            })
        
        if steps <= 0:
            return json.dumps({
                "success": False,
                "error": "Steps must be positive. Got steps={}".format(steps)
            })
        
        # Get display info to validate bounds
        displayInfo = client.device_display_real_size_get()
        width = displayInfo.x if hasattr(displayInfo, 'x') else 0
        height = displayInfo.y if hasattr(displayInfo, 'y') else 0
        
        if width > 0 and height > 0:
            if startX >= width or startY >= height or endX >= width or endY >= height:
                return json.dumps({
                    "success": False,
                    "error": "Coordinates out of bounds. Display is {}x{}, got start=({}, {}), end=({}, {})".format(
                        width, height, startX, startY, endX, endY
                    )
                })
        
        result = client.ui_device_swipe_post(body={
            "startX": startX,
            "startY": startY,
            "endX": endX,
            "endY": endY,
            "steps": steps
        })
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def wakeDevice() -> str:
    """
    Wake up the device (turn screen on).
    
    Returns:
        JSON string with success status
    """
    try:
        # Check if screen is already on
        is_on = client.ui_device_is_screen_on_get()
        if hasattr(is_on, 'value') and is_on.value:
            return json.dumps({
                "success": True,
                "data": "Screen already on"
            })
        
        # Wake up using power button press
        result = client.ui_device_press_key_code_get(key_code=26)  # KEYCODE_POWER
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def sleepDevice() -> str:
    """
    Put the device to sleep (turn screen off).
    
    Returns:
        JSON string with success status
    """
    try:
        # Check if screen is already off
        is_on = client.ui_device_is_screen_on_get()
        if hasattr(is_on, 'value') and not is_on.value:
            return json.dumps({
                "success": True,
                "data": "Screen already off"
            })
        
        # Sleep using power button press
        result = client.ui_device_press_key_code_get(key_code=26)  # KEYCODE_POWER
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def pressRecentApps() -> str:
    """
    Press the Recent Apps button to show recently used applications.
    
    Returns:
        JSON string with success status
    """
    try:
        result = client.ui_device_press_recent_apps_get()
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def getCurrentPackage() -> str:
    """
    Get the package name of the currently running application.
    
    Returns:
        JSON string with the current package name
    """
    try:
        package = client.ui_device_current_package_name_get()
        package_name = package.current_package_name if hasattr(package, 'current_package_name') else str(package)
        return json.dumps({
            "success": True,
            "packageName": package_name
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def forceStopApp(packageName: str) -> str:
    """
    Force stop an application.
    
    Args:
        packageName: The package name to force stop (e.g., "com.example.app")
        
    Returns:
        JSON string with success status
    """
    try:
        result = client.am_force_stop_get(package=packageName)
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def longClickElement(elementId: str) -> str:
    """
    Long click on a previously found UI element.
    
    Args:
        elementId: The ID of the element to long click (from findElementByText or findElementByResourceId)
        
    Returns:
        JSON string with success status
    """
    try:
        if not objectStore.exists(elementId):
            return json.dumps({
                "success": False,
                "error": "Element not found in store. Use findElementByText or findElementByResourceId first."
            })
        
        oid = objectStore.get(elementId)
        result = client.ui_object2_oid_long_click_get(oid)
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def clearText(elementId: str) -> str:
    """
    Clear text from a UI element (e.g., EditText field).
    
    Args:
        elementId: The ID of the element to clear text from
        
    Returns:
        JSON string with success status
    """
    try:
        if not objectStore.exists(elementId):
            return json.dumps({
                "success": False,
                "error": "Element not found in store. Use findElementByText or findElementByResourceId first."
            })
        
        oid = objectStore.get(elementId)
        result = client.ui_object2_oid_clear_get(oid)
        return json.dumps({
            "success": True,
            "data": str(result) if result else "OK"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })
