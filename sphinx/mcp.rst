MCP Server for AI-Powered Testing
==================================

The Model Context Protocol (MCP) server enables AI assistants to interact with Android devices through natural language commands.

Overview
--------

The CulebraTester2 MCP server exposes 20 tools that allow AI assistants like Kiro to:

* Find and interact with UI elements
* Perform coordinate-based gestures
* Control device state (wake, sleep, etc.)
* Launch applications and navigate
* Capture screenshots and UI hierarchies

Installation
------------

Install AndroidViewClient with MCP support::

    pip3 install androidviewclient --upgrade

The MCP server is automatically available as the ``culebra-mcp`` command.

Quick Start
-----------

1. **Start CulebraTester2 on your device**::

    adb install -r culebratester2.apk
    adb shell am instrument -w com.dtmilano.android.culebratester2/.CulebraTester2Instrumentation
    adb forward tcp:9987 tcp:9987

2. **Configure your AI assistant**

   Add to ``.kiro/settings/mcp.json``::

    {
      "mcpServers": {
        "culebratester2": {
          "command": "culebra-mcp",
          "env": {
            "CULEBRATESTER2_URL": "http://localhost:9987"
          }
        }
      }
    }

3. **Start testing with natural language**:

   * "Get the device screen size"
   * "Launch the Calculator app"
   * "Find the button with text Submit and click it"
   * "Take a screenshot"

Environment Variables
---------------------

.. envvar:: CULEBRATESTER2_URL

   Base URL where CulebraTester2 is running.
   
   Default: ``http://localhost:9987``

.. envvar:: CULEBRATESTER2_TIMEOUT

   HTTP request timeout in seconds.
   
   Default: ``30``

Available Tools
---------------

Element-Based Interactions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: getDeviceInfo()

   Get device display information including screen dimensions and density.
   
   :returns: JSON with display width, height, and density

.. function:: dumpUiHierarchy()

   Dump the current UI hierarchy as XML.
   
   :returns: JSON with complete UI hierarchy

.. function:: findElementByText(text)

   Find a UI element by its text content.
   
   :param text: The text to search for
   :returns: JSON with element ID and metadata

.. function:: findElementByResourceId(resourceId)

   Find a UI element by its resource ID.
   
   :param resourceId: The resource ID (e.g., "com.example:id/button")
   :returns: JSON with element ID and metadata

.. function:: clickElement(elementId)

   Click on a previously found UI element.
   
   :param elementId: The element ID from findElementByText or findElementByResourceId
   :returns: JSON with success status

.. function:: longClickElement(elementId)

   Long click on a previously found UI element.
   
   :param elementId: The element ID
   :returns: JSON with success status

.. function:: enterText(elementId, text)

   Enter text into a UI element (e.g., EditText field).
   
   :param elementId: The element ID
   :param text: The text to enter
   :returns: JSON with success status

.. function:: clearText(elementId)

   Clear text from a UI element.
   
   :param elementId: The element ID
   :returns: JSON with success status

.. function:: pressBack()

   Press the Android BACK button.
   
   :returns: JSON with success status

.. function:: pressHome()

   Press the Android HOME button.
   
   :returns: JSON with success status

.. function:: takeScreenshot()

   Take a screenshot of the current screen.
   
   :returns: JSON with base64-encoded screenshot data

.. function:: startApp(packageName, activityName)

   Start an Android application.
   
   :param packageName: The package name (e.g., "com.example.app")
   :param activityName: Optional activity name (e.g., ".MainActivity")
   :returns: JSON with success status

Coordinate-Based Interactions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: clickAtCoordinates(x, y)

   Click at specific screen coordinates.
   
   :param x: X coordinate (non-negative)
   :param y: Y coordinate (non-negative)
   :returns: JSON with success status

.. function:: longClickAtCoordinates(x, y)

   Long click at specific screen coordinates.
   
   :param x: X coordinate (non-negative)
   :param y: Y coordinate (non-negative)
   :returns: JSON with success status

.. function:: swipeGesture(startX, startY, endX, endY, steps)

   Perform a swipe gesture.
   
   :param startX: Starting X coordinate
   :param startY: Starting Y coordinate
   :param endX: Ending X coordinate
   :param endY: Ending Y coordinate
   :param steps: Number of steps (default: 10)
   :returns: JSON with success status

Device Actions
~~~~~~~~~~~~~~

.. function:: wakeDevice()

   Wake up the device (turn screen on).
   
   :returns: JSON with success status

.. function:: sleepDevice()

   Put the device to sleep (turn screen off).
   
   :returns: JSON with success status

.. function:: pressRecentApps()

   Press the Recent Apps button.
   
   :returns: JSON with success status

.. function:: getCurrentPackage()

   Get the package name of the currently running app.
   
   :returns: JSON with package name

.. function:: forceStopApp(packageName)

   Force stop an application.
   
   :param packageName: The package name to stop
   :returns: JSON with success status

Architecture
------------

The MCP server consists of three main components:

1. **CulebraTester2Client**: HTTP client wrapper for the CulebraTester2 API
2. **ObjectStore**: In-memory storage for UI element references
3. **MCP Tools**: 20 tool handlers that expose functionality to AI assistants

All tools return JSON responses with a consistent format::

    {
      "success": true,
      "data": { ... }
    }

Or on error::

    {
      "success": false,
      "error": "Error message"
    }

Examples
--------

See ``examples/mcp_config.json`` for complete MCP configuration and ``examples/test_calculator_mcp.py`` for usage examples.

Troubleshooting
---------------

**Connection Refused**

If you see "Connection refused" errors:

1. Verify CulebraTester2 is running on the device
2. Check port forwarding: ``adb forward tcp:9987 tcp:9987``
3. Verify the device is connected: ``adb devices``

**Element Not Found**

If elements cannot be found:

1. Use ``dumpUiHierarchy()`` to inspect the current UI
2. Verify the text or resource ID is correct
3. Wait for the UI to load before searching

**Timeout Errors**

If requests timeout:

1. Increase ``CULEBRATESTER2_TIMEOUT`` environment variable
2. Check network connectivity to the device
3. Verify CulebraTester2 is responding

API Reference
-------------

.. automodule:: com.dtmilano.android.mcp.server
   :members:

.. automodule:: com.dtmilano.android.mcp.client
   :members:

.. automodule:: com.dtmilano.android.mcp.object_store
   :members:

.. automodule:: com.dtmilano.android.mcp.tools
   :members:
