#! /usr/bin/env monkeyrunner
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''

import sys
import os
import StringIO
import unittest
import exceptions

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

from com.dtmilano.android.viewclient import *
from mocks import MockDevice
from mocks import DUMP, DUMP_SAMPLE_UI, VIEW_MAP, RUNNING, STOPPED

# this is probably the only reliable way of determining the OS in monkeyrunner
os_name = java.lang.System.getProperty('os.name')
if os_name.startswith('Linux'):
    TRUE = '/bin/true'
else:
    TRUE = '/usr/bin/true'

class ViewTest(unittest.TestCase):

    def setUp(self):
        self.view = View(VIEW_MAP, None, -1)

    def tearDown(self):
        try:
            del os.environ['ANDROID_SERIAL']
        except:
            pass

    def testViewFactory_View(self):
        attrs = {'class': 'android.widget.AnyView', 'text:mText': 'Button with ID'}
        view = View.factory(attrs, None, -1)
        self.assertTrue(isinstance(view, View))
        
    def testViewFactory_TextView(self):
        attrs = {'class': 'android.widget.TextView', 'text:mText': 'Button with ID'}
        view = View.factory(attrs, None, -1)
        self.assertTrue(isinstance(view, TextView))
        
    def testViewFactory_TextView(self):
        attrs = {'class': 'android.widget.EditText', 'text:mText': 'Button with ID'}
        view = View.factory(attrs, None, -1)
        self.assertTrue(isinstance(view, EditText))
    
    def testView_notSpecifiedSdkVersion(self):
        device = MockDevice()
        view = View(VIEW_MAP, device, -1)
        self.assertEqual(device.version, view.build[VERSION_SDK_PROPERTY])
        
    def testView_specifiedSdkVersion_10(self):
        view = View(VIEW_MAP, MockDevice(), 10)
        self.assertEqual(10, view.build[VERSION_SDK_PROPERTY])
        
    def testView_specifiedSdkVersion_16(self):
        view = View(VIEW_MAP, MockDevice(), 16)
        self.assertEqual(16, view.build[VERSION_SDK_PROPERTY])
        
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
    
    def testTextPropertyForDifferentSdkVersions(self):
        VTP = { -1:TEXT_PROPERTY, 8:TEXT_PROPERTY_API_10, 10:TEXT_PROPERTY_API_10, 15:TEXT_PROPERTY, 16:TEXT_PROPERTY_UI_AUTOMATOR, 17:TEXT_PROPERTY_UI_AUTOMATOR}
        for version, textProperty in VTP.items():
            view = View(None, None, version)
            self.assertEqual(textProperty, view.textProperty, msg='version %d' % version)
    
    def testTextPropertyForDifferentSdkVersions_device(self):
        VTP = { -1:TEXT_PROPERTY, 8:TEXT_PROPERTY_API_10, 10:TEXT_PROPERTY_API_10, 15:TEXT_PROPERTY, 16:TEXT_PROPERTY_UI_AUTOMATOR, 17:TEXT_PROPERTY_UI_AUTOMATOR}
        for version, textProperty in VTP.items():
            device = MockDevice(version=version)
            view = View(None, device, -1)
            self.assertEqual(textProperty, view.textProperty, msg='version %d' % version)
                
    def testGetText(self):
        self.assertTrue(self.view.map.has_key('text:mText'))
        self.assertEqual('Button with ID', self.view.getText())
        self.assertEqual('Button with ID', self.view['text:mText'])
       
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
    
    def testInit_adb(self):
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEqual(None, vc)
        
    def testInit_adbNone(self):
        device = MockDevice()
        try:
            vc = ViewClient(device, device.serialno, adb=None, autodump=False)
            self.assertNotEqual(None, vc)
        except subprocess.CalledProcessError:
            # This is needed because the ports cannot be forwarded if there is no device connected
            pass
        
    def testExceptionDeviceNotConnected(self):
        try:
            vc = ViewClient(None, None)
        except Exception, e:
            self.assertEqual('Device is not connected', e.message)
    
    def testConnectToDeviceOrExit_environ(self):
        sys.argv = ['']
        os.environ['ANDROID_SERIAL'] = 'ABC123'
        try:
            ViewClient.connectToDeviceOrExit(timeout=1, verbose=True)
        except exceptions.SystemExit, e:
            self.assertEquals(3, e.code)
        except java.lang.NullPointerException:
            self.fail('Serialno was not taken from environment')
       
    def testConnectToDeviceOrExit_serialno(self):
        sys.argv = ['']
        try:
            ViewClient.connectToDeviceOrExit(timeout=1, verbose=True, serialno='ABC123')
        except exceptions.SystemExit, e:
            self.assertEquals(3, e.code)
        except java.lang.NullPointerException:
            self.fail('Serialno was not taken from argument')
     
    def testConstructor(self):
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
    
    def testMapSerialNo_noPortSpecified(self):
        vc = ViewClient(MockDevice(), serialno='192.168.1.100', adb=TRUE, autodump=False)
        self.assertEqual('192.168.1.100:5555', vc.serialno)
        
    def testMapSerialNo_portSpecified(self):
        vc = ViewClient(MockDevice(), serialno='192.168.1.100:5555', adb=TRUE, autodump=False)
        self.assertEqual('192.168.1.100:5555', vc.serialno)
        
    def testMapSerialNo_emulator(self):
        vc = ViewClient(MockDevice(), serialno='emulator-5556', adb=TRUE, autodump=False)
        self.assertEqual('emulator-5556', vc.serialno)
        
    def testMapSerialNo_regex(self):
        # This is an edge case. A regex should not be used as the serialno in ViewClient as it's
        # behavior is not well defined.
        # MonkeyRunner.waitForConnection() accepts a regexp as serialno but adb -s doesn't
        try:
            ViewClient(MockDevice(),  serialno='.*', adb=TRUE, autodump=False)
            self.fail()
        except ValueError:
            pass
        
    def testMapSerialNo_None(self):
        device = MockDevice()
        try:
            ViewClient(device, None, adb=TRUE, autodump=False)
            self.fail()
        except ValueError:
            pass
        
    def __mockTree(self, dump=DUMP):
        device = MockDevice()
        vc = ViewClient(device, serialno=device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.setViews(dump)
        return vc

    def testRoot(self):
        vc = self.__mockTree()
        root = vc.root
        self.assertTrue(root != None)
        self.assertTrue(root.parent == None)
        self.assertTrue(root.getClass() == 'com.android.internal.policy.impl.PhoneWindow$DecorView')
        
    def testParseTree(self):
        vc = self.__mockTree()
        # eat all the output
        vc.traverse(vc.root, transform=self.__eatIt)
        # We know there are 23 views in mock tree
        self.assertEqual(23, len(vc.getViewIds()))
        
    def testNewViewClientInstancesDontDuplicateTree(self):
        vc = {}
        n = {}
        for i in range(10):
            vc[i] = self.__mockTree()
            n[i] = len(vc[i].getViewIds())
        
        for i in range(1, 10):
            self.assertEquals(n[0], n[i])
       
    def testTraverseShowClassIdAndText(self):
        device = MockDevice()
        root = View({'text:mText':'0'}, device)
        root.add(View({'text:mText':'1'}, device))
        root.add(View({'text:mText':'2'}, device))
        v3 = View({'text:mText':'3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'5', 'getTag()':'v35'}, device)
        v3.add(v35)
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        treeStr = StringIO.StringIO()
        vc.traverse(root=root, transform=ViewClient.TRAVERSE_CIT, stream=treeStr)
        self.assertNotEquals(None, treeStr.getvalue())
        lines = treeStr.getvalue().splitlines()
        self.assertEqual(5, len(lines))
        self.assertEqual('None None 0', lines[0])
        citRE = re.compile(' +None None \d+')
        for l in lines[1:]:
            self.assertTrue(citRE.match(l))
        
    
    def testTraverseShowClassIdTextAndCenter(self):
        device = MockDevice()
        root = View({'mID':'0', 'text:mText':'0', 'layout:mLeft':0, 'layout:mTop':0}, device)
        root.add(View({'mID':'1', 'text:mText':'1', 'layout:mLeft':1, 'layout:mTop':1}, device))
        root.add(View({'mID':'2', 'text:mText':'2', 'layout:mLeft':2, 'layout:mTop':2}, device))
        v3 = View({'mID':'3', 'text:mText':'3', 'layout:mLeft':3, 'layout:mTop':3}, device)
        root.add(v3)
        v35 = View({'mID':'5', 'text:mText':'5', 'getTag()':'v35', 'layout:mLeft':5, 'layout:mTop':5}, device)
        v3.add(v35)
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        treeStr = StringIO.StringIO()
        vc.traverse(root=root, transform=ViewClient.TRAVERSE_CITC, stream=treeStr)
        self.assertNotEquals(None, treeStr.getvalue())
        lines = treeStr.getvalue().splitlines()
        self.assertEqual(5, len(lines))
        self.assertEqual('None 0 0 (0, 0)', lines[0])
        citRE = re.compile(' +None \d+ \d+ \(\d+, \d+\)')
        for l in lines[1:]:
            self.assertTrue(citRE.match(l))
    
    def __getClassAndId(self, view):
        try:
            return "%s %s %s %s" % (view.getClass(), view.getId(), view.getUniqueId(), view.getCoords())
        except Exception, e:
            return "Exception in view=%s: %s" % (view.__smallStr__(), e)
    
    def __eatIt(self, view):
        return ""
    
    def testViewWithNoIdReceivesUniqueId(self):
        vc = self.__mockTree()
        
        # We know there are 6 views without id in the mock tree
        for i in range(1, 6):
            self.assertNotEquals(None, vc.findViewById("id/no_id/%d" % i))
     
    def testTextWithSpaces(self):
        vc = self.__mockTree()
        self.assertNotEqual(None, vc.findViewWithText('Medium Text'))
        
    def testTextWithVeryLargeContent(self):
        TEXT = """\
MOCK@412a9d08 mID=7,id/test drawing:mForeground=4,null padding:mForegroundPaddingBottom=1,0 text:mText=319,[!   "   #   $   %   &   '   (   )   *   +   ,   -   .   /   0   1   2   3   4   5   6   7   8   9   :   ;   <   =   >   ?   @   A   B   C   D   E   F   G   H   I   J   K   L   M   N   O   P   Q   R   S   T   U   V   W   X   Y   Z   [   \   ]   ^   _   `   a   b   c   d   e   f   g   h   i   j   k   l   m   n   o   p] mViewFlags=11,-1744830336\
"""
        vc = self.__mockTree(TEXT)
        test = vc.findViewById('id/test')
        text = test.getText()
        self.assertEqual(319, len(text))
        self.assertEqual('[', text[0])
        self.assertEqual(']', text[318])
        self.assertEqual('-1744830336', test['mViewFlags'])

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
        self.assertNotEqual(None, textView3.getText())
        self.assertNotEqual("", textView3.getText().strip())
        list = [ eval(v) for v in textView3.getText().strip().split() ]
        tx = list[0][0]
        ty = list[0][1]
        tsx = list[1][0]
        tsy = list[1][1]
        self.assertEqual(tx, x)
        self.assertEqual(ty, y)
        self.assertEqual((tsx, tsy), xy)
        self.assertEqual(((tsx, tsy), (xy[0] + w, xy[1] + h)), coords)
        
    def testServiceStoppedAfterDestructor(self):
        device = MockDevice()
        self.assertTrue(device.service == STOPPED)
        if True:
            vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
            self.assertTrue(device.service == RUNNING)
            vc.__del__()
        # Perhpas there are other ViewClients using the same server, we cannot expect it stops
        #self.assertTrue(device.service == STOPPED)

    def testFindViewByIdOrRaise(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        vc.findViewByIdOrRaise('id/up')
        
    def testFindViewByIdOrRaise_nonExistentView(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        try:
            vc.findViewByIdOrRaise('id/nonexistent')
            self.fail()
        except ViewNotFoundException:
            pass
           
    def testFindViewById_root(self):
        device = None
        root = View({'mID':'0'}, device)
        root.add(View({'mID':'1'}, device))
        root.add(View({'mID':'2'}, device))
        v3 = View({'mID':'3'}, device)
        root.add(v3)
        v35 = View({'mID':'5', 'getTag()':'v35'}, device)
        v3.add(v35)
        v4 = View({'mID':'4'}, device)
        root.add(v4)
        v45 = View({'mID':'5', 'getTag()':'v45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        v5 = vc.findViewById('5')
        self.assertNotEqual(v5, None)
        self.assertEqual('v35', v5.getTag())
        v5 = vc.findViewById('5', root=v4)
        self.assertNotEqual(v5, None)
        self.assertEqual('v45', v5.getTag())
        v5 = vc.findViewById('5', root=v3)
        self.assertNotEqual(v5, None)
        self.assertEqual('v35', v5.getTag())
        
    def testFindViewByIdOrRaise_root(self):
        device = None
        root = View({'mID':'0'}, device)
        root.add(View({'mID':'1'}, device))
        root.add(View({'mID':'2'}, device))
        v3 = View({'mID':'3'}, device)
        root.add(v3)
        v35 = View({'mID':'5', 'getTag()':'v35'}, device)
        v3.add(v35)
        v4 = View({'mID':'4'}, device)
        root.add(v4)
        v45 = View({'mID':'5', 'getTag()':'v45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        v5 = vc.findViewByIdOrRaise('5')
        self.assertEqual('v35', v5.getTag())
        v5 = vc.findViewByIdOrRaise('5', root=v4)
        self.assertEqual('v45', v5.getTag())
        v5 = vc.findViewByIdOrRaise('5', root=v3)
        self.assertEqual('v35', v5.getTag())
        
    def testFindViewWithText_root(self):
        device = None
        root = View({'text:mText':'0'}, device)
        root.add(View({'text:mText':'1'}, device))
        root.add(View({'text:mText':'2'}, device))
        v3 = View({'text:mText':'3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'5', 'getTag()':'v35'}, device)
        v3.add(v35)
        v4 = View({'text:mText':'4'}, device)
        root.add(v4)
        v45 = View({'text:mText':'5', 'getTag()':'v45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        v5 = vc.findViewWithText('5')
        self.assertNotEqual(v5, None)
        self.assertEqual('v35', v5.getTag())
        v5 = vc.findViewWithText('5', root=v4)
        self.assertNotEqual(v5, None)
        self.assertEqual('v45', v5.getTag())
        v5 = vc.findViewWithText('5', root=v3)
        self.assertNotEqual(v5, None)
        self.assertEqual('v35', v5.getTag())
        
    def testFindViewWithTextOrRaise_root(self):
        device = None
        root = View({'text:mText':'0'}, device)
        root.add(View({'text:mText':'1'}, device))
        root.add(View({'text:mText':'2'}, device))
        v3 = View({'text:mText':'3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'5', 'getTag()':'v35'}, device)
        v3.add(v35)
        v4 = View({'text:mText':'4'}, device)
        root.add(v4)
        v45 = View({'text:mText':'5', 'getTag()':'v45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        v5 = vc.findViewWithTextOrRaise('5')
        self.assertEqual('v35', v5.getTag())
        v5 = vc.findViewWithTextOrRaise('5', root=v4)
        self.assertEqual('v45', v5.getTag())
        v5 = vc.findViewWithTextOrRaise('5', root=v3)
        self.assertEqual('v35', v5.getTag())
        
    def testFindViewWithTextOrRaise_rootNonExistent(self):
        device = None
        root = View({'text:mText':'0'}, device)
        root.add(View({'text:mText':'1'}, device))
        root.add(View({'text:mText':'2'}, device))
        v3 = View({'text:mText':'3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'5', 'getTag()':'v35'}, device)
        v3.add(v35)
        v4 = View({'text:mText':'4'}, device)
        root.add(v4)
        v45 = View({'text:mText':'5', 'getTag()':'v45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        try:
            vc.findViewWithTextOrRaise('Non Existent', root=v4)
            self.fail()
        except ViewNotFoundException:
            pass
        
    def testUiAutomatorDump(self):
        device = MockDevice(version=16)
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=True)

         
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
