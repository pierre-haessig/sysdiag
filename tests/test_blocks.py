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
    # Check the ports:
    assert_equal(len(src.ports),  1)
    p = src.ports[0]
    assert_is_instance(p, blocks.OutputPort)
    assert_equal(p.direction, 'out')


def test_sink():
    '''test the Sink block class'''
    sink = blocks.Sink('sink')
    # Check the ports:
    assert_equal(len(sink.ports),  1)
    p = sink.ports[0]
    assert_is_instance(p, blocks.InputPort)
    assert_equal(p.direction, 'in')  


def test_simple_connection():
    '''Connect a few TransferFunction blocks'''
    r = blocks.System('root')
    # Create three TF blocks
    tf1 = blocks.TransferFunction('TF1', parent=r)
    tf2 = blocks.TransferFunction('TF2', parent=r)
    tf3 = blocks.TransferFunction('TF3', parent=r)

    # Manual connection tf1 -> tf2:
    w1 = blocks.SignalWire('w1', parent=r)
    w1.connect_port(tf1.ports_dict['out']) # output of tf1
    w1.connect_port(tf2.ports_dict['in']) # input of tf2

    # Only one output port can be connected to a SignalWire:
    with assert_raises(ValueError):
        w1.connect_port(tf3.ports_dict['out'])
    
    # Automated connection:
    w2 = blocks.connect_systems(tf2,tf3)

    # Check connection:
    assert tf2.ports_dict['out'] in w2.ports
    assert tf3.ports_dict['in'] in w2.ports

    # Print status:
    print(r)
    print('')
    print(tf1)


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

def test_json():
    '''basic test of JSON serialization/deserialization'''
    # PI controller block (example of Laplace tranfer)
    K = 1
    Ti = 0.1
    ctrl = blocks.TransferFunction('controller', [1, K*Ti],[0, Ti])
    s_json = '''{
      "__class__": "blocks.TransferFunction",
      "__sysdiagclass__": "System",
      "name": "controller",
      "params": {
        "den": [
          0,
          0.1
        ],
        "num": [
          1,
          0.1
        ]
      },
      "ports": [],
      "subsystems": [],
      "wires": []
    }'''
    # Compare JSON without whitespaces:
    assert_equal(ctrl.json_dump().replace(' ',''), s_json.replace(' ',''))
    
    import sysdiag
    ctrl1 = sysdiag.json_load(s_json)
    assert_is(type(ctrl1), blocks.TransferFunction)
    assert_equal(ctrl1.name, "controller")
    assert_equal(ctrl, ctrl1)
