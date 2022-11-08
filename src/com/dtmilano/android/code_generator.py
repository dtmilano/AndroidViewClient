import sys
import textwrap
from abc import ABC
from datetime import date

__version__ = '22.3.0'

from typing import TextIO, Union, Dict, List

from com.dtmilano.android.viewclient import CulebraOptions


class AbstractCodeGenerator(ABC):
    def __init__(self, options: Dict[str, Union[bool, None, str, List[str], float]]) -> None:
        self.options = options

    @staticmethod
    def get_shebang() -> str:
        return '#! /usr/bin/env python3'

    def header(self, out: TextIO = sys.stdout) -> None:
        print(textwrap.dedent(f'''
            {self.get_shebang()}
            # -*- coding: utf-8 -*-
            """
            Copyright (C) 2013-2022  Diego Torres Milano
            Created on {date.today()} by Culebra v{__version__}
                                  __    __    __    __
                                 /  \  /  \  /  \  /  \ 
            ____________________/  __\/  __\/  __\/  __\_____________________________
            ___________________/  /__/  /__/  /__/  /________________________________
                               | / \   / \   / \   / \   \___
                               |/   \_/   \_/   \_/   \    o \ 
                                                       \_____/--<
            @author: Diego Torres Milano
            @author: Jennifer E. Swofford (ascii art snake)
            """


            import os
            import re
            import sys
            import time
            ''')[1:], file=out)

    @staticmethod
    def import_unittest(out: TextIO = sys.stdout) -> None:
        print(textwrap.dedent('''
            import unittest
            '''), file=out)

    @staticmethod
    def prepend_to_syspath(out: TextIO = sys.stdout) -> None:
        print(textwrap.dedent('''
            try:
                sys.path.insert(0, os.path.join(os.environ['ANDROID_VIEW_CLIENT_HOME'], 'src'))
            except:
                pass
            '''), file=out)

    def import_viewclient(self, out: TextIO = sys.stdout) -> None:
        extra_import = ', CulebraTestCase' if self.options[CulebraOptions.UNIT_TEST_CLASS] else ''
        print(textwrap.dedent(f'''
            from com.dtmilano.android.viewclient import ViewClient, KEY_EVENT{extra_import}

            ''')[1:], file=out)

    @staticmethod
    def tag(tag: str, out: TextIO = sys.stdout) -> None:
        print(f'TAG = \'{tag}\'', file=out)

    def unittest(self, kwargs1: Dict[str, bool], kwargs2: Dict[str, Union[bool, dict]],
                 out: TextIO = sys.stdout) -> None:
        method = self.options[CulebraOptions.UNIT_TEST_METHOD] if self.options[
            CulebraOptions.UNIT_TEST_METHOD] else 'testSomething'
        print(textwrap.dedent(f'''
            class CulebraTests(CulebraTestCase):

                @classmethod
                def setUpClass(cls):
                    cls.kwargs1 = {kwargs1}
                    cls.kwargs2 = {kwargs2}
                    cls.options = {self.options}
                    cls.sleep = 5

                def setUp(self):
                    super(CulebraTests, self).setUp()

                def tearDown(self):
                    super(CulebraTests, self).tearDown()

                def preconditions(self):
                    if not super(CulebraTests, self).preconditions():
                        return False

                    if options[\'{CulebraOptions.INSTALL_APK}\']:
                        if self.vc.installPackage(options[\'{CulebraOptions.INSTALL_APK}\']) != 0:
                            return False
                            
                    return True
                    
                def {method}(self):
                    if not self.preconditions():
                        self.fail('Preconditions failed')
                        
                    _s = CulebraTests.sleep
                    _v = CulebraTests.verbose
                    pid = os.getpid()
                        
                    if options[\'{CulebraOptions.SAVE_SCREENSHOT}\']:
                        self.vc.writeImageToFile(options[\'{CulebraOptions.SAVE_SCREENSHOT}\'], 'PNG')
                        
                    if options[\'{CulebraOptions.USE_DICTIONARY}\']:
                        self.views = dict()
                    
            '''), file=out)

    # FIXME:
    # still missing these parts:
    #
    #     if not options[CulebraOptions.GUI]:
    #         vc.dump(window=options[CulebraOptions.WINDOW])
    #     indent = ' ' * 8
    #     prefix = 'self.'
    #
    #     #     if not options[CulebraOptions.DO_NOT_VERIFY_SCREEN_DUMP]:
    #     #         print '''\
    #     #         self.vc.dump(%s)
    #     #         ''' % getWindowOption()
    #     #         vc.traverse(transform=transform)
    #     #         print
    #
    #     if options[CulebraOptions.GUI]:
    #         runCulebron()
    #     elif not options[CulebraOptions.DO_NOT_VERIFY_SCREEN_DUMP]:
    #         if kwargs2.get(ViewClientOptions.USE_UIAUTOMATOR_HELPER, False):
    #             printDumpUiAutomatorHelper(getWindowOption())
    #         else:
    #             printDump(getWindowOption())
    #     else:
    #         print('''\
    #         ## your test code here ##
    #         ''')
    #
    #     print('''
    #
    # if __name__ == '__main__':
    #     CulebraTests.main()
    # ''')

    def find_object(self, view):
        raise NotImplementedError()


class HelperCodeGenerator(AbstractCodeGenerator):
    def header(self, out=sys.stdout):
        return AbstractCodeGenerator.header(self, out)

    def find_object(self, view):
        pass


class VcCodeGenerator(AbstractCodeGenerator):
    def header(self, out=sys.stdout):
        return AbstractCodeGenerator.header(self, out)

    def find_object(self, view):
        pass
