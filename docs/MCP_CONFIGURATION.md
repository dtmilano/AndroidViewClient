# CulebraTester2 MCP Server Configuration Guide

This guide provides detailed instructions for configuring the CulebraTester2 MCP server.

The server is a plain stdio MCP server configured entirely through environment variables, so it
works with any MCP client. **Claude Code** and **Kiro** are documented here in detail.

## Table of Contents

- [Overview](#overview)
- [Supported AI Assistants](#supported-ai-assistants)
- [Configuration File Locations](#configuration-file-locations)
- [Basic Configuration](#basic-configuration)
- [Configuration Options](#configuration-options)
- [Environment Variables](#environment-variables)
- [Tool Permissions](#tool-permissions)
- [Debug Logging](#debug-logging)
- [Complete Examples](#complete-examples)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

## Overview

The CulebraTester2 MCP server integrates with AI assistants through MCP (Model Context Protocol)
configuration files. These JSON files tell the assistant how to start and communicate with the
MCP server.

All assistants use the same `mcpServers` JSON shape, so the server entry itself looks nearly
identical everywhere. What differs is **where the file lives** and **how tools get approved**.

## Supported AI Assistants

| | Claude Code | Kiro |
|---|---|---|
| Project config | `.mcp.json` (repository root) | `.kiro/settings/mcp.json` |
| User config | `~/.claude.json` | `~/.kiro/settings/mcp.json` |
| Tool pre-approval | `permissions.allow` in `.claude/settings.json` | `autoApprove` in the server entry |
| Disable a server | `disabledMcpjsonServers`, `/mcp`, `claude mcp remove` | `"disabled": true` |
| Variable expansion | `${VAR}`, `${VAR:-default}` | `${workspaceFolder}` |

Other MCP clients work too — point them at the `culebra-mcp` command and set the
[environment variables](#environment-variables) below.

> **Server name matters on Claude Code.** The key you choose (`culebratester2` throughout this
> guide) becomes the prefix of every tool name (`mcp__culebratester2__getDeviceInfo`) and
> therefore of every permission rule. Pick it once and stay consistent. Claude Code accepts
> letters, digits, hyphens and underscores — no dots.

## Configuration File Locations

### Claude Code

Claude Code has three configuration scopes:

| Scope | Where | Shared? |
|---|---|---|
| `local` (default for `claude mcp add`) | `~/.claude.json`, under `projects["<abs project path>"].mcpServers` | No — you, in this project only |
| `project` | **`.mcp.json` in the repository root** | Yes — committed; each user is asked to approve it |
| `user` | `~/.claude.json`, top-level `mcpServers` | No — you, in every project |

**Priority:** when the same server name exists in several scopes, `local` wins over `project`,
which wins over `user`. The winning entry is used *whole* — fields from different scopes are not
merged.

Two common mistakes worth avoiding:

- `.mcp.json` goes in the **project root**, not in `.claude/`. Claude Code does not read
  `~/.claude/.mcp.json`, `~/.claude/mcp.json` or `~/.claude/config/mcp.json`.
- `settings.json` has no `mcpServers` key. Putting server definitions there silently does
  nothing.

### Kiro

**Workspace-level:** `.kiro/settings/mcp.json` (in your project workspace)

**Use when:**
- Working on a specific project
- You want different settings per project
- Developing or testing the MCP server itself

**Scope:** only active when the workspace is open

**User-level (global):** `~/.kiro/settings/mcp.json` (in your home directory)

**Use when:**
- Using `kiro-cli` (command-line interface)
- You want the MCP server available across all projects
- Using the installed package globally

**Scope:** active everywhere, across all workspaces

**Priority:** when both exist, workspace-level settings override user-level settings for that
workspace.

## Basic Configuration

Both sections below assume AndroidViewClient is installed (`pip install androidviewclient`),
CulebraTester2 is reachable at `http://localhost:9987`, and the default 30 second timeout is
fine.

### Claude Code

**The quickest route — no hand-edited JSON:**

```bash
claude mcp add culebratester2 \
  --env CULEBRATESTER2_URL=http://localhost:9987 \
  --env CULEBRATESTER2_TIMEOUT=30 \
  -- culebra-mcp
```

Everything after `--` is passed to the server untouched. stdio is the default transport, so no
`--transport` flag is needed. Add `--scope user` to make it available in every project, or
`--scope project` to write it to `.mcp.json`.

Then verify — `Added …` only means the config file was written, not that the command runs:

```bash
claude mcp list                  # all servers with health status
claude mcp get culebratester2    # scope, resolved command, and an "Issue:" line on failure
claude mcp remove culebratester2 # undo
```

**Equivalent `.mcp.json` (project root):**

```json
{
  "mcpServers": {
    "culebratester2": {
      "command": "culebra-mcp",
      "args": [],
      "env": {
        "CULEBRATESTER2_URL": "http://localhost:9987",
        "CULEBRATESTER2_TIMEOUT": "30"
      }
    }
  }
}
```

Claude Code reads `.mcp.json` at **session start** and asks you to approve the server the first
time it sees it — see [Project config approval](#project-config-approval-claude-code).

**Running from source** (working in an AndroidViewClient checkout). This repository already ships
a `.mcp.json` doing exactly this:

```json
{
  "mcpServers": {
    "culebratester2": {
      "command": "python3",
      "args": ["-m", "com.dtmilano.android.mcp.server"],
      "env": {
        "PYTHONPATH": "${ANDROID_VIEW_CLIENT_HOME:-.}/src",
        "CULEBRATESTER2_URL": "${CULEBRATESTER2_URL:-http://localhost:9987}",
        "CULEBRATESTER2_TIMEOUT": "${CULEBRATESTER2_TIMEOUT:-30}",
        "CULEBRATESTER2_DEBUG": "${CULEBRATESTER2_DEBUG:-0}"
      }
    }
  }
}
```

`${ANDROID_VIEW_CLIENT_HOME:-.}` falls back to the directory `claude` was started from, which
covers the normal case of running it from the repository root. Export
`ANDROID_VIEW_CLIENT_HOME=/abs/path/to/AndroidViewClient` if you start Claude Code anywhere else.

### Kiro

**User-level** (for `kiro-cli` or global use):

```json
{
  "mcpServers": {
    "culebratester2": {
      "command": "culebra-mcp",
      "args": []
    }
  }
}
```

**Workspace-level** (for development, or when working in the AndroidViewClient repository):

```json
{
  "mcpServers": {
    "culebratester2": {
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
    "culebratester2": {  // ← This is the server name
      ...
    }
  }
}
```

The server name is how you reference this MCP server. You can change it, but keep it
descriptive — and remember that on Claude Code it is baked into every tool name and permission
rule.

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

### Paths and Variable Expansion

**Claude Code** expands exactly two forms, in `command`, `args` and `env`:

- `${VAR}`
- `${VAR:-default}`

A missing variable does not break loading: `claude mcp list` and `/mcp` warn and name the
variable, and the literal `${VAR}` text is passed through.

Kiro's `${workspaceFolder}` is **not** supported by Claude Code. There is also **no `cwd`
field**, and relative paths in `command`/`args` resolve against the directory `claude` was
launched from — not the location of `.mcp.json`. So prefer a command found on `PATH`
(`culebra-mcp`, `python3`) and use an absolute path for a checkout-local entry point.

### Optional Fields (Claude Code)

```json
{
  "type": "stdio",
  "timeout": 60000
}
```

- `type` — `"stdio"`. An entry with no `type` is read as stdio, so it is optional here.
- `timeout` — per-server **tool execution** timeout in milliseconds; overrides
  `MCP_TOOL_TIMEOUT` for this server. Values below 1000 are ignored.

Claude Code has **no** `autoApprove`, `disabled` or `cwd` fields — see
[Tool Permissions](#tool-permissions) and
[Disabling a server](#disabling-a-server-claude-code) for the equivalents.

### Disabled Flag (Kiro)

Temporarily disable the server without removing the configuration:

```json
{
  "disabled": true  // Set to false or remove to enable
}
```

## Environment Variables

All environment variables are optional and have sensible defaults. They are the same for every
assistant.

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

> **Known limitation:** this value is not applied to the initial TCP connect, so it does not
> bound a hang against a host that silently drops packets. See
> [Slow startup](#slow-startup-or-failed-to-connect-on-claude-code).

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
    "ANDROID_VIEW_CLIENT_HOME": "/path/to/AndroidViewClient"
  }
}
```

On Kiro you can use `${workspaceFolder}` here. On Claude Code use an absolute path, or
`${ANDROID_VIEW_CLIENT_HOME:-.}` as shown above.

### PYTHONPATH

**Purpose:** Add source directory to Python path (for development)

**Required:** Only when running from source (not installed package)

**Example:**

```json
{
  "env": {
    "PYTHONPATH": "/path/to/AndroidViewClient/src"
  }
}
```

## Tool Permissions

Both assistants let you pre-approve tools so read-only operations run without a confirmation
prompt. The mechanisms are quite different.

### All Available Tools

There are 20 tools:

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

### Claude Code: `permissions.allow`

Claude Code exposes MCP tools to the model as `mcp__<server>__<tool>`, so with the server name
`culebratester2` the recommended read-only allowlist goes in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__culebratester2__getDeviceInfo",
      "mcp__culebratester2__getCurrentPackage",
      "mcp__culebratester2__dumpUiHierarchy",
      "mcp__culebratester2__takeScreenshot"
    ],
    "ask": [
      "mcp__culebratester2__startApp",
      "mcp__culebratester2__forceStopApp",
      "mcp__culebratester2__sleepDevice"
    ]
  }
}
```

This repository ships exactly that file as a working example. If being prompted before every
lookup gets tedious, `findElementByText` and `findElementByResourceId` are also safe additions —
they only read the UI hierarchy.

**Rule syntax:**

| Rule | Matches |
|---|---|
| `mcp__culebratester2__getDeviceInfo` | that one tool |
| `mcp__culebratester2__press*` | `pressBack`, `pressHome`, `pressRecentApps` |
| `mcp__culebratester2__*` or `mcp__culebratester2` | **every** tool from the server, including the 16 that change device state |

Things that will silently not do what you expect:

- Globs are only allowed in the tool position, after a literal `mcp__<server>__` prefix. An
  unanchored allow rule such as `"*"` or `"mcp__*"` is skipped with a warning and approves
  nothing.
- Never put parentheses on an `mcp__` rule (`mcp__culebratester2__startApp(...)`). Such rules
  are skipped and reported by `claude doctor`.

**Evaluation order** is `deny` → `ask` → `allow`, first match wins; specificity does not matter.
So an `ask` entry still prompts even when a narrower `allow` entry also matches — which is what
makes the three-way split above useful. Kiro's `autoApprove` is binary and cannot express it.

**Where to put it**, highest precedence first:

| File | Purpose |
|---|---|
| `.claude/settings.local.json` | your personal overrides — keep it out of git |
| `.claude/settings.json` | shared project settings — commit this |
| `~/.claude/settings.json` | your defaults for every project |

**Trust caveat:** `permissions.allow` from a *committed* `.claude/settings.json` only takes
effect after you accept the workspace-trust dialog for that checkout — a repository you clone
cannot grant itself permissions. `deny` and `ask` apply either way.

### Kiro: `autoApprove`

The `autoApprove` list in the server entry specifies which tools can run without user
confirmation:

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

Tool names are unprefixed here, unlike Claude Code.

### Project config approval (Claude Code)

Because `.mcp.json` is committed, Claude Code asks before launching anything from it — a
repository you clone cannot start processes on your machine without consent.

1. Claude Code reads `.mcp.json` at **session start**; edits require restarting the session.
2. The first time it sees a project-scoped server it prompts for approval. Until you answer,
   `claude mcp list` shows `⏸ Pending approval (run claude to approve)`.
3. Dismissed the prompt? Approve it later from `/mcp`, or run
   `claude mcp reset-project-choices` to reset all decisions for the project.
4. To pre-accept, set `enableAllProjectMcpServers: true` or
   `enabledMcpjsonServers: ["culebratester2"]` in a settings file. This only works from
   `~/.claude/settings.json`, managed settings, `--settings`, or
   `.claude/settings.local.json` in a trusted folder — a committed `.claude/settings.json`
   cannot approve its own repository's servers.

### Disabling a server (Claude Code)

There is no `disabled` field. Instead:

- `/mcp` — toggle the server off for this project.
- `disabledMcpjsonServers: ["culebratester2"]` in any settings file — the hard "never load
  this" switch.
- `claude mcp remove culebratester2` — delete the entry.

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

**In Claude Code:**
- Run with `claude --debug=mcp`, then read `~/.claude/debug/<session-id>.txt`. The category
  filter only binds in the `=` form — `--debug mcp` enables debug without filtering.
- `/mcp` shows connection status, tool count, and an `Issue:` row with the server-reported
  error.

**In Kiro IDE:**
- Open the MCP Server panel
- View logs in the server output

**With kiro-cli:**
- Logs appear in the terminal where you run `kiro-cli`

## Complete Examples

### Claude Code

#### Example 1: Production Setup

**File:** `~/.claude.json` (written by `claude mcp add --scope user`)

```bash
claude mcp add --scope user culebratester2 \
  --env CULEBRATESTER2_URL=http://localhost:9987 \
  --env CULEBRATESTER2_TIMEOUT=30 \
  -- culebra-mcp
```

Pair it with the read-only allowlist in `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__culebratester2__getDeviceInfo",
      "mcp__culebratester2__getCurrentPackage",
      "mcp__culebratester2__dumpUiHierarchy",
      "mcp__culebratester2__takeScreenshot"
    ]
  }
}
```

**Use case:** daily Android automation from any project.

#### Example 2: Development Setup

**File:** `.mcp.json` (in the AndroidViewClient repository root — already committed here)

See [Running from source](#claude-code-1) above. Add `"CULEBRATESTER2_DEBUG": "1"` or export
`CULEBRATESTER2_DEBUG=1` before starting Claude Code.

**Use case:** developing or debugging the MCP server itself.

#### Example 3: Remote Device

```json
{
  "mcpServers": {
    "culebratester2": {
      "command": "culebra-mcp",
      "args": [],
      "env": {
        "CULEBRATESTER2_URL": "http://192.168.1.100:9987",
        "CULEBRATESTER2_TIMEOUT": "60"
      },
      "timeout": 120000
    }
  }
}
```

**Use case:** connecting to CulebraTester2 running on a remote device or emulator. The extra
`timeout` gives individual tool calls more headroom over a slow link.

#### Example 4: Multiple Devices

```json
{
  "mcpServers": {
    "culebratester2-device1": {
      "command": "culebra-mcp",
      "args": [],
      "env": { "CULEBRATESTER2_URL": "http://localhost:9987" }
    },
    "culebratester2-device2": {
      "command": "culebra-mcp",
      "args": [],
      "env": { "CULEBRATESTER2_URL": "http://localhost:9988" }
    }
  }
}
```

**Use case:** testing on multiple devices simultaneously. Note that permission rules follow the
names, so you need `mcp__culebratester2-device1__…` *and* `mcp__culebratester2-device2__…`
entries.

### Kiro

#### Example 5: Production Setup (kiro-cli)

**File:** `~/.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "culebratester2": {
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

#### Example 6: Development Setup (Workspace)

**File:** `.kiro/settings/mcp.json` (in AndroidViewClient workspace)

```json
{
  "mcpServers": {
    "culebratester2": {
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

#### Example 7: Remote Device

**File:** `~/.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "culebratester2": {
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

#### Example 8: Multiple Devices

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

#### Example 9: Minimal Debug Setup

**File:** `~/.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "culebratester2": {
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

### Server Not Appearing

**Check:**
1. JSON syntax is valid
2. File is in the correct location
3. Restart the assistant or reconnect the MCP server

**Solution:**
```bash
# Validate JSON
python3 -m json.tool < .mcp.json
python3 -m json.tool < ~/.kiro/settings/mcp.json
```

**Claude Code specifically:**
```bash
claude mcp list                  # health status and config warnings
claude mcp get culebratester2    # scope, resolved command, "Issue:" line
```

Run `/mcp` inside a session for the same information plus a **Reconnect** action. If the status
is `⏸ Pending approval`, you still need to accept the project-config prompt — see
[Project config approval](#project-config-approval-claude-code).

`claude mcp list` also warns about a few things that are hard to spot by eye, such as stray
leading or trailing whitespace in `command` or an `env` value (it is not trimmed), and
environment variables referenced but not set.

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

### Slow Startup or "Failed to Connect" on Claude Code

The server validates its connection to CulebraTester2 *synchronously, before* the MCP event loop
starts. How long that takes depends on how the host fails:

- **Nothing listening on localhost** — the connection is refused immediately, the server logs a
  warning and starts anyway. This is the harmless case.
- **Host silently unreachable** (wrong IP, firewall dropping packets, device off the network) —
  the TCP connect has no deadline of its own, so startup can hang for **minutes**. Note that
  `CULEBRATESTER2_TIMEOUT` does *not* currently bound this. Claude Code gives a server 30 seconds
  to start by default, so it will report the server as failed to connect.

**Solutions:**
1. Start CulebraTester2 and `adb forward tcp:9987 tcp:9987` *before* starting Claude Code.
2. Double-check `CULEBRATESTER2_URL` — a typo in a remote IP is the usual cause of a hang, and
   `curl http://<host>:9987/v2/culebra/info` will reproduce it outside Claude Code.
3. Raise Claude Code's startup budget if your device is simply slow to answer:
   ```bash
   MCP_TIMEOUT=60000 claude
   ```

### `ImportError: cannot import name 'FastMCP' from 'mcp.server'`

The MCP Python SDK renamed `FastMCP` to `MCPServer` in version 2.0, and this server still uses
the v1 API. Install a v1 SDK:

```bash
pip install 'mcp<2'
```

AndroidViewClient pins this for you; you will only see this on an older release, or in an
environment where `mcp` 2.x was installed separately.

### Command Not Found

**Error:** `culebra-mcp: command not found`

**Solution:**
1. Install AndroidViewClient: `pip install androidviewclient`
2. Or use the Python module: `"command": "python3", "args": ["-m", "com.dtmilano.android.mcp.server"]`

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'com.dtmilano.android.mcp'`

**Solution:**
Point `PYTHONPATH` at the `src` directory of your checkout:
```json
{
  "env": {
    "PYTHONPATH": "/path/to/AndroidViewClient/src"
  }
}
```

On Kiro you can write `${workspaceFolder}/src`. On Claude Code use an absolute path or
`${ANDROID_VIEW_CLIENT_HOME:-.}/src` — `${workspaceFolder}` is not expanded, and a bare relative
path resolves against the directory `claude` was launched from.

### Tools Not Working

**Check:**
1. Enable debug logging: `"CULEBRATESTER2_DEBUG": "1"`
2. Check logs for error messages
3. Verify CulebraTester2 version is compatible (>= 2.0.73)
4. Test CulebraTester2 directly with curl

### A Tool Is Missing

If the server connects but a tool never shows up, count the tools in `/mcp` — all 20 should be
listed. Claude Code silently drops tools whose input schema it cannot use, and tells the model
which ones and why, so you can simply ask Claude why a tool is missing.

### Truncated Results

`dumpUiHierarchy` and `takeScreenshot` can return a lot of data. Claude Code caps MCP tool output
at 25,000 tokens by default and warns above 10,000; over-limit results are written to a file and
replaced by its path. Raise the cap with `MAX_MCP_OUTPUT_TOKENS` if you need the full hierarchy
inline.

### Timeout Issues

**Error:** Requests timing out

**Solution:**
Increase the HTTP timeout:
```json
{
  "env": {
    "CULEBRATESTER2_TIMEOUT": "60"
  }
}
```

On Claude Code, individual tool calls are also subject to `MCP_TOOL_TIMEOUT` or the per-server
`timeout` field (milliseconds).

## Additional Resources

- **CulebraTester2 Documentation:** https://github.com/dtmilano/CulebraTester2-public
- **AndroidViewClient Documentation:** https://github.com/dtmilano/AndroidViewClient
- **MCP Protocol Specification:** https://modelcontextprotocol.io/
- **Claude Code MCP Documentation:** https://code.claude.com/docs/en/mcp
- **Claude Code Permissions:** https://code.claude.com/docs/en/permissions
- **Kiro Documentation:** https://kiro.ai/docs

## Getting Help

If you encounter issues:

1. Enable debug logging
2. Check the troubleshooting section
3. Review the logs for error messages
4. Open an issue on GitHub with:
   - Your configuration file (sanitized)
   - Error messages from logs
   - Which AI assistant you are using, and its version
   - CulebraTester2 version
   - AndroidViewClient version
   - Operating system

## Version History

- **v24.1.0** (2024-12-20): Initial MCP server release
  - 20 MCP tools for Android automation
  - Support for official culebratester-client
  - Debug logging support
  - Comprehensive configuration options
- **Unreleased**: Claude Code support
  - Assistant-agnostic configuration guide covering Claude Code and Kiro
  - Committed `.mcp.json` and `.claude/settings.json` for development
  - `examples/mcp_config.json` and `examples/mcp_config_kiro.json`
