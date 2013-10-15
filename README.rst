=======
SysDiag
=======

This module enables representing *System diagrams* as Python *objects* in order to *manipulate* these diagrams, either in a Python script or interactively in a Python shell (e.g. IPython).

The module, still in early development phase, is open source (MIT license) with its source code available on https://github.com/pierre-haessig/sysdiag.

Application domains
-------------------

The definition of "System diagrams" is meant to be general enough to include different types of diagrams being used in various fields of application. Here are examples in the scope of the project:

* **block diagrams** (used in signal processing and control engineering)
* **electrical circuits** (lumped RLC elements connected with wires)
* **mechanical systems** (represented with lumped elements like masses, springs and dampings)
* **EMR diagrams** (Energetic Macroscopic Representation http://www.emrwebsite.org/)

Other diagrams that may be in the scope of the project but that haven't been investigated thoroughly enough:

* bond graphs
* compartment models (used in epidemiology, ...)

Library Design
--------------

This module defines *3 main categories* of objects (i.e. Python classes):

* `System` which can be either an "atomic" system
  or contain nested sub-systems. A System instance may have
  
  * ports, to connect with the "outside"
  * parameters (for example a resistance value, the coefficients of a Laplace transfer function)
  * subsystems, and wires to connect them.
  
* `Port` which represents the interface of a `System` with the "outside".
  Each system can have several ports
* `Wire` which connects together several ports from several systems.

Those classes can be subclassed to created specialized objects. For example a Voltage source or a Summation block are special kinds of Systems.

An important functionality of the module is the support for *hierarchically-defined* systems, that is systems defined by the interconnection of subsystems, which are themselves composed of subsystems, etc...

Possible manipulations on a system diagram
------------------------------------------

* **load and save** a diagram from a text-based file format (json format)
* **compute a model** of the diagram. Modeling examples in scope of the project:
  
  * Laplace transfer function of a block diagram, for example a closed-loop control of a dynamical system (this applies to a linear system described with a block diagram)
  * state-space model of an electrical circuit, of a mechanical system