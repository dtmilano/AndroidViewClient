#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Server Core for CulebraTester2

This module implements the main MCP server that exposes CulebraTester2
functionality to AI assistants via the Model Context Protocol.

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

import os
import sys
import logging
from mcp.server import FastMCP

from culebratester_client import ApiClient, Configuration
from culebratester_client.api import DefaultApi
from com.dtmilano.android.mcp.object_store import ObjectStore

__version__ = '25.0.0'

# Configure logging
DEBUG = os.environ.get('CULEBRATESTER2_DEBUG', '').lower() in ('1', 'true', 'yes')
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('culebratester2-mcp')

# Get configuration from environment variables
BASE_URL = os.environ.get('CULEBRATESTER2_URL', 'http://localhost:9987')
TIMEOUT = int(os.environ.get('CULEBRATESTER2_TIMEOUT', '30'))

logger.info("Starting CulebraTester2 MCP Server")
logger.info("  Base URL: {}".format(BASE_URL))
logger.info("  Timeout: {}s".format(TIMEOUT))
logger.info("  Debug mode: {}".format(DEBUG))

# Create FastMCP server instance
mcp = FastMCP(
    name="culebratester2-mcp-server",
    instructions="MCP server for Android UI automation using CulebraTester2. "
                 "Provides tools to interact with Android devices through the CulebraTester2 backend."
)

# Initialize official CulebraTester2 client
# Note: The official client's OpenAPI spec doesn't include /v2 prefix in paths,
# so we add it to the host URL
configuration = Configuration()
configuration.host = "{}/v2".format(BASE_URL)
api_client = ApiClient(configuration)
api_client.rest_client.pool_manager.connection_pool_kw['timeout'] = TIMEOUT
client = DefaultApi(api_client)

# Initialize object store (shared across all tool calls)
objectStore = ObjectStore()


def validateConnection():
    """Validate connection to CulebraTester2 server."""
    try:
        logger.debug("Validating connection to CulebraTester2...")
        # Use the info endpoint to check service health and version
        info = client.culebra_info_get()
        logger.info("Connected to CulebraTester2 at {}".format(BASE_URL))
        logger.info("  Version: {} (code: {})".format(
            info.version_name if hasattr(info, 'version_name') else 'unknown',
            info.version_code if hasattr(info, 'version_code') else 'unknown'
        ))
        print("Connected to CulebraTester2 at {}".format(BASE_URL), file=sys.stderr)
        print("  Version: {} (code: {})".format(
            info.version_name if hasattr(info, 'version_name') else 'unknown',
            info.version_code if hasattr(info, 'version_code') else 'unknown'
        ), file=sys.stderr)
        return True
    except Exception as e:
        logger.error("Could not connect to CulebraTester2 at {}: {}".format(BASE_URL, e))
        print("Warning: Could not connect to CulebraTester2 at {}: {}".format(BASE_URL, e), file=sys.stderr)
        print("Server will start but tools may fail until connection is established.", file=sys.stderr)
        return False


# Import tools after mcp instance is created (tools will register themselves)
from com.dtmilano.android.mcp import tools  # noqa: F401, E402


def main():
    """Main entry point for the MCP server."""
    logger.info("Initializing MCP server...")
    validateConnection()
    logger.info("MCP server ready, starting event loop...")
    mcp.run()


if __name__ == "__main__":
    main()
