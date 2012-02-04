'''
Created on Feb 2, 2012

@author: diego
'''

import subprocess
import re
import socket
import os

DEBUG = False

ANDROID_HOME = os.environ['ANDROID_HOME'] if os.environ.has_key('ANDROID_HOME') else '/opt/android-sdk'
VIEW_SERVER_HOST = 'localhost'
VIEW_SERVER_PORT = 4939

class ViewClient:
    '''
    ViewClient is a ViewServer client.
    
    If not running the ViewServer is started on the target device or emulator and then the port
    mapping is created.
    '''

    def __init__(self, device):
        if not device:
            raise Exception('Device is not connected')
        if not self.serviceResponse(device.shell('service call window 3')):
            self.assertServiceResponse(device.shell('service call window 1 i32 %d' %
                VIEW_SERVER_PORT))

        subprocess.check_call([ANDROID_HOME + '/platform-tools/adb',
            'forward', 'tcp:%d' % VIEW_SERVER_PORT, 'tcp:%d' % VIEW_SERVER_PORT])

        self.viewsById = {}
    
    def assertServiceResponse(self, response):
        if not self.serviceResponse(response):
            raise Exception('Invalid response received from service.')

    def serviceResponse(self, response):
        return response == "Result: Parcel(00000000 00000001   '........')\r\n"

    def dump(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((VIEW_SERVER_HOST, VIEW_SERVER_PORT))
        s.send('dump -1\r\n')
        received = ""
        doneRE = re.compile("DONE")
        while True:
            received += s.recv(1024)
            if doneRE.search(received[-7:]):
                break

        s.close()
        self.views = received.split("\n")
        if DEBUG:
            print "there are %d views in this dump" % len(self.views)

        idRE = re.compile("(?P<viewId>id/\S+)")
        attrRE = re.compile("(?P<attr>\S+)(\(\))?=\d+,(?P<val>\S+)")
        hashRE = re.compile("(?P<class>\S+)@(?P<oid>[0-9a-f]+)")

        for v in self.views:
            attrs = {}
            m = idRE.search(v)
            if m:
                viewId = m.group('viewId')
                if DEBUG:
                    print "found %s" % viewId
                for attr in v.split():
                    m = attrRE.match(attr)
                    if m:
                        attrs[m.group('attr')] = m.group('val')                    
                    else:
                        m = hashRE.match(attr)
                        if m:
                            attrs['class'] = m.group('class')
                            attrs['oid'] = m.group('oid')
                        else:
                            if DEBUG:
                                print attr, "doesn't match"

                    
                if viewId in self.viewsById:
                    i = 1
                    while True:
                        newId = viewId + '/%d' % i
                        if not newId in self.viewsById:
                            break
                        i += 1
                    viewId = newId
                if DEBUG:
                    print "adding viewById %s" % viewId
                self.viewsById[viewId] = attrs

        return self.views

    def findViewById(self, viewId):
        '''
        Finds the View with the specified viewId.
        '''
        return self.viewsById[viewId]

    def getViewIds(self):
        '''
        Returns the Views map.
        '''
        return self.viewsById



if __name__ == "__main__":
    ViewClient(None)