#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Elements for signal processing & control diagrams
Pierre Haessig — September 2013
"""

from __future__ import division, print_function

from sysdiag import System, InputPort, OutputPort, SignalWire

class SISOSystem(System):
    '''generic Single Input Single Output (SISO) system
    '''
    def __init__(self, name='S'):
        super(SISOSystem, self).__init__(name)
        self.add_port(InputPort('in'))
        self.add_port(OutputPort('out'))

class TransferFunction(SISOSystem):
    '''Dynamical description of a Single Input Single Output (SISO) system
    with a Laplace transfer function
    '''
    def __init__(self, name='TF', num=[1], den=[1]):
        super(TransferFunction, self).__init__(name)
        
        # Numerator and denominator of the transfer function:
        self.params['num'] = num
        self.params['den'] = den
