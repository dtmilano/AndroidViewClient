#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AndroidViewClient MCP Server Module

This module provides a Model Context Protocol (MCP) server that exposes
CulebraTester2 functionality to AI assistants, enabling AI-powered Android
test automation.

The MCP server acts as a bridge between MCP-compatible AI tools (like Kiro)
and Android devices running the CulebraTester2 service.

Example usage:
    # Start the MCP server
    $ culebra-mcp

    # Or with custom URL
    $ culebra-mcp --url http://192.168.1.100:9987

For more information, see:
    https://github.com/dtmilano/AndroidViewClient/
"""

__version__ = '25.0.0'
__author__ = 'Diego Torres Milano'
__email__ = 'dtmilano@gmail.com'

__all__ = [
    'server',
    'client',
    'object_store',
    'tools',
]
