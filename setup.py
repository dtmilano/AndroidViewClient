#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='androidviewclient',
      version='25.0.0',
      description='''AndroidViewClient is a 100% pure python library and tools
        that simplifies test script creation providing higher level
        operations and the ability of obtaining the tree of Views present at
        any given moment on the device or emulator screen.
        ''',
      license='Apache',
      keywords='android uiautomator viewclient monkeyrunner test automation mcp',
      author='Diego Torres Milano',
      author_email='dtmilano@gmail.com',
      url='https://github.com/dtmilano/AndroidViewClient/',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      package_data={'': ['*.png']},
      include_package_data=True,
      scripts=['tools/culebra', 'tools/dump', 'tools/culebra-mcp'],
      entry_points={
          'console_scripts': [
              'culebra-mcp=com.dtmilano.android.mcp.server:main',
          ],
      },
      python_requires='>=3.9',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License',
                   'Programming Language :: Python :: 3.9',
                   'Programming Language :: Python :: 3.10',
                   'Programming Language :: Python :: 3.11',
                   'Programming Language :: Python :: 3.12'],
      install_requires=[
          'setuptools',
          'requests',
          'numpy',
          'matplotlib',
          'culebratester-client >= 2.0.73',
          'mcp >= 0.9.0',
      ],
      extras_require={
          'dev': [
              'pytest >= 7.0.0',
              'pytest-asyncio >= 0.21.0',
              'hypothesis >= 6.0.0',
              'responses >= 0.23.0',
          ],
      },
      )
