AndroidViewClient
=================
<a href="#"><img src="https://github.com/dtmilano/AndroidViewClient/wiki/images/culebra-logo-transparent-204x209-rb-border.png" align="left" hspace="0" vspace="6"></a>
**AndroidViewClient/culebra** was initially conceived as an extension to [monkeyrunner](http://developer.android.com/tools/help/monkeyrunner_concepts.html)  but has since evolved
into a versatile pure Python tool.
It streamlines test script creation for Android applications by automating tasks and simplifying interactions. This test framework:
<ul><ul>
  <li>Automates the navigation of Android applications.</li>
  <li>Generates reusable scripts for efficient testing.</li>
  <li>Offers device-independent UI interaction based on views.</li>
  <li>Utilizes 'logical' screen comparison (UI Automator Hierarchy based) instead of image comparison, avoiding extraneous detail issues like time or data changes.</li>
  <li>Supports concurrent operation on multiple devices.</li>
  <li>Provides straightforward control for high-level operations such as language change and activity start.</li>
  <li>Fully supports all Android APIs.</li>
  <li>Written in Python with support for Python 3.6 and above in versions 20.x.y and beyond.</li>
</ul></ul>

**🛎** |A new Kotlin backend is under development to provide more functionality and improve performance.<br>Take a look at [CulebraTester2](https://github.com/dtmilano/CulebraTester2-public) and 20.x.y-series prerelease. |
---|----------------------------------------------------------------------------------------------|

[![Latest Version](https://img.shields.io/pypi/v/androidviewclient.svg)](https://pypi.python.org/pypi/androidviewclient/)
![Release](https://img.shields.io/github/v/release/dtmilano/AndroidViewClient?include_prereleases&label=release)
![Upload Python Package](https://github.com/dtmilano/AndroidViewClient/workflows/Upload%20Python%20Package/badge.svg)
[![Downloads](https://static.pepy.tech/badge/androidviewclient)](https://pepy.tech/project/androidviewclient)

**NOTE**: Pypi statistics are broken see [here](https://github.com/aclark4life/vanity/issues/22). The new statistics can be obtained from [BigQuery](https://bigquery.cloud.google.com/queries/culebra-tester).

As of February 2024 we have reached:

<p align="center">
  <img src="https://github.com/dtmilano/AndroidViewClient/wiki/images/androidviewclient-culebra-2-million-downloads.png" alt="culebra 2 million downloads" width="80%" align="center">
</p>

Thanks to all who made it possible.

# Installation
```
pip3 install androidviewclient --upgrade
```
Or check the wiki for more alternatives.

# AI-Powered Testing with MCP

**NEW!** AndroidViewClient now includes a Model Context Protocol (MCP) server that enables AI assistants like Kiro to interact with Android devices through natural language.

## Quick Start with MCP

1. **Install with MCP support:**
   ```bash
   pip3 install androidviewclient --upgrade
   ```

2. **Start CulebraTester2 on your device:**
   
   Check the details at [How to run CulebraTester2 ?](https://github.com/dtmilano/CulebraTester2-public?tab=readme-ov-file#how-to-run-culebratester2-)
   

4. **Configure your AI assistant:**
   
   Add to `.kiro/settings/mcp.json` or `~/.kiro/settings/mcp.json`:
   ```json
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
   ```

5. **Start testing with natural language:**
   - "Get the device screen size"
   - "Launch the Calculator app"
   - "Find the button with text Submit and click it"
   - "Take a screenshot"
   - "Swipe up to scroll"

## MCP Tools Available

The MCP server provides 20 tools for Android automation:

**Element-based interactions:**
- Find elements by text or resource ID
- Click, long-click, enter text, clear text
- Navigate with back/home buttons
- Launch applications

**Coordinate-based interactions:**
- Click/long-click at coordinates
- Swipe gestures

**Device actions:**
- Wake/sleep device
- Get current app
- Force stop apps
- Take screenshots

## Configuration

For detailed MCP configuration options, see the [MCP Configuration Guide](docs/MCP_CONFIGURATION.md).

Quick reference:
- **User-level config** (kiro-cli): `~/.kiro/settings/mcp.json`
- **Workspace config** (Kiro IDE): `.kiro/settings/mcp.json`
- **Examples:** `examples/mcp_config.json`
- **Usage examples:** `examples/test_calculator_mcp.py`

## Environment Variables

- `CULEBRATESTER2_URL`: Base URL for CulebraTester2 (default: `http://localhost:9987`)
- `CULEBRATESTER2_TIMEOUT`: HTTP timeout in seconds (default: `30`)
- `CULEBRATESTER2_DEBUG`: Enable debug logging (`1`, `true`, or `yes`)

# Want to learn more?

> 🚀 Check [Examples](https://github.com/dtmilano/AndroidViewClient/wiki/Resources#examples) and [Screencasts and videos](https://github.com/dtmilano/AndroidViewClient/wiki/Resources#screencasts-and-videos) page to see it in action.
> 
Detailed information can be found in the [AndroidViewClient/culebra wiki](https://github.com/dtmilano/AndroidViewClient/wiki)

