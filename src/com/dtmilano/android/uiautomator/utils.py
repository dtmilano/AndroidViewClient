# -*- coding: utf-8 -*-
"""
Copyright (C) 2012-2022  Diego Torres Milano
Created on Nov 7, 2022

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@author: Diego Torres Milano
"""

from __future__ import print_function

from typing import Union

from culebratester_client import WindowHierarchyChild, Selector, WindowHierarchy


def window_hierarchy_child_to_selector(window_hierarchy_child: WindowHierarchyChild) -> Selector:
    """
    Converts a WindowHierarchyChild to a Selector.

    :param window_hierarchy_child: the WindowHierarchyChild to convert
    :type window_hierarchy_child: WindowHierarchyChild
    :return: the Selector
    :rtype: Selector
    """
    sel = Selector()
    sel.checkable = window_hierarchy_child.checkable
    sel.checked = window_hierarchy_child.checked
    sel.clazz = window_hierarchy_child.clazz
    sel.clickable = window_hierarchy_child.clickable
    sel.depth = None
    sel.desc = window_hierarchy_child.content_description if window_hierarchy_child.content_description else None
    sel.pkg = window_hierarchy_child.package if window_hierarchy_child.package else None
    sel.res = window_hierarchy_child.resource_id if window_hierarchy_child.resource_id else None
    sel.scrollable = window_hierarchy_child.scrollable
    sel.text = window_hierarchy_child.text if window_hierarchy_child.text else None
    sel.index = None  # child.index (could be 0)
    sel.instance = None
    return sel


def window_hierarchy_to_selector_list(node: Union[WindowHierarchy, WindowHierarchyChild], selector_list=None) -> list[
        Selector]:
    """
    Converts a WindowHierarchy (obtained via ``window_hierarchy_dump()``) to a Selector list.

    :param node: the node being processed
    :type node: Union[WindowHierarchy, WindowHierarchyChild]
    :param selector_list: the list, could be ``None``
    :type selector_list: list[Selector]
    :return: the list
    :rtype: list[Selector]
    """
    if selector_list is None:
        selector_list = []
    if node.id != 'hierarchy':
        selector_list.append(window_hierarchy_child_to_selector(node))
    for ch in node.children:
        window_hierarchy_to_selector_list(ch, selector_list)
    return selector_list
