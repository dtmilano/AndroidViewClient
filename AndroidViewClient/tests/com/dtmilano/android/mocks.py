'''
Created on Feb 6, 2012

@author: diego
'''

import re

TRUE_PARCEL = "Result: Parcel(00000000 00000001   '........')\r\n"
FALSE_PARCEL = "Result: Parcel(00000000 00000000   '........')\r\n"

class MockDevice(object):
    '''
    Mocks an Android device
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
        pass
        
    def shell(self, cmd):
        if cmd == 'service call window 3':
            return FALSE_PARCEL
        elif re.compile('service call window 1 i32 \d+').match(cmd):
            return TRUE_PARCEL
        