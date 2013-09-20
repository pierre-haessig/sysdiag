#!/usr/bin/python
# -*- coding: utf-8 -*-
""" sysdiag
Pierre Haessig — September 2013
"""

from __future__ import division, print_function

def _create_name(name_list, base):
    '''Returns a name (str) built on `base` that doesn't exist in `name_list`.
    
    Useful for automatic creation of subsystems or wires
    '''
    base = str(base)
    if base == '':
        # avoid empty str, even if it's not forbidden
        base = 'S'
    if base not in name_list:
        return base
    
    # Else: build another name by counting
    i = 0
    name = base + str(i)
    while name in name_list:
        i += 1
        name = base + str(i)
    return name

class System(object):
    '''Diagram description of a system
    
    a System is either an interconnecion of subsystems
    or an atomic element (a leaf of the tree)
    '''
    def __init__(self, name='root', parent=None):
        self.name = name
        # Parent system, if any (None for top-level):
        self.parent = None
        # Children systems, if any (None for leaf-level):
        self.subsystems = []
        self.wires = []
        self.ports = []
        self.params = {}
        
        # If a parent system is provided, request its addition as a subsystem
        if parent is not None:
            parent.add_subsystem(self)
    
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
    
    def del_port(self, port):
        '''delete a Port of the System (and disconnect any connected wire)
        '''
        if port.wire is not None:
            # TODO : implement the wire disconnection
            raise NotImplementedError('Cannot yet delete a connected Port')
        # Remove the ports list:
        self.ports.remove(port)
    
    def add_subsystem(self, subsys):
        # 1) Check name uniqueness
        name = subsys.name
        subsys_names = [s.name for s in self.subsystems]
        if name in subsys_names:
            raise ValueError("system name '{}' already exists in {:s}!".format(
                              name, repr(self))
                             )
        # 2) Add parent relationship and add to the system list
        subsys.parent = self
        self.subsystems.append(subsys)
    
    def add_wire(self, wire):
        # 1) Check name uniqueness
        name = wire.name
        wire_names = [w.name for w in self.wires]
        if name in wire_names:
            raise ValueError("wire name '{}' already exists in {:s}!".format(
                              name, repr(self))
                             )
        # Add parent relationship and add to the ports dict:
        wire.parent = self
        self.wires.append(wire)
    
    def create_name(self, category, base):
        '''Returns a name (str) built on `base` that doesn't exist in
        within the names of `category`.
        '''
        if category == 'subsystem':
            components = self.subsystems
        elif category == 'wire':
            components = self.wires
        else:
            raise ValueError("Unknown category '{}'!".format(str(category)))
        
        name_list = [c.name for c in components]
        return _create_name(name_list, base)
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        s =  "{:s}('{.name}')".format(cls_name, self)
        return s
    
    def __str__(self):
        s = repr(self)
        if self.parent:
            s += '\n  Parent: {:s}'.format(repr(self.parent))
        if self.params:
            s += '\n  Parameters: {:s}'.format(str(self.params))
        if self.ports:
            s += '\n  Ports: {:s}'.format(str(self.ports))
        if self.subsystems:
            s += '\n  Subsytems: {:s}'.format(str(self.subsystems))
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
        cls_name = self.__class__.__name__
        s = '{:s}({:s}, {:s})'.format(cls_name, repr(self.name), repr(self.type))
        return s


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
    def __init__(self, name, wtype, parent=None):
        self.name = name
        self.parent = None
        self.type = wtype
        self.ports = []
        
        # If a parent system is provided, request its addition as a wire
        if parent is not None:
            parent.add_wire(self)
    
    def is_connect_allowed(self, port, raise_error=False):
        '''check that a connection to a Port `port` is allowed.
        Returns True or False
        
        if `raise_error`, raising an error replaces returning False
        '''
        # Check that the wire and port.system are siblings:
        if self.parent is port.system.parent:
            return True
        else:
            if raise_error:
                raise ValueError('wire and port.system should have a common parent!')
            else:
                return False
                
        # Wire-Port Type checking:
        if not self.type:
            # untyped wire: connection is always possible
            return True
        elif port.type == self.type:
            return True
        else:
            # Incompatible types
            if raise_error:
                raise TypeError("Wire type '{:s}'".format(str(self.type)) + \
                                " and Port type '{:s}'".format(str(port.type)) + \
                                " are not compatible!")
            else:
                return False
    
    def connect_port(self, port):
        '''Connect the Wire to a Port `port`'''
        if port in self.ports:
            return # Port is aleady connected
        # Type checking:
        self.is_connect_allowed(port, raise_error=True)
        # Add parent relationship:
        port.wire = self
        self.ports.append(port)
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        s = '{:s}({:s}, {:s})'.format(cls_name, repr(self.name), repr(self.type))
        return s    


class SignalWire(Wire):
    '''Signal Wire for the interconnection of several Systems
    through their Input and Output Ports.
    
    Each SignalWire can be connected to a unique Output Port (signal source)
    and several Input Ports (signal sinks)
    '''
    def __init__(self, name, wtype='', parent=None):
        super(SignalWire, self).__init__(name, wtype, parent)        
    
    def is_connect_allowed(self, port, raise_error=False):
        '''check that a connection to a Port `port` is allowed.
        Returns True or False
        
        if `raise_error`, raising an error replaces returning False
        '''
        if port.direction not in ['in', 'out']:
            if raise_error:
                raise TypeError('Only Input/Output Port can be connected!')
            else:
                return False
        
        # Now we have an I/O Port for sure:    
        if port.direction == 'out':
            # check that there is not already a signal source
            other_ports = [p for p in self.ports if (p.direction=='out' and
                                                     p is not port)]
            if other_ports:
                if raise_error:
                    raise ValueError('Only one output port can be connected!')
                else:
                    return False

        # Now the I/O aspect is fine. Launch some further checks:        
        return super(SignalWire, self).is_connect_allowed(port, raise_error)
