#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test screenshot functionality via MCP server.

This script tests the takeScreenshot tool to verify it properly handles
the byte string conversion and base64 encoding.
"""

import sys
import os
import json
import base64

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

print("Testing screenshot API...")
print("Base URL: {}".format(BASE_URL))

try:
    # Get screenshot from API
    screenshot_data = client.ui_device_screenshot_get()
    print("\nScreenshot data type: {}".format(type(screenshot_data)))
    print("Screenshot data (first 100 chars): {}".format(str(screenshot_data)[:100]))
    
    # Test the conversion logic from tools.py
    if isinstance(screenshot_data, str):
        print("\nData is a string")
        if screenshot_data.startswith("b'") or screenshot_data.startswith('b"'):
            print("String starts with b' or b\" - using ast.literal_eval")
            import ast
            screenshot_bytes = ast.literal_eval(screenshot_data)
            print("Converted to bytes, length: {}".format(len(screenshot_bytes)))
        else:
            print("String doesn't start with b' - encoding as UTF-8")
            screenshot_bytes = screenshot_data.encode('utf-8')
    else:
        print("\nData is already bytes")
        screenshot_bytes = screenshot_data
    
    # Convert to base64
    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
    print("\nBase64 encoded, length: {}".format(len(screenshot_b64)))
    print("Base64 (first 100 chars): {}".format(screenshot_b64[:100]))
    
    # Try to decode back to verify it's valid
    decoded_bytes = base64.b64decode(screenshot_b64)
    print("\nDecoded back to bytes, length: {}".format(len(decoded_bytes)))
    
    # Check if it's a valid PNG
    if decoded_bytes.startswith(b'\x89PNG'):
        print("✅ Valid PNG header detected!")
    else:
        print("❌ Not a valid PNG - header: {}".format(decoded_bytes[:10]))
    
    # Save to file for verification
    output_file = '/tmp/test_screenshot.png'
    with open(output_file, 'wb') as f:
        f.write(decoded_bytes)
    print("\n✅ Screenshot saved to: {}".format(output_file))
    
except Exception as e:
    print("\n❌ Error: {}".format(e))
    import traceback
    traceback.print_exc()
