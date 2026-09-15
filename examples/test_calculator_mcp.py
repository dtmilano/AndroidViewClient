#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Calculator app using CulebraTester2 MCP server.

This example demonstrates how to use the CulebraTester2 client directly
to interact with the Android Calculator app. The same operations can be
performed through the MCP server by an AI assistant.

Requirements:
1. CulebraTester2 server running on device (http://localhost:9987)
2. Calculator app installed on device
3. culebratester-client package installed

Copyright (C) 2012-2024  Diego Torres Milano
"""

import sys
import os
import json
import base64
import time

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from culebratester_client import ApiClient, Configuration
from culebratester_client.api import DefaultApi
from culebratester_client.rest import ApiException

# Initialize client
BASE_URL = os.environ.get('CULEBRATESTER2_URL', 'http://localhost:9987')
configuration = Configuration()
configuration.host = "{}/v2".format(BASE_URL)
api_client = ApiClient(configuration)
client = DefaultApi(api_client)

print("=" * 70)
print("CulebraTester2 Calculator Test Example")
print("=" * 70)

# 1. Get device info
print("\n1. Getting device info...")
try:
    displayInfo = client.device_display_real_size_get()
    print("   Device: {}".format(displayInfo.device if hasattr(displayInfo, 'device') else 'unknown'))
    print("   Display: {}x{}".format(
        displayInfo.x if hasattr(displayInfo, 'x') else 0,
        displayInfo.y if hasattr(displayInfo, 'y') else 0
    ))
except Exception as e:
    print("   Error: {}".format(e))
    sys.exit(1)

# 2. Start Calculator app
print("\n2. Starting Calculator app...")
try:
    # Try Google Calculator first
    package = "com.google.android.calculator"
    result = client.target_context_start_activity_get(component=package)
    print("   Started: {}".format(package))
    time.sleep(2)  # Wait for app to start
except Exception as e:
    print("   Error: {}".format(e))
    print("   Note: Make sure Calculator app is installed")

# 3. Get current package to verify
print("\n3. Verifying current app...")
try:
    current = client.ui_device_current_package_name_get()
    package_name = current.current_package_name if hasattr(current, 'current_package_name') else str(current)
    print("   Current package: {}".format(package_name))
except Exception as e:
    print("   Error: {}".format(e))

# 4. Dump UI hierarchy to see available elements
print("\n4. Dumping UI hierarchy...")
try:
    hierarchy = client.ui_device_dump_window_hierarchy_get()
    hierarchy_dict = hierarchy.to_dict() if hasattr(hierarchy, 'to_dict') else hierarchy
    if 'hierarchy' in hierarchy_dict:
        xml_len = len(hierarchy_dict['hierarchy'])
        print("   Got hierarchy XML ({} chars)".format(xml_len))
        
        # Extract some button texts
        import re
        texts = re.findall(r'text="([^"]+)"', hierarchy_dict['hierarchy'])
        digit_buttons = [t for t in texts if t.isdigit()]
        if digit_buttons:
            print("   Found digit buttons: {}".format(', '.join(digit_buttons[:10])))
except Exception as e:
    print("   Error: {}".format(e))

# 5. Perform calculation: 5 + 3 = 8
print("\n5. Performing calculation: 5 + 3 = 8")
calculation_steps = [
    ("5", "digit 5"),
    ("+", "plus operator"),
    ("3", "digit 3"),
    ("=", "equals")
]

element_store = {}  # Simulate the ObjectStore

for text, description in calculation_steps:
    print("   Finding {}...".format(description))
    try:
        selector = {"text": text}
        oid_response = client.ui_device_find_object_post(body=selector)
        
        if oid_response and hasattr(oid_response, 'oid'):
            oid = oid_response.oid
            element_id = "element_{}".format(oid)
            element_store[element_id] = oid
            print("     Found: {} (OID: {})".format(text, oid))
            
            # Click the element
            print("     Clicking...")
            result = client.ui_object2_oid_click_get(oid)
            print("     Clicked successfully")
            time.sleep(0.5)  # Small delay between clicks
        else:
            print("     Not found: {}".format(text))
            
    except ApiException as e:
        if e.status == 404:
            print("     Not found: {} (404)".format(text))
        else:
            print("     API error: {} - {}".format(e.status, e.reason))
    except Exception as e:
        print("     Error: {}".format(e))

# 6. Take a screenshot
print("\n6. Taking screenshot...")
try:
    screenshot_data = client.ui_device_screenshot_get()
    
    # Convert string representation to bytes
    if isinstance(screenshot_data, str):
        if screenshot_data.startswith("b'") or screenshot_data.startswith('b"'):
            import ast
            screenshot_bytes = ast.literal_eval(screenshot_data)
        else:
            screenshot_bytes = screenshot_data.encode('utf-8')
    else:
        screenshot_bytes = screenshot_data
    
    # Save screenshot
    output_file = '/tmp/calculator_test.png'
    with open(output_file, 'wb') as f:
        f.write(screenshot_bytes)
    print("   Screenshot saved: {}".format(output_file))
    
    # Also show base64 length (as MCP would return)
    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    print("   Base64 length: {} chars".format(len(screenshot_b64)))
    
except Exception as e:
    print("   Error: {}".format(e))

# 7. Try to read the result
print("\n7. Reading calculation result...")
result_ids = [
    "com.google.android.calculator:id/result_final",
    "com.google.android.calculator:id/result",
    "com.google.android.calculator:id/formula"
]

for resource_id in result_ids:
    try:
        print("   Trying resource ID: {}".format(resource_id))
        selector = {"res": resource_id}
        oid_response = client.ui_device_find_object_post(body=selector)
        
        if oid_response and hasattr(oid_response, 'oid'):
            oid = oid_response.oid
            print("     Found result element (OID: {})".format(oid))
            
            # Try to get text from the element
            try:
                text_response = client.ui_object2_oid_get_text_get(oid)
                text = text_response.text if hasattr(text_response, 'text') else str(text_response)
                print("     Result text: '{}'".format(text))
                break
            except Exception as e:
                print("     Could not get text: {}".format(e))
        else:
            print("     Not found")
            
    except ApiException as e:
        if e.status == 404:
            print("     Not found (404)")
        else:
            print("     API error: {} - {}".format(e.status, e.reason))
    except Exception as e:
        print("     Error: {}".format(e))

print("\n" + "=" * 70)
print("Test completed!")
print("=" * 70)
print("\nNote: These same operations can be performed by an AI assistant")
print("through the MCP server using natural language commands.")
print("\nExample MCP tool calls:")
print("  - getDeviceInfo()")
print("  - startApp(packageName='com.google.android.calculator')")
print("  - findElementByText(text='5')")
print("  - clickElement(elementId='element_123')")
print("  - takeScreenshot()")
print("  - dumpUiHierarchy()")
