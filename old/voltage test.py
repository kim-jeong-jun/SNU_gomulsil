# -*- coding: utf-8 -*-
"""
Created on Fri May 30 15:43:15 2025

@author: user
"""
import time
import datetime
from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from qm import QuantumMachinesManager
from config_time_tagging_ongoing import *
import matplotlib.pyplot as plt
from qualang_tools.loops import from_array
import numpy as np 

#%%
################### 
# The QUA program #
###################
simulate = False
test = True

prog_trace = False
prog_freq_sweep = False

microwave_cycle = 20 * u.us //4 # 40* u.us // 4
laser_cycle = 2 * u.us // 4
wait_cycle = 100 * u.us // 4

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
# N = 100_00000000000

with program() as prog:
    with infinite_loop_():
        adc_stream = declare_stream(adc_trace=True)
        measure('readout', 'SPCM1', adc_stream)

    with stream_processing():
        adc_stream.input1().save('raw_adc')
        # n_st.save("iteration")


# with program() as hello_QUA:
#     i = declare(int, 0)
#     n = declare(int, 0)
#     Iarr = declare(fixed,size=readout_array_length)
#     Iarr_st = declare_stream()
#     n_st = declare_stream()
        
#     with while_(n < N):


#         measure("readout", "SPCM1", 
#                 integration.sliced("integ_weights_cos", Iarr, slice_size))


        
#         with for_(i, 0, i < readout_array_length, i + 1) :
#             save(Iarr[i], Iarr_st)    
        
        
#         save(n, n_st)
#         assign(n, n+1)
        
#     with stream_processing():
#         Iarr_st.buffer(readout_array_length).average().save('Iarr')
#         n_st.save("iteration")


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
    #     job = qm.execute(Test_prog)
    # elif prog_trace == True:
        job = qm.execute(prog)
    
        res_handles = job.result_handles
        fetching_mode = "live"
        results = fetching_tool(job, data_list=["raw_adc"], mode=fetching_mode)
        res_handles.wait_for_all_values()
        # Fetch the raw ADC traces and convert them into Volts
        raw_adc = u.raw2volts(res_handles.get("raw_adc").fetch_all())

    # plt.figure()
    # plt.subplot(121)
    plt.title("Single run")
    # plt.plot(adc_dc_single_run, label="DC input")
    plt.plot(raw_adc, label="input voltage")
    plt.xlabel("Time [ns]")
    plt.ylabel("Signal amplitude [V]")
    plt.legend()
    plt.show()

    #     # results = fetching_tool(job, data_list=["Iarr", "iteration"], mode=fetching_mode)
    # fig,ax = plt.subplots(figsize=(8,5))
    # interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    # my_stream_res = res.adc_results.fetch_all()['raw_adc']
    # while results.is_processing():
    #     Iarr = results.fetch_all()
    #         # progress_counter(iteration, N, start_time=results.get_start_time())
            
        
    #     try: cbar.remove()
    #     except: pass
    #     plt.cla()
    #     ax.plot(trange, Iarr)
    #     ax.ticklabel_format(useOffset=False)
    #     ax.set_xlabel('Time(ns)')
    #     ax.set_ylabel('Signal')
    #     ax.set_title(f'{formattedDate}')
    #     plt.show()
            
    #     plt.pause(1)
            
    #     get_ipython().run_line_magic('matplotlib', 'inline')
    #     ax.plot(trange, Iarr)
    #     ax.ticklabel_format(useOffset=False)
    #     ax.set_xlabel('Time(ns)')
    #     ax.set_ylabel('Signal')
    #     ax.set_title(f'{formattedDate}')
    #     plt.show()
        
        
    # job.halt()