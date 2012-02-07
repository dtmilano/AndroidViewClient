'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''

import sys
import os
import unittest
try:
    ANDROID_VIEW_CLIENT_HOME = os.environ['ANDROID_VIEW_CLIENT_HOME']
except KeyError:
    print >>sys.stderr, "%s: ERROR: ANDROID_VIEW_CLIENT_HOME not set in environment" % __file__
    sys.exit(1)
sys.path.append(ANDROID_VIEW_CLIENT_HOME + '/src')
from com.dtmilano.android.viewclient import View
from com.dtmilano.android.viewclient import ViewClient
from mocks import MockDevice


class ViewTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testInnerMethod(self):
        v = View({'isChecked()':'true'}, None)
        self.assertTrue(v.isChecked())
        v.map['isChecked()'] = 'false'
        self.assertFalse(v.isChecked(), "Expected False but is %s {%s}" % (v.isChecked(), v.map['isChecked()']) )
        self.assertFalse(v.isChecked())
        v.map['other'] = 1
        self.assertEqual(1, v.other())
        v.map['evenMore'] = "ABC"
        self.assertEqual("ABC", v.evenMore())
        v.map['more'] = "abc"
        v.map['more'] = v.evenMore()
        self.assertEqual("ABC", v.more())
        v.map['isMore()'] = 'true'
        self.assertTrue(v.isMore())

    def testName_Layout_mLeft(self):
        v = View({'layout:mLeft':200}, None)
        self.assertEqual(200, v.layout_mLeft())
        
    def testNameWithColon_this_is_a_fake_name(self):
        v = View({'this:is_a_fake_name':1}, None)
        self.assertEqual(1, v.this_is_a_fake_name())

    def testNameWith2Colons_this_is_another_fake_name(self):
        v = View({'this:is:another_fake_name':1}, None)
        self.assertEqual(1, v.this_is_another_fake_name())
        
    def testInexistentMethodName(self):
        v = View({'foo':1}, None)
        try:
            v.bar()
            raise Exception("AttributeError not raised")
        except AttributeError:
            pass


class ViewClientTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def testExceptionDeviceNotConnected(self):
        try:
            vc = ViewClient(None)
        except Exception, e:
            self.assertEqual('Device is not connected', e.message)
            
    def testConstructor(self):
        vc = ViewClient(MockDevice(), adb='/usr/bin/true')
        self.assertNotEquals(None, vc)

         
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()