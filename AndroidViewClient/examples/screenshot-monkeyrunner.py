#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Set 5, 2013

@author: diego
'''


import sys
import os

from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice

if len(sys.argv) < 2:
    print >> sys.stderr, "usage: %s filename.png" % sys.argv[0]
    sys.exit(1)

filename = sys.argv.pop(1)
device = MonkeyRunner.waitForConnection()
device.takeSnapshot().writeToFile(filename, 'PNG')
