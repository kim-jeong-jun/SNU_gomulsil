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

plot = True

#############################
####### Parameters ##########

# S_counter parameters
total_integration_time = int(0.1 * u.us)  # Total duration of the measurement
single_integration_time_ns = int(0.1 * u.us)  # 500us # Duration of a single chunk. Needed because the OPX cannot measure for more than ~1ms
single_integration_time_cycles = single_integration_time_ns // 4
n_count = int(total_integration_time / single_integration_time_ns) # Number of chunks to get the total measurement time
count_wait_time = 0.1 *u.us // 4


#S_galvo mirror parameters
pixel_x = 5 #default 320
pixel_y = 5 #default 320
# buffer_x = pixel_x + 1
# buffer_y = pixel_y + 1
voltage_x_add = 2*( - mirror_amp) / (pixel_x * mirror_amp)
voltage_y_add = 2*( - mirror_amp) / (pixel_y * mirror_amp)

galvo_wait_time = 0.1 * u.us // 4
galvo_x_time = 0.5 *u.us // 4 + total_integration_time + count_wait_time
galvo_y_time = galvo_x_time * (pixel_x + 2) + galvo_wait_time
galvo_ramp_time = 15000 *u.ns // 4

ramp_x_voltage = (mirror_amp - (voltage_x_add/mirror_amp))/(galvo_ramp_time*4)
ramp_y_voltage = (mirror_amp - (voltage_x_add*mirror_amp))/(galvo_ramp_time*4)
# (mirror_amp - (voltage_y_add/mirror_amp))/(galvo_ramp_time*4)


laser_cycle = total_integration_time*1.1

wait_time = 0.1*u.us //4

#############################################################
# #counter parameters
# total_integration_time = int(5 * u.ms //4)  # Total duration of the measurement
# single_integration_time_ns = int(0.1 * u.ms // 4)  # 500us # Duration of a single chunk. Needed because the OPX cannot measure for more than ~1ms
# single_integration_time_cycles = single_integration_time_ns // 4
# n_count = int(total_integration_time / single_integration_time_ns) # Number of chunks to get the total measurement time
# count_wait_time = 0.1 *u.ms // 4


# #galvo mirror parameters
# pixel_x = 50 #default 320
# pixel_y = 50 #default 320
# buffer_x = pixel_x + 1
# buffer_y = pixel_y + 1
# voltage_x_add = -2 * mirror_amp / (pixel_x * mirror_amp)
# voltage_y_add = -2 * mirror_amp  / (pixel_y * mirror_amp)

# galvo_wait_time = 0.1 * u.ms // 4
# galvo_x_time = 5 *u.ms // 4 + total_integration_time + count_wait_time
# galvo_y_time = galvo_x_time * (pixel_x + 2) + galvo_wait_time
# galvo_ramp_time = 15 *u.ms //4

# ramp_x_voltage = mirror_amp - voltage_x_add
# ramp_y_voltage = mirror_amp - voltage_x_add

# measure_delay = 1*u.ms // 4
# laser_cycle = (total_integration_time + count_wait_time)*1.2

# wait_time = 1*u.ms //4


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
    counts_array = declare(int, size = pixel_x * pixel_y) # counts array for a heatmap
    
    n_y = declare(int)
    n_x = declare(int)
    
    
    play(ramp(ramp_y_voltage), "mirror_y", duration = galvo_ramp_time)

    with for_(n_y, 0, n_y < pixel_y, n_y + 1):
        play(amp(voltage_y_add)*"const", "mirror_y", duration = galvo_y_time)
            
        play(ramp(ramp_x_voltage), "mirror_x", duration = galvo_ramp_time)

        with for_(n_x, 0, n_x < pixel_x, n_x + 1):
            play(amp(voltage_x_add) * "const", "mirror_x", duration = galvo_x_time) ## Galvo mirror1
            # wait(count_wait_time, "SPCM1")
            
            # play("laser_ON", "AOM", duration=laser_cycle)   

            wait(count_wait_time, "SPCM1")

            #counter
            with for_(n, 0, n < n_count, n + 1):
                measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
                assign(total_counts, total_counts + counts)

            # save(total_counts, counts_st)
            
            # assign(counts_array[n_y*pixel_y + n_x], total_counts)
            # assign(total_counts, 0)      
            # save(counts_array, counts_st)
            
            save(total_counts, counts_st)
            assign(total_counts, 0)
            
        ramp_to_zero("mirror_x", duration = galvo_ramp_time)                  
                
    ramp_to_zero("mirror_y", duration = galvo_ramp_time)
    # play(ramp_to_zero(""), "mirror_y", duration = galvo_ramp_time)   
                
        

    #     with else_():
    #         play(amp(voltage_y_add)*"const", "mirror_y", duration = galvo_y_time)
    #         # wait(galvo_wait_time, "mirror_x")

    #         with for_(n_x, 0, n_x < (pixel_x + 1), n_x + 1):
    #             with if_(n_x == 0):
    #                 # play(ramp(-0.2),'mirror_x',duration=10)
    #                 play(ramp(mirror_amp/(galvo_ramp_time*8)),'mirror_x',duration=galvo_ramp_time)
    #                 play(ramp(mirror_amp/(galvo_ramp_time*8)),'mirror_x',duration=galvo_ramp_time)
    #                 play(amp(0)*"const", "mirror_x", duration = galvo_x_time)
    #                 # wait(count_wait_time, "SPCM1")
    #                 # wait(wait_time)
    #                 play("laser_ON", "AOM", duration=laser_cycle)   

    #                 wait(count_wait_time, "SPCM1")

    #                 with for_(n, 0, n < n_count, n + 1):
    #                     measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
    #                     assign(total_counts, total_counts + counts)
                    
                    
    #                 # assign(counts_array[n_y*pixel_y + n_x], total_counts)
    #                 save(total_counts, counts_st)
    #                 assign(total_counts, 0)

    #                 # assign(n_x, n_x + 1)
                    
    #             with else_():
    #                 play(amp(voltage_x_add)*"const", "mirror_x", duration = galvo_x_time) ## Galvo mirror1
    #                 play("laser_ON", "AOM", duration=laser_cycle)   

    #                 wait(count_wait_time, "SPCM1") 
    #                 #counter
    #                 with for_(n, 0, n < n_count, n + 1):
    #                     measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
    #                     assign(total_counts, total_counts + counts)
    #                     measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
    #                     assign(total_counts, total_counts + counts)
                        
                  
    #                 # assign(counts_array[n_y*pixel_y + n_x], total_counts)
    #                 # assign(total_counts, 0)
    #                 # save(counts_array, counts_st)
    #                 save(total_counts, counts_st)
    #                 assign(total_counts, 0)
                
    #         play(ramp(mirror_amp/(galvo_ramp_time*8)),'mirror_x',duration=galvo_ramp_time)    
    #         play(ramp(mirror_amp/(galvo_ramp_time*8)),'mirror_x',duration=galvo_ramp_time)    
            
    # play(ramp(mirror_amp/(galvo_ramp_time*8)),'mirror_y',duration=galvo_ramp_time)        
    # play(ramp(mirror_amp/(galvo_ramp_time*8)),'mirror_y',duration=galvo_ramp_time)
            
            
    # with stream_processing():
    #     # counts_st.buffer(len(voltage_x)).save("counts") 
    #     counts_st.buffer(buffer_x*buffer_y).save("counts_array")
            


#%%
        
#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

###########################
# Run or Simulate Program #
###########################

simulate = True


get_ipython().run_line_magic('matplotlib', 'qt')
# now = datetime.datetime.now()
# formattedDate = now.strftime("%Y%m%d_%H%M%S")

if simulate:
    simul_duration = 500 * u.us // 4
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
    
    res_handles.wait_for_all_values()
    
    counts_array = res_handles.get("counts_array").fetch_all()
    
    # counts_array = np.arange(0, (pixel_x+1)*(pixel_y+1),1 )
    
    counts_2d = counts_array.reshape((pixel_y+1, pixel_x+1))  
    
    def format_coord(x, y):
        # x and y are in axes (data) coordinates
        return f"x={x:.2f}, y={y:.2f}"


    
    

    fig, ax = plt.subplots(figsize=(8,5))
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    
    image = ax.imshow(counts_2d,
                  extent=[mirror_amp, -mirror_amp,mirror_amp, -mirror_amp],origin="lower",
                  aspect='auto', cmap='viridis', vmin=min(counts_array), vmax=max(counts_array))
    
    ax.format_coord = format_coord
    
    
    
    cbar = plt.colorbar(image, ax=ax, label="Photon Counts")
    

    
    plt.ion()
    
    # while results.is_processing():
    #     counts = results.fetch_all()[0]
    #     # progress_counter(iteration, N, start_time=results.get_start_time())
        
    #     # try: cbar.remove()
    #     # except: pass
    #     # plt.cla()
        
    #     # count_data = fetching_tool.fetch_all()[0]

    #     ax.set_xlabel("X Voltage (V)")
    #     ax.set_ylabel("Y Voltage (V)")  
    #     ax.ticklabel_format(useOffset=False)
    #     # ax.set_title(f'{formattedDate}')

    #     image.set_data(counts)
        
    #     plt.pause(0.1)

    
    # plt.ioff()             
    # plt.show()
        
        
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

# time.sleep(0.5)
job.halt()