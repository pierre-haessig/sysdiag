#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Test the modeling functions of System Diagram
Pierre Haessig — October 2013
"""

from nose.tools import assert_equal, assert_true, assert_raises, assert_is, assert_is_instance

import sympy
from sympy import symbols

# Import sysdiag:
import sys
try:
    import blocks
    import transfer_func
except ImportError:
    sys.path.append('..')
    import blocks
    import transfer_func


def testl_laplace_output():
    '''laplace_output function'''
    # A simple Single Input Single Output block
    s = blocks.SISOSystem('s1')
    TF = symbols('TF_s1')
    U = symbols('U')
    out = transfer_func.laplace_output(s, [U])
    assert_equal(len(out),1)
    assert_equal(out[0], TF*U) # Sympy expressions comparison


def test_transfer_syst():
    '''test transfer function modeling class'''
    # 1) Empty system
    s = blocks.SISOSystem('s1')
    TF = symbols('TF_s1')
    U,Y = symbols('U_s1_in Y_s1_out')
    for depth in [0,1,2,'unlimited']:
        out_expr, out_var, in_var = transfer_func.transfer_syst(s, depth=depth)
        assert_equal(out_expr[0], TF*U) # Sympy expressions comparison

    # 2) Traversing system: Y=U
    s = blocks.SISOSystem('s1')
    w = blocks.SignalWire('w1', parent=s)
    w.connect_port(s.ports_dict['in'],  'parent')
    w.connect_port(s.ports_dict['out'], 'parent')
    # 2a) depth=0, the inside is not analyzed
    out_expr, out_var, in_var = transfer_func.transfer_syst(s, depth=0)
    assert_equal(out_expr[0], TF*U)
    # 2b) depth=1, the inside is analyzed. Traversing connection is solved
    out_expr, out_var, in_var = transfer_func.transfer_syst(s, depth=1)
    assert_equal(out_expr[0], U)
