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
import pandas as pd

#%%
################### 
# The QUA program #
###################

plot = True
test = False

#############################
####### Simulation Parameters ##########

# S_counter parameters
# total_integration_time = int(0.5 * u.us) // 4  # Total duration of the measurement
# single_integration_time_ns = int(0.1 * u.us) // 4 # 500us # Duration of a single chunk. Needed because the OPX cannot measure for more than ~1ms
# single_integration_time_cycles = single_integration_time_ns // 4
# n_count = int(total_integration_time / single_integration_time_ns) # Number of chunks to get the total measurement time
# count_wait_time = 0.1 * u.us // 4


#S_galvo mirror parameters
# pixel_x = 5 #default 321
# pixel_y = 5 #default 321

# voltage_x_add = 2 * ( - mirror_amp) / ((pixel_x-1) * mirror_amp)
# voltage_y_add = 2 * ( - mirror_amp) / ((pixel_y-1) * mirror_amp)

# galvo_ramp_time = 1_000 *u.ns // 4 # 1 us

# galvo_x_time = 1 * u.us // 4 + total_integration_time + 2*count_wait_time

# galvo_y_time = galvo_ramp_time + galvo_x_time * (pixel_x + 1)

# ramp_x_voltage = (mirror_amp)/(galvo_ramp_time*4)
# ramp_y_voltage = (mirror_amp)/(galvo_ramp_time*4)


# laser_cycle = 10 * u.ms //4
# laser_cycle = total_integration_time*1.1


# wait_time = 0.1*u.us //4

#############################################################
#counter parameters
# #############################################################



total_integration_time = int(1000 * u.us) // 4 # Total duration of the measurement
single_integration_time_ns = int(1000* u.us) // 4  # 500us # Duration of a single chunk. Needed because the OPX cannot measure for more than ~1ms
single_integration_time_cycles = single_integration_time_ns // 4
n_count = int(total_integration_time / single_integration_time_ns) # Number of chunks to get the total measurement time
count_wait_time = 1 * u.ms // 4
integration_time_sec = total_integration_time * 1e-9 * 4

#galvo mirror parameters
pixel_x = 101 #default 321
pixel_y = 101 #default 321

voltage_x_add = 2 * ( - mirror_amp) / ((pixel_x-1) * mirror_amp)
voltage_y_add = 2 * ( - mirror_amp) / ((pixel_y-1) * mirror_amp)

galvo_ramp_time = 1_000_000 * u.ns // 4 # 1ms
# galvo_wait_time = 0.1 * u.us // 4
galvo_x_time = 5 *u.ms // 4 + total_integration_time + 2 * count_wait_time
# galvo_y_time = galvo_x_time * (pixel_x + 2) + galvo_wait_time
galvo_y_time = galvo_ramp_time + (galvo_x_time * (pixel_x + 1))
single_galvo_y_time = galvo_y_time
# galvo_y_time = galvo_x_time

ramp_x_voltage = (mirror_amp)/(galvo_ramp_time*4)
ramp_y_voltage = (mirror_amp)/(galvo_ramp_time*4)


# laser_cycle = 10 * u.ms //4
laser_cycle = total_integration_time*1.1
laser_wait_time = count_wait_time
wait_time = 1 * u.us //4


######### Need to add with proper timing ##################

# 컨피규어 파일에서 포트 세팅 등 어떻게 되어있는지 포트 번호, element 한번 파악하고 진행하세요.

## 1. RF codes 추가

    # play(amp(1.0)*"cw", "RF3", duration=microwave_cycle)

## 2. 좌표 찾아서 ODMR 코드 돌려보기 -> 기존에 있는 거 찾아서 변형


############################################################

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
    
    a = declare(int)
    b = declare(int)
    c = declare(int) 
    
    n_y = declare(int)
    n_x = declare(int)
    y = declare(int)
    
    
    # with for_(c, 0, c<1200, c+1):
    #     play("laser_ON", "AOM", duration=laser_cycle+(c*0))                                   # CW로 laser 켜짐, 10ms 변수사용, 설정해둔 duration 짧으니까 스캔하다 꺼질 것임. 꺼진다고 이상하다고 생각하지 말것
        
    with for_(a, 0, a < 6, a+1):
        play(ramp(ramp_y_voltage/6), "mirror_y", duration = galvo_ramp_time+(a*0))              # 1. y ramp to mirror_amp


    with for_(n_y, 0, n_y < pixel_y , n_y + 1):                                                 # 2. set and keep y voltage during x scan cycle(galvo_y_time)        
        with if_(n_y == 0):                                                                     
            wait(galvo_y_time+(n_y*0), "mirror_y")                                                  # if 1st: keep 1st y voltage
        with else_():
            play(amp(voltage_y_add) * "const", "mirror_y", duration = galvo_y_time+(n_y*0))         # else: add y voltage step and keep it
                                                            
        
        with for_(b, 0, b < 6, b+1):
            play(ramp(ramp_x_voltage/6), "mirror_x", duration = galvo_ramp_time+(b*0))          # 3. x ramp to mirror_amp after set y voltage

        with for_(n_x, 0, n_x < pixel_x, n_x + 1):                                              # 4. set and keep x voltage during measure cycle(galvo_x_time)
            with if_(n_x == 0):
                wait(galvo_x_time+(n_x*0), "mirror_x")                                              # if 1st: keep 1st x voltage
            with else_():
                play(amp(voltage_x_add) * "const", "mirror_x", duration = galvo_x_time+(n_x*0))     # else: add x voltage step and keep it
                
            wait(laser_wait_time, "AOM", "SPCM1")

            play("laser_ON", "AOM", duration=laser_cycle)  
                                            # 5. Laser On before measurement

            wait(count_wait_time, "SPCM1")
            
            with for_(n, 0, n < n_count, n + 1):                                                # 6. measurement
                measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
                assign(total_counts, total_counts + counts)
                                
            save(total_counts, counts_st)                                                       # 7. save photon counts result for a pixel as stream
            assign(total_counts, 0)                                                             # 8. reset result to zero to prepare next measurement
            
        ramp_to_zero("mirror_x", duration = galvo_ramp_time*12)                                 # 9. x ramp to zero voltage                             
                
    ramp_to_zero("mirror_y", duration = galvo_ramp_time*12)                                     # 10. y ramp to zero voltage
    
    
    with stream_processing(): 
        counts_st.buffer(pixel_x*pixel_y).save("counts_array")
            

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

now = datetime.datetime.now()
formattedDate = now.strftime("%Y%m%d_%H%M%S")

if simulate:
    simul_duration = 100 * u.us // 4
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
    ax.plot(samples.con1.analog["4"], '-', linewidth=2 ,label="Analog 4(y)")
    ax.plot(samples.con1.digital["1"],'-', linewidth=1 , label="Digital 1") # measure timing
    plt.grid(':', color = '0.5', linewidth=0.1)
    ax.plot(samples.con1.digital["7"], linewidth=1, label="Digital 7") # AOM timing
    ax.set_ylim(-0.2, 0.2)
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
    # counts_array = np.arange(0, (pixel_x)*(pixel_y),1 )
    counts_per_second = counts_array / integration_time_sec
    
    
    
    # counts_2d = counts_array.reshape((pixel_y, pixel_x))  
    counts_2d = counts_per_second.reshape((pixel_y, pixel_x)) 
    
    
    voltage_range_x = np.linspace(mirror_amp, -mirror_amp, pixel_x, endpoint=True)
    voltage_range_y = np.linspace(mirror_amp, -mirror_amp, pixel_y, endpoint=True)
    
    df = pd.DataFrame(counts_2d, index=voltage_range_y, columns=voltage_range_x)
    df.index.name = "Voltage Y / Voltage X"
    
    output_file = f"{formattedDate}_pixel_x_{pixel_x}_pixel_y_{pixel_y}_no_RF.csv"
    
        
    df.to_csv(output_file)
    
    
    
    
    
    
    
    
    
    def format_coord(x, y):
        # x and y are in axes (data) coordinates
        return f"x={x:.2f}, y={y:.2f}"


    fig, ax = plt.subplots(figsize=(8,5))
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    
    image = ax.imshow(counts_2d,
                  extent=[mirror_amp, -mirror_amp,mirror_amp, -mirror_amp],origin="lower",
                  aspect='auto', cmap='viridis', vmin=min(counts_per_second), vmax=max(counts_per_second)) # 250611 데이터 범위 counts_array->counts_per_second 반영
    
    ax.format_coord = format_coord
    

    ax.set_xlabel("X Voltage (V)")
    ax.set_ylabel("Y Voltage (V)")  
#     ax.ticklabel_format(useOffset=False)
    ax.set_title(f'{formattedDate} Without RF')

    
    cbar = plt.colorbar(image, ax=ax, label="Photon Counts/s")
    

    
    # plt.ion()
    
    # while results.is_processing():
    #     counts = results.fetch_all()[0]
    #     # progress_counter(iteration, N, start_time=results.get_start_time())
        
    #     # try: cbar.remove()
    #     # except: pass
    #     # plt.cla()
        
    #     # count_data = fetching_tool.fetch_all()[0]

    #     image.set_data(counts)
        
    #     plt.pause(0.1)

    
    # plt.ioff()         
   
    plt.pause(5)
    get_ipython().run_line_magic('matplotlib', 'inline')    
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

# time.sleep(0.5)
 
elif test:
    qm = qmm.open_qm(config)
    job = qm.execute(raster_scan)

    # job = qm.execute(hello_QUA)


    # job.halt()