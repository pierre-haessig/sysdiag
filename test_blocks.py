#!/usr/bin/python
# -*- coding: utf-8 -*-
""" test the blocks module
Pierre Haessig — September 2013
"""

from __future__ import division, print_function

import blocks

root = blocks.System('root')
# Create two blocks 
TF1 = blocks.TransferFunction('TF1')
TF2 = blocks.TransferFunction('TF2')

root.add_subsystem(TF1)
root.add_subsystem(TF2)

# Create one wire:
w = blocks.SignalWire('w1', parent=root)

w.connect_port(TF1.ports_dict['out']) # output of TF1
w.connect_port(TF2.ports_dict['in']) # input of TF2

print(root)
print('')
print(TF1)


