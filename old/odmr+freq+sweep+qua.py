# -*- coding: utf-8 -*-
"""
ODMR Frequency Sweep from SPCM Sum using QUA
"""

import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
from qm import QuantumMachinesManager
from qm.qua import *
from configuration_class import *  # Your configuration file
from qualang_tools.loops import from_array


#%% Parameters
simulate = False
N = 1000  # Number of iterations (per frequency point)
readout_array_length = int(meas_len_1 / (slice_size * 4))
pulse_freq = np.linspace(20, 120, 501) * u.MHz
microwave_cycle = 1 * u.us // 4
laser_cycle = 1 * u.ms // 4
wait_cycle = 1 * u.us // 4

#%% QUA Program for ODMR with summed SPCM signal
with program() as ODMR_SUMMED:
    n = declare(int)
    i = declare(int)
    f = declare(int)
    Iarr = declare(fixed, size=readout_array_length)
    summed_val = declare(fixed)
    tmp_val = declare(fixed)
    summed_val_st = declare_stream()
    n_st = declare_stream()

    with while_(n < N):
        with for_(*from_array(f, pulse_freq)):
            update_frequency("RF3", f)
            reset_phase("RF3")
            play("laser_ON", "AOM", duration=laser_cycle)

            assign(summed_val, 0.0)

            # Loop over 10 repetitions
            with for_(i, 0, i < 10, i + 1):
                play(amp(1.0) * "cw", "RF3", duration=microwave_cycle)
                # wait(25, "SPCM1")

                measure("readout", "SPCM1",
                        integration.sliced("integ_weights_cos", Iarr, slice_size))
                
                # Sum all elements of Iarr
                with for_(j := declare(int), 0, j < readout_array_length, j + 1):
                    assign(tmp_val, Iarr[j])
                    assign(summed_val, summed_val + tmp_val)
                
                wait(9*25000, "SPCM1")  # 100 us wait

            save(summed_val, summed_val_st)
        save(n, n_st)
        assign(n, n + 1)

    with stream_processing():
        summed_val_st.buffer(len(pulse_freq)).average().save("summed_signal")
        n_st.save("iteration")

#%% Run / Simulate
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)
now = datetime.datetime.now()
formattedDate = now.strftime("%Y%m%d_%H%M%S")

if simulate:
    from qm import SimulationConfig
    simulation_config = SimulationConfig(duration=300 * u.us // 4)
    job = qmm.simulate(config, ODMR_SUMMED, simulation_config)
    samples = job.get_simulated_samples()
    plt.plot(samples.con1.analog["1"])
    plt.show()
else:
    qm = qmm.open_qm(config)
    qmm.clear_all_job_results()
    job = qm.execute(ODMR_SUMMED)

    res_handles = job.result_handles
    results = fetching_tool(job, data_list=["summed_signal", "iteration"], mode="live")
    fig, ax = plt.subplots(figsize=(8, 5))
    interrupt_on_close(fig, job)

    # 누적 신호와 카운터 초기화
    accumulated_signal = None
    accumulated_count = 0
    
    while results.is_processing():
        summed_signal, iteration = results.fetch_all()
    
        # ensure shape compatibility
        summed_signal = np.squeeze(summed_signal)
    
        # accumulate
        if accumulated_signal is None:
            accumulated_signal = np.array(summed_signal, dtype=np.float64)
        else:
            accumulated_signal += summed_signal
    
        accumulated_count += 1
        average_signal = accumulated_signal / accumulated_count
    
        # progress 표시
        progress_counter(iteration, len(pulse_freq), start_time=results.get_start_time())
    
        # plot 갱신
        plt.cla()
        ax.plot(pulse_freq / 1e6, average_signal, "o-")
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("Averaged SPCM Signal")
        ax.set_title(f"ODMR - {formattedDate}")
        plt.pause(1)
        plt.show()

    job.halt()
