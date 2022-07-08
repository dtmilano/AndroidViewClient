AndroidViewClient
=================
<a href="#"><img src="https://github.com/dtmilano/AndroidViewClient/wiki/images/culebra-logo-transparent-204x209-rb-border.png" align="left" hspace="0" vspace="6"></a>
**AndroidViewClient** was originally conceived as an extension to [monkeyrunner](http://developer.android.com/tools/help/monkeyrunner_concepts.html) but lately evolved
as a pure python tool that automates or simplifies test script creation.
It is a test framework for Android applications that:
<ul><ul>
    <li>Automates driving Android applications</li>
    <li>Generates re-usable scripts</li>
    <li>Provides view-based <i>device independent</i> UI interaction</li>
    <li>Uses 'logical' screen comparison (UI Automator Hierarchy based) over image comparison (Avoiding extraneous 
    detail issues, such as time or data changes)</li>
    <li>Supports running concurrently on multiple devices</li>
    <li>Provides simple control for high level operations like language change and activity start</li>
    <li>Supports all Android APIs</li>
    <li>Is written in python (python 3.6+ support in 20.x.y+)</li>
</ul></ul>

**🛎** |A new Kotlin backend is under development to provide more functionality and improve performance.<br>Take a look at [CulebraTester2](https://github.com/dtmilano/CulebraTester2-public) and 20.x.y-series prerelease. |
---|----------------------------------------------------------------------------------------------|

[![Latest Version](https://img.shields.io/pypi/v/androidviewclient.svg)](https://pypi.python.org/pypi/androidviewclient/)
![Release](https://img.shields.io/github/v/release/dtmilano/AndroidViewClient?include_prereleases&label=release)
![Upload Python Package](https://github.com/dtmilano/AndroidViewClient/workflows/Upload%20Python%20Package/badge.svg)
[![Downloads](https://pepy.tech/badge/androidviewclient)](https://pepy.tech/project/androidviewclient)

**NOTE**: Pypi statistics are broken see [here](https://github.com/aclark4life/vanity/issues/22). The new statistics can be obtained from [BigQuery](https://bigquery.cloud.google.com/queries/culebra-tester).

As of August 2021 we have reached:

<img src="https://github.com/dtmilano/AndroidViewClient/wiki/images/androidviewclient-culebra-1million.png" alt="culebra 1 million downloads" width="80%" align="center">

Thanks to all who made it possible.

# Installation
```
pip3 install androidviewclient --upgrade
```
Or check the wiki for more alternatives.

# Want to learn more?
Detailed information can be found in the [AndroidViewClient/culebra wiki](https://github.com/dtmilano/AndroidViewClient/wiki)

