#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Test the main module of System Diagram
Pierre Haessig — September 2013
"""

from nose.tools import assert_equal, assert_true, assert_raises

# Import sysdiag:
import sys
try:
    import sysdiag
except ImportError:
    sys.path.append('..')
    import sysdiag

def test_create_name():
    create = sysdiag._create_name
    # 1) Name creation when the base is not already taken:
    assert_equal(create([],'abc'), 'abc')
    assert_equal(create(['def'],'abc'), 'abc')
    assert_equal(create(['d','e','f'],'abc'), 'abc')
    # 2) when the basename is empty:
    with assert_raises(ValueError):
        create([],'')
    with assert_raises(ValueError):
        create([],' ')
    # 3) when the basename is already taken
    assert_equal(create(['a'],'a'), 'a0')
    assert_equal(create(['a', 'a0'],'a'), 'a1')
