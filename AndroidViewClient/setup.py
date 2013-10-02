#!/usr/bin/env python

from setuptools import setup

setup(name='AndroidViewClient',
    version='4.5.0',
    description='''AndroidViewClient is a 100% pure python tool that
        simplifies test script creation providing higher level operations and the ability of
        obtaining the tree of Views present at any given moment on the device or emulator screen.
        ''',
    license='Apache',
    keywords='android uiautomator viewclient monkeyrunner',
    author='Diego Torres Milano',
    author_email='dtmilano@gmail.com',
    url='https://github.com/dtmilano/AndroidViewClient/',
    package_dir={'com.dtmilano.android':'src'},
    packages=['com.dtmilano.android', 'tests.com.dtmilano.android'],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License']
    )
