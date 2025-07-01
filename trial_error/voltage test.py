# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 18:15:04 2025

@author: user
"""

"""
        Voltage attenuation test operation
"""

import time
import datetime
from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from qm import QuantumMachinesManager
from configuration_class import *
import matplotlib.pyplot as plt
from qualang_tools.loops import from_array
import numpy as np 

#%%
################### 
# The QUA program #
###################
simulate = False
test = False
prog_test2 = False
prog_trace = True

readout_array_length = int(meas_len_1/(slice_size*4))

# %%
N = 100_000

with program() as hello_QUA:
    i = declare(int, 0)
    n = declare(int, 0)
    Iarr = declare(fixed,size=readout_array_length)
    Iarr_st = declare_stream()
    n_st = declare_stream()
    # a = declare(fixed)
        
    with while_(n < N):
        # play(amp(1.0)*"cw", "RF3", duration=microwave_cycle)
        # wait(microwave_cycle, "SPCM1","AOM")

        measure("readout", "SPCM1", 
                integration.sliced("integ_weights_cos", Iarr, slice_size))
        # wait(5000, "AOM")
        # play("laser_ON", "AOM", duration=laser_cycle) ## AOM 
        
        with for_(i, 0, i < readout_array_length, i + 1) :
            save(Iarr[i], Iarr_st)    
        
        # wait(wait_cycle, "AOM")
        
            # play(amp(1.0)*"cw", "RF3", duration=microwave_cycle) #20us
            
            # wait(microwave_cycle, "AOM", "SPCM1")
            # wait(4, "AOM") 
            # play("laser_ON", "AOM", duration=laser_cycle) ## AOM 200us
            # measure("readout", "SPCM1", 
            #         integration.full("constant", valA))
            # # ABmeasureinterval = 100000
            # wait(time_AB, "SPCM1")
            # measure("readout", "SPCM1", 
            #         integration.full("constant", valB))  
        
        save(n, n_st)
        assign(n, n+1)
        
    with stream_processing():
        #Iarr_st.buffer(readout_array_length).average().save('Iarr')
        Iarr_st.buffer(readout_array_length).save("Iarr")
        n_st.save("iteration")
        


#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

###########################
# Run or Simulate Program #
###########################
get_ipython().run_line_magic('matplotlib', 'qt')
now = datetime.datetime.now()
formattedDate = now.strftime("%Y%m%d_%H%M%S")
trange = np.linspace(0, meas_len_1, readout_array_length)
if simulate:
    # simul_duration = 0.01 * u.s // 4
    simul_duration = 300 * u.s // 4
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=simul_duration)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, CW_ODMR, simulation_config)
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
else:
    qm = qmm.open_qm(config)
    qmm.clear_all_job_results()
    if test == True:
        job = qm.execute(Test_prog)
    elif prog_trace == True:
        job = qm.execute(hello_QUA)
    
        res_handles = job.result_handles
        fetching_mode = "live"
        results = fetching_tool(job, data_list=["Iarr", "iteration"], mode=fetching_mode)

        fig, ax = plt.subplots(figsize=(8,5))

        interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
        while results.is_processing():
            Iarr, iteration = results.fetch_all()

            progress_counter(iteration, N, start_time=results.get_start_time())
            
            try: cbar.remove()
            except: pass
            plt.cla()
            ax.plot(trange, Iarr)
            ax.ticklabel_format(useOffset=False)
            ax.set_xlabel('Time(ns)')
            ax.set_ylabel('Signal')
            ax.set_title(f'{formattedDate}')
            ax.set_ylim(0, 1)
            plt.show()
                
            plt.pause(1)
            
    # elif prog_freq_sweep == True:
    #     job = qm.execute(CW_ODMR)
    
    #     res_handles = job.result_handles
    #     fetching_mode = "live"
        
    #     #results = fetching_tool(job, data_list=["deltaAB", "iteration"], mode=fetching_mode)
    #     results = fetching_tool(job, data_list=["A", "B", "deltaAB","iteration"], mode=fetching_mode)

    #     fig, ax = plt.subplots(1,2,figsize=(16,5))
    #     interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
        
    #     while results.is_processing():
    #         #deltaAB, iteration = results.fetch_all()
    #         A, B, deltaAB, iteration = results.fetch_all()

    #         print(deltaAB)
    #         progress_counter(iteration, N, start_time=results.get_start_time())
            
    #         try: cbar.remove()
    #         except: pass
    #         ax[0].cla()
    #         ax[1].cla()
    #         ax[0].plot(pulse_freq/1e6, deltaAB, "o-")
    #         ax[1].plot(pulse_freq/1e6, A, "o-", label="A")
    #         ax[1].plot(pulse_freq/1e6, B, "o-", label="B")
    #         ax[0].ticklabel_format(useOffset=False)
    #         ax[0].set_xlabel('frequency(MHZ)')
    #         ax[0].set_ylabel('Signal')
    #         ax[1].ticklabel_format(useOffset=False)
    #         ax[1].set_xlabel('frequency(MHZ)')
    #         ax[1].set_ylabel('Signal')
    #         ax[0].set_title(f'B-A, {formattedDate}')
    #         ax[1].set_title(f'B and A, {formattedDate}')
            
            
            
    #         ax[1].legend()
    #         plt.show()
                
    #         plt.pause(1)
    # elif prog_test2 == True:
    #     job = qm.execute(test2)
    
    #     res_handles = job.result_handles
    #     fetching_mode = "live"
    #     results = fetching_tool(job, data_list=["deltaAB", "iteration"], mode=fetching_mode)
    #     fig, ax = plt.subplots(figsize=(8,5))
    #     interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
        
    #     while results.is_processing():
    #         deltaAB, iteration = results.fetch_all()
    #         progress_counter(iteration, N, start_time=results.get_start_time())
            
    #         try: cbar.remove()
    #         except: pass
    #         plt.cla()
    #         ax.plot(pulse_freq/1e6, deltaAB, "o-")
    #         ax.ticklabel_format(useOffset=False)
    #         ax.set_xlabel('frequency(MHZ)')
    #         ax.set_ylabel('Signal')
                    
    #         ax.set_title(f'{formattedDate}')
    #         plt.show()
                
    #         plt.pause(1)

    job.halt()
