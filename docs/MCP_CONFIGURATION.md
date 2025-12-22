# CulebraTester2 MCP Server Configuration Guide

This guide provides detailed instructions for configuring the CulebraTester2 MCP server with Kiro.

## Table of Contents

- [Overview](#overview)
- [Configuration File Locations](#configuration-file-locations)
- [Basic Configuration](#basic-configuration)
- [Configuration Options](#configuration-options)
- [Environment Variables](#environment-variables)
- [Auto-Approve Settings](#auto-approve-settings)
- [Debug Logging](#debug-logging)
- [Complete Examples](#complete-examples)
- [Troubleshooting](#troubleshooting)

## Overview

The CulebraTester2 MCP server integrates with Kiro (IDE or CLI) through MCP (Model Context Protocol) configuration files. These JSON files tell Kiro how to start and communicate with the MCP server.

## Configuration File Locations

### Workspace-Level Configuration (Kiro IDE)

**Location:** `.kiro/settings/mcp.json` (in your project workspace)

**Use when:**
- Working on a specific project
- Want different settings per project
- Developing or testing the MCP server itself

**Scope:** Only active when the workspace is open

### User-Level Configuration (Global)

**Location:** `~/.kiro/settings/mcp.json` (in your home directory)

**Use when:**
- Using `kiro-cli` (command-line interface)
- Want the MCP server available across all projects
- Using the installed package globally

**Scope:** Active everywhere, across all workspaces

### Priority

When both exist, workspace-level settings override user-level settings for that workspace.

## Basic Configuration

### Minimal Configuration (User-Level)

For `kiro-cli` or global use after installing via pip:

```json
{
  "mcpServers": {
    "culebratester2-mcp": {
      "command": "culebra-mcp",
      "args": []
    }
  }
}
```

This assumes:
- AndroidViewClient is installed via `pip install androidviewclient`
- CulebraTester2 is running on `http://localhost:9987` (default)
- Default timeout of 30 seconds

### Minimal Configuration (Workspace-Level)

For development or when working in the AndroidViewClient repository:

```json
{
  "mcpServers": {
    "culebratester2-mcp": {
      "command": "python3",
      "args": ["-m", "com.dtmilano.android.mcp.server"],
      "env": {
        "ANDROID_VIEW_CLIENT_HOME": "${workspaceFolder}",
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    }
  }
}
```

## Configuration Options

### Server Name

```json
{
  "mcpServers": {
    "culebratester2-mcp": {  // ← This is the server name
      ...
    }
  }
}
```

The server name (`culebratester2-mcp`) is how you reference this MCP server in Kiro. You can change it, but keep it descriptive.

### Command and Arguments

**Option 1: Using the installed command-line tool**

```json
{
  "command": "culebra-mcp",
  "args": []
}
```

**Option 2: Using Python module directly**

```json
{
  "command": "python3",
  "args": ["-m", "com.dtmilano.android.mcp.server"]
}
```

**Option 3: Using absolute path to script**

```json
{
  "command": "/path/to/AndroidViewClient/tools/culebra-mcp",
  "args": []
}
```

### Disabled Flag

Temporarily disable the server without removing the configuration:

```json
{
  "disabled": true  // Set to false or remove to enable
}
```

## Environment Variables

All environment variables are optional and have sensible defaults.

### CULEBRATESTER2_URL

**Purpose:** URL where CulebraTester2 service is running

**Default:** `http://localhost:9987`

**Examples:**

```json
{
  "env": {
    "CULEBRATESTER2_URL": "http://localhost:9987"
  }
}
```

```json
{
  "env": {
    "CULEBRATESTER2_URL": "http://192.168.1.100:9987"
  }
}
```

### CULEBRATESTER2_TIMEOUT

**Purpose:** HTTP request timeout in seconds

**Default:** `30`

**Example:**

```json
{
  "env": {
    "CULEBRATESTER2_TIMEOUT": "60"
  }
}
```

### CULEBRATESTER2_DEBUG

**Purpose:** Enable debug logging for troubleshooting

**Default:** `0` (disabled)

**Values:** `1`, `true`, `yes` (enable) or `0`, `false`, `no` (disable)

**Example:**

```json
{
  "env": {
    "CULEBRATESTER2_DEBUG": "1"
  }
}
```

**Debug output includes:**
- Server startup information
- Connection validation details
- Tool call parameters and results
- Error details and stack traces

### ANDROID_VIEW_CLIENT_HOME

**Purpose:** Path to AndroidViewClient repository (for development)

**Required:** Only when running from source (not installed package)

**Example:**

```json
{
  "env": {
    "ANDROID_VIEW_CLIENT_HOME": "${workspaceFolder}"
  }
}
```

### PYTHONPATH

**Purpose:** Add source directory to Python path (for development)

**Required:** Only when running from source (not installed package)

**Example:**

```json
{
  "env": {
    "PYTHONPATH": "${workspaceFolder}/src"
  }
}
```

## Auto-Approve Settings

The `autoApprove` list specifies which tools can run without user confirmation. This is useful for read-only operations that are safe to execute automatically.

### Recommended Auto-Approve List

```json
{
  "autoApprove": [
    "getDeviceInfo",
    "dumpUiHierarchy",
    "takeScreenshot",
    "getCurrentPackage"
  ]
}
```

### All Available Tools

You can auto-approve any of these 20 tools:

**Device Information:**
- `getDeviceInfo` - Get screen dimensions
- `getCurrentPackage` - Get current app package name

**UI Inspection:**
- `dumpUiHierarchy` - Get UI element tree
- `takeScreenshot` - Capture screen image

**Element Finding:**
- `findElementByText` - Find element by text
- `findElementByResourceId` - Find element by resource ID

**Element Interaction:**
- `clickElement` - Click on element
- `longClickElement` - Long click on element
- `enterText` - Enter text into element
- `clearText` - Clear text from element

**Coordinate-Based Interaction:**
- `clickAtCoordinates` - Click at X,Y position
- `longClickAtCoordinates` - Long click at X,Y position
- `swipeGesture` - Swipe from one point to another

**Hardware Keys:**
- `pressBack` - Press BACK button
- `pressHome` - Press HOME button
- `pressRecentApps` - Press Recent Apps button

**App Management:**
- `startApp` - Launch an application
- `forceStopApp` - Force stop an application

**Device Power:**
- `wakeDevice` - Turn screen on
- `sleepDevice` - Turn screen off

### Security Considerations

**Safe to auto-approve (read-only):**
- `getDeviceInfo`
- `dumpUiHierarchy`
- `takeScreenshot`
- `getCurrentPackage`

**Use caution (modifies device state):**
- All click/tap operations
- Text entry operations
- App launching/stopping
- Hardware key presses

**Recommendation:** Only auto-approve tools you trust and understand.

## Debug Logging

### Enabling Debug Logs

Add to your configuration:

```json
{
  "env": {
    "CULEBRATESTER2_DEBUG": "1"
  }
}
```

### Log Output

Logs are written to **stderr** and include:

```
[2025-12-20 16:24:39,576] INFO [culebratester2-mcp] Starting CulebraTester2 MCP Server
[2025-12-20 16:24:39,576] INFO [culebratester2-mcp]   Base URL: http://localhost:9987
[2025-12-20 16:24:39,576] INFO [culebratester2-mcp]   Timeout: 30s
[2025-12-20 16:24:39,576] INFO [culebratester2-mcp]   Debug mode: True
[2025-12-20 16:24:39,624] INFO [culebratester2-mcp] Connected to CulebraTester2 at http://localhost:9987
[2025-12-20 16:24:39,624] INFO [culebratester2-mcp]   Version: 2.0.75-alpha (code: 20075)
[2025-12-20 16:24:39,624] INFO [culebratester2-mcp] MCP server ready, starting event loop...
```

### Viewing Logs

**In Kiro IDE:**
- Open the MCP Server panel
- View logs in the server output

**With kiro-cli:**
- Logs appear in the terminal where you run `kiro-cli`

## Complete Examples

### Example 1: Production Setup (kiro-cli)

**File:** `~/.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "culebratester2-mcp": {
      "command": "culebra-mcp",
      "args": [],
      "env": {
        "CULEBRATESTER2_URL": "http://localhost:9987",
        "CULEBRATESTER2_TIMEOUT": "30"
      },
      "disabled": false,
      "autoApprove": [
        "getDeviceInfo",
        "dumpUiHierarchy",
        "takeScreenshot",
        "getCurrentPackage"
      ]
    }
  }
}
```

**Use case:** Daily use with kiro-cli for Android automation

### Example 2: Development Setup (Workspace)

**File:** `.kiro/settings/mcp.json` (in AndroidViewClient workspace)

```json
{
  "mcpServers": {
    "culebratester2-mcp": {
      "command": "python3",
      "args": ["-m", "com.dtmilano.android.mcp.server"],
      "env": {
        "ANDROID_VIEW_CLIENT_HOME": "${workspaceFolder}",
        "PYTHONPATH": "${workspaceFolder}/src",
        "CULEBRATESTER2_URL": "http://localhost:9987",
        "CULEBRATESTER2_TIMEOUT": "30",
        "CULEBRATESTER2_DEBUG": "1"
      },
      "disabled": false,
      "autoApprove": [
        "getDeviceInfo",
        "dumpUiHierarchy",
        "getCurrentPackage"
      ]
    }
  }
}
```

**Use case:** Developing or debugging the MCP server itself

### Example 3: Remote Device

**File:** `~/.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "culebratester2-mcp": {
      "command": "culebra-mcp",
      "args": [],
      "env": {
        "CULEBRATESTER2_URL": "http://192.168.1.100:9987",
        "CULEBRATESTER2_TIMEOUT": "60"
      },
      "disabled": false,
      "autoApprove": [
        "getDeviceInfo",
        "getCurrentPackage"
      ]
    }
  }
}
```

**Use case:** Connecting to CulebraTester2 running on a remote device or emulator

### Example 4: Multiple Devices

You can configure multiple MCP servers for different devices:

**File:** `~/.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "culebratester2-device1": {
      "command": "culebra-mcp",
      "args": [],
      "env": {
        "CULEBRATESTER2_URL": "http://localhost:9987"
      },
      "disabled": false
    },
    "culebratester2-device2": {
      "command": "culebra-mcp",
      "args": [],
      "env": {
        "CULEBRATESTER2_URL": "http://localhost:9988"
      },
      "disabled": false
    }
  }
}
```

**Use case:** Testing on multiple devices simultaneously

### Example 5: Minimal Debug Setup

**File:** `~/.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "culebratester2-mcp": {
      "command": "culebra-mcp",
      "env": {
        "CULEBRATESTER2_DEBUG": "1"
      }
    }
  }
}
```

**Use case:** Quick troubleshooting with debug logs enabled

## Troubleshooting

### Server Not Appearing in Kiro

**Check:**
1. JSON syntax is valid (use a JSON validator)
2. File is in the correct location
3. Restart Kiro or reconnect the MCP server

**Solution:**
```bash
# Validate JSON
cat ~/.kiro/settings/mcp.json | python3 -m json.tool
```

### Connection Errors

**Error:** `Could not connect to CulebraTester2`

**Check:**
1. CulebraTester2 is running on the device
2. URL is correct in `CULEBRATESTER2_URL`
3. Device is accessible from your machine
4. Firewall isn't blocking the connection

**Test connection:**
```bash
curl http://localhost:9987/v2/culebra/info
```

**Expected output:**
```json
{"versionCode":20075,"versionName":"2.0.75-alpha"}
```

### Command Not Found

**Error:** `culebra-mcp: command not found`

**Solution:**
1. Install AndroidViewClient: `pip install androidviewclient`
2. Or use Python module: `"command": "python3", "args": ["-m", "com.dtmilano.android.mcp.server"]`

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'com.dtmilano.android.mcp'`

**Solution:**
Add to configuration:
```json
{
  "env": {
    "PYTHONPATH": "${workspaceFolder}/src"
  }
}
```

### Tools Not Working

**Check:**
1. Enable debug logging: `"CULEBRATESTER2_DEBUG": "1"`
2. Check logs for error messages
3. Verify CulebraTester2 version is compatible (>= 2.0.73)
4. Test CulebraTester2 directly with curl

### Timeout Issues

**Error:** Requests timing out

**Solution:**
Increase timeout:
```json
{
  "env": {
    "CULEBRATESTER2_TIMEOUT": "60"
  }
}
```

## Additional Resources

- **CulebraTester2 Documentation:** https://github.com/dtmilano/CulebraTester2-public
- **AndroidViewClient Documentation:** https://github.com/dtmilano/AndroidViewClient
- **MCP Protocol Specification:** https://modelcontextprotocol.io/
- **Kiro Documentation:** https://kiro.ai/docs

## Getting Help

If you encounter issues:

1. Enable debug logging
2. Check the troubleshooting section
3. Review the logs for error messages
4. Open an issue on GitHub with:
   - Your configuration file (sanitized)
   - Error messages from logs
   - CulebraTester2 version
   - AndroidViewClient version
   - Operating system

## Version History

- **v24.1.0** (2024-12-20): Initial MCP server release
  - 20 MCP tools for Android automation
  - Support for official culebratester-client
  - Debug logging support
  - Comprehensive configuration options
