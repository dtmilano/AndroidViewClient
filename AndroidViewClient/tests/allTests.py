#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''
import unittest
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
    sys.path.append(os.environ['ANDROID_VIEW_CLIENT_HOME'])
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass



if __name__ == "__main__":
    #sys.argv = ['', 'ViewTest.testName']
    import tests.com.dtmilano.android.viewclient
    unittest.main()
