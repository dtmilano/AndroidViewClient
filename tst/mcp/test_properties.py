#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-Based Tests for MCP Server

This module contains property-based tests that verify universal correctness
properties of the MCP server components using the Hypothesis library.

Each test runs a minimum of 100 iterations with randomly generated inputs
to ensure the properties hold across all valid executions.

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
from hypothesis import given, strategies as st, settings
from com.dtmilano.android.mcp.object_store import ObjectStore


class TestObjectStoreProperties:
    """
    Property-based tests for ObjectStore.
    
    These tests verify that the ObjectStore maintains consistency across
    all possible sequences of operations.
    """
    
    @given(
        oid=st.integers(min_value=0, max_value=1000000),
        metadata=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.booleans(),
                st.dictionaries(
                    keys=st.text(min_size=1, max_size=10),
                    values=st.text(max_size=50)
                )
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_property_3_object_store_consistency(self, oid, metadata):
        """
        Feature: culebratester2-mcp-server, Property 3: Object Store Consistency
        
        Property: For any object ID returned by a find operation, subsequent
        operations using that object ID SHALL either succeed or return a
        descriptive error message if the object no longer exists in the store.
        
        Validates: Requirements 3.6, 8.2
        """
        store = ObjectStore()
        
        # Store the object
        store.store(oid, metadata)
        
        # Verify the object exists
        assert store.exists(oid), "Object should exist after storing"
        
        # Verify we can retrieve it
        retrieved = store.get(oid)
        assert retrieved is not None, "Should be able to retrieve stored object"
        assert retrieved == metadata, "Retrieved metadata should match stored metadata"
        
        # Remove the object
        store.remove(oid)
        
        # Verify the object no longer exists
        assert not store.exists(oid), "Object should not exist after removal"
        
        # Verify get returns None for non-existent object
        assert store.get(oid) is None, "Should return None for non-existent object"
    
    @given(
        oid=st.integers(min_value=0, max_value=1000000),
        selector=st.dictionaries(
            keys=st.sampled_from(['text', 'resourceId', 'className', 'description']),
            values=st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=4
        ),
        selector_type=st.sampled_from(['text', 'resourceId', 'className', 'description'])
    )
    @settings(max_examples=100)
    def test_property_9_selector_preservation(self, oid, selector, selector_type):
        """
        Feature: culebratester2-mcp-server, Property 9: Selector Preservation
        
        Property: For any UI element found using a selector, the object store
        SHALL preserve the selector information such that it can be retrieved
        using the returned object ID.
        
        Validates: Requirements 3.6
        """
        store = ObjectStore()
        
        # Create metadata with selector information
        metadata = {
            "selector": selector,
            "type": selector_type
        }
        
        # Store the object with selector metadata
        store.store(oid, metadata)
        
        # Retrieve the object
        retrieved = store.get(oid)
        
        # Verify selector information is preserved
        assert retrieved is not None, "Should be able to retrieve stored object"
        assert "selector" in retrieved, "Metadata should contain selector"
        assert "type" in retrieved, "Metadata should contain type"
        assert retrieved["selector"] == selector, "Selector should be preserved exactly"
        assert retrieved["type"] == selector_type, "Selector type should be preserved"
    
    @given(
        operations=st.lists(
            st.tuples(
                st.sampled_from(['store', 'get', 'exists', 'remove']),
                st.integers(min_value=0, max_value=100),
                st.dictionaries(
                    keys=st.text(min_size=1, max_size=10),
                    values=st.text(max_size=50),
                    min_size=1,
                    max_size=5
                )
            ),
            min_size=1,
            max_size=50
        )
    )
    @settings(max_examples=100)
    def test_object_store_operation_sequence(self, operations):
        """
        Property: The object store should maintain consistency across any
        sequence of operations.
        
        This test verifies that no matter what sequence of store, get, exists,
        and remove operations are performed, the object store maintains
        internal consistency.
        """
        store = ObjectStore()
        stored_oids = set()
        
        for operation, oid, metadata in operations:
            if operation == 'store':
                store.store(oid, metadata)
                stored_oids.add(oid)
                # After storing, object should exist
                assert store.exists(oid)
                assert store.get(oid) == metadata
                
            elif operation == 'get':
                result = store.get(oid)
                # Result should be None if not stored, otherwise should match
                if oid in stored_oids:
                    assert result is not None
                else:
                    assert result is None
                    
            elif operation == 'exists':
                result = store.exists(oid)
                # Should return True if stored, False otherwise
                assert result == (oid in stored_oids)
                
            elif operation == 'remove':
                store.remove(oid)
                stored_oids.discard(oid)
                # After removing, object should not exist
                assert not store.exists(oid)
                assert store.get(oid) is None
    
    @given(
        oids_and_metadata=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=1000),
                st.dictionaries(
                    keys=st.text(min_size=1, max_size=10),
                    values=st.text(max_size=50),
                    min_size=1,
                    max_size=5
                )
            ),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_clear_removes_all_objects(self, oids_and_metadata):
        """
        Property: Calling clear() should remove all objects from the store,
        regardless of how many objects were stored.
        """
        store = ObjectStore()
        
        # Store all objects
        for oid, metadata in oids_and_metadata:
            store.store(oid, metadata)
            assert store.exists(oid)
        
        # Clear the store
        store.clear()
        
        # Verify all objects are gone
        for oid, _ in oids_and_metadata:
            assert not store.exists(oid), "Object {} should not exist after clear".format(oid)
            assert store.get(oid) is None, "get({}) should return None after clear".format(oid)
