#!/usr/bin/python
# -*- coding: utf-8 -*-
""" test the elec module
Pierre Haessig — September 2013
"""

from __future__ import division, print_function

import elec
reload(elec)

root = elec.System('root')
R1 = elec.Resistor('R1', 1e3)
root.add_subsystem(R1)

R2 = elec.Resistor('R2', 1e3)
root.add_subsystem(R2)

print(root)
print(R1)
