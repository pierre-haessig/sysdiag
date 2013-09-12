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
        self.subsystems = {}
        self.ports = {}
        self.params = {}
        
    def add_port(self, port):
        '''add a Port to the System'''
        # extract the port's name
        name = port.name
        if name in self.ports:
            raise ValueError("port name '{}' already exists in {:s}!".format(
                              name, repr(self))
                             )
        # Add parent relationship and add to the ports dict:
        port.system = self
        self.ports[name] = port
    
    def add_subsystem(self, subsys):
        name = subsys.name
        if name in self.subsystems:
            raise ValueError("system name '{}' already exists in {:s}!".format(
                              name, repr(self))
                             )
        # Add parent relationship and add to the ports dict:
        subsys.parent = self
        self.subsystems[name] = subsys
            
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
    def __init__(self, name, ptype):
        self.name = name
        self.type = ptype
        self.system = None
    
    
class Wire(object):
    '''Wire enables the interconnection of several Systems
    through their Ports'''
    def __init__(self, name, wtype):
        self.name = name
        self.type = wtype
        self.system = None
