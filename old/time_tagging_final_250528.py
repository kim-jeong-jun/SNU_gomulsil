"""
        COUNTER
The program consists in playing a laser pulse while performing time tagging continuously.
This allows measuring the received photons as a function of time while adjusting external parameters
to validate the experimental set-up.
"""

from qm import QuantumMachinesManager
from qm.qua import *
from qm import SimulationConfig
import matplotlib.pyplot as plt
from config_time_tagging_ongoing import *
from qualang_tools.results.data_handler import DataHandler

##################
#   Parameters   #
##################
# Parameters Definition
total_integration_time = int(10 * u.ms)  # Total duration of the measurement
# Duration of a single chunk. Needed because the OPX cannot measure for more than ~1ms
single_integration_time_ns = int(1 * u.us)  # 500us
single_integration_time_cycles = single_integration_time_ns // 4
# Number of chunks to get the total measurement time
n_count = int(total_integration_time / single_integration_time_ns)

###################
# The QUA program #
###################
with program() as counter:
    times = declare(int, size=1000)  # QUA vector for storing the time-tags
    counts = declare(int)  # variable for number of counts of a single chunk
    total_counts = declare(int)  # variable for the total number of counts
    n = declare(int)  # number of iterations
    counts_st = declare_stream()  # stream for counts

    # Infinite loop to allow the user to work on the experimental set-up while looking at the counts
    with infinite_loop_():
        # Loop over the chunks to measure for the total integration time
        with for_(n, 0, n < n_count, n + 1):
            # Play the laser pulse...
            #play("laser_ON", "AOM", duration=single_integration_time_cycles)
            #play("trigger", "Trigger", duration=5)
            # ... while measuring the events from the SPCM
            measure("readout", "SPCM1",time_tagging.analog(times, single_integration_time_ns, counts))
            # Increment the received counts
            assign(total_counts, total_counts + counts)
        # Save the counts
        save(total_counts, counts_st)
        assign(total_counts, 0)

    with stream_processing():
        counts_st.with_timestamps().save("counts")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

#######################
# Simulate or execute #
#######################
simulate = False

if simulate:
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=130000)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, counter, simulation_config)
    # Get the simulated samples
    samples = job.get_simulated_samples()
    # Plot the simulated samples
    samples.con1.plot()
    # Get the waveform report object
    # waveform_report = job.get_simulated_waveform_report()
    # # Cast the waveform report to a python dictionary
    # waveform_dict = waveform_report.to_dict()
    # # Visualize and save the waveform report
    # waveform_report.create_plot(samples, plot=True, save_path=str(Path(__file__).resolve()))
else:
    qm = qmm.open_qm(config)

    job = qm.execute(counter)
    # Get results from QUA program
    res_handles = job.result_handles
    counts_handle = res_handles.get("counts")
    counts_handle.wait_for_values(1)
    time = []
    counts = []
    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    while res_handles.is_processing():
        new_counts = counts_handle.fetch_all()
        #counts.append(new_counts["value"] / single_integration_time_ns/1000)
        counts.append(new_counts["value"])
        time.append(new_counts["timestamp"] / u.s)  # Convert timestamps to seconds
        plt.cla()
        if len(time) > 50:
            plt.plot(time[-50:], counts[-50:])
        else:
            plt.plot(time, counts)

        plt.xlabel("Time [s]")
        plt.ylabel("Counts [cps]")
        plt.title("Counter")
        plt.pause(0.1)
