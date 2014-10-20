#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='androidviewclient',
    version='8.3.1',
    description='''AndroidViewClient is a 100% pure python tool that
        simplifies test script creation providing higher level operations and the ability of
        obtaining the tree of Views present at any given moment on the device or emulator screen.
        ''',
    license='Apache',
    keywords='android uiautomator viewclient monkeyrunner test automation',
    author='Diego Torres Milano',
    author_email='dtmilano@gmail.com',
    url='https://github.com/dtmilano/AndroidViewClient/',
    packages=find_packages('src'),
    package_dir={'':'src'},
    scripts=['tools/culebra', 'tools/dump'],
    classifiers=['Development Status :: 5 - Production/Stable',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License'],
    install_requires=['setuptools'],
    )
