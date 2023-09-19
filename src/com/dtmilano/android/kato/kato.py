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
import re
import sys
import textwrap
from collections import OrderedDict

from culebratester_client import Selector
from culebratester_client.rest import ApiException

from com.dtmilano.android.distance import levenshtein_distance
from com.dtmilano.android.uiautomator.utils import window_hierarchy_to_selector_list

#
# https://en.wikipedia.org/wiki/Kato_(The_Green_Hornet)
#

DEBUG = False
DEBUG_WRAPPER = False


class Kato:
    def __init__(self):
        self.enabled = False
        self.selectors = []
        self.distances = OrderedDict()
        # If pkg has been specified in the selector, only finds other selectors with the same pkg when True
        self.comply_with_pkg = False
        self.max_num_of_selectors = 5


def kato(func):
    """
    Kato decorator.

    :param func: the function to invoke
    :type func: function
    :return: the wrapper
    :rtype:
    """

    def wrapper(*args, **kwargs):
        if DEBUG_WRAPPER:
            print('kato.wrapper:', args, kwargs)
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            helper = args[0].uiAutomatorHelper
            if not helper.kato.enabled:
                raise e
            find_me_the_selectors(e, *args, **kwargs, func=func.__name__, distance_func=levenshtein_distance,
                                  distance_func_argument_mapper=str,
                                  max_num_of_selectors=helper.kato.max_num_of_selectors)

    return wrapper


def find_me_the_selectors(e: ApiException, *args, **kwargs):
    """
    Finds the selectors that would lead to a successful `find_object()`.
    The selectors found are added to the `selectors` list.

    :param e: the exception from a `find_object()` that couldn't find an object matching the selector
    :param args: args[0] is the UiDevice object
    :param kwargs:  - `body` the body of the request
                    - `distance_func` the distance function to apply
                    - `distance_func_argument_mapper` maps the arguments to distance_func from Selector to a type suitable
                    - `max_num_of_selectors` limit the number of selectors returned
                    for that function
    :return: re-raise the original exception
    """
    if DEBUG:
        print('🐝 find_me_the_selectors', args, kwargs, file=sys.stderr)
    helper = args[0].uiAutomatorHelper
    msg = ''
    if helper.kato.enabled:
        if e.status == 404:
            distance = kwargs['distance_func']
            mapper = kwargs['distance_func_argument_mapper']
            selector = Selector(**kwargs['body'])
            helper.kato.selectors = window_hierarchy_to_selector_list(
                helper.ui_device.dump_window_hierarchy(_format='JSON'))
            if selector.pkg and helper.kato.comply_with_pkg:
                helper.kato.selectors = list(filter(lambda _s: _s.pkg == selector.pkg, helper.kato.selectors))
            _d = dict()
            for n, s in enumerate(helper.kato.selectors):
                _d[distance(mapper(selector), mapper(s))] = s
            helper.kato.distances = OrderedDict(sorted(_d.items(), reverse=False))
            msg = f"Kato: selector distances:\n"
            for n, (k, v) in enumerate(helper.kato.distances.items()):
                msg += textwrap.indent(f"{k} ➡ {v}\n", "    ", lambda line: re.match(r"^\d+ ", line) is None)
                if n >= kwargs["max_num_of_selectors"]:
                    break
    raise ApiException(msg, e)
