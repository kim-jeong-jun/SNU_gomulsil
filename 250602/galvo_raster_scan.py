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

time = 100 * u.us
cycle = time // 4
wait_cycle = cycle * 2
total_cycle = cycle + wait_cycle
galvo_time = 1 *u.s // 4

# voltage_x = np.linspace(0, 0.2, 321)
voltage_x = np.linspace(-0.2, 0.2, 5)
# voltage_y = np.linspace(-0.2, 0.2, 321)

with program() as raster_scan:
    v_x = declare(fixed)
    # v_y = declare(fixed)
    
        # Trigger pulses
        # play("laser_ON", "AOM", duration=cycle) ## AOM 
        
    # with for_each_(v_y, voltage_y):
    #     play("const", "mirror_y", duration = galvo_time) ## Galvo mirror2
        # reset_phase("mirror_x")
        # set_dc_offset("mirror_y", "single", v_y)
        # with for_(*from_array(v_x, voltage_x)):
    with for_(*from_array(v_x, voltage_x)):
        # set_dc_offset("mirror_x", "single", v_x)
        # update_frequency("mirror_x", v_x)
        play(amp(v_x)*"const", "mirror_x", duration = galvo_time) ## Galvo mirror1
        wait(galvo_time, "mirror_x")

                # play(amp(1.0)*"cw", "RF3", duration=t)

        # Galvo mirror  pulse 0.2V 1Hz
        
        # wait(wait_cycle, "AOM", "TCSPC")

        
#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

###########################
# Run or Simulate Program #
###########################

simulate = False

if simulate:
    simul_duration = 0.1 * u.s // 4
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=simul_duration)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, raster_scan, simulation_config)
    # Get the simulated samples
    samples = job.get_simulated_samples()
    # Plot the simulated samples
    fig, ax = plt.subplots()
    ax.plot(samples.con1.analog["3"], label="Analog 3(x)")
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
else:
    if plot:
        qm = qmm.open_qm(config)
        job = qm.execute(raster_scan)
        
        # res_handles = job.result_handles
        # fetching_mode = "live"
        # results = fetching_tool(job, data_list=["deltaAB", "iteration"], mode=fetching_mode)
        # fig, ax = plt.subplots(figsize=(8,5))
        # interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
        
        # while results.is_processing():
        #     deltaAB, iteration = results.fetch_all()
        #     progress_counter(iteration, N, start_time=results.get_start_time())
            
        #     x, y = np.meshgrid(tsweep*4, pulse_freq)
        #     try: cbar.remove()
        #     except: pass
        #     plt.cla()
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
    # job.halt()