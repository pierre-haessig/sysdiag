#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Elements for electrical diagrams
Pierre Haessig — September 2013
"""

from __future__ import division, print_function

from sysdiag import System, Port

class Dipole(System):
    '''Common class for electrical dipoles (Resistor, Capacitor, Inductor)
    '''
    def __init__(self, name='D'):
        super(Dipole, self).__init__(name)
        self.add_port(Port('p', 'elec'))
        self.add_port(Port('n', 'elec'))


class Resistor(Dipole):
    def __init__(self, name='R', R=1e3):
        super(Resistor, self).__init__(name)
        self.params['R'] = R
