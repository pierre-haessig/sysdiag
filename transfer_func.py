#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Compute the tranfer function of a system

based on SymPy for equation handling and solving

Pierre Haessig — September 2013
"""

from __future__ import division, print_function
import sympy
from sympy import symbols, Eq

import blocks

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
        for op, var in zip(syst._operators, input_var):
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

def transfer_syst(syst, input_var=None, depth='unlimited'):
    '''Compute the transfer function of `syst`
    
    Returns `output_expr`, `output_var`
    `output_var` is of length n_out + number of internal sink blocks
    '''
    # Analyze the IO Ports: of `syst`
    in_ports  = [p for p in syst.ports if p.direction=='in']
    out_ports = [p for p in syst.ports if p.direction=='out']
    n_in = len(in_ports)
    n_out = len(out_ports)
    # Initialize the input and output variables
    # (more variables may come from the subsystem analysis)
    if input_var is None:
        input_var = [symbols('U_{}_{}'.format(syst.name, p.name)) for p in in_ports]
    else:
        assert len(input_var) == n_in
    output_var = [symbols('Y_{}_{}'.format(syst.name, p.name)) for p in out_ports]
    
    output_expr = []
    
    if depth==0:
        #output_expr = laplace_output(syst, input_var)
        #return [Eq(var, tf) for var,tf in zip(output_var,output_expr)]
        output_expr = laplace_output(syst, input_var)
        return output_expr, output_var, input_var
    
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
            source_var = symbols('U_' + subsys.name)
            input_var.append(source_var)
            # Output equation: W_out = U
            subsys_eqs.append(Eq(sub_var_out[0], source_var))

        elif isinstance(subsys, blocks.Sink):
            assert len(sub_var_out) == 0
            assert len(sub_var_in) == 1
            sink_var = symbols('Y_' + subsys.name)
            output_var.append(sink_var)
            # Output equation: Y = W_in
            subsys_eqs.append(Eq(sink_var, sub_var_in[0]))
        
        else:
            # Recursive call:
            sub_output_expr, sub_output_var, sub_input_var = transfer_syst(subsys,
                                                    sub_var_in, depth=sub_depth)
            # TODO: manage extraneous output var/expressions
            print(sub_output_var[n_out:])
            # and extraneous input variables
            subsys_eqs.extend([Eq(var, tf) for var,tf in
                               zip(sub_var_out, sub_output_expr)])
    # end for each subsystem
    
    # Add the output port equations
    # TODO...
    #subsys_eqs.append(Eq())
        
    # Solve the equations:
    print(subsys_eqs)
    eqs_sol = sympy.solve(subsys_eqs, wires_var.values() + output_var)
    print(eqs_sol)
    # filter out the wire variables
    output_expr = [eqs_sol[var] for var in eqs_sol if var in output_var]
    
    return output_expr, output_var, input_var
# end transfer_syst


if __name__ == '__main__':
    # Example tranfer function modeling of a closed loop system

    # Main blocks:
    root = blocks.System('top level system')
    src = blocks.Source('src', root)
    K = 2
    Ti = 0.2
    #ctrl = blocks.TransferFunction('controller', [1, K*Ti],[0, Ti], root) # PI control
    ctrl = blocks.SISOSystem('controller', root) # generic controller
    #plant = blocks.TransferFunction('plant', [1], [0, 1], root) # integrator
    plant = blocks.SISOSystem('plant', root) # generic plant
    comp = blocks.Summation('compare', ops = ['+','-'], parent = root)
    out = blocks.Sink('out',parent=root)
    # Connect the blocks together
    w0 = blocks.connect_systems(src, comp, d_pname='in0')
    w1 = blocks.connect_systems(comp, ctrl)
    w2 = blocks.connect_systems(ctrl, plant)
    w3 = blocks.connect_systems(plant, comp, d_pname='in1')
    w4 = blocks.connect_systems(plant, out)

    ### test laplace_output
    u = symbols('u')
    siso = blocks.SISOSystem('SISO')
    print(laplace_output(siso, [u]))
    print(laplace_output(ctrl, [u]))
    
    ### Tranfer function:
    Y_expr,Y,U = transfer_syst(root, depth=1)
    print(Y_expr,Y,U)
    TF = sympy.simplify(Y_expr[0]/U[0])
    print('\nTransfer function:')
    print(TF)
