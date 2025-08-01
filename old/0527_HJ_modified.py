# -*- coding: utf-8 -*-
"""
Created on Tue May 27 13:43:20 2025

@author: user
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
prog_test2 = True
prog_trace = False
prog_freq_sweep = False
microwave_cycle = 50 * u.us //4 #50 * u.us // 4
laser_cycle = 400 * u.us // 4 #600 * u.us // 4 
wait_cycle = 100 * u.us // 4
total_cycle = laser_cycle + wait_cycle
readout_array_length = int(meas_len_1/(slice_size*4)) # Length of the rf trace array (Iarr)
numspl = 1001 # number of freqs
pulse_freq = np.linspace(20, 120 , numspl) * u.MHz
time_AB = 400 * u.us // 4 # 400 1.4 * u.us // 4 # time between A and B
# %%
#frequency sweep

# %%
N = 1_000_000


with program() as hello_QUA_HJ:
    i = declare(int, 0)
    n = declare(int, 0)
    Iarr = declare(fixed,size=readout_array_length)
    Iarr_st = declare_stream()
    n_st = declare_stream()
    # a = declare(fixed)
        
    with while_(n < N):
        play(amp(0.0)*"cw", "RF3", duration=microwave_cycle)
        wait(microwave_cycle+25_000, "SPCM1","AOM")

        measure("readout", "SPCM1", 
                integration.sliced("integ_weights_cos", Iarr, slice_size))
        wait(25_000, "AOM")
        play("laser_ON", "AOM", duration=laser_cycle) ## AOM 
        
        with for_(i, 0, i < readout_array_length, i + 1) :
            save(Iarr[i], Iarr_st)    
        
        wait(wait_cycle, "AOM")
        

        save(n, n_st)
        assign(n, n+1)
        
    with stream_processing():
        Iarr_st.buffer(readout_array_length).average().save('Iarr')
        n_st.save("iteration")

with program() as hello_QUA:
    i = declare(int, 0)
    n = declare(int, 0)
    Iarr = declare(fixed,size=readout_array_length)
    Iarr_st = declare_stream()
    n_st = declare_stream()
    # a = declare(fixed)
    
        
    with while_(n < N):
        play("laser_ON", "AOM", duration=laser_cycle) #CW 10 ms

        play(amp(1.0)*"cw", "RF3", duration=microwave_cycle)        
        wait(25, "SPCM1") #100ns
        measure("readout", "SPCM1", 
                integration.sliced("integ_weights_cos", Iarr, slice_size))
        wait(25000, "SPCM1") #100 us

#         play(amp(1.0)*"cw", "RF3", duration=microwave_cycle)        
#         wait(25, "SPCM1")
#         measure("readout", "SPCM1", 
#                 integration.sliced("integ_weights_cos", Iarr, slice_size))
#         wait(25000, "SPCM1")
        
#         play(amp(1.0)*"cw", "RF3", duration=microwave_cycle)        
#         wait(25, "SPCM1")
#         measure("readout", "SPCM1", 
#                 integration.sliced("integ_weights_cos", Iarr, slice_size))
#         wait(25000, "SPCM1")

#         play(amp(1.0)*"cw", "RF3", duration=microwave_cycle)        
#         wait(25, "SPCM1")
#         measure("readout", "SPCM1", 
#                 integration.sliced("integ_weights_cos", Iarr, slice_size))
#         wait(25000, "SPCM1")

# #        wait(microwave_cycle, "SPCM1","AOM")

        
#         with for_(i, 0, i < readout_array_length, i + 1) :
#             save(Iarr[i], Iarr_st)    
        
#         wait(wait_cycle, "AOM")
        
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
        
        with for_(i, 0, i < readout_array_length, i + 1) :
            save(Iarr[i], Iarr_st)    
        
        wait(wait_cycle, "AOM")
        
        
        save(n, n_st)
        assign(n, n+1)
        
    with stream_processing():
        Iarr_st.buffer(readout_array_length).average().save('Iarr')
        n_st.save("iteration")
        
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
        # wait(wait_cycle, "AOM", "TCSPC")

with program() as CW_ODMR:
    
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

    with while_(n < N):
        with for_(*from_array(f, pulse_freq)):
            update_frequency("RF3", f)
            reset_if_phase("RF3")

            
            play(amp(1.0)*"cw", "RF3", duration=microwave_cycle) #20us
            # play(amp(1.0)*"cw", "RF3", duration=microwave_cycle+laser_cycle) #20us
            
            wait(microwave_cycle, "AOM", "SPCM1")
            wait(4, "AOM") 
            play("laser_ON", "AOM", duration=laser_cycle) ## AOM 200us
            #wait(25, "SPCM1") #25
            measure("readout", "SPCM1", 
                    integration.full("constant", valA))
            # ABmeasureinterval = 100000
            wait(time_AB, "SPCM1")
            measure("readout", "SPCM1", 
                    integration.full("constant", valB))  
            
            assign(deltaAB, valB-valA)
            assign(A, valA)
            assign(B, valB)
            wait(wait_cycle, "SPCM1")
#            wait(wait_cycle, "AOM")
            
            save(deltaAB, deltaAB_st)
            save(A, A_st)
            save(B, B_st)
        save(n, n_st)
        assign(n, n+1)
        
    with stream_processing():
        deltaAB_st.buffer(numspl).average().save('deltaAB')
        n_st.save("iteration")
        
with program() as test2:
    
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

    with while_(n < N):
        with for_(*from_array(f, pulse_freq)):
            update_frequency("RF3", f)
            reset_if_phase("RF3")

            
            play("laser_ON", "AOM", duration=440_000>>2) ## AOM 200us -> 420us
            
            # wait(4000, "RF3", "SPCM1")
            
            play(amp(2.0)*"cw", "RF3", duration=220_000>>2) #200us
            
            wait(4000, "SPCM1")
            
            measure("readout", "SPCM1", 
                    integration.full("constant", valA)) # measure with RF
            # ABmeasureinterval = 100000
                       
            
            wait(4000, "SPCM1") #16_000 us
            
            
            
            measure("readout", "SPCM1", 
                    integration.full("constant", valB)) # measure without RF
            
            assign(deltaAB, valA-valB)
            assign(A, valA)
            assign(B, valB)
            
            save(deltaAB, deltaAB_st)
            save(A, A_st)
            save(B, B_st)
        save(n, n_st)
        assign(n, n+1)
        
    with stream_processing():
        deltaAB_st.buffer(numspl).average().save('deltaAB')
        A_st.buffer(numspl).save('A')
        # A_st.buffer(numspl).average().save('A')
        B_st.buffer(numspl).average().save('B')

        # deltaAB_st.buffer(N, numspl).save('deltaAB')
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
        job = qm.execute(hello_QUA_HJ)
    
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
            
    elif prog_freq_sweep == True:
        job = qm.execute(CW_ODMR)
    
        res_handles = job.result_handles
        fetching_mode = "live"
        results = fetching_tool(job, data_list=["deltaAB", "iteration"], mode=fetching_mode)
        fig, ax = plt.subplots(figsize=(8,5))
        interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
        
        while results.is_processing():
            deltaAB, iteration = results.fetch_all()
            progress_counter(iteration, N, start_time=results.get_start_time())
            
            try: cbar.remove()
            except: pass
            plt.cla()
            ax.plot(pulse_freq/1e6, deltaAB, "o-")
            ax.ticklabel_format(useOffset=False)
            ax.set_xlabel('frequency(MHz)')
            ax.set_ylabel('Signal')
            #ax.ylim(0.25, 0.27)                    
            ax.set_title(f'{formattedDate}')
            plt.show()
                
            plt.pause(1)
            
    elif prog_test2 == True:
        job = qm.execute(test2)
    
        res_handles = job.result_handles
        fetching_mode = "live"
#        results = fetching_tool(job, data_list=["deltaAB", "iteration"], mode=fetching_mode)
        results = fetching_tool(job, data_list=["A", "B", "iteration"], mode=fetching_mode)

        fig, ax = plt.subplots(figsize=(8,5))
        interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
        
        A_temp = np.zeros(numspl)
        avg = True
        while results.is_processing():
#            deltaAB, iteration = results.fetch_all()
            A, B, iteration = results.fetch_all()
            progress_counter(iteration, N, start_time=results.get_start_time())
            if iteration > 10:
                A_temp = A_temp + A/N
            else:
                if avg:
                    plt.cla()
                else:
                    pass
            try: cbar.remove()
            except: pass
            if avg:
                plt.cla()
                ax.plot(pulse_freq/1e6, -A_temp, "-")
            else:
                ax.plot(pulse_freq/1e6, -A, "-")
            # ax.plot(pulse_freq/1e6, deltaAB, "o-")
            # ax.plot(pulse_freq/1e6, B, "--")
            ax.ticklabel_format(useOffset=False)
            ax.set_xlabel('frequency(MHZ)')
            ax.set_ylabel('Signal')
            #ax.set_yticks([])
            ax.set_title(f'{formattedDate}')
            plt.show()
                
            plt.pause(1)

    job.halt()
#%%
plt.close()
get_ipython().run_line_magic('matplotlib', 'inline')
fig, ax = plt.subplots(figsize=(8,5))

if prog_trace == True:
    ax.plot(trange, Iarr)
    ax.ticklabel_format(useOffset=False)
    ax.set_xlabel('Time(ns)')
    ax.set_ylabel('Signal')
    ax.set_title(f'{formattedDate}')
    plt.show()
        
elif prog_freq_sweep == True:
    ax.plot(pulse_freq/1e6, deltaAB, "o-")
    ax.ticklabel_format(useOffset=False)
    ax.set_xlabel('frequency(MHz)')
    ax.set_ylabel('Signal')
    #ax.ylim(0.25, 0.27)                    
    ax.set_title(f'{formattedDate}')
    plt.show()
            
elif prog_test2 == True:
    if avg:
        ax.plot(pulse_freq/1e6, -A_temp, "-")
    else:
        ax.plot(pulse_freq/1e6, -A, "-")
    # ax.plot(pulse_freq/1e6, deltaAB, "o-")
    ax.ticklabel_format(useOffset=False)
    ax.set_xlabel('frequency(MHZ)')
    ax.set_ylabel('Signal')
    # ax.set_ylim(0, 0.03)       
    ax.set_title(f'{formattedDate}')
    plt.show()
            
