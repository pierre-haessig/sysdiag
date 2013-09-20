#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Elements for signal processing & control diagrams
Pierre Haessig — September 2013
"""

from __future__ import division, print_function
import numpy as np

from sysdiag import System, InputPort, OutputPort, SignalWire

class Source(System):
    '''generic signal source'''
    def __init__(self, name='Src', parent=None):
        super(Source, self).__init__(name, parent)
        self.add_port(OutputPort('out'))
    
class SISOSystem(System):
    '''generic Single Input Single Output (SISO) system
    '''
    def __init__(self, name='S', parent=None):
        super(SISOSystem, self).__init__(name, parent)
        self.add_port(InputPort('in'))
        self.add_port(OutputPort('out'))

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
        self.add_port(OutputPort('out'))
        self.set_operators(ops)
    
    def set_operators(self, ops):
        '''set the list of operations of the Summation block
        and add input Ports accordingly
        '''
        # flush the any existing list:
        self._op = []
        
        # Remove the input ports:
        in_ports = [p for p in self.ports if p.direction=='in']
        for p in in_ports:
            self.del_port(p)
        
        for i,op_i in enumerate(ops):
            if not op_i in self.VALID_OPS:
                raise ValueError("Operator '{:s}' is not valid!".format(str(op_i)))
            
            self._op.append(op_i)
            self.add_port(InputPort('in{:d}'.format(i)))

def connect_systems(source, dest, s_pname='out', d_pname='in'):
    '''Connect systems `source` to `dest` using
    port names `s_pname` (default 'out') and `d_pname` (default 'in')
    with a SignalWire
    
    The wire is created if necessary
    
    Returns: the wire
    '''
    # 1) find the ports
    s_port = source.ports_dict[s_pname]
    d_port =   dest.ports_dict[d_pname]
 
    # 2) find a prexisting wire:
    w = None
    if s_port.wire is not None:
        w = s_port.wire
    elif d_port.wire is not None:
        w = d_port.wire
    else:        
        parent = s_port.system.parent
        wname = parent.create_name('wire','W')
        wtype = s_port.type
        w = SignalWire(wname, wtype, parent)
    
    # 3) Make the connection:
    w.connect_port(s_port)
    w.connect_port(d_port)
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
            
            
    
