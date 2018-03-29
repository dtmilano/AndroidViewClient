'''
Created on Aug 6, 2013

@author: diego
'''
import os
import re
import subprocess
import sys
import time
import unittest

try:
    sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
except:
    pass

from com.dtmilano.android.adb.adbclient import AdbClient
from com.dtmilano.android.common import obtainAdbPath

VERBOSE = False

TEST_TEMPERATURE_CONVERTER_APP = False
TEMPERATURE_CONVERTER_PKG = 'com.example.i2at.tc'
TEMPERATURE_CONVERTER_ACTIVITY = 'TemperatureConverterActivity'
CALCULATOR_KEYWORD = 'calculator'
CALCULATOR_ACTIVITY = 'Calculator'

#ANDROIANDROID_SERIAL = 'emulator-5554'

class AdbClientTest(unittest.TestCase):

    androidSerial = None
    ''' The Android device serial number used by default'''

    @classmethod
    def setUpClass(cls):
        cls.adb = obtainAdbPath()
        # we use 'fakeserialno' and settransport=False so AdbClient does not try to find the
        # serialno in setTransport()
        try:
            adbClient = AdbClient('fakeserialno', settransport=False)
        except RuntimeError, ex:
            if re.search('Connection refused', str(ex)):
                raise RuntimeError("adb is not running")
            raise(ex)
        devices = adbClient.getDevices()
        if len(devices) == 0:
            raise RuntimeError("This tests require at least one device connected. None was found.")
        for device in devices:
            if device.status == 'device':
                cls.androidSerial = device.serialno
                if VERBOSE:
                    print "AdbClientTest: using device %s" % cls.androidSerial
                return
        raise RuntimeError("No on-line devices found")

    def setUp(self):
        subprocess.check_call([self.adb, '-s', self.androidSerial, 'forward', '--remove-all'])
        self.adbClient = AdbClient(self.androidSerial)
        self.assertIsNotNone(self.adbClient, "adbClient is None")

    def tearDown(self):
        self.adbClient.close()
        subprocess.check_call([self.adb, '-s', self.androidSerial, 'forward', '--remove-all'])

    def testSerialno_none(self):
        try:
            adbClient = AdbClient(None)
            self.assertTrue(adbClient.checkConnected())
            # because serialno is None, transport cannot be set, so next statement
            # will raise an exception
            adbClient.getSdkVersion()
            self.fail("No exception was generated")
        except RuntimeError, ex:
            self.assertIsNotNone(re.search("ERROR: Transport is not set", str(ex)), "Couldn't find error message: %s" % ex)

    def testSerialno_nonExistent(self):
        try:
            AdbClient('doesnotexist')
        except RuntimeError, ex:
            self.assertIsNotNone(re.search("ERROR: couldn't find device that matches 'doesnotexist'", str(ex)), "Couldn't find error message: %s" % ex)

    def testSerialno_empty(self):
        try:
            AdbClient('')
            self.fail("No exception was generated")
        except ValueError:
            pass

    def testGetDevices(self):
        # we use 'fakeserialno' and settransport=False so AdbClient does not try to find the
        # serialno in setTransport()
        adbclient = AdbClient('fakeserialno', settransport=False)
        self.assertTrue(len(adbclient.getDevices()) >= 1)

    def testGetDevices_androidSerial(self):
        devs = self.adbClient.getDevices()
        self.assertTrue(self.androidSerial in [d.serialno for d in devs])

    def testGetDevices_regex(self):
        adbclient = AdbClient('.*', settransport=False)
        self.assertTrue(len(adbclient.getDevices()) >= 1)

    #@unittest.skipIf(not re.search('emulator-5554', AdbClientTest.androidSerial), "Supported only when emulator is connected")
    def testAdbClient_serialnoNoRegex(self):
        if re.search('emulator-5554', AdbClientTest.androidSerial):
            adbClient = AdbClient('emulator-5554')
            self.assertIsNotNone(adbClient)
            self.assertEqual('emulator-5554', adbClient.serialno)

    #@unittest.skipIf(not re.search('emulator', AdbClientTest.androidSerial), "Supported only when emulator is connected")
    def testAdbClient_serialnoRegex(self):
        if re.search('emulator', AdbClientTest.androidSerial):
            adbClient = AdbClient('emulator-.*')
            self.assertIsNotNone(adbClient)
            self.assertTrue(re.match('emulator-.*', adbClient.serialno))

    def testAdbClient_serialnoRegexIP(self):
        IPRE = re.compile('(\d+\.){3}\d+')
        if IPRE.search(AdbClientTest.androidSerial):
            adbClient = AdbClient('\d+.*')
            self.assertIsNotNone(adbClient)
            self.assertTrue(IPRE.match(adbClient.serialno))

    def testCheckVersion(self):
        self.adbClient.checkVersion()

    def testShell(self):
        date = self.adbClient.shell('date +"%Y/%m/%d"')
        # this raises a ValueError if the format is not correct
        time.strptime(date, '%Y/%m/%d\r\n')

    def testShell_noOutput(self):
        empty = self.adbClient.shell('sleep 3')
        self.assertIs('', empty, "Expected empty output but found '%s'" % empty)

    def testGetProp_ro_serialno(self):
        serialno = self.adbClient.getProperty('ro.serialno')
        self.assertIsNotNone(serialno)
        if re.search('emulator-.*', self.androidSerial):
            self.assertEqual(serialno, '')
        elif re.search('VirtualBox', self.adbClient.getProperty('ro.product.model')):
            self.assertEqual(serialno, '')
        else:
            self.assertEqual(serialno, self.androidSerial)

    def testGetProp_ro_kernel_qemu(self):
        qemu = self.adbClient.getProperty('ro.kernel.qemu')
        self.assertIsNotNone(qemu)
        if re.search('emulator-.*', self.androidSerial):
            self.assertEqual(qemu, '1')
        else:
            self.assertEqual(qemu, '')

    def testPress(self):
        self.adbClient.press('KEYCODE_DPAD_UP')

    def testTouch(self):
        self.adbClient.touch(480, 1250)

    def testType(self):
        self.adbClient.type('Android is cool')

    def testType_digits(self):
        self.adbClient.type('1234')

    def testType_digits_asInt(self):
        self.adbClient.type(1234)


    def __checkPackageInstalled(self):
        packages = self.adbClient.shell('pm list packages').splitlines()
        self.assertTrue(packages, "Could not detect any packages installed")
        if TEST_TEMPERATURE_CONVERTER_APP:
            self.assertIn('package:' + TEMPERATURE_CONVERTER_PKG, packages, TEMPERATURE_CONVERTER_PKG + " is not installed")
            return (TEMPERATURE_CONVERTER_PKG, TEMPERATURE_CONVERTER_ACTIVITY)
        else:
            for line in packages:
                if CALCULATOR_KEYWORD in line:
                    pkg = line[line.index(':')+1:]
                    self.assertTrue(pkg, "No calculator package to use for testing")
                    return (pkg, CALCULATOR_ACTIVITY)
            return False

    def testStartActivity_component(self):
        pkg = self.__checkPackageInstalled()
        if pkg:
            self.adbClient.startActivity(pkg[0] + '/.' + pkg[1])

    def testGetWindows(self):
        self.assertIsNotNone(self.adbClient.getWindows())
        
    def testGetFocusedWindow(self):
        pkg = self.__checkPackageInstalled()
        if pkg:
            self.adbClient.startActivity(pkg[0] + '/.' + pkg[1])
            time.sleep(3)
            w = self.adbClient.getFocusedWindow()
            self.assertIsNotNone(w)
            self.assertEqual(pkg[0] + '/' + pkg[0] + '.' + pkg[1], w.activity)
        
    def testGetFocusedWindowName(self):
        pkg = self.__checkPackageInstalled()
        if pkg:
            self.adbClient.startActivity(pkg[0] + '/.' + pkg[1])
            time.sleep(3)
            n = self.adbClient.getFocusedWindowName()
            self.assertIsNotNone(n)
            self.assertEqual(pkg[0] + '/' + pkg[0] + '.' + pkg[1], n)
        
    def testStartActivity_uri(self):
        self.adbClient.startActivity(uri='http://www.google.com')

    #@unittest.skip("sequence")
    def testCommandsSequence(self):
        self.adbClient.setReconnect(True)
        if VERBOSE:
            print "Sending touch(480, 800)"
        self.adbClient.touch(480, 800)
        self.assertTrue(self.adbClient.checkConnected())
        if VERBOSE:
            print "Typing 'command 1'"
        self.adbClient.type("command 1")
        self.assertTrue(self.adbClient.checkConnected())
        if VERBOSE:
            print "Typing 'command 2'"
        self.adbClient.type("command 2")
        self.assertTrue(self.adbClient.checkConnected())
        if VERBOSE:
            print "Pressing ENTER"
        self.adbClient.press('KEYCODE_ENTER')
        self.assertTrue(self.adbClient.checkConnected())

    def testPressRepeat(self):
        self.adbClient.press('DEL', repeat=4)

    #def testWake(self):
    #    self.adbClient.wake()

if __name__ == "__main__":
    #print >> sys.stderr, "sys.path=", sys.path
    #sys.argv = ['', 'AdbClientTest']
    unittest.main()
