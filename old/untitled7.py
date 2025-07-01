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

# %% Parameters
simulate = False
N = 10000  # Number of iterations (per frequency point)
readout_array_length = int(meas_len_1 / (slice_size * 4))
pulse_freq = np.linspace(40, 100, 1001) * u.MHz
microwave_cycle = 5 * u.us // 4
laser_cycle = 20 * u.us // 4
wait_cycle = 10 * u.us // 4
time_AB = 10 * u.us // 4 # interval time

# %% QUA Program for ODMR with summed SPCM signal
with program() as ODMR_SUMMED:
    n = declare(int)
    i = declare(int)
    f = declare(int)

    valA = declare(fixed)
    valB = declare(fixed)
    A = declare(fixed)
    B = declare(fixed)
    deltaAB = declare(fixed)
    deltaAB_st = declare_stream()
    A_st = declare_stream()
    B_st = declare_stream()

    Iarr = declare(fixed, size=readout_array_length)
    summed_val = declare(fixed)
    tmp_val = declare(fixed)
    summed_val_st = declare_stream()
    n_st = declare_stream()

    with while_(n < N):
        with for_(*from_array(f, pulse_freq)):
            update_frequency("RF3", f)
            reset_phase("RF3")

            play(amp(1.0)*"cw", "RF3", duration = microwave_cycle) # 20us

            wait(microwave_cycle, "AOM", "SPCM1")
            # wait(5, "AOM")
            play("laser_ON", "AOM", duration = laser_cycle) ## AOM 200us
            measure("readout", "SPCM1",
                    integration.full("constant", valA))
            ## AB measure interval = 100000
            wait(time_AB, "SPCM1")
            measure("readout", "SPCM1",
                    integration.full("constant", valB))
            assign(deltaAB, valB - valA)
            assign(A, valA)
            assign(B, valB)

            wait(wait_cycle, "SPCM1")

            save(deltaAB, deltaAB_st)
            save(A, A_st)
            save(B, B_st)

        save(n, n_st)
        assign(n, n+1)

    with stream_processing():
        deltaAB_st.buffer(len(pulse_freq)).average().save("summed_signal")
        n_st.save("iteration")


# %% Run / Simulate
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)
now = datetime.datetime.now()
formattedDate = now.strftime("%Y%m%d_%H%M%S")

if simulate:
    from qm import SimulationConfig

    simulation_config = SimulationConfig(duration = 300 * u.us // 4)
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
        ax.plot(pulse_freq / 1e6, average_signal, "-")
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("Averaged SPCM Signal")
        ax.set_title(f"ODMR - {formattedDate}")
        ax.set_ylim(-0.0003, 0.0001)  # 원하는 y축 범위로 수정
        plt.pause(1)
        plt.show()
        print(np.min(average_signal), np.max(average_signal))


    job.halt()


