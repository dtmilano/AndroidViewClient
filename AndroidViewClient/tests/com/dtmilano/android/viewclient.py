'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''

import sys
import os
import unittest

# PyDev sets PYTHONPATH, use it
for p in os.environ['PYTHONPATH'].split(':'):
    if not p in sys.path:
        sys.path.append(p)
try:
    sys.path.append(os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import View, ViewClient
from mocks import MockDevice
from mocks import DUMP, DUMP_SAMPLE_UI, VIEW_MAP


class ViewTest(unittest.TestCase):

    def setUp(self):
        self.view = View(VIEW_MAP, None)

    def tearDown(self):
        pass

    def testInnerMethod(self):
        v = View({'isChecked()':'true'}, None)
        self.assertTrue(v.isChecked())
        v.map['isChecked()'] = 'false'
        self.assertFalse(v.isChecked(), "Expected False but is %s {%s}" % (v.isChecked(), v.map['isChecked()']))
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

    def testGetClass(self):
        self.assertEqual('android.widget.ToggleButton', self.view.getClass())
        
    def testGetId(self):
        self.assertEqual('id/button_with_id', self.view.getId())
    
    def testGetText(self):
        self.assertEqual('Button with ID', self.view.getText())
       
    def testGetWidth(self):
        self.assertEqual(1140, self.view.getWidth())
    
    def testGetHeight(self): 
        self.assertEqual(48, self.view.getHeight())
    
    def testGetUniqueId(self):
        self.assertEqual('id/button_with_id', self.view.getUniqueId())
        
    def testGetUniqueIdEqualsToIdWhenIdIsSpecified(self):
        self.assertEqual(self.view.getId(), self.view.getUniqueId())
                           
    def testName_Layout_mLeft(self):
        v = View({'layout:mLeft':200}, None)
        self.assertEqual(200, v.layout_mLeft())
        
    def testNameWithColon_this_is_a_fake_name(self):
        v = View({'this:is_a_fake_name':1}, None)
        self.assertEqual(1, v.this_is_a_fake_name())

    def testNameWith2Colons_this_is_another_fake_name(self):
        v = View({'this:is:another_fake_name':1}, None)
        self.assertEqual(1, v.this_is_another_fake_name())
        
    def testViewWithoutId(self):
        v = View({'mID':'id/NO_ID', 'text:mText':'Some text'}, None)
        self.assertEqual('id/NO_ID', v.getId())
        
    def testInexistentMethodName(self):
        v = View({'foo':1}, None)
        try:
            v.bar()
            raise Exception("AttributeError not raised")
        except AttributeError:
            pass
    
    def testViewTreeRoot(self):
        root = View({'root':1}, None)
        self.assertTrue(root.parent == None)
        
    def testViewTree(self):
        root = View({'root':1}, None)
        children = ["A", "B", "C"]
        for s in children:
            root.add(View({s:1}, None))
        
        self.assertEquals(len(children), len(root.children)) 

    def testViewTreeParent(self):
        root = View({'root':1}, None)
        children = ["A", "B", "C"]
        for s in children:
            root.add(View({s:1}, None))
        
        for ch in root.children:
            self.assertTrue(ch.parent == root)

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
        vc = ViewClient(MockDevice(), adb='/usr/bin/true', autodump=False)
        self.assertNotEquals(None, vc)
    
    def __mockTree(self, dump=DUMP):
        vc = ViewClient(MockDevice(), adb='/usr/bin/true', autodump=False)
        self.assertNotEquals(None, vc)
        vc.setViews(dump)
        vc.parseTree(vc.views)
        return vc

    def testRoot(self):
        vc = self.__mockTree()
        root = vc.root
        self.assertTrue(root != None)
        self.assertTrue(root.parent == None)
        self.assertTrue(root.getClass() == 'com.android.internal.policy.impl.PhoneWindow$DecorView')
        
    def testParseTree(self):
        vc = self.__mockTree()
        print
        print "TRAVERSE:"
        vc.traverse(vc.root, transform=self.__getClassAndId)
        print
        # We know there are 23 views in mock tree
        self.assertEqual(23, len(vc.getViewIds()))
        
    def __getClassAndId(self, view):
        try:
            return "%s %s %s %s" % (view.getClass(), view.getId(), view.getUniqueId(), view.getCoords())
        except Exception, e:
            return "Exception in view=%s: %s" % (view.__smallStr__(), e)
    
    def testViewWithNoIdReceivesUniqueId(self):
        vc = self.__mockTree()
        
        # We know there are 6 views without id in the mock tree
        for i in range(1, 6):
            self.assertNotEquals(None, vc.findViewById("id/no_id/%d" % i))
     
    def testTextWithSpaces(self):
        vc = self.__mockTree()
        self.assertNotEqual(None, vc.findViewWithText('Medium Text'))

    def testActionBarSubtitleCoordinates(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        toggleButton = vc.findViewById('id/button_with_id')
        self.assertNotEqual(None, toggleButton)
        textView3 = vc.findViewById('id/textView3')
        self.assertNotEqual(None, textView3)
        x = toggleButton.getX()
        y = toggleButton.getY()
        w = toggleButton.getWidth()
        h = toggleButton.getHeight()
        xy = toggleButton.getXY()
        coords = toggleButton.getCoords()
        list = [ eval(v) for v in textView3.getText().strip().split() ]
        tx = list[0][0]
        ty = list[0][1]
        tsx = list[1][0]
        tsy = list[1][1]
        self.assertEqual(tx, x)
        self.assertEqual(ty, y)
        self.assertEqual((tsx, tsy), xy)
        self.assertEqual(((tsx, tsy), (xy[0] + w, xy[1] + h)), coords)

         
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
