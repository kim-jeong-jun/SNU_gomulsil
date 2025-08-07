# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 18:15:04 2025

@author: user
"""

"""
        HELLO QUA
A simple sandbox to showcase different QUA functionalities during the installation.
"""
import time
import datetime
from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from qm import QuantumMachinesManager
from galvo_laser_config import *
import matplotlib.pyplot as plt
from qualang_tools.loops import from_array
import numpy as np 

#%%
################### 
# The QUA program #
###################
time = 100 * u.us
cycle = time // 4
wait_cycle = cycle * 2
total_cycle = cycle + wait_cycle

with program() as hello_QUA:
    # a = declare(fixed)
    with infinite_loop_():
            play("laser_ON", "AOM", duration = total_cycle)        
        
        # # # ## Galvo mirror  pulse 0.2V 1Hz
            play("const", "mirror_x", duration = total_cycle) ## Galvo mirror1
            play("const", "mirror_y", duration = total_cycle) ## Galvo mirror2
        
        # wait(wait_cycle, "AOM", "TCSPC")

        
#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

###########################
# Run or Simulate Program #
###########################

simulate = False

if simulate:
    simul_duration = 0.01 * u.s // 4
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=simul_duration)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, hello_QUA, simulation_config)
    # Get the simulated samples
    samples = job.get_simulated_samples()
    # Plot the simulated samples
    fig, ax = plt.subplots()
    ax.plot(samples.con1.analog["1"], label="Analog 1")
    ax.plot(samples.con1.analog["2"], '--', label="Analog 2")
    ax.plot(samples.con1.digital["3"], label="Digital 3")
    ax.plot(samples.con1.digital["4"], label="Digital 4")
    ax.legend()
    ax.set_xlabel("Time [ns]")
    ax.set_ylabel("Output")
    # Get the waveform report object
    # waveform_report = job.get_simulated_waveform_report()
    # Cast the waveform report to a python dictionary
    # waveform_dict = waveform_report.to_dict()
    # Visualize and save the waveform report
    # waveform_report.create_plot(samples, plot=True, save_path=str(Path(__file__).resolve()))
else:
    qm = qmm.open_qm(config)
    job = qm.execute(hello_QUA)
    

    # job.halt()
