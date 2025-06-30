"""
Galvo mirror raster scan
"""

import time
from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from qm import QuantumMachinesManager
from galvo_raster_config import *
import matplotlib.pyplot as plt

#%%
################### 
# The QUA program #
###################

plot = False
test = True

#############################
####### Parameters ##########

#counter parameters
total_integration_time = int(1 * u.ms)  # Total duration of the measurement
single_integration_time_ns = int(1 * u.ms)  # 500us # Duration of a single chunk. Needed because the OPX cannot measure for more than ~1ms
single_integration_time_cycles = single_integration_time_ns // 4
n_count = int(total_integration_time / single_integration_time_ns) # Number of chunks to get the total measurement time
count_wait_time = 1 *u.ms // 4

#galvo mirror parameters
pixel_x = 50 #default 320
pixel_y = 50 #default 320
voltage_x_add = -2*mirror_amp / (pixel_x * mirror_amp)
voltage_y_add = -2*mirror_amp  / (pixel_y * mirror_amp)

galvo_wait_time = 5 * u.ms // 4
galvo_x_time = 5 *u.ms // 4 + total_integration_time + count_wait_time
galvo_y_time = galvo_x_time * (pixel_x + 2) + galvo_wait_time
galvo_ramp_time = 5 *u.ms


# pixel_x = 10 #default 320
# pixel_y = 10 #default 320
# buffer_x = pixel_x + 1
# buffer_y = pixel_y + 1
# voltage_x_add = -2*mirror_amp / (pixel_x * mirror_amp)
# voltage_y_add = -2*mirror_amp  / (pixel_y * mirror_amp)

# galvo_wait_time = 0.1 * u.us // 4
# galvo_x_time = 0.5 *u.us // 4 + total_integration_time + count_wait_time
# galvo_y_time = galvo_x_time * (pixel_x + 2) + galvo_wait_time
# galvo_ramp_time = 0.15 *u.us

# laser_cycle = total_integration_time*1.1

# wait_time = 0.1*u.us //4


##### end of parameters #####
#############################

with program() as raster_scan:
    v_x = declare(fixed)
    v_y = declare(fixed)
    
    times = declare(int, size=1000)  # QUA vector for storing the time-tags
    counts = declare(int)  # variable for number of counts of a single chunk
    total_counts = declare(int)  # variable for the total number of counts
    n = declare(int)  # number of iterations
    counts_st = declare_stream()  # stream for counts
    
    n_y = declare(int)
    n_x = declare(int)
    
    # Indexing rule
    # (0,0), (1,0), (2,0) .... (nx,0), (nx,1)
    # 0      1        2         nx-1    nx
    
    
    
    
        # Trigger pulses
        # play("laser_ON", "AOM", duration=cycle) ## AOM 
        
    with for_(n_y, 1, n_y < (pixel_y + 2), n_y + 1):
        with if_(n_y == 1):
            play(ramp(mirror_amp/(galvo_ramp_time*4)),'mirror_y',duration=galvo_ramp_time)
            play(amp(0)*"const", "mirror_y", duration = galvo_y_time)
            # play(amp(1.0)*"const", "mirror_y", duration = galvo_y_time)
            wait(galvo_wait_time, "mirror_x")
            
            with for_(n_x, 1, n_x < (pixel_x + 2), n_x + 1):
                with if_(n_x == 1):
                    # play(ramp(-0.2),'mirror_x',duration=10)
                    play(ramp(mirror_amp/(galvo_ramp_time*4)),'mirror_x',duration=galvo_ramp_time)
                    play(amp(0)*"const", "mirror_x", duration = galvo_x_time)
                    
                    wait(count_wait_time, "SPCM1")
                    
                    with for_(n, 0, n < n_count, n + 1):
                        measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
                        assign(total_counts, total_counts + counts)
                    
                
                    
                    
                    
                    save(total_counts, counts_st)
                    assign(total_counts, 0)
                    
                    # assign(n_x, n_x + 1)
                    
                with else_():
                    play(amp(voltage_x_add) * "const", "mirror_x", duration = galvo_x_time) ## Galvo mirror1
                    wait(count_wait_time, "SPCM1")
                    
                    #counter
                    with for_(n, 0, n < n_count, n + 1):
                        measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
                        assign(total_counts, total_counts + counts)
                    save(total_counts, counts_st)
                    assign(total_counts, 0)
 
            play(ramp(mirror_amp/(galvo_ramp_time*4)),'mirror_x',duration=galvo_ramp_time)   

        with else_():
            play(amp(voltage_y_add)*"const", "mirror_y", duration = galvo_y_time)
            # wait(galvo_wait_time, "mirror_x")

            with for_(n_x, 1, n_x < (pixel_x + 2), n_x + 1):
                with if_(n_x == 1):
                    # play(ramp(-0.2),'mirror_x',duration=10)
                    play(ramp(mirror_amp/(galvo_ramp_time*4)),'mirror_x',duration=galvo_ramp_time)
                    play(amp(0)*"const", "mirror_x", duration = galvo_x_time)
                    wait(count_wait_time, "SPCM1")
                    
                    with for_(n, 0, n < n_count, n + 1):
                        measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
                        assign(total_counts, total_counts + counts)
                    save(total_counts, counts_st)
                    assign(total_counts, 0)
                    
                    # assign(n_x, n_x + 1)
                    
                with else_():
                    play(amp(voltage_x_add)*"const", "mirror_x", duration = galvo_x_time) ## Galvo mirror1
                    wait(count_wait_time, "SPCM1")
                    
                    #counter
                    with for_(n, 0, n < n_count, n + 1):
                        measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
                        assign(total_counts, total_counts + counts)
                    save(total_counts, counts_st)
                    assign(total_counts, 0)
                
            play(ramp(mirror_amp/(galvo_ramp_time*4)),'mirror_x',duration=galvo_ramp_time)    
            
            
    play(ramp(mirror_amp/(galvo_ramp_time*4)),'mirror_y',duration=galvo_ramp_time)


            
            
    # with stream_processing():
    #     # counts_st.buffer(len(voltage_x)).save("counts") 
    #     counts_st.buffer(len(voltage_y)).buffer(len(voltage_x)).save_all("counts")
            


#%%
        
#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

###########################
# Run or Simulate Program #
###########################

simulate = False


get_ipython().run_line_magic('matplotlib', 'qt')
# now = datetime.datetime.now()
# formattedDate = now.strftime("%Y%m%d_%H%M%S")

if simulate:
    simul_duration = 80 * u.us // 4
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=simul_duration)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, raster_scan, simulation_config)
    # Get the simulated samples
    samples = job.get_simulated_samples()
    # Plot the simulated samples
    fig, ax = plt.subplots()
    ax.plot(samples.con1.analog["1"], ':', label="measure")
    ax.plot(samples.con1.analog["3"], '-', label="Analog 3(x)")
    ax.plot(samples.con1.analog["4"], '--', label="Analog 4(y)")
    # ax.plot(samples.con1.digital["3"], label="Digital 3")
    # ax.plot(samples.con1.digital["4"], label="Digital 4")
    ax.legend()
    ax.set_xlabel("Time [ns]")
    ax.set_ylabel("Output")
    # Get the waveform report object
    # waveform_report = job.get_simulated_waveform_report()
    # Cast the waveform report to a python dictionary
    # waveform_dict = waveform_report.to_dict()
    # Visualize and save the waveform report
    # waveform_report.create_plot(samples, plot=True, save_path=str(Path(__file__).resolve()))
elif plot:
    qm = qmm.open_qm(config)
    job = qm.execute(raster_scan)
    
    res_handles = job.result_handles
    fetching_mode = "live"
    results = fetching_tool(job, data_list=["counts"], mode=fetching_mode)
    fig, ax = plt.subplots(figsize=(8,5))
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    
    image = ax.imshow(np.zeros((len(voltage_y), len(voltage_x))),
                  extent=[-0.2, 0.2, 0.2, -0.2],
                  aspect='auto', cmap='viridis', vmin=0, vmax=100)
    
    cbar = plt.colorbar(image, ax=ax, label="Photon Counts")
    

    
    plt.ion()
    
    while results.is_processing():
        counts = results.fetch_all()[0]
        # progress_counter(iteration, N, start_time=results.get_start_time())
        
        # try: cbar.remove()
        # except: pass
        # plt.cla()
        
        # count_data = fetching_tool.fetch_all()[0]

        ax.set_xlabel("X Voltage (V)")
        ax.set_ylabel("Y Voltage (V)")  
        ax.ticklabel_format(useOffset=False)
        # ax.set_title(f'{formattedDate}')

        image.set_data(counts)
        
        plt.pause(0.1)

    
    plt.ioff()             
    plt.show()
        
        
    #     if numspl > 1 and tlen > 1:
    #         pc = ax.pcolor(x, y, deltaAB)
    #         cbar = plt.colorbar(mappable=pc, ax=ax)
    #     elif numspl == 1:
    #         ax.plot(tsweep*4, np.squeeze(deltaAB), "o-")
    #     else:
    #         ax.plot(pulse_freq, np.squeeze(deltaAB), "o-")
    #     ax.ticklabel_format(useOffset=False)
    #     # ax.set_xlabel('frequency(MHZ)')
    #     ax.set_ylabel('Signal')
                
    #     ax.set_xlabel('time (ns)')
    #     ax.set_ylabel('Frequency')
                
    #     ax.set_title(f'{formattedDate}')
    #     plt.show()
            
    #     plt.pause(1)
elif test:
     qm = qmm.open_qm(config)
     job = qm.execute(raster_scan)
    
# time.sleep(0.5)
job.halt()