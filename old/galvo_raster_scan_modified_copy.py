"""
Galvo mirror raster scan
"""

import datetime
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
test = False


#############################################################
#counter parameters
# #############################################################
total_integration_time = int(5 * u.ms) // 4 # Total duration of the measurement
single_integration_time_ns = int(1 * u.ms) // 4  # 500us # Duration of a single chunk. Needed because the OPX cannot measure for more than ~1ms
single_integration_time_cycles = single_integration_time_ns // 4
n_count = int(total_integration_time / single_integration_time_ns) # Number of chunks to get the total measurement time
count_wait_time = 1 * u.ms // 4
integration_time_sec = total_integration_time * 0.000000001 * 4

#galvo mirror parameters
pixel_x = 10 #default 320
pixel_y = 10 #default 320

voltage_x_add = 2 * ( - mirror_amp) / (pixel_x * mirror_amp)
voltage_y_add = 2 * ( - mirror_amp) / (pixel_y * mirror_amp)

galvo_ramp_time = 1_000_000 * u.ns // 4 # 1ms
# galvo_wait_time = 0.1 * u.us // 4
galvo_x_time = 5 *u.ms // 4 + total_integration_time + 2 * count_wait_time
# galvo_y_time = galvo_x_time * (pixel_x + 2) + galvo_wait_time
galvo_y_time = galvo_ramp_time + (galvo_x_time * (pixel_x + 1))
single_galvo_y_time = galvo_y_time
# galvo_y_time = galvo_x_time

ramp_x_voltage = (mirror_amp)/(galvo_ramp_time*4)
ramp_y_voltage = (mirror_amp)/(galvo_ramp_time*4)



laser_cycle = total_integration_time*1.1

wait_time = 0.1*u.us //4


##### end of parameters #####
#############################

#This structure supports a confocal microscopy raster scan

with program() as raster_scan:  

    v_x = declare(fixed) # Creates a variable named "v_x" of type fixed point that can have fractional bits
    v_y = declare(fixed) # Creates a variable named "v_y" of type fixed point that can have fractional bits 

    times = declare(int, size=1000)  # QUA vector for storing the time-tags
    counts = declare(int)  # variable for number of counts of a single chunk
    total_counts = declare(int)  # variable for the total number of counts
    n = declare(int)  # number of iterations
    counts_st = declare_stream()  # stream for counts
    counts_array = declare(int, size = pixel_x * pixel_y) # counts array for a heatmap
    
    n_y = declare(int) # Creates a variable named"n_x" of type integer
    n_x = declare(int) # Creates a variable named "n_y_ of type integer
    y = declare(int) # Creates a variable named "y" of type integer 
    #position voltages(v_x and v_y) use fixed for sub-millivolt precision, while pixel indicies and counts use int since they represent discrete values    

#%%
        
#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

###########################
# Run or Simulate Program #
###########################

simulate = False # False: Runs the experiment on actual HW rather than simulation mode, and vise 
get_ipython().run_line_magic('matplotlib', 'qt')
now = datetime.datetime.now()
formattedDate = now.strftime("%Y%m%d_%H%M%S")

if simulate:
    simul_duration = 700 * u.us // 4
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=simul_duration)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, raster_scan, simulation_config)
    # Get the simulated samples
    samples = job.get_simulated_samples()
    # Plot the simulated samples
    fig, ax = plt.subplots()
    # ax.plot(samples.con1.analog["1"], ':', label="measure")
    ax.plot(samples.con1.analog["3"], '-', linewidth=2 ,label="Analog 3(x)")
    ax.plot(samples.con1.analog["8"], '-', linewidth=2 ,label="Analog 4(y)")
    # ax.plot(samples.con1.digital["1"],'-', linewidth=0.5 , label="Digital 1")
    plt.grid(':', color = '0.5', linewidth=0.1)
    # ax.plot(samples.con1.digital["4"], label="Digital 4")
    ax.set_ylim(-0.6, 0.6)
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
    qm = qmm.open_qm(config) #open QM
    job = qm.execute(raster_scan) #Execute raster scan
    
    res_handles = job.result_handles 
    
    res_handles.wait_for_all_values() #wait until we know all values were processed for this named result
    
    counts_array = np.arange(0, (pixel_x)*(pixel_y),1 ) #np.arange(start, stop, step) creates a NumPy array with evenly spaced values 
    counts_per_second = counts_array / integration_time_sec
    
    
    
    counts_2d = counts_array.reshape((pixel_y, pixel_x))  
    
    def format_coord(x, y):
        # x and y are in axes (data) coordinates
        return f"x={x:.2f}, y={y:.2f}"


    fig, ax = plt.subplots(figsize=(8,5))
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    
    image = ax.imshow(counts_2d,
                  extent=[mirror_amp, -mirror_amp,mirror_amp, -mirror_amp],origin="lower",
                  aspect='auto', cmap='viridis', vmin=min(counts_array), vmax=max(counts_array))
    
    ax.format_coord = format_coord
    

    ax.set_xlabel("X Voltage (V)")
    ax.set_ylabel("Y Voltage (V)")  
#     ax.ticklabel_format(useOffset=False)
    ax.set_title(f'{formattedDate}')

    
    cbar = plt.colorbar(image, ax=ax, label="Photon Counts/s")
    
    
            
    plt.show()
        
 
 
elif test:
    qm = qmm.open_qm(config)
    job = qm.execute(raster_scan)

    # job = qm.execute(hello_QUA)


    # job.halt()