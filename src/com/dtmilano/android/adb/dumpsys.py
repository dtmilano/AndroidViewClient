'''
Copyright (C) 2012-2018  Diego Torres Milano
Created on Dec 1, 2012

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
'''
from __future__ import print_function

import re
import sys
from _warnings import warn

__version__ = '15.8.0'

DEBUG = False


class Dumpsys:
    FRAMESTATS = 'framestats'
    GFXINFO = 'gfxinfo'
    MEMINFO = 'meminfo'
    RESET = 'reset'

    ACTIVITIES = 'activities'
    TOTAL = 'total'
    VIEW_ROOT_IMPL = 'viewRootImpl'
    VIEWS = 'views'

    FLAGS = 0
    INTENDED_VSYNC = 1
    FRAME_COMPLETED = 13

    def __init__(self, adbclient, subcommand, *args):
        self.nativeHeap = -1
        self.dalvikHeap = -1
        self.total = 0
        self.views = -1
        self.activities = -1
        self.appContexts = -1
        self.viewRootImpl = -1
        self.gfxProfileData = []
        self.framestats = []
        if args:
            args_str = ' '.join(args)
        else:
            args_str = ''
        if adbclient:
            cmd = 'dumpsys ' + subcommand + (' ' + args_str if args_str else '')
            self.parse(adbclient.shell(cmd), subcommand, *args)
        else:
            warn('No adbclient specified')

    @staticmethod
    def listSubCommands(adbclient):
        return Dumpsys(adbclient, '-l')

    @staticmethod
    def meminfo(adbclient, args=None):
        return Dumpsys(adbclient, Dumpsys.MEMINFO, args)

    def get(self, name):
        return getattr(self, name)

    def parse(self, out, subcommand, *args):
        if subcommand == Dumpsys.MEMINFO:
            self.parseMeminfo(out)
        elif subcommand == Dumpsys.GFXINFO:
            if Dumpsys.RESET in args:
                # Actually, reset does not need to parse anything
                pass
            elif Dumpsys.FRAMESTATS in args:
                self.parseGfxinfoFramestats(out)
            else:
                self.parseGfxinfo(out)
        elif '-l':
            # list dumpsys subcommands
            return out
        else:
            pass

    def parseMeminfo(self, out):
        m = re.search('Native Heap[ \t]*(\d+)', out, re.MULTILINE)
        if m:
            self.nativeHeap = int(m.group(1))
        m = re.search('Dalvik Heap[ \t]*(\d+)', out, re.MULTILINE)
        if m:
            self.dalvikHeap = int(m.group(1))
        m = re.search('Views:[ \t]*(\d+)', out, re.MULTILINE)
        if m:
            self.views = int(m.group(1))
        m = re.search('Activities:[ \t]*(\d+)', out, re.MULTILINE)
        if m:
            self.activities = int(m.group(1))
        m = re.search('AppContexts:[ \t]*(\d+)', out, re.MULTILINE)
        if m:
            self.appContexts = int(m.group(1))
        m = re.search('ViewRootImpl:[ \t]*(\d+)', out, re.MULTILINE)
        if m:
            self.viewRootImpl = int(m.group(1))

        m = re.search('TOTAL[ \t]*(\d+)', out, re.MULTILINE)
        if m:
            self.total = int(m.group(1))
        else:
            raise RuntimeError('Cannot find TOTAL in "' + out + '"')

    def parseGfxinfo(self, out):
        pass

    def parseGfxinfoFramestats(self, out):
        pd = '---PROFILEDATA---'
        l = re.findall(r'%s.*?%s' % (pd, pd), out, re.DOTALL)
        if l:
            s = ''
            for e in l:
                if not e:
                    continue
                sl = e.splitlines()
                for s in sl:
                    if s == pd:
                        continue
                    pda = s.split(',')
                    if pda[Dumpsys.FLAGS] == 'Flags':
                        if pda[Dumpsys.INTENDED_VSYNC] != 'IntendedVsync' and pda[
                                Dumpsys.FRAME_COMPLETED] != 'FrameCompleted':
                            raise RuntimeError('Unsupported gfxinfo version')
                        continue
                    if pda[Dumpsys.FLAGS] == '0':
                        # Only keep lines with Flags=0
                        # If this is non-zero the row should be ignored, as the frame has been determined as being an
                        # outlier from normal performance, where it is expected that layout & draw take longer than
                        # 16ms.
                        # See https://developer.android.com/training/testing/performance.html#timing-info for details
                        # on format
                        if DEBUG:
                            print('pda={}'.format(pda), file=sys.stderr)
                        self.gfxProfileData.append(pda[:-1])
                        # All done! The total time spent working on this frame can be computed by doing
                        # FRAME_COMPLETED - INTENDED_VSYNC.
                        self.framestats.append(
                            (int(pda[Dumpsys.FRAME_COMPLETED]) - int(pda[Dumpsys.INTENDED_VSYNC])) / 10 ** 6)
        else:
            raise RuntimeError('No profile data found')

    @staticmethod
    def gfxinfo(adbclient, *args):
        return Dumpsys(adbclient, Dumpsys.GFXINFO, *args)

    @staticmethod
    def resetGfxinfo(adbclient, pkg):
        return Dumpsys(adbclient, Dumpsys.GFXINFO, pkg, Dumpsys.RESET)
