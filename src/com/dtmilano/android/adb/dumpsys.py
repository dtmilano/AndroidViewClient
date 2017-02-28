'''
Copyright (C) 2012-2017  Diego Torres Milano
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
import re

__version__ = '12.6.0'


class Dumpsys:
    def __init__(self, adbclient, subcommand, args=None):
        self.total = 0
        self.parse(subcommand, adbclient.shell('dumpsys ' + subcommand + ((' ' + args) if args else '')))

    def parse(self, subcommand, out):
        if subcommand == 'meminfo':
            self.parseMeminfo(out)
        else:
            pass

    def parseMeminfo(self, out):
        m = re.search('TOTAL[ \t]*(\d+)', out, re.MULTILINE)
        if m:
            self.total = m.group(1)
        else:
            raise RuntimeError('Cannot find TOTAL in "' + out + '"')
