import time
import datetime
from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from qm import QuantumMachinesManager
from galvo_raster_config import *
import matplotlib.pyplot as plt
from qualang_tools.loops import from_array
import numpy as np 

#%%

# parameters for scan position
galvo_ramp_time = 0.05 * u.us // 4
ramp_x_voltage = -0.05/(galvo_ramp_time*4)
ramp_y_voltage = 0.05/(galvo_ramp_time*4)
total_duration = 0.05 * u.ms // 4  # to keep above voltage during ODMR

# odmr
microwave_cycle = 50 * u.us //4 #50 * u.us // 4
laser_cycle = 40 * u.us // 4 #600 * u.us // 4 
wait_cycle = 10 * u.us // 4

numspl = 1001 # number of freqs
pulse_freq = np.linspace(20, 120 , numspl) * u.MHz
time_AB = 40 * u.us // 4 # 400 1.4 * u.us // 4 # time between A and B



# intialization_pulse = 30*u.us//4
microwave_pulse = 20 * u.us//4



#%%
simulate = False

N = 100_000

with program() as CW_ODMR:
    
    a = declare(int)
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


    # ramp to NV position

    
    with for_(a, 0, a < 6, a+1):
        play(ramp(ramp_x_voltage/6), "mirror_x", duration = galvo_ramp_time+(a*0))
        play(ramp(ramp_y_voltage/6), "mirror_y", duration = galvo_ramp_time+(a*0))
        

    with while_(n < N):
        wait(total_duration, "mirror_x", "mirror_y")
        
        with for_(*from_array(f, pulse_freq)):
            update_frequency("RF3", f)
            reset_if_phase("RF3")
      
            play(amp(1.0)*"cw", "RF3", duration = microwave_pulse) #20us           
            wait(microwave_pulse, "AOM", "SPCM1")
            
            # please check meas_len_1 in the config file
            measure("readout", "SPCM1", 
                    integration.full("constant", valA))

            wait(4, "AOM") 
            play("laser_ON", "AOM", duration=laser_cycle) ## AOM 200us
                        
            wait(time_AB, "SPCM1")
            
            measure("readout", "SPCM1", 
                    integration.full("constant", valB))  
            
            assign(deltaAB, valB-valA)
            assign(A, valA)
            assign(B, valB)
            # wait(wait_cycle, "SPCM1")
            wait(wait_cycle, "AOM")
            
            save(deltaAB, deltaAB_st)
            save(A, A_st)
            save(B, B_st)
        save(n, n_st)
        assign(n, n+1)
        
    with stream_processing():
        deltaAB_st.buffer(numspl).average().save('deltaAB')
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
# trange = np.linspace(0, meas_len_1, readout_array_length)
if simulate:
    # simul_duration = 0.01 * u.s // 4
    simul_duration = 500 * u.us // 4
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=simul_duration)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, CW_ODMR, simulation_config)
    # Get the simulated samples
    samples = job.get_simulated_samples()
    # Plot the simulated samples
    fig, ax = plt.subplots()
    ax.plot(samples.con1.analog["1"],'-', linewidth=0.1 , label="Analog 1(RF)")
    ax.plot(samples.con1.analog["3"], '-', linewidth=2 ,label="Analog 3(V_x)")
    ax.plot(samples.con1.analog["4"], '-', linewidth=2 ,label="Analog 4(V_y)")
    ax.plot(samples.con1.digital["5"],'-', linewidth=2 , label="Digital 5 SPCM timing") # measure timing
    ax.plot(samples.con1.digital["7"], linewidth=2, label="Digital 7 AOM timing") # AOM timing
    plt.grid(':', color = '0.5', linewidth=0.1)
    ax.set_ylim(-0.2, 0.2)
    ax.set_xlabel("Time [ns]")
    ax.set_ylabel("Output")

    
else:
    qm = qmm.open_qm(config)
    qmm.clear_all_job_results()


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


    job.halt()