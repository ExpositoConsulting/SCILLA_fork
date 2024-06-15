#!/usr/bin/env python 

# Multi-step workflow for 4-local coupler search

import numpy as np
import time
import subprocess
import pickle

from circuit_searcher import CircuitSearcher

def generate_spice_netlist(c_specs, j_specs, l_specs, phiOffs_specs):
    netlist = "* SPICE Netlist for JoSIM\n"
    
    # Dynamically add capacitors based on c_specs
    for i in range(c_specs['dimension']):
        netlist += f"C{i+1} 0 {i+1} {np.random.uniform(c_specs['low'], c_specs['high']):.2f}pF\n"

    # Dynamically add Josephson junctions based on j_specs and include phase offsets
    for i in range(j_specs['dimension']):
        phase_offset = phiOffs_specs['values'][i % len(phiOffs_specs['values'])]  # loop over if fewer phases than junctions
        netlist += f"JJ{i+1} {i+1} 0 type=JJ model='JJMODEL' icrit={np.random.uniform(j_specs['low'], j_specs['high']):.2f}uA PHI={phase_offset}\n"

    # Dynamically add inductors based on l_specs
    for i in range(l_specs['dimension']):
        netlist += f"L{i+1} {i+1} 0 {np.random.uniform(l_specs['low'], l_specs['high']):.2f}nH\n"

    netlist += ".tran 0.1ns 100ns\n"  # Define the simulation type and duration
    netlist += ".end\n"
    return netlist

def run_josim(netlist_content, output_file="josim_output.csv"):
    # Write the netlist to a file
    netlist_path = "current_netlist.cir"
    with open(netlist_path, 'w') as file:
        file.write(netlist_content)
    
    try:
        # Execute the JoSIM command
        subprocess.run(['josim-cli', netlist_path, '-o', output_file], check=True)
        print(f"Simulation completed successfully, results saved to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the simulation: {e}")

if __name__ == '__main__':
    # Set parameters and run the inverse design algorithm
    c_specs = {'dimension': 6, 'low': 1., 'high': 100., 'keep_prob': 0.5}
    j_specs = {'dimension': 6, 'low': 99., 'high': 1982., 'keep_num': 3}
    l_specs = {'dimension': 6, 'low': 75., 'high': 300., 'keep_prob': 0.5}
    phiOffs_specs = {'dimension': 4, 'values': [0.0, 0.5]}
    circuit_params = {'c_specs': c_specs, 'j_specs': j_specs, 'l_specs': l_specs, 'phiOffs_specs': phiOffs_specs}
    general_params = {'solver': 'JoSIM', 'phiExt': None, 'target_spectrum': None}

    # Loss function settings
    dw_options = {'max_peak': 1.5, 'max_split': 10, 'norm_p': 4, 'flux_sens': True, 'max_merit': 100}

    # Initialize circuit searcher
    circuit_searcher = CircuitSearcher(circuit_params, general_params, database_path='Experiments')

    # Set up and run tasks
    mc_options = {'max_iters': 3, 'max_concurrent': 2, 'batch_size': 10}
    computing_task_0 = circuit_searcher.add_task(name='random_search', designer='random', designer_options=mc_options, merit='DoubleWell', merit_options=dw_options)
    filtering_task_0 = circuit_searcher.add_task(name='filtering', designer='filter_db', designer_options={'num_circuits': 2})
    swarm_options = {'max_iters': 2, 'max_concurrent': 2, 'n_particles': 2}
    computing_task_2 = circuit_searcher.add_task(name='swarm_search', designer='particle_swarms', designer_options=swarm_options, merit='DoubleWell', merit_options=dw_options)

    # Generate the SPICE netlist
    netlist = generate_spice_netlist(c_specs, j_specs, l_specs, phiOffs_specs)

    # Run the simulation with JoSIM
    run_josim(netlist)

    # Continue with optimization and other tasks
    tic_glob = time.time()
    circuit_searcher.execute()
    print('#### TOTAL TIME: {} s ####'.format(time.time() - tic_glob))
