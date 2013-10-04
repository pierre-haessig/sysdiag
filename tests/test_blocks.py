#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Test the blocks module of System Diagram
Pierre Haessig — September 2013
"""

from nose.tools import assert_equal, assert_true, assert_raises, assert_is, assert_is_instance

# Import sysdiag:
import sys
try:
    import blocks
except ImportError:
    sys.path.append('..')
    import blocks

def test_source():
    '''test the Source block class'''
    src = blocks.Source('src')
    # Check the ports:
    assert_equal(len(src.ports),  1)
    p = src.ports[0]
    assert_is_instance(p, blocks.OutputPort)
    assert_equal(p.direction, 'out')
  
def test_sink():
    '''test the Sink block class'''
    sink = blocks.Sink('sink')
    # Check the ports:
    assert_equal(len(sink.ports),  1)
    p = sink.ports[0]
    assert_is_instance(p, blocks.InputPort)
    assert_equal(p.direction, 'in')  

def test_closed_loop_diagram():
    '''Create a closed loop diagram.
    
    Not many checks, except that it works fine!
    '''
    root = blocks.System('top level system')

    # Main blocks:
    src = blocks.Source('src', root)
    K = 1
    Ti = 0.1
    ctrl = blocks.TransferFunction('controller', [1, K*Ti],[0, Ti], root) # PI control
    plant = blocks.TransferFunction('plant', [1], [0, 1], root) # integrator
    comp = blocks.Summation('compare', ops = ['+','-'], parent = root)
    out = blocks.Sink(parent=root)
    
    assert_is(ctrl.parent, root)

    # Connect the blocks together
    w0 = blocks.connect_systems(src, comp, d_pname='in0')
    w1 = blocks.connect_systems(comp, ctrl)
    w2 = blocks.connect_systems(ctrl, plant)
    w3 = blocks.connect_systems(plant, comp, d_pname='in1')
    w4 = blocks.connect_systems(plant, out)
    # Check that the reuse of wires:
    assert_equal(w3, w4)
    print(root)
