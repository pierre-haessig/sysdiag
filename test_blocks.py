#!/usr/bin/python
# -*- coding: utf-8 -*-
""" test the blocks module
Pierre Haessig — September 2013
"""

from __future__ import division, print_function

import blocks

root = blocks.System('root')
TF = blocks.TransferFunction('TF1', 1e3)
root.add_subsystem(TF)

print(root)
print(TF)


