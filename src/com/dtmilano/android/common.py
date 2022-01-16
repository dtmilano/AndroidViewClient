# -*- coding: utf-8 -*-
'''
Copyright (C) 2012-2018  Diego Torres Milano
Created on Jan 5, 2015

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

__version__ = '20.5.0'

import ast
import os
import platform
import re


def _nd(name):
    '''
    @return: Returns a named decimal regex
    '''
    return '(?P<%s>\d+)' % name


def _nh(name):
    '''
    @return: Returns a named hex regex
    '''
    return '(?P<%s>[0-9a-f]+)' % name


def _ns(name, greedy=False):
    '''
    NOTICE: this is using a non-greedy (or minimal) regex

    @type name: str
    @param name: the name used to tag the expression
    @type greedy: bool
    @param greedy: Whether the regex is greedy or not

    @return: Returns a named string regex (only non-whitespace characters allowed)
    '''
    return '(?P<%s>\S+%s)' % (name, '' if greedy else '?')


def obtainPxPy(m):
    px = int(m.group('px'))
    py = int(m.group('py'))
    return (px, py)


def obtainVxVy(m):
    wvx = int(m.group('vx'))
    wvy = int(m.group('vy'))
    return wvx, wvy


def obtainVwVh(m):
    (wvx, wvy) = obtainVxVy(m)
    wvx1 = int(m.group('vx1'))
    wvy1 = int(m.group('vy1'))
    return (wvx1 - wvx, wvy1 - wvy)


def which(program, isWindows=False):
    import os

    def is_exe(_fpath, _isWindows):
        return os.path.isfile(_fpath) and os.access(_fpath, os.X_OK if not _isWindows else os.F_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program, isWindows):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file, isWindows):
                return exe_file

    return None


def obtainAdbPath():
    '''
    Obtains the ADB path attempting know locations for different OSs
    '''

    FORCE_FAIL = False
    ''' Sometimes, you want it to fail to check the error messages '''
    osName = platform.system()
    isWindows = False
    adb = 'adb'

    if (osName.startswith('Windows')) or (osName.startswith('Java')):
        envOSName = os.getenv('os')  # this should work as it has been set since xp.
        if envOSName.startswith('Windows'):
            adb = 'adb.exe'
            isWindows = True

    exeFile = which(adb, isWindows)
    if exeFile:
        return exeFile

    ANDROID_HOME = os.environ['ANDROID_HOME'] if 'ANDROID_HOME' in os.environ else '/opt/android-sdk'
    HOME = os.environ['HOME'] if 'HOME' in os.environ else ''

    possibleChoices = [os.path.join(ANDROID_HOME, 'platform-tools', adb),
                       os.path.join(HOME, "android", 'platform-tools', adb),
                       os.path.join(HOME, "android-sdk", 'platform-tools', adb),
                       ]

    if osName.startswith('Windows'):
        possibleChoices.append(os.path.join("""C:\Program Files\Android\android-sdk\platform-tools""", adb))
        possibleChoices.append(os.path.join("""C:\Program Files (x86)\Android\android-sdk\platform-tools""", adb))
    elif osName.startswith('Linux'):
        possibleChoices.append(os.path.join(os.sep, "opt", "android-sdk-linux", 'platform-tools', adb))
        possibleChoices.append(os.path.join(HOME, "opt", "android-sdk-linux", 'platform-tools', adb))
        possibleChoices.append(os.path.join(HOME, "android-sdk-linux", 'platform-tools', adb))
        possibleChoices.append(os.path.join(HOME, 'Android', 'Sdk', 'platform-tools', adb))
    elif osName.startswith('Mac'):
        possibleChoices.append(os.path.join(HOME, "Library", "Android", "sdk", 'platform-tools', adb))
        possibleChoices.append(os.path.join(os.sep, "opt", "android-sdk-mac_x86", 'platform-tools', adb))
        possibleChoices.append(os.path.join(HOME, "opt", "android-sdk-mac", 'platform-tools', adb))
        possibleChoices.append(os.path.join(HOME, "android-sdk-mac", 'platform-tools', adb))
        possibleChoices.append(os.path.join(HOME, "opt", "android-sdk-mac_x86", 'platform-tools', adb))
        possibleChoices.append(os.path.join(HOME, "android-sdk-mac_x86", 'platform-tools', adb))
    else:
        # Unsupported OS
        pass

    possibleChoices.append(adb)

    checkedFiles = []

    for exeFile in possibleChoices:
        checkedFiles.append(exeFile)
        if not FORCE_FAIL and os.access(exeFile, os.X_OK):
            return exeFile

    for path in os.environ["PATH"].split(os.pathsep):
        exeFile = os.path.join(path, adb)
        checkedFiles.append(exeFile)
        if not FORCE_FAIL and exeFile is not None and os.access(exeFile, os.X_OK if not isWindows else os.F_OK):
            return exeFile

    if 'ANDROID_HOME' not in os.environ:
        helpMsg = 'Did you forget to set ANDROID_HOME in the environment?'
    else:
        helpMsg = ''

    raise Exception('''adb="%s" is not executable. %s

These files we unsuccessfully checked to find a suitable '%s' executable:
    %s
    ''' % (adb, helpMsg, adb, "\n    ".join(checkedFiles)))


def profileStart():
    import cProfile
    global profile
    profile = cProfile.Profile()
    profile.enable()


def profileEnd():
    profile.disable()
    import io, pstats
    import sys
    s = io.StringIO()
    ps = pstats.Stats(profile, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print('.' * 60, file=sys.stderr)
    print("STATS:\n", s.getvalue(), file=sys.stderr)
    print('.' * 60, file=sys.stderr)


def debugArgsToDict(a):
    """
    Converts a string representation of debug arguments to a dictionary.
    The string can be of the form

       IDENTIFIER1=val1,IDENTIFIER2=val2


     :param a: the argument string
     :return: the dictionary

    """
    s = a.replace('+', ' ')
    s = s.replace('=', ':')
    s = re.sub(r'([A-Z][A-Z_]+)', r"'\1'", s)
    return ast.literal_eval('{ ' + s + ' }')


def substituteDeviceTemplate(filename):
    # FIXME: do replacement as ViewClient.substituteDeviceTemplate but not depending on AdbClient as it is used by
    # UiAutomatorHelper
    return filename
