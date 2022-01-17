#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='androidviewclient',
      version='20.5.1',
      description='''AndroidViewClient is a 100% pure python library and tools
        that simplifies test script creation providing higher level
        operations and the ability of obtaining the tree of Views present at
        any given moment on the device or emulator screen.
        ''',
      license='Apache',
      keywords='android uiautomator viewclient monkeyrunner test automation',
      author='Diego Torres Milano',
      author_email='dtmilano@gmail.com',
      url='https://github.com/dtmilano/AndroidViewClient/',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      package_data={'': ['*.png']},
      include_package_data=True,
      scripts=['tools/culebra', 'tools/dump'],
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License'],
      install_requires=['setuptools', 'requests', 'numpy', 'matplotlib', 'culebratester-client >= 2.0.19'],
      )
