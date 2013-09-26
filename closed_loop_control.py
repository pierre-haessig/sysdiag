#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Diagram of a closed loop control

Pierre Haessig — September 2013
"""

from __future__ import division, print_function

import blocks

root = blocks.System('CL control')

# Main blocks:
Src = blocks.Source('src', root)
K = 2; Ti = .2
Ctrl = blocks.TransferFunction('controller', [1, K*Ti],[0, Ti], root) # PI control
Plant = blocks.TransferFunction('plant', [1], [0, 1], root) # integrator
Cmp = blocks.Summation('compare', ops = ['+','-'], parent = root)

Out = blocks.Sink(parent=root)

w0 = blocks.connect_systems(Src, Cmp, d_pname='in0')
w1 = blocks.connect_systems(Cmp, Ctrl)
w2 = blocks.connect_systems(Ctrl, Plant)
w3 = blocks.connect_systems(Plant, Cmp, d_pname='in1')

w4 = blocks.connect_systems(Plant, Out)
assert w3 == w4

print(root)

print('Compute incidence matrix')
inc_mat = blocks.incidence_matrix(root)
print(inc_mat)




