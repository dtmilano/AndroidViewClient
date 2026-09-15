#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test find and click functionality via MCP server.

This script tests the findElementByText and clickElement tools to verify
they properly handle the selector format and element interaction.
"""

import sys
import os
import json

try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from culebratester_client import ApiClient, Configuration
from culebratester_client.api import DefaultApi

# Initialize client
BASE_URL = os.environ.get('CULEBRATESTER2_URL', 'http://localhost:9987')
configuration = Configuration()
configuration.host = "{}/v2".format(BASE_URL)
api_client = ApiClient(configuration)
client = DefaultApi(api_client)

print("Testing find element and click...")
print("Base URL: {}".format(BASE_URL))

# First, get current package to see what's running
try:
    package = client.ui_device_current_package_name_get()
    package_name = package.current_package_name if hasattr(package, 'current_package_name') else str(package)
    print("\nCurrent package: {}".format(package_name))
except Exception as e:
    print("\n❌ Error getting current package: {}".format(e))

# Get UI hierarchy to see what elements are available
try:
    print("\nGetting UI hierarchy...")
    hierarchy = client.ui_device_dump_window_hierarchy_get()
    hierarchy_dict = hierarchy.to_dict() if hasattr(hierarchy, 'to_dict') else hierarchy
    
    # Extract some text elements from hierarchy
    if 'hierarchy' in hierarchy_dict:
        xml_content = hierarchy_dict['hierarchy']
        print("Hierarchy XML length: {} chars".format(len(xml_content)))
        
        # Look for text attributes in the XML
        import re
        text_matches = re.findall(r'text="([^"]+)"', xml_content)
        if text_matches:
            print("\nFound {} text elements:".format(len(text_matches)))
            for i, text in enumerate(text_matches[:10]):  # Show first 10
                if text.strip():  # Only show non-empty text
                    print("  [{}] {}".format(i, text))
        else:
            print("\nNo text elements found in hierarchy")
    
except Exception as e:
    print("\n❌ Error getting hierarchy: {}".format(e))
    import traceback
    traceback.print_exc()

# Try to find an element by text (using a common Android text)
test_texts = ["Search", "Apps", "Settings", "OK", "Cancel"]
found_element = None

for test_text in test_texts:
    try:
        print("\n\nTrying to find element with text: '{}'".format(test_text))
        selector = {"text": test_text}
        print("Selector: {}".format(selector))
        
        oid = client.ui_device_find_object_post(body=selector)
        print("Response type: {}".format(type(oid)))
        print("Response: {}".format(oid))
        
        if oid and hasattr(oid, 'oid'):
            print("✅ Found element! OID: {}".format(oid.oid))
            found_element = (test_text, oid.oid)
            break
        else:
            print("Element not found (no OID in response)")
            
    except Exception as e:
        print("❌ Error finding element: {}".format(e))
        import traceback
        traceback.print_exc()

# If we found an element, try to click it
if found_element:
    text, oid = found_element
    print("\n\n=== Testing click on element '{}' (OID: {}) ===".format(text, oid))
    try:
        result = client.ui_object2_oid_click_get(oid)
        print("✅ Click successful!")
        print("Result: {}".format(result))
    except Exception as e:
        print("❌ Error clicking element: {}".format(e))
        import traceback
        traceback.print_exc()
else:
    print("\n\nNo elements found to test clicking")
