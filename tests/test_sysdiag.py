#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Test the main module of System Diagram
Pierre Haessig — September 2013
"""

from nose.tools import assert_equal, assert_true, assert_raises, assert_is

# Import sysdiag:
import sys
try:
    import sysdiag
except ImportError:
    sys.path.append('..')
    import sysdiag

def test_create_name():
    '''error proofing of the `_create_name` routine'''
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


def test_add_subsystem():
    '''check the add_subsystem machinery'''
    r = sysdiag.System('root')
    # a subsystem, assigned with parent.add_subsystem
    s1 = sysdiag.System('s1')
    assert_is(s1.parent, None)
    r.add_subsystem(s1)
    assert_is(s1.parent, r)
    # a subsystem, assigned at creation
    s2 = sysdiag.System('s2', parent=r)
    assert_is(s2.parent, r)


def test_add_ports():
    r = sysdiag.System('root')
    p1 = sysdiag.Port('p1', 'type1')
    p2 = sysdiag.Port('p2', 'type1')
    r.add_port(p1)
    r.add_port(p2)

    # Check ports list and dict:
    assert_equal(len(r.ports), 2)
    assert 'p1' in r.ports_dict.keys()
    assert 'p2' in r.ports_dict.keys()

    # duplicate addition:
    with assert_raises(ValueError):
        r.add_port(p1)

    # duplicate name:
    p11 = sysdiag.Port('p1', 'type1')
    with assert_raises(ValueError):
        r.add_port(p11)

def test_connect_port():
    '''check the connect_port method of Wire'''
    r = sysdiag.System('root')
    s1 = sysdiag.System('s1', parent=r)
    p1 = sysdiag.Port('p1', 'type1')
    s1.add_port(p1)
    
    w1 = sysdiag.Wire('w1', 'type1', parent=r)
    w2 = sysdiag.Wire('w2', 'type1', parent=r)
    w3 = sysdiag.Wire('w3', 'other type', parent=r)
    
    # failure of wrong type:
    with assert_raises(TypeError):
        w3.connect_port(p1)
    
    # wire connection that works:
    w1.connect_port(p1)
    assert_is(p1.wire, w1)
    
    # failure if a port is already taken:
    with assert_raises(ValueError):
        w2.connect_port(p1)

def test_connect_systems():
    '''check the connect_systems routine'''
    r = sysdiag.System('root')
    s1 = sysdiag.System('s1', parent=r)
    s2 = sysdiag.System('s2') # parent is None 
    # add some ports
    s1.add_port(sysdiag.Port('p1', 'type1'))
    s2.add_port(sysdiag.Port('p2', 'type1'))
    p_other = sysdiag.Port('p_other', 'other type')
    s2.add_port(p_other)

    # failure if no common parents
    with assert_raises(ValueError):
        w1 = sysdiag.connect_systems(s1,s2, 'p1', 'p2')
    r.add_subsystem(s2)
    w1 = sysdiag.connect_systems(s1,s2, 'p1', 'p2')
    assert_equal(len(w1.ports), 2)

    # failure if wrong types of ports:
    assert_equal(w1.is_connect_allowed(p_other, 'sibling'), False)
    with assert_raises(TypeError):
        w = sysdiag.connect_systems(s1,s2, 'p1', 'p_other')

    # double connection: no change is performed
    w2 = sysdiag.connect_systems(s1,s2, 'p1', 'p2')
    assert_is(w2,w1)
    assert_equal(len(w1.ports), 2)

def test_to_json():
    '''basic test of JSON serialization of System, Wire and Port'''
    # An empty System
    s = sysdiag.System('syst')
    s_dict = {'__class__': 'System',
              '__sysdiagclass__': 'System',
              '__value__': {'name': 'syst',
              'params': {},
              'ports': [],
              'subsystems': [],
              'wires': []}}
    assert_equal(s._to_json(), s_dict)

    # An empty Wire (no connected ports):
    w = sysdiag.Wire('w1', 'type1')
    w_dict = {'__class__': 'Wire',
              '__sysdiagclass__': 'Wire',
              '__value__': {'name': 'w1', 'ports': [], 'type': 'type1'}}
    assert_equal(w._to_json(), w_dict)

    # A port:
    p = sysdiag.Port('p1', 'type1')
    p_dict = {'__class__': 'Port',
              '__sysdiagclass__': 'Port',
              '__value__': {'name': 'p1', 'type': 'type1'}}
    assert_equal(p._to_json(), p_dict)
    
    # A system with some ports:
    s.add_port(p)
    assert_equal(s._to_json()['__value__']['ports'], [p])
    
    # A system with "default port" (i.e. created by the system)
    s.del_port(p)
    s.add_port(p, created_by_system=True)
    assert_equal(s._to_json()['__value__']['ports'], [])
    
    # TODO : test a wire with connected ports:

