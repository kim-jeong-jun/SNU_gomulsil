# -*- coding: utf-8 -*-
"""
Created on Thu May 15 16:07:40 2025

@author: user
"""

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
prog_trace = False
prog_freq_sweep = False
piezo_test_bool = True

microwave_cycle = 20 * u.us //4 # 40* u.us // 4
laser_cycle = 2 * u.us // 4
wait_cycle = 100 * u.us // 4
piezo_cycle = 10 * u.us // 4
Eulmana = 1 * u.us // 4
total_cycle = laser_cycle + wait_cycle
readout_array_length = int(meas_len_1/(slice_size*4)) # Length of the rf trace array (Iarr)
numspl = 1001
pulse_freq = np.linspace(20, 120 , numspl) * u.MHz
# tsweep = np.arange(20, 5000+20/2, 20) //4
# pulse_freq = np.array([70e6])
tsweep = np.array([microwave_cycle])
tlen = len(tsweep)
# %%
N = 100_000

with program() as hello_QUA:
    i = declare(int, 0)
    n = declare(int, 0)
    Iarr = declare(fixed,size=readout_array_length)
    Iarr_st = declare_stream()
    n_st = declare_stream()
        
    with while_(n < N):
        play(amp(1.0)*"cw", "RF3", duration=microwave_cycle)
        wait(microwave_cycle, "SPCM1", "AOM")
        measure("readout", "SPCM1", 
                integration.sliced("integ_weights_cos", Iarr, slice_size))


        wait(250, "AOM")

        play("laser_ON", "AOM", duration=laser_cycle) ## AOM 
        
        with for_(i, 0, i < readout_array_length, i + 1) :
            save(Iarr[i], Iarr_st)    
        
        wait(wait_cycle, "AOM")
        
        save(n, n_st)
        assign(n, n+1)
        
    with stream_processing():
        Iarr_st.buffer(readout_array_length).average().save('Iarr')
        n_st.save("iteration")
        
with program() as piezo_test: # edited from laser_ON AOM

    n = declare(int, 0)

    n_st = declare_stream()
        
    with while_(n < N):
        for i in [0, 0.1, 0.2, 0.3, 0.4, 0.3, 0.2, 0.1]:
            play("laser_ON", "AOM", duration=piezo_cycle) ## AOM 
            wait(piezo_cycle, "AOM")
            
        save(n, n_st)
        assign(n, n+1)
        
        
with program() as Test_prog:
    i = declare(int, 0)
    n = declare(int, 0)
    Iarr = declare(fixed,size=readout_array_length)
    Iarr_st = declare_stream()
    n_st = declare_stream()
    # a = declare(fixed)
    
    with infinite_loop_():
        play("laser_ON", "AOM", duration=laser_cycle) ## AOM 
        # play("cw", "RF3", duration = cycle)
        wait(wait_cycle, "AOM", "TCSPC")


with program() as helpme_QUA:
    
    i = declare(int, 0)
    n = declare(int, 0)
    valA = declare(fixed)
    valB = declare(fixed)
    A = declare(fixed)
    B = declare(fixed)
    deltaAB = declare(fixed)
    n_st = declare_stream()
    deltaAB_st = declare_stream()
    A_st = declare_stream()
    B_st = declare_stream()
    f = declare(int)
    t = declare(int)

    with while_(n < N):
        with for_(*from_array(f, pulse_freq)):
            with for_(*from_array(t, tsweep)):
                update_frequency("RF3", f)
                reset_if_phase("RF3")
                play(amp(1.0)*"cw", "RF3", duration=t) #20us
                
                wait(t, "AOM", "SPCM1")
                wait(4, "AOM")
                measure("readout", "SPCM1", 
                        integration.full("constant", valA))
                play("laser_ON", "AOM", duration=laser_cycle) ## AOM 200us
                # ABmeasureinterval = 100000
                wait(125, "SPCM1")
                measure("readout", "SPCM1", 
                        integration.full("constant", valB))  
                
                assign(deltaAB, valB-valA)
                assign(A, valA)
                assign(B, valB)
                
                wait(wait_cycle, "SPCM1")
                
                save(deltaAB, deltaAB_st)
        save(n, n_st)
        assign(n, n+1)
            
    with stream_processing():
        deltaAB_st.buffer(numspl, tlen).average().save('deltaAB')
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
formattedDate = now.strftime("%Y%m%d_%H_%M_%S")
trange = np.linspace(0, meas_len_1, readout_array_length)
if simulate:
    # simul_duration = 0.01 * u.s // 4
    simul_duration = 300 * u.s // 4
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=simul_duration)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, helpme_QUA, simulation_config)
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
            plt.show()
                
            plt.pause(1)
            
        get_ipython().run_line_magic('matplotlib', 'inline')
        ax.plot(trange, Iarr)
        ax.ticklabel_format(useOffset=False)
        ax.set_xlabel('Time(ns)')
        ax.set_ylabel('Signal')
        ax.set_title(f'{formattedDate}')
        plt.show()
            
    elif prog_freq_sweep == True:
        job = qm.execute(helpme_QUA)
    
        res_handles = job.result_handles
        fetching_mode = "live"
        results = fetching_tool(job, data_list=["deltaAB", "iteration"], mode=fetching_mode)
        fig, ax = plt.subplots(figsize=(8,5))
        interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
        
        while results.is_processing():
            deltaAB, iteration = results.fetch_all()
            progress_counter(iteration, N, start_time=results.get_start_time())
            
            x, y = np.meshgrid(tsweep*4, pulse_freq)
            try: cbar.remove()
            except: pass
            plt.cla()
            if numspl > 1 and tlen > 1:
                pc = ax.pcolor(x, y, deltaAB)
                cbar = plt.colorbar(mappable=pc, ax=ax)
            elif numspl == 1:
                ax.plot(tsweep*4, np.squeeze(deltaAB), "o-")
            else:
                ax.plot(pulse_freq, np.squeeze(deltaAB), "o-")
            ax.ticklabel_format(useOffset=False)
            # ax.set_xlabel('frequency(MHZ)')
            ax.set_ylabel('Signal')
                    
            ax.set_xlabel('time (ns)')
            ax.set_ylabel('Frequency')
                    
            ax.set_title(f'{formattedDate}')
            plt.show()
                
            plt.pause(1)
    elif piezo_test_bool == True:
        job = qm.execute(piezo_test)
        
    job.halt()
