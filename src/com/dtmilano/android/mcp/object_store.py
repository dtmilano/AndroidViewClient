#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Object Store for MCP Server

This module provides an in-memory storage mechanism for UI element references
returned by CulebraTester2 find operations. The object store allows MCP tools
to cache and reuse object identifiers across multiple operations.

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

from typing import Dict, Any, Optional

__version__ = '25.0.0'


class ObjectStore:
    """
    In-memory storage for UI element references.
    
    The ObjectStore maintains a mapping between object IDs (returned by
    CulebraTester2) and metadata about those objects (such as the selector
    used to find them). This allows MCP tools to validate object IDs before
    performing operations and to retrieve information about cached objects.
    
    Example:
        >>> store = ObjectStore()
        >>> store.store(123, {"selector": {"text": "Login"}, "type": "text"})
        >>> store.exists(123)
        True
        >>> store.get(123)
        {'selector': {'text': 'Login'}, 'type': 'text'}
        >>> store.remove(123)
        >>> store.exists(123)
        False
    """
    
    def __init__(self):
        """Initialize an empty object store."""
        self._objects: Dict[int, Dict[str, Any]] = {}
    
    def store(self, oid: int, metadata: Dict[str, Any]) -> None:
        """
        Store an object reference with associated metadata.
        
        Args:
            oid: The object ID returned by CulebraTester2
            metadata: Dictionary containing information about the object,
                     typically including the selector used to find it
        
        Example:
            >>> store.store(456, {
            ...     "selector": {"resourceId": "com.example:id/button"},
            ...     "type": "resourceId"
            ... })
        """
        self._objects[oid] = metadata
    
    def get(self, oid: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a stored object.
        
        Args:
            oid: The object ID to look up
        
        Returns:
            Dictionary containing the object's metadata, or None if the
            object ID is not found in the store
        
        Example:
            >>> metadata = store.get(456)
            >>> if metadata:
            ...     print(metadata['selector'])
            {'resourceId': 'com.example:id/button'}
        """
        return self._objects.get(oid)
    
    def exists(self, oid: int) -> bool:
        """
        Check if an object ID exists in the store.
        
        Args:
            oid: The object ID to check
        
        Returns:
            True if the object ID exists, False otherwise
        
        Example:
            >>> if store.exists(456):
            ...     print("Object found")
            Object found
        """
        return oid in self._objects
    
    def remove(self, oid: int) -> None:
        """
        Remove an object from the store.
        
        This method is idempotent - removing a non-existent object ID
        does not raise an error.
        
        Args:
            oid: The object ID to remove
        
        Example:
            >>> store.remove(456)
            >>> store.exists(456)
            False
        """
        if oid in self._objects:
            del self._objects[oid]
    
    def clear(self) -> None:
        """
        Clear all objects from the store.
        
        This removes all cached object references, effectively resetting
        the store to its initial empty state.
        
        Example:
            >>> store.clear()
            >>> len(store._objects)
            0
        """
        self._objects.clear()
