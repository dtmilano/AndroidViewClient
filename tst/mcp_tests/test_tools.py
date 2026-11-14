#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for MCP Tools

Minimal test implementation to enable prototype development.
Full test suite to be implemented later.

Copyright (C) 2012-2024  Diego Torres Milano
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest

class TestMCPTools:
    """Minimal tests for MCP tools."""
    
    def test_tools_module_imports(self):
        """Test that tools module can be imported."""
        try:
            from com.dtmilano.android.mcp import tools
            assert tools is not None
        except ImportError as e:
            if 'mcp.server' in str(e):
                pytest.skip("MCP SDK not installed in test environment")
            raise
    
    def test_mcp_server_exists(self):
        """Test that MCP server is initialized."""
        try:
            from com.dtmilano.android.mcp.server import mcp
            assert mcp is not None
            assert mcp.name == "culebratester2-mcp-server"
        except ImportError as e:
            if 'mcp.server' in str(e):
                pytest.skip("MCP SDK not installed in test environment")
            raise


class TestStartApp:
    """startApp must call the endpoint with pkg and cls, which are both required query params."""

    @pytest.fixture
    def tools(self):
        try:
            from com.dtmilano.android.mcp import tools
        except ImportError as e:
            if 'mcp.server' in str(e):
                pytest.skip("MCP SDK not installed in test environment")
            raise
        return tools

    def _start(self, tools, monkeypatch, *args):
        import json
        from unittest import mock
        fake = mock.Mock()
        fake.target_context_start_activity_get.return_value = None
        monkeypatch.setattr(tools, 'client', fake)
        return json.loads(tools.startApp(*args)), fake.target_context_start_activity_get

    def test_relative_activity_is_expanded(self, tools, monkeypatch):
        # The server passes cls to the Intent verbatim, so ".Main" must be expanded client-side.
        result, call = self._start(tools, monkeypatch, 'com.example.app', '.MainActivity')
        assert result['success'] is True
        call.assert_called_once_with(pkg='com.example.app', cls='com.example.app.MainActivity')

    def test_fully_qualified_activity_is_passed_through(self, tools, monkeypatch):
        result, call = self._start(tools, monkeypatch, 'com.example.app', 'com.other.Launcher')
        assert result['success'] is True
        call.assert_called_once_with(pkg='com.example.app', cls='com.other.Launcher')

    def test_missing_activity_fails_without_calling_the_api(self, tools, monkeypatch):
        result, call = self._start(tools, monkeypatch, 'com.example.app', None)
        assert result['success'] is False
        assert 'activityName is required' in result['error']
        call.assert_not_called()
