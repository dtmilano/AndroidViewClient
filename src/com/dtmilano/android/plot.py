# -*- coding: utf-8 -*-
"""
Copyright (C) 2012-2017  Diego Torres Milano
Created on mar 11, 2017

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
import types

import matplotlib.pyplot as plt

from com.dtmilano.android.adb.dumpsys import Dumpsys

__version__ = '13.1.0'


NumberTypes = (types.IntType, types.LongType, types.FloatType)


class Plot:

    def __init__(self):
        self.n = 0
        self.na = []
        self.va = []
        self.ava = {}

    def append(self, value):
        self.n += 1
        self.na.append(self.n)
        if isinstance(value, NumberTypes):
            self.va.append(value)
        elif isinstance(value, Dumpsys):
            dumpsys = value
            if not self.ava:
                self.__initAva()
            self.ava[Dumpsys.TOTAL].append(dumpsys.get(Dumpsys.TOTAL)/(1024*1024))
            self.ava[Dumpsys.ACTIVITIES].append(dumpsys.get(Dumpsys.ACTIVITIES))
            self.ava[Dumpsys.VIEWS].append(dumpsys.get(Dumpsys.VIEWS))
            self.ava[Dumpsys.VIEW_ROOT_IMPL].append(dumpsys.get(Dumpsys.VIEW_ROOT_IMPL))

    def __initAva(self):
        self.ava[Dumpsys.TOTAL] = []
        self.ava[Dumpsys.ACTIVITIES] = []
        self.ava[Dumpsys.VIEWS] = []
        self.ava[Dumpsys.VIEW_ROOT_IMPL] = []

    def plot(self):
        plt.xlabel('N')
        plt.ylabel('V')
        if self.ava:
            for k in self.ava.keys():
                plt.plot(self.na, self.ava[k], label=k)
        elif self.va:
            plt.plot(self.na, self.va, label="A")
        else:
            raise RuntimeError("No values to plot")
        plt.title('About as simple as it gets, folks')
        plt.grid(True)
        plt.savefig("plot.png")
        plt.show()
