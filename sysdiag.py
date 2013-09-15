#!/usr/bin/python
# -*- coding: utf-8 -*-
""" sysdiag
Pierre Haessig — September 2013
"""

from __future__ import division, print_function

class System(object):
    '''Diagram description of a system
    
    a System is either an interconnecion of subsystems
    or an atomic element (a leaf of the tree)
    '''
    def __init__(self, name='root'):
        self.name = name
        # Parent system, if any (None for top-level):
        self.parent = None
        # Children systems, if any (None for leaf-level):
        self.subsystems = []
        self.ports = []
        self.params = {}
    
    @property
    def ports_dict(self):
        '''list of ports seen as a dict were names are the keys'''
        return {p.name:p for p in self.ports}
        
    def add_port(self, port):
        '''add a Port to the System'''
        # extract the port's name
        name = port.name
        port_names = [p.name for p in self.ports]
        if name in port_names:
            raise ValueError("port name '{}' already exists in {:s}!".format(
                              name, repr(self))
                             )
        # Add parent relationship and add to the ports dict:
        port.system = self
        self.ports.append(port)
    
    def add_subsystem(self, subsys):
        name = subsys.name
        subsys_names = [s.name for s in self.subsystems]
        if name in subsys_names:
            raise ValueError("system name '{}' already exists in {:s}!".format(
                              name, repr(self))
                             )
        # Add parent relationship and add to the ports dict:
        subsys.parent = self
        self.subsystems.append(subsys)
            
    def __str__(self):
        s = "{:s} '{:s}'".format(self.__class__.__name__, self.name)
        if self.parent:
            s += '\nParent: {:s}'.format(repr(self.parent))
        if self.params:
            s += '\nParameters: {:s}'.format(str(self.params))
        if self.ports:
            s += '\nPorts: {:s}'.format(str(self.ports))
        if self.subsystems:
            s += '\nSubsytems: {:s}'.format(str(self.subsystems))
        return s
        
    
class Port(object):
    '''Port enables the connection of a System to a Wire
    
    Each port has a `type` which only allowsthe connection of a Wire
    of the same type.
    '''
    direction = 'none'
    
    def __init__(self, name, ptype):
        self.name = name
        self.type = ptype
        self.system = None
        self.wire = None
    
    def __repr__(self):
        return '{:s}({:s}, {:s})'.format(self.__class__.__name__,
                     repr(self.name), repr(self.type))


class InputPort(Port):
    '''Input Port'''
    direction = 'in'
    
    def __init__(self, name, ptype=''):
        super(InputPort, self).__init__(name, ptype)    

class OutputPort(Port):
    '''Output Port'''
    direction = 'out'
    
    def __init__(self, name, ptype=''):
        super(OutputPort, self).__init__(name, ptype)    


class Wire(object):
    '''Wire enables the interconnection of several Systems
    through their Ports'''
    def __init__(self, name, wtype):
        self.name = name
        self.type = wtype
        self.ports = []
    
    def is_connect_allowed(self, port):
        if not self.type:
            # untyped wire: connection is always possible
            return True
        else:
            return port.type == self.type
    
    def connect_port(self, port):
        if not self.is_connect_allowed(port):
            raise ValueError('Port connection is not allowed!')
        # Add parent relationship:
        port.wire = self
        self.ports.append(port)
            


class SignalWire(Wire):
    '''Signal Wire for the interconnection of several Systems
    through their Input and Output Ports.
    
    Each SignalWire can be connected to a unique Output Port (signal source)
    and several Input Ports (signal sinks)
    '''
    def __init__(self, name, wtype=''):
        super(SignalWire, self).__init__(name, wtype)        
    
    def is_connect_allowed(self, port):
        if port.direction == 'in':
            # many signal sinks are allowed
            return super(SignalWire, self).is_connect_allowed(port)
        elif port.direction == 'out':
            # check that there is not already a signal source
            out_ports = [p for p in self.ports if p.direction=='out']
            if out_ports:
                return False
            else:
                return super(SignalWire, self).is_connect_allowed(port)
        else:
            # Not an input or output Port
            return False
    
    def connect_port(self, port):
        if not self.is_connect_allowed(port):
            raise ValueError('Port connection is not allowed!')
        # Add parent relationship:
        port.wire = self
        self.ports.append(port) 
