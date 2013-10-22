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
    #end __init__()

    def is_empty(self):
        '''True if the System contains no subsystems and no wires'''
        return (not self.subsystems) and (not self.wires)

    @property
    def ports_dict(self):
        '''dict of ports, which keys are the names of the ports'''
        return {p.name:p for p in self.ports}

    @property
    def subsystems_dict(self):
        '''dict of subsystems, which keys are the names of the systems'''
        return {s.name:s for s in self.subsystems}

    def add_port(self, port, created_by_system = False):
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
        port._created_by_system = bool(created_by_system)
        self.ports.append(port)

    def del_port(self, port):
        '''delete a Port of the System (and disconnect any connected wire)
        '''
        if (port.wire is not None) or (port.internal_wire is not None):
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

    def __eq__(self, other):
        '''Systems compare equal if their class, `name` and `params` are equal.
        and also their lists of ports and wires are *similar*
        (see `_is_similar` methods of Port and Wire)
        and finally their subsystems recursively compare equal.
        
        parent systems are not compared (would generate infinite recursion).
        '''
        if not isinstance(other, System):
            return NotImplemented
        # Basic similarity
        basic_sim = self.__class__  == other.__class__  and \
                    self.name       == other.name       and \
                    self.params     == other.params
        if not basic_sim:
            return False
        # Port similarity: (sensitive to the order)
        ports_sim = all(p1._is_similar(p2) for (p1,p2)
                        in zip(self.ports, other.ports))
        if not ports_sim:
            return False
        # Wires similarity
        wires_sim = all(w1._is_similar(w2) for (w1,w2)
                        in zip(self.wires, other.wires))
        if not wires_sim:
            return False
        print('equality at level {} is true'.format(self.name))
        # Since everything matches, compare subsystems:
        return self.subsystems == other.subsystems
    # end __eq__()
    
    def __ne__(self,other):
        return not (self==other)

    def _to_json(self):
        '''convert the System instance to a JSON-serializable object
        
        System is serialized with list of ports, subsystems and wires
        but without connectivity information (e.g. no parent information)
        
        ports created at the initialization of the system ("default ports")
        are not serialized.
        '''
        # Filter out ports created at the initialization of the system
        ports_list = [p for p in self.ports if not p._created_by_system]
        cls_name = self.__module__ +'.'+ self.__class__.__name__
        return {'__sysdiagclass__': 'System',
                '__class__': cls_name,
                'name':self.name,
                'subsystems':self.subsystems,
                'wires':self.wires,
                'ports':ports_list,
                'params':self.params
               }
    # end _to_json
    def json_dump(self, output=None, indent=2, sort_keys=True):
        '''dump (e.g. save) the System structure in json format
        
        if `output` is None: return a json string
        if `output` is a writable file: write in this file
        '''
        import json
        if output is None:
            return json.dumps(self, default=to_json, indent=indent, sort_keys=sort_keys)
        else:
            json.dump(self, output, default=to_json, indent=indent, sort_keys=sort_keys)
            return
        # end json_dump

        
class Port(object):
    '''Port enables the connection of a System to a Wire
    
    Each port has a `type` which only allows the connection of a Wire
    of the same type.
    
    it also have a `direction` ('none', 'in', 'out') that is set
    at the class level
    
    private attribute `_created_by_system` tells whether the port was created
    automatically by the system's class at initialization or by a custom code
    (if True, the port is not serialized by its system).
    '''
    direction = 'none'
    
    def __init__(self, name, ptype):
        self.name = name
        self.type = ptype
        self.system = None
        self.wire = None
        self.internal_wire = None
        self._created_by_system = False
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        s = '{:s}({:s}, {:s})'.format(cls_name, repr(self.name), repr(self.type))
        return s
    
    def __str__(self):
        s = repr(self) + ' of ' + repr(self.system)
        return s
    
    def _is_similar(self, other):
        '''Ports are *similar* if their class, `type` and `name`  are equal.

        (their parent system are not compared)
        '''
        if not isinstance(other, Port):
            return NotImplemented
        return self.__class__ == other.__class__ and \
               self.type      == other.type      and \
               self.name      == other.name
    
    def _to_json(self):
        '''convert the Port instance to a JSON-serializable object
        
        Ports are serialized without any connectivity information
        '''
        cls_name = self.__module__ +'.'+ self.__class__.__name__
        return {'__sysdiagclass__': 'Port',
                '__class__': cls_name,
                'name':self.name,
                'type':self.type
               }
    # end _to_json

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
    
    @property
    def ports_by_name(self):
        '''triplet representation of port connections
        (level, port.system.name, port.name)
        
        (used for serialization)
        '''
        def port_triplet(p):
            '''triplet representation (level, port.system.name, port.name)'''
            if p.system is self.parent:
                level = 'parent'
            elif p.system.parent is self.parent:
                level = 'sibling'
            else:
                raise ValueError('The system of Port {}'.format(repr(p)) +\
                                 'is neither a parent nor a sibling!')
            return (level, p.system.name, p.name)

        return [port_triplet(p) for p in self.ports]
    
    def connect_by_name(self, s_name, p_name, level='sibling'):
        '''Connects the ports named `p_name` of system named `s_name`
        to be found at level `level` ('parent' or 'sibling' (default))
        '''
        # TODO (?) merge the notion of level in the name (make parent a reserved name)
        assert level in ['sibling', 'parent']
        # 1) find the system:
        if level == 'parent':
            syst = self.parent
            assert self.parent.name == s_name
        elif level == 'sibling':
            syst = self.parent.subsystems_dict[s_name]
        port = syst.ports_dict[p_name]
        self.connect_port(port, level)

    def __repr__(self):
        cls_name = self.__class__.__name__
        s = '{:s}({:s}, {:s})'.format(cls_name, repr(self.name), repr(self.type))
        return s

    def _is_similar(self, other):
        '''Wires are *similar* if their class, `type` and `name`  are equal
        and if their connectivity (`ports_by_name`) is the same

        (their parent system are not compared)
        '''
        if not isinstance(other, Wire):
            return NotImplemented
        return self.__class__ == other.__class__ and \
               self.type      == other.type      and \
               self.name      == other.name      and \
               self.ports_by_name == other.ports_by_name

    def _to_json(self):
        '''convert the Wire instance to a JSON-serializable object
        
        Wires are serialized with the port connectivity in tuples
        (but parent relationship is not serialized)
        '''
        
        cls_name = self.__module__ +'.'+ self.__class__.__name__
        return {'__sysdiagclass__': 'Wire',
                '__class__': cls_name,
                'name': self.name,
                'type': self.type,
                'ports': self.ports_by_name
               }
    # end _to_json

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
            if level=='detect':
                wire = self
                if wire.parent == port.system:
                    level = 'parent'
                elif wire.parent == port.system.parent:
                    level = 'sibling'
                else:
                    raise ValueError('Port is neither sibling nor parent')
            is_out = (level=='sibling' and port.direction == 'out') or \
                     (level=='parent'  and port.direction == 'in')
            return is_out
        
        # Now we have an I/O Port for sure:    
        if is_output(port, port_level):
            # check that there is not already a signal source
            other_ports = [p for p in self.ports if (is_output(p, 'detect')
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

def to_json(py_obj):
    '''convert `py_obj` to JSON-serializable objects
    
    `py_obj` should be an instance of `System`, `Wire` or `Port`
    '''
    if isinstance(py_obj, System):
        return py_obj._to_json()
    if isinstance(py_obj, Wire):
        return py_obj._to_json()
    if isinstance(py_obj, Port):
        return py_obj._to_json()
        
    raise TypeError(repr(py_obj) + ' is not JSON serializable')
# end to_json

import sys
def _str_to_class(mod_class):
    '''retreives the class from a "module.class" string'''
    mod_name, cls_name = mod_class.split('.')
    mod = sys.modules[mod_name]
    return getattr(mod, cls_name)

def from_json(json_object):
    '''deserializes a sysdiag json object'''
    if '__sysdiagclass__' in json_object:
        cls = _str_to_class(json_object['__class__'])

        if json_object['__sysdiagclass__'] == 'Port':
            port = cls(name = json_object['name'], ptype = json_object['type'])
            return port

        if json_object['__sysdiagclass__'] == 'System':
            # TODO: specialize the instanciation for each class using
            # _from_json class methods
            syst = cls(name = json_object['name'])
            syst.params = json_object['params']
            # add ports if any:
            for p in json_object['ports']:
                syst.add_port(p)
            # add subsystems
            for s in json_object['subsystems']:
                syst.add_subsystem(s)
            # add wires
            for w_dict in json_object['wires']:
                # 1) decode the wire:
                w_cls = _str_to_class(w_dict['__class__'])
                w = w_cls(name = w_dict['name'], wtype = w_dict['type'])
                syst.add_wire(w)
                # make the connections:
                for level, s_name, p_name in w_dict['ports']:
                    w.connect_by_name(s_name, p_name, level)
            # end for each wire
            return syst

    return json_object

def json_load(json_dump):
    import json
    syst = json.loads(json_dump, object_hook=from_json)
    return syst
