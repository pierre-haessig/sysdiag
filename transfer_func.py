#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Compute the tranfer function of a system

based on SymPy for equation handling and solving

Pierre Haessig — September 2013
"""

from __future__ import division, print_function
import sympy
from sympy import symbols, Eq, simplify

import blocks

def transfer_func(syst, depth='unlimited'):
    '''Compute the transfer function of `syst`'''
    pass

from closed_loop_control import root as r


In  = []
Out = []
W = {} # wires
TF = {}

diagram_eqs = []

def wires_to_sym(w):
    if w not in W:
        # Add wire w to the dict W:
        W[w] = symbols('W_' + w.name)
    return W[w]

for s in r.subsystems:
    print(s)
    
    # Output Wires
    w_out = [p.wire for p in s.ports if p.direction=='out']
    if len(w_out) == 0:
        w_out = None
    else:
        assert len(w_out) == 1
        w_out = w_out[0]
        # Convert Wires to SymPy symbols
        w_out = wires_to_sym(w_out)
    
    # Input Wires
    w_in  = [p.wire for p in s.ports if p.direction=='in']
    # Convert Wires to SymPy symbols
    w_in  = [wires_to_sym(w) for w in w_in]
    
    # Manage the different blocks
    if not w_in:
        # Source block
        assert type(s) is blocks.Source
        In_s = symbols('U_' + s.name)
        In.append(In_s)
        # Output equation:
        Out_s = In_s
    
    elif type(s) is blocks.Summation:
        sum_terms = []
        for op, w in zip(s._op, w_in):
            if op == '+':
                sum_terms.append(+w)
            elif op == '-':
                sum_terms.append(-w)
            else:
                raise ValueError('unknow operator')
        
        Out_s = sympy.Add(*sum_terms)
    elif type(s) is blocks.TransferFunction:
        TF_s = symbols('H_' + s.name)
        TF[s] = TF_s
        assert len(w_in) == 1
        Out_s = TF_s * w_in[0]
    elif type(s) is blocks.Sink:
        assert w_out is None
        assert len(w_in) == 1
        Out_s = symbols('Y_' + s.name)
        Out.append(Out_s)
        diagram_eqs.append(Eq(Out_s, w_in[0]))
    else:
        raise ValueError('unknown block!')
    
    # Store IO equation:
    if w_out is not None:
        diagram_eqs.append(Eq(w_out, Out_s))
    
print('\nDiagram Equations:')
print(diagram_eqs)

sol = sympy.solve(diagram_eqs, W.values()+ Out)

#out = W[r.wires[3]]
out = Out[0]

Out_TF = sympy.simplify(sol[out]/In[0]) # TODO : define simplification so that it yields a nice fraction
print('\nTransfer function:')
print(Out_TF)

### Apply a PI controller:

Hp, Hc = TF.values()

s = symbols('s')
tau, K, Ti = symbols('tau K T_i')

H = Out_TF.subs(Hp, 1/(1+tau*s)).subs(Hc, K+Ti/s)
print('\n1st order plant with a PI controller')
print(simplify(H))
