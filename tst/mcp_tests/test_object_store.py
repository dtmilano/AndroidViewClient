#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for ObjectStore

This module contains unit tests for the ObjectStore class, verifying
specific examples and edge cases.

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

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from com.dtmilano.android.mcp.object_store import ObjectStore


class TestObjectStore:
    """Unit tests for ObjectStore class."""
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving an object."""
        store = ObjectStore()
        oid = 123
        metadata = {"selector": {"text": "Login"}, "type": "text"}
        
        store.store(oid, metadata)
        retrieved = store.get(oid)
        
        assert retrieved is not None
        assert retrieved == metadata
        assert retrieved["selector"]["text"] == "Login"
        assert retrieved["type"] == "text"
    
    def test_exists_with_valid_id(self):
        """Test exists() returns True for stored object."""
        store = ObjectStore()
        oid = 456
        metadata = {"selector": {"resourceId": "button1"}, "type": "resourceId"}
        
        store.store(oid, metadata)
        
        assert store.exists(oid) is True
    
    def test_exists_with_invalid_id(self):
        """Test exists() returns False for non-existent object."""
        store = ObjectStore()
        
        assert store.exists(999) is False
    
    def test_get_nonexistent_object(self):
        """Test get() returns None for non-existent object."""
        store = ObjectStore()
        
        result = store.get(999)
        
        assert result is None
    
    def test_remove_existing_object(self):
        """Test removing an existing object."""
        store = ObjectStore()
        oid = 789
        metadata = {"selector": {"className": "Button"}, "type": "className"}
        
        store.store(oid, metadata)
        assert store.exists(oid) is True
        
        store.remove(oid)
        
        assert store.exists(oid) is False
        assert store.get(oid) is None
    
    def test_remove_nonexistent_object(self):
        """Test removing a non-existent object (should not raise error)."""
        store = ObjectStore()
        
        # Should not raise an exception
        store.remove(999)
        
        assert store.exists(999) is False
    
    def test_clear_empty_store(self):
        """Test clearing an empty store."""
        store = ObjectStore()
        
        # Should not raise an exception
        store.clear()
        
        assert store.exists(1) is False
    
    def test_clear_populated_store(self):
        """Test clearing a store with multiple objects."""
        store = ObjectStore()
        
        # Store multiple objects
        store.store(1, {"selector": {"text": "A"}, "type": "text"})
        store.store(2, {"selector": {"text": "B"}, "type": "text"})
        store.store(3, {"selector": {"text": "C"}, "type": "text"})
        
        assert store.exists(1) is True
        assert store.exists(2) is True
        assert store.exists(3) is True
        
        # Clear the store
        store.clear()
        
        # All objects should be gone
        assert store.exists(1) is False
        assert store.exists(2) is False
        assert store.exists(3) is False
    
    def test_overwrite_existing_object(self):
        """Test storing a new value for an existing object ID."""
        store = ObjectStore()
        oid = 100
        
        # Store initial metadata
        metadata1 = {"selector": {"text": "Old"}, "type": "text"}
        store.store(oid, metadata1)
        assert store.get(oid) == metadata1
        
        # Overwrite with new metadata
        metadata2 = {"selector": {"text": "New"}, "type": "text"}
        store.store(oid, metadata2)
        
        # Should have new metadata
        retrieved = store.get(oid)
        assert retrieved == metadata2
        assert retrieved["selector"]["text"] == "New"
    
    def test_store_multiple_objects(self):
        """Test storing multiple objects with different IDs."""
        store = ObjectStore()
        
        objects = {
            10: {"selector": {"text": "Button1"}, "type": "text"},
            20: {"selector": {"resourceId": "id1"}, "type": "resourceId"},
            30: {"selector": {"className": "View"}, "type": "className"},
        }
        
        # Store all objects
        for oid, metadata in objects.items():
            store.store(oid, metadata)
        
        # Verify all objects exist and have correct metadata
        for oid, expected_metadata in objects.items():
            assert store.exists(oid) is True
            assert store.get(oid) == expected_metadata
    
    def test_metadata_with_complex_selector(self):
        """Test storing metadata with complex nested selector."""
        store = ObjectStore()
        oid = 500
        
        metadata = {
            "selector": {
                "text": "Submit",
                "resourceId": "com.example:id/submit_button",
                "className": "android.widget.Button",
                "clickable": True,
                "enabled": True
            },
            "type": "complex",
            "timestamp": "2024-12-20T10:00:00Z"
        }
        
        store.store(oid, metadata)
        retrieved = store.get(oid)
        
        assert retrieved is not None
        assert retrieved["selector"]["text"] == "Submit"
        assert retrieved["selector"]["clickable"] is True
        assert retrieved["type"] == "complex"
        assert retrieved["timestamp"] == "2024-12-20T10:00:00Z"
    
    def test_zero_object_id(self):
        """Test that object ID 0 is valid."""
        store = ObjectStore()
        oid = 0
        metadata = {"selector": {"text": "Zero"}, "type": "text"}
        
        store.store(oid, metadata)
        
        assert store.exists(oid) is True
        assert store.get(oid) == metadata
    
    def test_negative_object_id(self):
        """Test that negative object IDs can be stored (edge case)."""
        store = ObjectStore()
        oid = -1
        metadata = {"selector": {"text": "Negative"}, "type": "text"}
        
        store.store(oid, metadata)
        
        assert store.exists(oid) is True
        assert store.get(oid) == metadata
    
    def test_empty_metadata(self):
        """Test storing empty metadata dictionary."""
        store = ObjectStore()
        oid = 600
        metadata = {}
        
        store.store(oid, metadata)
        
        assert store.exists(oid) is True
        assert store.get(oid) == {}
