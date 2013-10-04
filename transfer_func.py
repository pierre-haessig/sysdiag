#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Compute the tranfer function of a system

based on SymPy for equation handling and solving

Pierre Haessig — September 2013
"""

from __future__ import division, print_function
import sympy
from sympy import symbols, Eq, simplify

import blocks

from closed_loop_control import root as r

def laplace_output(syst, input_var):
    '''Laplace tranform of the output of the block `syst`.
    
    The list of input variables should match the list of input ports.
    '''
    in_ports  = [p for p in syst.ports if p.direction=='in']
    out_ports = [p for p in syst.ports if p.direction=='out']
    n_in = len(in_ports)
    n_out = len(out_ports)
    assert len(input_var) == n_in

    ### Model the system of the block
    output_expr = []
    
    # 1) Model a Summation block:
    if type(syst) is blocks.Summation:
        sum_terms = []
        for op, var in zip(s._op, input_var):
            if op == '+':
                sum_terms.append(+var)
            elif op == '-':
                sum_terms.append(-var)
            else:
                raise ValueError('unknow operator')
        # end for
        output_expr.append(sympy.Add(*sum_terms))

    # 2) Model a TransferFunction block:
    elif type(syst) is blocks.TransferFunction:
        assert n_in == 1
        num = syst.params['num']
        den = syst.params['den']
        # Convert to Laplace:
        s = symbols('s')
        num_s = [n*s**i for i,n in enumerate(num)]
        den_s = [d*s**i for i,d in enumerate(den)]
        TF = sympy.Add(*num_s)/sympy.Add(*den_s)
        output_expr.append(TF*input_var[0])

    # Model a generic IO block:
    else:
        for p_out in out_ports:
            out = 0
            for p_in, var in zip(in_ports, input_var):
                # Generate a symbol with an *hopefully* unique name:
                TF_name = 'TF_{}'.format(syst.name)
                if n_in > 1 or n_out>1:
                    TF_name += '{}_{}'.format(p_in.name, p_out.name)
                TF = symbols(TF_name)
                out += TF*var
            output_expr.append(out)
            # end for each input
        # end for each ouput

    return output_expr
# end laplace_output

### test laplace_output
u = symbols('u')
siso = blocks.SISOSystem('SISO')
print(laplace_output(siso, [u]))
ctrl = r.subsystems[1]
print(laplace_output(ctrl, [u]))



def transfer_syst(syst, depth='unlimited'):
    '''Compute the transfer function of `syst`'''
    # Analyze the IO Ports: of `syst`
    in_ports  = [p for p in syst.ports if p.direction=='in']
    out_ports = [p for p in syst.ports if p.direction=='out']
    n_in = len(in_ports)
    n_out = len(out_ports)
    # Initialize the input and output variables
    # (more variables may come from the subsystem analysis)
    input_var = [symbols('U_{}_{}'.format(syst.name, p.name)) for p in in_ports]
    output_var = [symbols('Y_{}_{}'.format(syst.name, p.name)) for p in out_ports]
    
    if depth==0:
        output_expr = laplace_output(syst, input_var)
        return [Eq(var, tf) for var,tf in zip(output_var,output_expr)]
    
    # else depth>0: analyse the subsystems
    
    # 1) Generate wire variables: (those to be eliminated)
    wires_var = {w:symbols('W_' + w.name) for w in syst.wires}
    
    # 2) Parse the subsystems
    subsys_eqs = []
    for subsys in syst.subsystems:
        sub_depth = 'unlimited' if depth=='unlimited' \
                                else (depth - 1)
        # Input and Output Wires
        sub_wire_in  = [p.wire for p in subsys.ports if p.direction=='in']
        sub_wire_out = [p.wire for p in subsys.ports if p.direction=='out']
        # retreive the SymPy variables of the wires:
        sub_var_in = [wires_var[w] for w in sub_wire_in]
        sub_var_out = [wires_var[w] for w in sub_wire_out]
        
        # Manage the different blocks
        if isinstance(subsys, blocks.Source):
            # Source block
            assert len(sub_var_in) == 0
            assert len(sub_var_out) == 1
            source_var = symbols('U_' + s.name)
            input_var.append(source_var)
            # Output equation: W_out = U
            subsys_eqs.append(Eq(sub_var_out[0], source_var))

        elif isinstance(subsys, blocks.Sink):
            assert len(sub_var_out) == 0
            assert len(sub_var_in) == 1
            sink_var = symbols('Y_' + s.name)
            output_var.append(sink_var)
            # Output equation: Y = W_in
            print(sink_var, sub_wire_in[0])
            subsys_eqs.append(Eq(sink_var, sub_var_in[0]))

#        elif type(s) is blocks.TransferFunction:
#            TF_s = symbols('H_' + s.name)
#            TF[s] = TF_s
#            assert len(w_in) == 1
#            Out_s = TF_s * w_in[0]
        
        elif sub_depth == 0:
            output_expr = laplace_output(subsys, sub_wire_in)
            subsys_eqs.extend([Eq(var, tf) for var,tf in zip(sub_wire_out, output_expr)])
        else:
            # Recursive call:
            output_eq = transfer_syst(subsys, depth=sub_depth)
            # TODO: connect the ports variables to the equation
            # or indicate the output equation

    # end for each subsystem
    return subsys_eqs

In  = []
Out = []
W = {} # wires
TF = {}

diagram_eqs = []

def wires_to_sym(w):
    if w not in W:
        # Add wire w to the dict W:
        W[w] = symbols('W_' + w.name)
    return W[w]

for s in r.subsystems:
    print(s)
    
    # Output Wires
    w_out = [p.wire for p in s.ports if p.direction=='out']
    if len(w_out) == 0:
        w_out = None
    else:
        assert len(w_out) == 1
        w_out = w_out[0]
        # Convert Wires to SymPy symbols
        w_out = wires_to_sym(w_out)
    
    # Input Wires
    w_in  = [p.wire for p in s.ports if p.direction=='in']
    # Convert Wires to SymPy symbols
    w_in  = [wires_to_sym(w) for w in w_in]
    
    # Manage the different blocks
    if not w_in:
        # Source block
        assert type(s) is blocks.Source
        In_s = symbols('U_' + s.name)
        In.append(In_s)
        # Output equation:
        Out_s = In_s
    
    elif type(s) is blocks.Summation:
        sum_terms = []
        for op, w in zip(s._op, w_in):
            if op == '+':
                sum_terms.append(+w)
            elif op == '-':
                sum_terms.append(-w)
            else:
                raise ValueError('unknow operator')
        
        Out_s = sympy.Add(*sum_terms)
    elif type(s) is blocks.TransferFunction:
        TF_s = symbols('H_' + s.name)
        TF[s] = TF_s
        assert len(w_in) == 1
        Out_s = TF_s * w_in[0]
    elif type(s) is blocks.Sink:
        assert w_out is None
        assert len(w_in) == 1
        Out_s = symbols('Y_' + s.name)
        Out.append(Out_s)
        diagram_eqs.append(Eq(Out_s, w_in[0]))
    else:
        raise ValueError('unknown block!')
    
    # Store IO equation:
    if w_out is not None:
        diagram_eqs.append(Eq(w_out, Out_s))
    
print('\nDiagram Equations:')
print(diagram_eqs)

sol = sympy.solve(diagram_eqs, W.values()+ Out)

#out = W[r.wires[3]]
out = Out[0]

Out_TF = sympy.simplify(sol[out]/In[0]) # TODO : define simplification so that it yields a nice fraction
print('\nTransfer function:')
print(Out_TF)

### Apply a PI controller:

Hp, Hc = TF.values()

s = symbols('s')
tau, K, Ti = symbols('tau K T_i')

H = Out_TF.subs(Hp, 1/(1+tau*s)).subs(Hc, K+Ti/s)
print('\n1st order plant with a PI controller')
print(simplify(H))
