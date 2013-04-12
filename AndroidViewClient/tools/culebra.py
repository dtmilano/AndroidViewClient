#! /usr/bin/env monkeyrunner
# -*- coding: utf-8 -*-
'''
Copyright (C) 2013  Diego Torres Milano
Created on Mar 28, 2013

Scripter helps you create AndroidViewClient scripts generating a working template that can be
modified to suit more specific needs.
                      __    __    __    __
                     /  \  /  \  /  \  /  \ 
____________________/  __\/  __\/  __\/  __\_____________________________
___________________/  /__/  /__/  /__/  /________________________________
                   | / \   / \   / \   / \  \____
                   |/   \_/   \_/   \_/   \    o \ 
                                           \_____/--<
@author: diego
@author: Jennifer E. Swofford (ascii art snake)
'''

__version__ = '0.9.4'

import re
import sys
import os
import getopt
import warnings
from datetime import date

# This must be imported before MonkeyRunner and MonkeyDevice,
# otherwise the import fails.
# PyDev sets PYTHONPATH, use it
try:
    for p in os.environ['PYTHONPATH'].split(':'):
        if not p in sys.path:
            sys.path.append(p)
except:
    pass
    
try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

HELP = 'help'
VERBOSE = 'verbose'
IGNORE_SECURE_DEVICE = 'ignore-secure-device'
FORCE_VIEW_SERVER_USE = 'force-view-server-use'
DO_NOT_START_VIEW_SERVER = 'do-not-start-view-server'
FIND_VIEWS_BY_ID = 'find-views-by-id'
FIND_VIEWS_WITH_TEXT = 'find-views-with-text'
USE_REGEXPS = 'use-regexps'
VERBOSE_COMMENTS = 'verbose-comments'
UNIT_TEST = 'unit-test'
USAGE = 'usage: %s [OPTION]... [serialno]'
# -u,-s,-p,-v eaten by monkeyrunner
SHORT_OPTS = 'HVIFSi:t:rCU'
LONG_OPTS =  [HELP, VERBOSE, IGNORE_SECURE_DEVICE, FORCE_VIEW_SERVER_USE, DO_NOT_START_VIEW_SERVER,
              FIND_VIEWS_BY_ID+'=', FIND_VIEWS_WITH_TEXT+'=',  USE_REGEXPS, VERBOSE_COMMENTS, UNIT_TEST]
LONG_OPTS_ARG = {FIND_VIEWS_BY_ID: 'BOOL', FIND_VIEWS_WITH_TEXT: 'BOOL'}
OPTS_HELP = {
    'H': 'prints this help',
    'i': 'whether to use findViewById() in script',
    't': 'whether to use findViewWithText() in script',
    'U': 'generates unit test script',
    }
ID_RE = re.compile('id/([^/]*)(/(\d+))?')

def shortAndLongOptions():
    '''
    @return: the list of corresponding (short-option, long-option) tuples
    '''

    short_opts = SHORT_OPTS.replace(':', '')
    if len(short_opts) != len(LONG_OPTS):
        raise Exception('There is a mismatch between short and long options')
    t = tuple(short_opts) + tuple(LONG_OPTS)
    l2 = len(t)/2
    sl = []
    for i in range(l2):
        sl.append((t[i], t[i+l2]))
    return sl

def usage(exitVal=1):
    print >> sys.stderr, USAGE % progname
    print >> sys.stderr, "Try '%s --help' for more information." % progname
    sys.exit(exitVal)

def help():
    print >> sys.stderr, USAGE % progname
    print >> sys.stderr
    print >> sys.stderr, "Options:"
    for so, lo in shortAndLongOptions():
        o = '  -%c, --%s' % (so, lo)
        if lo[-1] == '=':
            o += LONG_OPTS_ARG[lo[:-1]]
        try:
            o = '%-35s %-44s' % (o, OPTS_HELP[so])
        except:
            pass
        print >> sys.stderr, o
    sys.exit(0)

def printVerboseComments(view):
    '''
    Prints the verbose comments for view.
    '''

    print '\n# class=%s' % view.getClass(),
    try:
        text = view.getText()
        if text:
            print 'text="%s"' % text,
    except:
        pass
    try:
        tag = view.getTag()
        if tab != 'null':
            print 'tag=%s' % tag
    except:
        pass
    print

def variableNameFromId(id):
    '''
    Returns a suitable variable name from the id.
    
    @type id: str
    @param id: the I{id}
    @return: the variable name from the id
    '''
    
    m = ID_RE.match(id)
    if m:
        var = m.group(1)
        if m.group(3):
            var += m.group(3)
        if re.match('^\d', var):
            var = 'id_' + var
        return var
    else:
        raise Exception('Not an id: %s' % id)

def printFindViewWithText(view, useregexp):
    '''
    Prints the corresponding statement.
    
    @type view: L{View}
    @param view: the View
    '''
    
    id = view.getUniqueId()
    text = view.getText()
    if text:
        var = variableNameFromId(id)
        if useregexp:
            text = "re.compile('%s')" % text
        else:
            text = "'%s'" % text
        print '%s = vc.findViewWithTextOrRaise(%s)' % (var, text)
    elif kwargs1[VERBOSE]:
        warnings.warn('View with id=%s has no text' % id)

def printFindViewById(view):
    '''
    Prints the corresponding statement.
    
    @type view: L{View}
    @param view: the View
    '''
    
    id = view.getUniqueId()
    var = variableNameFromId(id)
    print '%s = vc.findViewByIdOrRaise("%s")' % (var, id)
    
def traverseAndPrint(view):
    '''
    Traverses the View tree and prints the corresponding statement.
    
    @type view: L{View}
    @param view: the View
    '''
    
    if options[VERBOSE_COMMENTS]:
        printVerboseComments(view)
    if options[FIND_VIEWS_BY_ID]:
        printFindViewById(view)
    if options[FIND_VIEWS_WITH_TEXT]:
        printFindViewWithText(view, options[USE_REGEXPS])

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1", "on")

# __main__
progname = os.path.basename(sys.argv[0])
try:
    optlist, args = getopt.getopt(sys.argv[1:], SHORT_OPTS, LONG_OPTS)
except getopt.GetoptError, e:
    print >>sys.stderr, 'ERROR:', str(e)
    usage()

sys.argv[1:] = args
kwargs1 = {VERBOSE: False, 'ignoresecuredevice': False}
kwargs2 = {'forceviewserveruse': False, 'startviewserver': True}
options = {FIND_VIEWS_BY_ID: True, FIND_VIEWS_WITH_TEXT: False, USE_REGEXPS: False, VERBOSE_COMMENTS: False, UNIT_TEST: False}
transform = traverseAndPrint
for o, a in optlist:
    o = o.strip('-')
    if o in ['H', HELP]:
        help()
    elif o in ['V', VERBOSE]:
        kwargs1[VERBOSE] = True
    elif o in ['I', IGNORE_SECURE_DEVICE]:
        kwargs1['ignoresecuredevice'] = True
    elif o in ['F', FORCE_VIEW_SERVER_USE]:
        kwargs2['forceviewserveruse'] = True
    elif o in ['S', DO_NOT_START_VIEW_SERVER]:
        kwargs2['startviewserver'] = False
    elif o in ['i', FIND_VIEWS_BY_ID]:
        options[FIND_VIEWS_BY_ID] = str2bool(a)
    elif o in ['t', FIND_VIEWS_WITH_TEXT]:
        options[FIND_VIEWS_WITH_TEXT] = str2bool(a)
    elif o in ['r', USE_REGEXPS]:
        options[USE_REGEXPS] = True
    elif o in ['C', VERBOSE_COMMENTS]:
        options[VERBOSE_COMMENTS] = True
    elif o in ['U', UNIT_TEST]:
        warnings.warn('Not implemented yet: %s' % o)
        options[UNIT_TEST] = True

if not (options[FIND_VIEWS_BY_ID] or options[FIND_VIEWS_WITH_TEXT]):
    if not options[VERBOSE_COMMENTS]:
        warnings.warn('All printing options disabled. Output will be empty.')
    else:
        warnings.warn('Only verbose comments will be printed')

device, serialno = ViewClient.connectToDeviceOrExit(**kwargs1)
vc = ViewClient(device, serialno, **kwargs2)
print '''#! /usr/bin/env monkeyrunner
# -*- coding: utf-8 -*-
\'\'\'
Copyright (C) 2013  Diego Torres Milano
Created on %s by Scripter v%s

                      __    __    __    __
                     /  \  /  \  /  \  /  \ 
____________________/  __\/  __\/  __\/  __\_____________________________
___________________/  /__/  /__/  /__/  /________________________________
                   | / \   / \   / \   / \  \____
                   |/   \_/   \_/   \_/   \    o \ 
                                           \_____/--<
@author: diego
@author: Jennifer E. Swofford (ascii art snake)
\'\'\'


import re
import sys
import os

# This must be imported before MonkeyRunner and MonkeyDevice,
# otherwise the import fails.
# PyDev sets PYTHONPATH, use it
try:
    for p in os.environ['PYTHONPATH'].split(':'):
        if not p in sys.path:
            sys.path.append(p)
except:
    pass
    
try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import ViewClient

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
  
device, serialno = ViewClient.connectToDeviceOrExit()
vc = ViewClient(device, serialno)
''' % (date.today(), __version__)

vc.traverse(transform=transform)
