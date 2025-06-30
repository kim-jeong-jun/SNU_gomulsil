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


#counter parameters
total_integration_time = int(0.1 * u.us)  # Total duration of the measurement
single_integration_time_ns = int(0.1 * u.us)  # 500us # Duration of a single chunk. Needed because the OPX cannot measure for more than ~1ms
single_integration_time_cycles = single_integration_time_ns // 4
n_count = int(total_integration_time / single_integration_time_ns) # Number of chunks to get the total measurement time
count_wait_time = 0.1 *u.us // 4

#galvo mirror parameters
# voltage_x = np.linspace(-0.2, 0.2, 5)
voltage_x = np.linspace(0, 0.4, 5)
voltage_x_temp = voltage_x / 0.25
# voltage_y = np.linspace(-0.2, 0.2, 5)
voltage_y_temp = voltage_y / 0.25

0.4 / 321

galvo_wait_time = 1 * u.us // 4
galvo_x_time = 1 *u.us // 4 + total_integration_time + count_wait_time
galvo_y_time = galvo_x_time * (len(voltage_x)+1) + galvo_wait_time


with program() as raster_scan:
    v_x = declare(fixed)
    v_y = declare(fixed)
    
    times = declare(int, size=1000)  # QUA vector for storing the time-tags
    counts = declare(int)  # variable for number of counts of a single chunk
    total_counts = declare(int)  # variable for the total number of counts
    n = declare(int)  # number of iterations
    counts_st = declare_stream()  # stream for counts
    
        # Trigger pulses
        # play("laser_ON", "AOM", duration=cycle) ## AOM 
        
    with for_(*from_array(v_y, voltage_y_temp)):
        play(amp(v_y)*"const", "mirror_y", duration = galvo_y_time)
        wait(galvo_wait_time, "mirror_x")


        with for_(*from_array(v_x, voltage_x_temp)):
            play(amp(v_x)*"const", "mirror_x", duration = galvo_x_time) ## Galvo mirror1
            wait(count_wait_time, "SPCM1")
            
            #counter
            with for_(n, 0, n < n_count, n + 1):
                measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
                assign(total_counts, total_counts + counts)
            
            
            
            
            
            save(total_counts, counts_st)
            assign(total_counts, 0)
         
    with stream_processing():
        # counts_st.buffer(len(voltage_x)).save("counts") 
        counts_st.buffer(len(voltage_y)).buffer(len(voltage_x)).save_all("counts")
            

    #     with stream_processing():
    #         counts_st.with_timestamps().save("counts")


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
    simul_duration = 10 * u.us // 4
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