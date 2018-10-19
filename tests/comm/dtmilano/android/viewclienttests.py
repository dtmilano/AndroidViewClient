#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2012  Diego Torres Milano
Created on Feb 5, 2012

@author: diego
'''

import exceptions
import os
import sys

# PyDev sets PYTHONPATH, use it
try:
    for p in os.environ['PYTHONPATH'].split(':'):
        if not p in sys.path:
            sys.path.append(p)
except:
    pass

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.viewclient import *
from mocks import MockDevice
from mocks import DUMP, DUMP_SAMPLE_UI, VIEW_MAP, VIEW_MAP_API_8, VIEW_MAP_API_17, RUNNING, STOPPED, WINDOWS

os_name = platform.system()
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

    def testView_specifiedSdkVersion_8(self):
        view = View(VIEW_MAP_API_8, MockDevice(), 8)
        self.assertEqual(8, view.build[VERSION_SDK_PROPERTY])

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
        VP = { -1:TEXT_PROPERTY, 8:TEXT_PROPERTY_API_10, 10:TEXT_PROPERTY_API_10, 15:TEXT_PROPERTY, 16:TEXT_PROPERTY_UI_AUTOMATOR, 17:TEXT_PROPERTY_UI_AUTOMATOR}
        for version, textProperty in VP.items():
            view = View(None, None, version)
            self.assertEqual(textProperty, view.textProperty, msg='version %d: expected: %s actual: %s' % (version, textProperty, view.textProperty))

    def testTextPropertyForDifferentSdkVersions_device(self):
        VP = { -1:TEXT_PROPERTY, 8:TEXT_PROPERTY_API_10, 10:TEXT_PROPERTY_API_10, 15:TEXT_PROPERTY, 16:TEXT_PROPERTY_UI_AUTOMATOR, 17:TEXT_PROPERTY_UI_AUTOMATOR}
        for version, textProperty in VP.items():
            device = MockDevice(version=version)
            view = View(None, device, -1)
            self.assertEqual(textProperty, view.textProperty, msg='version %d' % version)

    def testLeftPropertyForDifferentSdkVersions(self):
        VP = { -1:LEFT_PROPERTY, 8:LEFT_PROPERTY_API_8, 10:LEFT_PROPERTY, 15:LEFT_PROPERTY, 16:LEFT_PROPERTY, 17:LEFT_PROPERTY}
        for version, leftProperty in VP.items():
            view = View(None, None, version)
            self.assertEqual(leftProperty, view.leftProperty, msg='version %d' % version)

    def testLeftPropertyForDifferentSdkVersions_device(self):
        VP = { -1:LEFT_PROPERTY, 8:LEFT_PROPERTY_API_8, 10:LEFT_PROPERTY, 15:LEFT_PROPERTY, 16:LEFT_PROPERTY, 17:LEFT_PROPERTY}
        for version, leftProperty in VP.items():
            device = MockDevice(version=version)
            view = View(None, device, -1)
            self.assertEqual(leftProperty, view.leftProperty, msg='version %d' % version)

    def testTopPropertyForDifferentSdkVersions(self):
        VP = { -1:TOP_PROPERTY, 8:TOP_PROPERTY_API_8, 10:TOP_PROPERTY, 15:TOP_PROPERTY, 16:TOP_PROPERTY, 17:TOP_PROPERTY}
        for version, topProperty in VP.items():
            view = View(None, None, version)
            self.assertEqual(topProperty, view.topProperty, msg='version %d' % version)

    def testTopPropertyForDifferentSdkVersions_device(self):
        VP = { -1:TOP_PROPERTY, 8:TOP_PROPERTY_API_8, 10:TOP_PROPERTY, 15:TOP_PROPERTY, 16:TOP_PROPERTY, 17:TOP_PROPERTY}
        for version, topProperty in VP.items():
            device = MockDevice(version=version)
            view = View(None, device, -1)
            self.assertEqual(topProperty, view.topProperty, msg='version %d' % version)

    def testWidthPropertyForDifferentSdkVersions(self):
        VP = { -1:WIDTH_PROPERTY, 8:WIDTH_PROPERTY_API_8, 10:WIDTH_PROPERTY, 15:WIDTH_PROPERTY, 16:WIDTH_PROPERTY, 17:WIDTH_PROPERTY}
        for version, widthProperty in VP.items():
            view = View(None, None, version)
            self.assertEqual(widthProperty, view.widthProperty, msg='version %d' % version)

    def testWidthPropertyForDifferentSdkVersions_device(self):
        VP = { -1:WIDTH_PROPERTY, 8:WIDTH_PROPERTY_API_8, 10:WIDTH_PROPERTY, 15:WIDTH_PROPERTY, 16:WIDTH_PROPERTY, 17:WIDTH_PROPERTY}
        for version, widthProperty in VP.items():
            device = MockDevice(version=version)
            view = View(None, device, -1)
            self.assertEqual(widthProperty, view.widthProperty, msg='version %d' % version)

    def testHeightPropertyForDifferentSdkVersions(self):
        VP = { -1:HEIGHT_PROPERTY, 8:HEIGHT_PROPERTY_API_8, 10:HEIGHT_PROPERTY, 15:HEIGHT_PROPERTY, 16:HEIGHT_PROPERTY, 17:HEIGHT_PROPERTY}
        for version, heightProperty in VP.items():
            view = View(None, None, version)
            self.assertEqual(heightProperty, view.heightProperty, msg='version %d' % version)

    def testHeightPropertyForDifferentSdkVersions_device(self):
        VP = { -1:HEIGHT_PROPERTY, 8:HEIGHT_PROPERTY_API_8, 10:HEIGHT_PROPERTY, 15:HEIGHT_PROPERTY, 16:HEIGHT_PROPERTY, 17:HEIGHT_PROPERTY}
        for version, heightProperty in VP.items():
            device = MockDevice(version=version)
            view = View(None, device, -1)
            self.assertEqual(heightProperty, view.heightProperty, msg='version %d' % version)

    def testGetText(self):
        self.assertTrue(self.view.map.has_key('text:mText'))
        self.assertEqual('Button with ID', self.view.getText())
        self.assertEqual('Button with ID', self.view['text:mText'])

    def testGetX_specifiedSdkVersion_8(self):
        view = View(VIEW_MAP_API_8, MockDevice(), 8)
        self.assertEqual(8, view.build[VERSION_SDK_PROPERTY])
        self.assertEqual(50, view.getX())

    def testGetX_specifiedSdkVersion_10(self):
        view = View(VIEW_MAP, MockDevice(), 10)
        self.assertEqual(10, view.build[VERSION_SDK_PROPERTY])
        self.assertEqual(50, view.getX())

    def testGetY_specifiedSdkVersion_8(self):
        view = View(VIEW_MAP_API_8, MockDevice(), 8)
        self.assertEqual(8, view.build[VERSION_SDK_PROPERTY])
        self.assertEqual(316, view.getY())

    def testGetY_specifiedSdkVersion_10(self):
        view = View(VIEW_MAP, MockDevice(), 10)
        self.assertEqual(10, view.build[VERSION_SDK_PROPERTY])
        self.assertEqual(316, view.getY())

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

    def testContainsPoint_api15(self):
        v = View(VIEW_MAP, MockDevice(), 15)
        (X, Y, W, H) = v.getPositionAndSize()
        self.assertEqual(X, v.getX())
        self.assertEqual(Y, v.getY())
        self.assertEqual(W, v.getWidth())
        self.assertEqual(H, v.getHeight())
        self.assertTrue(v.containsPoint((v.getCenter())))

    def testContainsPoint_api17(self):
        v = View(VIEW_MAP_API_17, MockDevice(), 17)
        (X, Y, W, H) = v.getPositionAndSize()
        self.assertEqual(X, v.getX())
        self.assertEqual(Y, v.getY())
        self.assertEqual(W, v.getWidth())
        self.assertEqual(H, v.getHeight())
        self.assertTrue(v.containsPoint((v.getCenter())))

    def testIsClickable_api15(self):
        v = View(VIEW_MAP, MockDevice(), 15)
        self.assertTrue(v.isClickable())

    def testIsClickable_api17(self):
        v = View(VIEW_MAP_API_17, MockDevice(), 17)
        self.assertTrue(v.isClickable())

    def testCopyConstructor(self):
        device = MockDevice()
        mv = VIEW_MAP_API_17.copy()
        mv['class'] = u'android.widget.View'
        v = View(mv, device, 17)
        self.assertEqual(v.getClass(), u'android.widget.View')

        mt = VIEW_MAP_API_17.copy()
        mt['class'] = u'android.widget.TextView'
        t = TextView(mt, device, 17)
        self.assertEqual(t.getClass(), u'android.widget.TextView')

        me = VIEW_MAP_API_17.copy()
        me['class'] = u'android.widget.EditText'
        e = TextView(me, device, 17)
        self.assertEqual(e.getClass(), u'android.widget.EditText')

        v1 = View.clone(v)
        self.assertEqual(u'android.widget.View', v1.getClass())

        t1 = TextView.clone(t)
        self.assertEqual(u'android.widget.TextView', t1.getClass())

        e1 = EditText.clone(e)
        self.assertEqual(u'android.widget.EditText', e1.getClass())

        t2 = TextView.clone(v)
        self.assertEqual(u'android.widget.TextView', t2.getClass())

        e2 = EditText.clone(v)
        self.assertEqual(u'android.widget.EditText', e2.getClass())

        e2.setText("hello")



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
        # FIXME: there's a problem here when the mock device is created,
        # it's intended to be API=15, mock ViewServer is started and then
        # adb tries (unsuccessfuly) to forward the ports (expected because
        # adb does not know anything about mock devices).
        # Then
        #    error: device not found
        # appears in the console
        device = MockDevice()
        try:
            vc = ViewClient(device, device.serialno, adb=None, autodump=False)
            self.assertIsNotNone(vc)
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
        except RuntimeError, e:
            msg = str(e)
            if re.search('Is adb running on your computer?', msg):
                # This test required adb running
                self.fail(msg)
            elif re.search("There are no connected devices", msg):
                # special case, when there are no devices connected then the
                # serialno specified doesn't matter
                pass
            elif not re.search("couldn't find device that matches 'ABC123'", msg):
                self.fail(msg)
        except exceptions.SystemExit, e:
            self.assertEquals(3, e.code)
        except Exception, e: #FIXME: java.lang.NullPointerException:
            self.fail('Serialno was not taken from environment: ' + msg)

    def testConnectToDeviceOrExit_serialno(self):
        sys.argv = ['']
        try:
            ViewClient.connectToDeviceOrExit(timeout=1, verbose=True, serialno='ABC123')
        except RuntimeError, e:
            msg = str(e)
            if re.search('Is adb running on your computer?', msg):
                # This test required adb running
                self.fail(msg)
            elif re.search("There are no connected devices", msg):
                # special case, when there are no devices connected then the
                # serialno specified doesn't matter
                pass
            elif not re.search("couldn't find device that matches 'ABC123'", msg):
                self.fail(msg)
        except exceptions.SystemExit, e:
            self.assertEquals(3, e.code)
        except Exception, e: #FIXME: java.lang.NullPointerException:
            self.fail('Serialno was not taken from argument: ' + str(e))

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

    def testGetProperty_displayWidth(self):
        device = MockDevice()
        self.assertEqual(768, device.getProperty('display.width'))

    def testGetProperty_displayHeight(self):
        device = MockDevice()
        self.assertEqual(1184, device.getProperty('display.height'))

    def __mockTree(self, dump=DUMP, version=15, language='en'):
        device = MockDevice(version=version, language=language)
        vc = ViewClient(device, serialno=device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        if version <= 15:
            # We don't want to invoke the ViewServer or MockViewServer for this
            vc.setViews(dump)
        else:
            vc.dump()
        return vc

    def __mockWindows(self, windows=WINDOWS):
        device = MockDevice()
        vc = ViewClient(device, serialno=device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.windows = windows
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
        # We know there are 23 views in ViewServer mock tree
        self.assertEqual(23, len(vc.getViewIds()))

    def testParsetree_api17(self):
        vc = self.__mockTree(version=17)
        # eat all the output
        vc.traverse(vc.root, transform=self.__eatIt)
        # We know there are 9 views in UiAutomator mock tree
        self.assertEqual(9, len(vc.getViewIds()))

    def testParsetree_api17_zh(self):
        vc = self.__mockTree(version=17, language='zh')
        # eat all the output
        vc.traverse(vc.root, transform=self.__eatIt)
        # We know there are 21 views in UiAutomator mock tree
        self.assertEqual(21, len(vc.getViewIds()))

    def __testViewByIds_apiIndependent(self, vc):
        viewsbyId = vc.getViewsById()
        self.assertNotEquals(None, viewsbyId)
        for k, v in viewsbyId.items():
            self.assertTrue(isinstance(k, str) or isinstance(k, unicode))
            self.assertTrue(isinstance(v, View), "v=" + unicode(v) + " is not a View")
            self.assertTrue(re.match("id/.*", v.getUniqueId()) != None)
            self.assertEquals(k, v.getUniqueId())

    def testGetViewsById(self):
        vc = self.__mockTree()
        self.__testViewByIds_apiIndependent(vc)

    def testGetViewsById_api17(self):
        vc = self.__mockTree(version=17)
        self.__testViewByIds_apiIndependent(vc)

    def testGetViewsById_api17_zh(self):
        vc = self.__mockTree(version=17, language='zh')
        self.__testViewByIds_apiIndependent(vc)

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
        root = View({'text:mText':'0', 'class': 'android.widget.View', 'mID': 0}, device)
        root.add(View({'text:mText':'1', 'class': 'android.widget.View', 'mID': 1}, device))
        root.add(View({'text:mText':'2', 'class': 'android.widget.View', 'mID': 2}, device))
        v3 = View({'text:mText':'3', 'class': 'android.widget.View', 'mID':3}, device)
        root.add(v3)
        v35 = View({'text:mText':'5', 'getTag()':'v35', 'class': 'android.widget.View', 'mID': 35}, device)
        v3.add(v35)
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        treeStr = StringIO.StringIO()
        vc.traverse(root=root, transform=ViewClient.TRAVERSE_CIT, stream=treeStr)
        self.assertNotEquals(None, treeStr.getvalue())
        lines = treeStr.getvalue().splitlines()
        self.assertEqual(5, len(lines), "lines=%s" % lines)
        self.assertEqual('android.widget.View 0 0', lines[0])
        citRE = re.compile(' +android.widget.View \d+ \d+')
        for l in lines[1:]:
            self.assertTrue(citRE.match(l), 'l=%s' % l)


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
        lv = textView3.getText().strip().split()
        _list = [ eval(str(v)) for v in lv ]
        tx = _list[1][0]
        ty = _list[1][1]
        tsx = _list[1][0]
        tsy = _list[1][1]
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

    def testList(self):
        vc = self.__mockWindows()
        self.assertNotEqual(None, vc.windows)

    def testFindViewByIdOrRaise(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        vc.findViewByIdOrRaise('id/up')

    def testFindViewByIdOrRaise_api17(self):
        vc = self.__mockTree(version=17)
        vc.traverse(stream=self.openDevNull())
        vc.findViewByIdOrRaise('id/no_id/9')

    def testFindViewByIdOrRaise_api17_zh(self):
        vc = self.__mockTree(version=17, language='zh')
        vc.traverse(stream=self.openDevNull())
        vc.findViewByIdOrRaise('id/no_id/21')

    def testFindViewByIdOrRaise_nonExistentView(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        try:
            vc.findViewByIdOrRaise('id/nonexistent')
            self.fail()
        except ViewNotFoundException:
            pass

    def testFindViewByIdOrRaise_nonExistentView_api17(self):
        vc = self.__mockTree(version=17)
        try:
            vc.findViewByIdOrRaise('id/nonexistent')
            self.fail()
        except ViewNotFoundException:
            pass

    def testFindViewByIdOrRaise_nonExistentView_api17_zh(self):
        vc = self.__mockTree(version=17, language='zh')
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

    def testFindViewById_viewFilter(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        def vf(view):
            return view.getClass() == 'android.widget.ImageView'
        view = vc.findViewById('id/up', viewFilter=vf)
        self.assertNotEqual(view, None)

    def testFindViewById_viewFilterUnmatched(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        def vf(view):
            return view.getClass() == 'android.widget.TextView'
        view = vc.findViewById('id/up', viewFilter=vf)
        self.assertEqual(view, None)

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

    def testFindViewByIdOrRaise_viewFilter(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        def vf(view):
            return view.getClass() == 'android.widget.ImageView'
        view = vc.findViewByIdOrRaise('id/up', viewFilter=vf)

    def testFindViewByIdOrRaise_viewFilterUnmatched(self):
        vc = self.__mockTree(dump=DUMP_SAMPLE_UI)
        def vf(view):
            return view.getClass() == 'android.widget.TextView'
        try:
            view = vc.findViewByIdOrRaise('id/up', viewFilter=vf)
        except ViewNotFoundException:
            pass

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

    def testFindViewWithText_regexRoot(self):
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
        v5 = vc.findViewWithText(re.compile('[5]'))
        self.assertNotEqual(v5, None)
        self.assertEqual('v35', v5.getTag())
        v5 = vc.findViewWithText(re.compile('[5]'), root=v4)
        self.assertNotEqual(v5, None)
        self.assertEqual('v45', v5.getTag())
        v5 = vc.findViewWithText(re.compile('[5]'), root=v3)
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

    def testFindViewWithTextOrRaise_root_disappearingView(self):
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
        # Then remove v4 and its children
        root.children.remove(v4)
        #vc.dump()
        v4 = vc.findViewWithText('4')
        self.assertEqual(v4, None, "v4 has not disappeared")

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

    def testFindViewWithTextOrRaise_api17(self):
        vc = self.__mockTree(version=17)
        vc.findViewWithTextOrRaise("Apps")

    def openDevNull(self):
        return open('/dev/null', 'a+')

    def testFindViewWithTextOrRaise_api17_zh(self):
        vc = self.__mockTree(version=17, language='zh')
        vc.traverse(transform=ViewClient.TRAVERSE_CIT, stream=self.openDevNull())
        vc.findViewWithTextOrRaise(u'语言')

    def testFindViewWithTextOrRaise_nonExistent_api17(self):
        vc = self.__mockTree(version=17)
        try:
            vc.findViewWithTextOrRaise('nonexistent text')
            self.fail()
        except ViewNotFoundException:
            pass

    def testFindViewWithTextOrRaise_nonExistent_api17_zh(self):
        vc = self.__mockTree(version=17, language='zh')
        try:
            vc.findViewWithTextOrRaise(u'不存在的文本')
            self.fail()
        except ViewNotFoundException:
            pass

    def testFindViewWithContentDescription_root(self):
        device = None
        root = View({'text:mText':'0', 'content-desc':'CD0'}, device)
        root.add(View({'text:mText':'1', 'content-desc':'CD1'}, device))
        root.add(View({'text:mText':'2', 'content-desc':'CD2'}, device))
        v3 = View({'text:mText':'3', 'content-desc':'CD3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'35', 'content-desc':'CD35'}, device)
        v3.add(v35)
        v4 = View({'text:mText':'4', 'conent-desc':'CD4'}, device)
        root.add(v4)
        v45 = View({'text:mText':'45', 'content-desc':'CD45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        v45 = vc.findViewWithContentDescription('CD45')
        self.assertNotEqual(v45, None)
        self.assertEqual('45', v45.getText())
        v45 = vc.findViewWithContentDescription('CD45', root=v4)
        self.assertNotEqual(v45, None)
        self.assertEqual('45', v45.getText())
        v35 = vc.findViewWithContentDescription('CD35', root=v3)
        self.assertNotEqual(v35, None)
        self.assertEqual('35', v35.getText())

    def testFindViewWithContentDescription_regexRoot(self):
        device = None
        root = View({'text:mText':'0', 'content-desc':'CD0'}, device)
        root.add(View({'text:mText':'1', 'content-desc':'CD1'}, device))
        root.add(View({'text:mText':'2', 'content-desc':'CD2'}, device))
        v3 = View({'text:mText':'3', 'content-desc':'CD3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'35', 'content-desc':'CD35'}, device)
        v3.add(v35)
        v4 = View({'text:mText':'4', 'conent-desc':'CD4'}, device)
        root.add(v4)
        v45 = View({'text:mText':'45', 'content-desc':'CD45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        v45 = vc.findViewWithContentDescription(re.compile('CD4\d'))
        self.assertNotEqual(v45, None)
        self.assertEqual('45', v45.getText())
        v45 = vc.findViewWithContentDescription(re.compile('CD4\d'), root=v4)
        self.assertNotEqual(v45, None)
        self.assertEqual('45', v45.getText())
        v35 = vc.findViewWithContentDescription(re.compile('CD3\d'), root=v3)
        self.assertNotEqual(v35, None)
        self.assertEqual('35', v35.getText())

    def testFindViewWithContentDescriptionOrRaise_root(self):
        device = None
        root = View({'text:mText':'0', 'content-desc':'CD0'}, device)
        root.add(View({'text:mText':'1', 'content-desc':'CD1'}, device))
        root.add(View({'text:mText':'2', 'content-desc':'CD2'}, device))
        v3 = View({'text:mText':'3', 'content-desc':'CD3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'35', 'content-desc':'CD35'}, device)
        v3.add(v35)
        v4 = View({'text:mText':'4', 'conent-desc':'CD4'}, device)
        root.add(v4)
        v45 = View({'text:mText':'45', 'content-desc':'CD45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        v45 = vc.findViewWithContentDescriptionOrRaise('CD45')
        self.assertEqual('45', v45.getText())
        v45 = vc.findViewWithContentDescriptionOrRaise('CD45', root=v4)
        self.assertEqual('45', v45.getText())
        v35 = vc.findViewWithContentDescriptionOrRaise('CD35', root=v3)
        self.assertEqual('35', v35.getText())

    def testFindViewWithContentDescriptionOrRaise_rootNonExistent(self):
        device = None
        root = View({'text:mText':'0', 'content-desc':'CD0'}, device)
        root.add(View({'text:mText':'1', 'content-desc':'CD1'}, device))
        root.add(View({'text:mText':'2', 'content-desc':'CD2'}, device))
        v3 = View({'text:mText':'3', 'content-desc':'CD3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'35', 'content-desc':'CD35'}, device)
        v3.add(v35)
        v4 = View({'text:mText':'4', 'conent-desc':'CD4'}, device)
        root.add(v4)
        v45 = View({'text:mText':'45', 'content-desc':'CD45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        try:
            vc.findViewWithContentDescriptionOrRaise('Non Existent', root=v4)
            self.fail()
        except ViewNotFoundException:
            pass

    def testFindViewWithContentDescriptionOrRaiseExceptionMessage_regexpRoot(self):
        device = None
        root = View({'text:mText':'0', 'content-desc':'CD0'}, device)
        root.add(View({'text:mText':'1', 'content-desc':'CD1'}, device))
        root.add(View({'text:mText':'2', 'content-desc':'CD2'}, device))
        v3 = View({'text:mText':'3', 'content-desc':'CD3'}, device)
        root.add(v3)
        v35 = View({'text:mText':'35', 'content-desc':'CD35'}, device)
        v3.add(v35)
        v4 = View({'text:mText':'4', 'conent-desc':'CD4'}, device)
        root.add(v4)
        v45 = View({'text:mText':'45', 'content-desc':'CD45'}, device)
        v4.add(v45)
        device = MockDevice()
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
        self.assertNotEquals(None, vc)
        vc.root = root
        try:
            vc.findViewWithContentDescriptionOrRaise(re.compile('Non Existent'), root=v4)
            self.fail()
        except ViewNotFoundException, e:
            self.assertNotEquals(None, re.search("that matches 'Non Existent'", e.message))

    def testUiAutomatorDump(self):
        device = MockDevice(version=16)
        vc = ViewClient(device, device.serialno, adb=TRUE, autodump=True)

    def testUiAutomatorKilled(self):
        device = MockDevice(version=16, uiautomatorkilled=True)
        try:
            vc = ViewClient(device, device.serialno, adb=TRUE, autodump=True, ignoreuiautomatorkilled=True)
        except Exception, e:
            self.assertIsNotNone(re.search('''ERROR: UiAutomator output contains no valid information. UiAutomator was killed, no reason given.''', str(e)))

    def testUiViewServerDump(self):
        device = None
        try:
            device = MockDevice(version=15, startviewserver=True)
            vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
            vc.dump()
            vc.findViewByIdOrRaise('id/home')
        finally:
            if device:
                device.shutdownMockViewServer()

    def testUiViewServerDump_windowStr(self):
        device = None
        try:
            device = MockDevice(version=15, startviewserver=True)
            vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
            vc.dump(window='StatusBar')
            vc.findViewByIdOrRaise('id/status_bar')
        finally:
            if device:
                device.shutdownMockViewServer()

    def testUiViewServerDump_windowInt(self):
        device = None
        try:
            device = MockDevice(version=15, startviewserver=True)
            vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
            vc.dump(window=0xb52f7c88)
            vc.findViewByIdOrRaise('id/status_bar')
        finally:
            if device:
                device.shutdownMockViewServer()

    def testUiViewServerDump_windowIntStr(self):
        device = None
        try:
            device = MockDevice(version=15, startviewserver=True)
            vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
            vc.dump(window='0xb52f7c88')
            vc.findViewByIdOrRaise('id/status_bar')
        finally:
            if device:
                device.shutdownMockViewServer()

    def testUiViewServerDump_windowIntM1(self):
        device = None
        try:
            device = MockDevice(version=15, startviewserver=True)
            vc = ViewClient(device, device.serialno, adb=TRUE, autodump=False)
            vc.dump(window=-1)
            vc.findViewByIdOrRaise('id/home')
        finally:
            if device:
                device.shutdownMockViewServer()

    def testFindViewsContainingPoint_api15(self):
        device = None
        try:
            device = MockDevice(version=15, startviewserver=True)
            vc = ViewClient(device, device.serialno, adb=TRUE)
            list = vc.findViewsContainingPoint((200, 200))
            self.assertNotEquals(None, list)
            self.assertNotEquals(0, len(list))
        finally:
            if device:
                device.shutdownMockViewServer()

    def testFindViewsContainingPoint_api17(self):
        device = MockDevice(version=17)
        vc = ViewClient(device, device.serialno, adb=TRUE)
        list = vc.findViewsContainingPoint((55, 75))
        self.assertNotEquals(None, list)
        self.assertNotEquals(0, len(list))

    def testFindViewsContainingPoint_filterApi15(self):
        device = None
        try:
            device = MockDevice(version=15, startviewserver=True)
            vc = ViewClient(device, device.serialno, adb=TRUE)
            list = vc.findViewsContainingPoint((200, 200), _filter=View.isClickable)
            self.assertNotEquals(None, list)
            self.assertNotEquals(0, len(list))
        finally:
            if device:
                device.shutdownMockViewServer()

    def testFindViewsContainingPoint_filterApi17(self):
        device = MockDevice(version=17)
        vc = ViewClient(device, device.serialno, adb=TRUE)
        list = vc.findViewsContainingPoint((55, 75), _filter=View.isClickable)
        self.assertNotEquals(None, list)
        self.assertNotEquals(0, len(list))

if __name__ == "__main__":
    print >> sys.stderr, "ViewClient.__main__:"
    print >> sys.stderr, "argv=", sys.argv
    #import sys;sys.argv = ['', 'Test.testName']
    #sys.argv.append('ViewClientTest.testFindViewsContainingPoint_filterApi17')
    unittest.main()
