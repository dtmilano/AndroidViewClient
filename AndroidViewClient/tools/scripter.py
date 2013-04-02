#! /usr/bin/env monkeyrunner
# -*- coding: utf-8 -*-
'''
Copyright (C) 2013  Diego Torres Milano
Created on Mar 28, 2013

Scripter helps you create AndroidViewClient scripts generating a working template that can be
modified to suit more specific needs.

@author: diego
'''

__version__ = '0.9.2'

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
# -u,-s,-p,-v eaten by monkeyrunner
SHORT_OPTS = 'HVIFSitrC'
LONG_OPTS =  [HELP, VERBOSE, IGNORE_SECURE_DEVICE, FORCE_VIEW_SERVER_USE, DO_NOT_START_VIEW_SERVER,
              FIND_VIEWS_BY_ID, FIND_VIEWS_WITH_TEXT,  USE_REGEXPS, VERBOSE_COMMENTS]
ID_RE = re.compile('id/([^/]*)(/(\d+))?')

def shortAndLongOptions():
    '''
    @return: the list of corresponding (short-option, long-option) tuples
    '''

    if len(SHORT_OPTS) != len(LONG_OPTS):
        raise Exception('There is a mismatch between short and long options')
    t = tuple(SHORT_OPTS) + tuple(LONG_OPTS)
    l2 = len(t)/2
    sl = []
    for i in range(l2):
        sl.append((t[i], t[i+l2]))
    return sl

def usage(exitVal=1):
    print >> sys.stderr, 'usage: scripter.py ',
    for so, lo in shortAndLongOptions():
        print >> sys.stderr, '[-%c|--%s]' % (so, lo),
    print >> sys.stderr, '[serialno]'
    sys.exit(exitVal)

def verboseComments(view):
    if options[VERBOSE_COMMENTS]:
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

def traverseAndPrintFindViewById(view):
    '''
    Traverses the View tree and prints the corresponding statement.
    
    @type view: L{View}
    @param view: the View
    '''
    
    id = view.getUniqueId()
    var = variableNameFromId(id)
    verboseComments(view)
    print '%s = vc.findViewByIdOrRaise("%s")' % (var, id)

def traverseAndPrintFindViewWithText(view):
    '''
    Traverses the View tree and prints the corresponding statement.
    
    @type view: L{View}
    @param view: the View
    '''
    
    id = view.getUniqueId()
    text = view.getText()
    if text:
        verboseComments(view)
        var = variableNameFromId(id)
        if options[USE_REGEXPS]:
            text = "re.compile('%s')" % text
        else:
            text = "'%s'" % text
        print '%s = vc.findViewWithTextOrRaise(%s)' % (var, text)
    elif kwargs1[VERBOSE]:
        warnings.warn('View with id=%s has no text' % id)

try:
    opts, args = getopt.getopt(sys.argv[1:], SHORT_OPTS, LONG_OPTS)
except getopt.GetoptError, e:
    print >>sys.stderr, 'ERROR:', str(e)
    usage()

kwargs1 = {VERBOSE: False, 'ignoresecuredevice': False}
kwargs2 = {'forceviewserveruse': False, 'startviewserver': True}
options = {USE_REGEXPS: False, VERBOSE_COMMENTS: False}
transform = traverseAndPrintFindViewById
for o, a in opts:
    o = o.strip('-')
    if o in ['H', HELP]:
        usage(0)
    elif o in ['V', VERBOSE]:
        kwargs1[VERBOSE] = True
    elif o in ['I', IGNORE_SECURE_DEVICE]:
        kwargs1['ignoresecuredevice'] = True
    elif o in ['F', FORCE_VIEW_SERVER_USE]:
        kwargs2['forceviewserveruse'] = True
    elif o in ['S', DO_NOT_START_VIEW_SERVER]:
        kwargs2['startviewserver'] = False
    elif o in ['i', FIND_VIEWS_BY_ID]:
        transform = traverseAndPrintFindViewById
    elif o in ['t', FIND_VIEWS_WITH_TEXT]:
        transform = traverseAndPrintFindViewWithText
    elif o in ['r', USE_REGEXPS]:
        options[USE_REGEXPS] = True
    elif o in ['C', VERBOSE_COMMENTS]:
        options[VERBOSE_COMMENTS] = True

device, serialno = ViewClient.connectToDeviceOrExit(**kwargs1)
vc = ViewClient(device, serialno, **kwargs2)
print '''#! /usr/bin/env monkeyrunner
# -*- coding: utf-8 -*-
\'\'\'
Copyright (C) 2013  Diego Torres Milano
Created on %s by Scripter v%s
  
@author: diego
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
