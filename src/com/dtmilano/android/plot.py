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
import sys
import types
from math import ceil

import matplotlib.pyplot as plt
import mpl_toolkits.axisartist as AA
import numpy as np
from mpl_toolkits.axes_grid1 import host_subplot

from com.dtmilano.android.adb.dumpsys import Dumpsys

__version__ = '13.3.4'

DEBUG = True

NumberTypes = (types.IntType, types.LongType, types.FloatType)


class Plot:
    def __init__(self):
        self.n = 0
        self.na = []
        self.va = []
        self.ava = {}
        ''' Associative values array '''
        self.aava = {}
        ''' (another) Associative values array '''

    def append(self, value):
        self.n += 1
        self.na.append(self.n)
        if isinstance(value, NumberTypes):
            self.va.append(value)
        elif isinstance(value, Dumpsys):
            if not self.ava:
                self.__initAva()
            if not self.aava:
                self.__initAava()
            dumpsys = value
            self.ava[Dumpsys.TOTAL].append(dumpsys.get(Dumpsys.TOTAL))
            self.ava[Dumpsys.ACTIVITIES].append(dumpsys.get(Dumpsys.ACTIVITIES))
            self.ava[Dumpsys.VIEWS].append(dumpsys.get(Dumpsys.VIEWS))
            # self.ava[Dumpsys.VIEW_ROOT_IMPL].append(dumpsys.get(Dumpsys.VIEW_ROOT_IMPL))
            self.aava[Dumpsys.FRAMESTATS].append(dumpsys.get(Dumpsys.FRAMESTATS))
        return self

    def __initAva(self):
        self.ava[Dumpsys.TOTAL] = []
        self.ava[Dumpsys.ACTIVITIES] = []
        self.ava[Dumpsys.VIEWS] = []
        # self.ava[Dumpsys.VIEW_ROOT_IMPL] = []

    def __initAava(self):
        self.aava[Dumpsys.FRAMESTATS] = []

    def plot(self, _type=Dumpsys.MEMINFO, filename=None):
        title = "Dumpsys"
        if _type == Dumpsys.FRAMESTATS:
            subtitle = "gfxinfo " + Dumpsys.FRAMESTATS
        else:
            subtitle = _type
        if _type == Dumpsys.MEMINFO:
            if self.ava:
                if DEBUG:
                    print >> sys.stderr, "plot:"
                    for k in self.ava.keys():
                        print >> sys.stderr, "   ", k, ":", self.ava[k]

                host = host_subplot(111, axes_class=AA.Axes)
                plt.subplots_adjust(right=0.75)
                par = {}
                for k in self.ava.keys():
                    if k != Dumpsys.TOTAL:
                        par[k] = host.twinx()

                axis = 1
                for k in self.ava.keys():
                    if k != Dumpsys.TOTAL and k != Dumpsys.ACTIVITIES:
                        offset = axis * 60
                        axis += 1
                        new_fixed_axis = par[k].get_grid_helper().new_fixed_axis
                        par[k].axis["right"] = new_fixed_axis(loc="right",
                                                              axes=par[k],
                                                              offset=(offset, 0))
                        par[k].axis["right"].toggle(all=True)

                if DEBUG:
                    print >> sys.stderr, "setting host x lim ", (np.amin(self.na), np.amax(self.na))
                minx = np.amin(self.na)
                maxx = np.amax(self.na)
                divx = abs(maxx - minx) / (len(self.na) * 1.0)
                host.set_xlim(minx - divx, maxx + divx)
                miny = np.amin(self.ava[Dumpsys.TOTAL])
                maxy = np.amax(self.ava[Dumpsys.TOTAL])
                divy = ceil(abs(maxy - miny) / (len(self.ava[Dumpsys.TOTAL]) * 1.0))
                if DEBUG:
                    print >> sys.stderr, "setting host y lim ", (miny - divy, maxy + divy)
                host.set_ylim(miny - divy, maxy + divy)
                host.set_xlabel('N')
                host.set_ylabel(Dumpsys.TOTAL)

                for k in self.ava.keys():
                    if k != Dumpsys.TOTAL:
                        par[k].set_ylabel(k)

                plots = {}
                if DEBUG:
                    print >> sys.stderr, "    host plot", self.na, ":", self.ava[Dumpsys.TOTAL]
                plots[Dumpsys.TOTAL], = host.plot(self.na, self.ava[Dumpsys.TOTAL], label=Dumpsys.TOTAL, linewidth=2)
                for k in self.ava.keys():
                    if k != Dumpsys.TOTAL:
                        if DEBUG:
                            print >> sys.stderr, "   ", k, " plot", self.na, ":", self.ava[k]
                        plots[k], = par[k].plot(self.na, self.ava[k], label=k, linewidth=2)

                for k in self.ava.keys():
                    if k != Dumpsys.TOTAL:
                        miny = np.amin(self.ava[k])
                        maxy = np.amax(self.ava[k])
                        divy = ceil(abs(maxy - miny) / (len(self.ava[k]) * 1.0))
                        if DEBUG:
                            print >> sys.stderr, "setting", k, "y lim ", (miny - divy, maxy + divy)
                        par[k].set_ylim(miny - divy, maxy + divy)

                host.legend()

                # host.axis["left"].label.set_color(plots[Dumpsys.TOTAL].get_color())
                # for k in self.ava.keys():
                #     if k != Dumpsys.TOTAL:
                #         par[k].axis["right"].label.set_color(plots[k].get_color())

            elif self.va:
                plt.xlabel('N')
                plt.ylabel('V')
                plt.plot(self.na, self.va, label="A")
            else:
                raise RuntimeError("No values to plot")
        elif _type == Dumpsys.FRAMESTATS:
            n, bins, patches = plt.hist(self.aava[Dumpsys.FRAMESTATS])
            ymax = np.amax(n)
            x = []
            y = []
            for v in range(int(ceil(ymax)) + 1):
                x.append(1 / 60.0 * 10 ** 9)
                y.append(v)
            plt.plot(x, y, linewidth=2, color='c')
            x = []
            y = []
            for v in range(int(ceil(ymax)) + 1):
                x.append(1 / 30.0 * 10 ** 9)
                y.append(v)
            plt.plot(x, y, linewidth=2, color='r')
            plt.xlabel('ms')
            plt.ylabel('Frames')

        plt.title(title + ' ' + subtitle)
        plt.grid(True)
        plt.draw()
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
