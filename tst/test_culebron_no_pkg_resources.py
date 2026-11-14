#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
culebron must import without pkg_resources.

setuptools removed pkg_resources (it is absent from setuptools 84), and
setuptools is not pinned, so a fresh install gets a setuptools without it.
A module-level ``from pkg_resources import ...`` then makes culebron fail to
import at all.

The import is checked in a subprocess with pkg_resources blocked, so the test
means the same thing whichever setuptools happens to be installed here.
"""

import os
import subprocess
import sys
import textwrap

SRC = os.path.join(os.path.dirname(__file__), '..', 'src')

_BLOCK_AND_IMPORT = textwrap.dedent("""
    import sys

    class _BlockPkgResources:
        def find_spec(self, name, path=None, target=None):
            if name == 'pkg_resources' or name.startswith('pkg_resources.'):
                raise ModuleNotFoundError("No module named 'pkg_resources'", name=name)
            return None

    sys.meta_path.insert(0, _BlockPkgResources())
    sys.modules.pop('pkg_resources', None)

    import com.dtmilano.android.culebron as culebron
    print('ICON', culebron._culebra_icon_path())
""")


def _run():
    env = dict(os.environ, PYTHONPATH=os.path.abspath(SRC))
    return subprocess.run([sys.executable, '-c', _BLOCK_AND_IMPORT],
                          capture_output=True, text=True, env=env, timeout=120)


def test_culebron_imports_without_pkg_resources():
    result = _run()
    assert result.returncode == 0, result.stderr[-2000:]


def test_icon_is_found_from_a_source_checkout():
    # From a source tree there is no installed distribution to ask, so the lookup
    # must fall back to the checked-in src/share/pixmaps/culebra.png.
    result = _run()
    assert result.returncode == 0, result.stderr[-2000:]
    line = [l for l in result.stdout.splitlines() if l.startswith('ICON ')][-1]
    path = line[len('ICON '):]
    assert path != 'None', 'icon not found'
    assert os.path.isfile(path), path
    assert path.replace('\\', '/').endswith('share/pixmaps/culebra.png'), path
