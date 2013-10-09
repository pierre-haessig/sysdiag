#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Elements for signal processing & control diagrams
Pierre Haessig — September 2013
"""

from __future__ import division, print_function
import numpy as np

import sysdiag
from sysdiag import System, InputPort, OutputPort, SignalWire

class Source(System):
    '''generic signal input source ("generator")'''
    def __init__(self, name='In', parent=None):
        super(Source, self).__init__(name, parent)
        self.add_port(OutputPort('out'), created_by_system = True)

class Sink(System):
    '''generic signal output sink'''
    def __init__(self, name='Out', parent=None):
        super(Sink, self).__init__(name, parent)
        self.add_port(InputPort('in'), created_by_system = True)
    
class SISOSystem(System):
    '''generic Single Input Single Output (SISO) system
    '''
    def __init__(self, name='S', parent=None):
        super(SISOSystem, self).__init__(name, parent)
        self.add_port(InputPort('in'), created_by_system = True)
        self.add_port(OutputPort('out'), created_by_system = True)

class TransferFunction(SISOSystem):
    '''Dynamical description of a Single Input Single Output (SISO) system
    with a Laplace transfer function
    '''
    def __init__(self, name='TF', num=[1], den=[1], parent=None):
        super(TransferFunction, self).__init__(name, parent)
        
        # Numerator and denominator of the transfer function:
        self.params['num'] = num
        self.params['den'] = den


class Summation(System):
    '''Summation block'''
    VALID_OPS = ['+', '-']
    
    def __init__(self, name='Sum', ops=['+', '+'], parent=None):
        super(Summation, self).__init__(name, parent)
        self.add_port(OutputPort('out'), created_by_system = True)
        self.set_operators(ops)
    
    def set_operators(self, ops):
        '''set the list of operations of the Summation block
        and add input Ports accordingly
        '''
        # flush the any existing list:
        self._operators = []
        
        # Remove the input ports:
        in_ports = [p for p in self.ports if p.direction=='in']
        for p in in_ports:
            self.del_port(p)
        
        for i,op_i in enumerate(ops):
            if not op_i in self.VALID_OPS:
                raise ValueError("Operator '{:s}' is not valid!".format(str(op_i)))
            
            self._operators.append(op_i)
            self.add_port(InputPort('in{:d}'.format(i)),
                          created_by_system = True)
    
    def _to_json(self):
        '''convert the Summation instance to a JSON-serializable object'''
        dict_obj = super(Summation, self)._to_json()
        dict_obj.update({'_operators': self._operators})
        return dict_obj
    # end _to_json

def connect_systems(source, dest, s_pname='out', d_pname='in'):
    '''Connect systems `source` to `dest` using
    port names `s_pname` (default 'out') and `d_pname` (default 'in')
    with a SignalWire
    
    The wire is created if necessary
    
    Returns: the wire
    '''
    # Use the generic function:
    w = sysdiag.connect_systems(source, dest, s_pname, d_pname,
                                wire_cls=SignalWire)
    return w

def incidence_matrix(syst):
    '''computes the incidence matrix of the system `syst` taking into account
    the IO Ports (Port direction 'in' and 'out').
    An ouput port yields +1, an input -1
    '''
    nw = len(syst.wires)
    ns = len(syst.subsystems)
    inc_mat = np.zeros((nw, ns), dtype=np.int8)
    # build a Look-up Table for wire indices:
    wires_ind = {w:i for i,w in enumerate(syst.wires)}
    
    for s_ind, s in enumerate(syst.subsystems):
        for p in s.ports:
            if p.wire is None:
                print('Warning: unconnected port {:s}'.format(str(p)))
                continue # (unconnected port)
            # find the index of the Port's wire
            w_ind = wires_ind[p.wire]
            # Put an entry in the incidence matrix:
            if p.direction == 'out':
                inc_mat[w_ind, s_ind] = 1
            elif p.direction == 'in':
                inc_mat[w_ind, s_ind] = -1
    
    return inc_mat
            
            
    
