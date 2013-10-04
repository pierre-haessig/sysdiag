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
    base = str(base).strip()
    if base == '':
        # avoid having '' as name (although it would not break the code...)
        raise ValueError('base name should not be empty!')
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
        if port in self.ports:
            raise ValueError('port already added!')
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
        self.internal_wire = None
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        s = '{:s}({:s}, {:s})'.format(cls_name, repr(self.name), repr(self.type))
        return s
    
    def __str__(self):
        s = repr(self) + ' of ' + repr(self.system)
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
    
    def is_connect_allowed(self, port, port_level, raise_error=False):
        '''Check that a connection between Wire ̀ self` and a Port `port` is allowed.
        
        Parameters
        ----------
        
        `port`: the Port instance to connect to
        `port_level`: whether `port` belongs to a 'sibling' (usual case) or a
                      'parent' system (to enable connections to the upper level)
        `raise_error`: if True, raising an error replaces returning False
        
        Returns
        -------
        allowed: True or False
        '''
        assert port_level in ['sibling', 'parent']
        
        # Port availability (is there already a wire connected?):
        if port_level == 'sibling':
            connected_wire = port.wire
        elif port_level == 'parent':
            connected_wire = port.internal_wire
        if connected_wire is not None:
            if raise_error:
                    raise ValueError('port is already connected to '+\
                                     '{:s}!'.format(repr(connected_wire)))
            else:
                return False

        # Check parent relationship:
        if port_level == 'sibling':
            # Check that the wire and port.system are siblings:
            if self.parent is not port.system.parent:
                if raise_error:
                    raise ValueError('wire and port.system should have a common parent!')
                else:
                    return False
        elif port_level == 'parent':
            # Check that the port.system is the parent of the wire:
            if self.parent is not port.system:
                if raise_error:
                    raise ValueError('port.system should be the parent of the wire!')
                else:
                    return False

        # Wire-Port Type checking:
        if self.type == '':
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
    
    def connect_port(self, port, port_level='sibling'):
        '''Connect the Wire to a Port `port`'''
        if port in self.ports:
            return # Port is aleady connected
        # Type checking:
        self.is_connect_allowed(port, port_level, raise_error=True)
        
        # Add parent relationship:
        assert port_level in ['sibling', 'parent']
        if port_level=='sibling':
            port.wire = self
        elif port_level == 'parent':
            port.internal_wire = self
        # Book keeping of ports:
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
    
    def is_connect_allowed(self, port, port_level, raise_error=False):
        '''Check that a connection between SignalWire ̀ self` and a Port `port`
        is allowed.
        
        Parameters
        ----------
        
        `port`: the Port instance to connect to
        `port_level`: whether `port` belongs to a 'sibling' (usual case) or a
                      'parent' system (to enable connections to the upper level)
        `raise_error`: if True, raising an error replaces returning False
        
        Returns
        -------
        allowed: True or False
        '''
        if port.direction not in ['in', 'out']:
            if raise_error:
                raise TypeError('Only Input/Output Port can be connected!')
            else:
                return False
        
        def is_output(port, level):
            '''an output port is either:
               * a sibling system'port with direction == 'out' or
               * a parent system'port with direction == 'in'
            '''
            is_out = (level=='sibling' and port.direction == 'out') or \
                     (level=='parent'  and port.direction == 'in')
            return is_out
        
        # Now we have an I/O Port for sure:    
        if is_output(port, port_level):
            # check that there is not already a signal source
            other_ports = [p for p in self.ports if (is_output(p, port_level)
                                                     and p is not port)]
            if other_ports:
                if raise_error:
                    raise ValueError('Only one output port can be connected!')
                else:
                    return False

        # Now the I/O aspect is fine. Launch some further checks:
        return super(SignalWire, self).is_connect_allowed(port, port_level, raise_error)


def connect_systems(source, dest, s_pname, d_pname, wire_cls=Wire):
    '''Connect systems `source` to `dest` using
    port names `s_pname` and `d_pname`
    with a wire of instance `wire_cls` (defaults to Wire)
    
    The wire is created if necessary
    
    Returns: the wire used for the connection
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
        w = wire_cls(wname, wtype, parent)
    
    # 3) Make the connection:
    w.connect_port(s_port)
    w.connect_port(d_port)
    return w
