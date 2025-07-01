from pathlib import Path
import numpy as np
from qualang_tools.units import unit
from qualang_tools.plot import interrupt_on_close
from qualang_tools.results import progress_counter, fetching_tool
from qualang_tools.loops import from_array
import plotly.io as pio

pio.renderers.default = "browser"

#######################
# AUXILIARY FUNCTIONS #
#######################
u = unit(coerce_to_integer=True)


# IQ imbalance matrix
def IQ_imbalance(g, phi):
    """
    Creates the correction matrix for the mixer imbalance caused by the gain and phase imbalances, more information can
    be seen here:
    https://docs.qualang.io/libs/examples/mixer-calibration/#non-ideal-mixer
    :param g: relative gain imbalance between the 'I' & 'Q' ports. (unit-less), set to 0 for no gain imbalance.
    :param phi: relative phase imbalance between the 'I' & 'Q' ports (radians), set to 0 for no phase imbalance.
    """
    c = np.cos(phi)
    s = np.sin(phi)
    N = 1 / ((1 - g**2) * (2 * c**2 - 1))
    return [float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]


######################
# Network parameters #
######################
qop_ip = "192.168.0.50"  # Write the OPX IP address
cluster_name = "Cluster_1"  # Write your cluster_name if version >= QOP220
qop_port = 9510  # Write the QOP port if version < QOP220

#############
# Save Path #
#############
# Path to save data
save_dir = Path(__file__).parent.resolve() / "Data"
save_dir.mkdir(exist_ok=True)

default_additional_files = {
    Path(__file__).name: Path(__file__).name,
    "optimal_weights.npz": "optimal_weights.npz",
}

#####################
# OPX configuration #
#####################
# Set octave_config to None if no octave are present
octave_config = None

# Frequencies
NV_IF_freq = 40 * u.MHz
NV_LO_freq = 2.83 * u.GHz

######################################################################

# Pulses lengths
slice_size = 5 * u.us // 4 #4us

initialization_len_1 = 16 * u.ns
meas_len_1 = 600 * u.us #5 * u.us #trace
#meas_len_1 = 10 * u.us #frequency sweep
intWarray_size_1 = meas_len_1 // 4
long_meas_len_1 = 5_000 * u.ns
long_intWarray_size_1= long_meas_len_1 // 4

######################################################################

initialization_len_2 = 3000 * u.ns
meas_len_2 = 500 * u.ns
intWarray_size_2 = meas_len_2 // 4
long_meas_len_2 = 5_000 * u.ns
long_intWarray_size_2= long_meas_len_2 // 4


# Relaxation time from the metastable state to the ground state after during initialization
relaxation_time = 300 * u.ns
wait_for_initialization = 5 * relaxation_time

# MW parameters
mw_amp_NV = 0.2  # in units of volts
mw_len_NV = 100 * u.ns

x180_amp_NV = 0.1  # in units of volts
x180_len_NV = 32  # in units of ns

x90_amp_NV = x180_amp_NV / 2  # in units of volts
x90_len_NV = x180_len_NV  # in units of ns

# RF parameters
rf_frequency = 70 * u.MHz 
rf_amp = 0.2
rf_length = 1000

# Galvo mirror setting
mirror_frequency = 1 * u.Hz 
mirror_amp = 0.2

# Readout parameters
signal_threshold_1 = -2_000  # ADC untis, to convert to volts divide by 4096 (12 bit ADC)
signal_threshold_2 = -2_000  # ADC untis, to convert to volts divide by 4096 (12 bit ADC)

# Delays
detection_delay_1 = 80 * u.ns
detection_delay_2 = 80 * u.ns
laser_delay_1 = 0 * u.ns
laser_delay_2 = 0 * u.ns
mw_delay = 0 * u.ns
rf_delay = 0 * u.ns


wait_between_runs = 100

config = {
    "version": 1,
    "controllers": {
        "con1": {
            "analog_outputs": {
                1: {"offset": 0.0, "delay": mw_delay},  # I
                2: {"offset": 0.0, "delay": mw_delay},  # Q
                3: {"offset": 0.0, "delay": rf_delay},  # mirror
                4: {"offset": 0.0, "delay": rf_delay},  # mirror
                5: {"offset": 0.0, "delay": 0.0},  # mirror
            },
            "digital_outputs": {
                1: {},  # AOM/Laser
                2: {},  # AOM/Laser
                3: {},  # SPCM1 - indicator
                4: {},  # SPCM2 - indicator
                5: {},
                6: {},
                7: {},
                8: {},
                9: {},
                10:{}
            },
            "analog_inputs": {
                1: {"offset": 0},  # SPCM1
                2: {"offset": 0},  # SPCM2
            },
        }
    },
    "elements": {
        
        "mirror_x": {
            "singleInput": {"port": ("con1", 3)},
            "intermediate_frequency": mirror_frequency,
            "operations": {
                "const": "const_pulse_single",
            },
        },
        "mirror_y": {
            "singleInput": {"port": ("con1", 4)},
            "intermediate_frequency": mirror_frequency,
            "operations": {
                "const": "const_pulse_single",
            },
        },
        "RF3": {
            'mixInputs': {
                'I': ('con1', 1),
                'Q': ('con1', 2),
        },
            "intermediate_frequency": rf_frequency,
            "operations": {
                "cw" : "constIQ_pulse",
            },
            "digitalInputs": {
                "marker": {
                    "port": ("con1", 1),
                    "delay": laser_delay_1,
                    "buffer": 0,
                },
            },
        },
        "AOM": {
            "digitalInputs": {
                "marker": {
                    "port": ("con1", 3),
                    "delay": laser_delay_1,
                    "buffer": 0,
                },
            },
            "operations": {
                "laser_ON": "laser_ON_1",
            },
        },
        "TCSPC": {
            "digitalInputs": {
                "marker": {
                    "port": ("con1", 4),
                    "delay": laser_delay_2,
                    "buffer": 0,
                },
            },
            "operations": {
                "Sync" : "laser_ON_2"
            },
        },
        "Trigger": {
            "digitalInputs": {
                "marker": {
                    "port": ("con1", 5),
                    "delay": laser_delay_2,
                    "buffer": 0,
                },
            },
            "operations": {
                "trigger": "zero_pulse_2",
            },
        },
        "SPCM1": {
            "singleInput": {"port": ("con1", 5)},  # not used
            "digitalInputs": {  # for visualization in simulation
                "marker": {
                    "port": ("con1", 5),
                    "delay": detection_delay_1,
                    "buffer": 0,
                },
            },
            "operations": {
                "readout": "readout_pulse_1",
                "long_readout": "long_readout_pulse_1",
                "cw" : "const_pulse_single"
            },
            "outputs": {"out1": ("con1", 1)},
            'timeTaggingParameters': {   # Time tagging parameters
                'signalThreshold': signal_threshold_1,
                'signalPolarity': 'Below',
                'derivativeThreshold': -2_000,
                'derivativePolarity': 'Above'
            },
            "time_of_flight": detection_delay_1,
            "smearing": 0,
        },
        "SPCM2": {
            "singleInput": {"port": ("con1", 2)},  # not used
            "digitalInputs": {  # for visualization in simulation
                "marker": {
                    "port": ("con1", 2),
                    "delay": detection_delay_2,
                    "buffer": 0,
                },
            },
            "operations": {
                "readout": "readout_pulse_2",
                "long_readout": "long_readout_pulse_2",
                "cw" : "const_pulse_single"
            },
            "outputs": {"out1": ("con1", 2)},
            'timeTaggingParameters': {   # Time tagging parameters
                'signalThreshold': signal_threshold_2,
                'signalPolarity': 'Below',
                'derivativeThreshold': -2_000,
                'derivativePolarity': 'Above'
            },
            "time_of_flight": detection_delay_2,
            "smearing": 0,
        },
    },
    "pulses": {
        "constIQ_pulse": {
            "operation": "control",
            "length": mw_len_NV,
            "waveforms": {"I": "rf_const_wf", "Q": "zero_wf"},
            "digital_marker": "MW_ON",
        },
        "x180_pulse": {
            "operation": "control",
            "length": x180_len_NV,
            "waveforms": {"I": "x180_wf", "Q": "zero_wf"},
        },
        "x90_pulse": {
            "operation": "control",
            "length": x90_len_NV,
            "waveforms": {"I": "x90_wf", "Q": "zero_wf"},
        },
        "-x90_pulse": {
            "operation": "control",
            "length": x90_len_NV,
            "waveforms": {"I": "minus_x90_wf", "Q": "zero_wf"},
        },
        "-y90_pulse": {
            "operation": "control",
            "length": x90_len_NV,
            "waveforms": {"I": "zero_wf", "Q": "minus_x90_wf"},
        },
        "y90_pulse": {
            "operation": "control",
            "length": x90_len_NV,
            "waveforms": {"I": "zero_wf", "Q": "x90_wf"},
        },
        "y180_pulse": {
            "operation": "control",
            "length": x180_len_NV,
            "waveforms": {"I": "zero_wf", "Q": "x180_wf"},
        },
        "const_pulse_single": {
            "operation": "control",
            "length": 1000,  # in ns
            "waveforms": {"single": "const_wf"},
            # "digital_marker": "MW_ON",
        },
        "laser_ON_1": {
            "operation": "control",
            "length": initialization_len_1,
            "digital_marker": "MW_ON",
            # "waveforms": {"single": "zero_wf"},
        },
        "laser_ON_2": {
            "operation": "control",
            "length": initialization_len_2,
            "digital_marker": "ON",
        },
        "readout_pulse_1": {
            "operation": "measurement",
            "length": meas_len_1,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
            "integration_weights" : {
                "integ_weights_cos" : "int_weights",
                "constant" : "constant_weights",
                },
        },
        "long_readout_pulse_1": {
            "operation": "measurement",
            "length": long_meas_len_1,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
            "integration_weights" : {
                "integ_weights_cos" : "long_int_weights",
                "constant" : "constant_weights",
                },
        },
        "readout_pulse_2": {
            "operation": "measurement",
            "length": meas_len_2,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
            "integration_weights" : {
                "integ_weights_cos2" : "int_weights2",
                "constant" : "constant_weights2",
                }
        },
        "long_readout_pulse_2": {
            "operation": "measurement",
            "length": long_meas_len_2,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
            "integration_weights" : {
                "integ_weights_cos2" : "long_int_weights2",
                "constant" : "constant_weights2",
                },
        },
        "zero_pulse": {
            "operation": "control",
            "length": 16,
            "digital_marker": "ON",
            "waveforms": {"single": "zero_wf"},
        },
        "zero_pulse_2": {
            "operation": "control",
            "length": 16,
            "digital_marker": "ON",
        },
    },
    "waveforms": {
        "cw_wf": {"type": "constant", "sample": mw_amp_NV},
        "const_wf": {"type": "constant", "sample": mirror_amp},
        "rf_const_wf": {"type": "constant", "sample": rf_amp},
        "x180_wf": {"type": "constant", "sample": x180_amp_NV},
        "x90_wf": {"type": "constant", "sample": x90_amp_NV},
        "minus_x90_wf": {"type": "constant", "sample": -x90_amp_NV},
        "zero_wf": {"type": "constant", "sample": 0.0},
    },
    "digital_waveforms": {
        "ON": {"samples": [(1, 10)]},  # [(on/off, ns)]
        "OFF": {"samples": [(0, 0)]},  # [(on/off, ns)]
        "MW_ON" : {"samples": [(1, 0)]},  # [(on/off, ns)]
    },
    "integration_weights": {
        "constant_weights": {
            "cosine": [(1.0, meas_len_1)],
            "sine": [(0.0, meas_len_1)],
        },
        "constant_weights2": {
            "cosine": [(1, meas_len_2)],
            "sine": [(0.0, meas_len_2)],
        },
        "int_weights": {
            "cosine": [1.0 for i in range(intWarray_size_1)],
            "sine": [0.0 for i in range(intWarray_size_1)],
        },
        "long_int_weights": {
            "cosine": [-1.0 for i in range(long_intWarray_size_1)],
            "sine": [0.0 for i in range(long_intWarray_size_1)],
        },
        "int_weights2": {
            "cosine": [1.0 for i in range(intWarray_size_2)],
            "sine": [0.0 for i in range(intWarray_size_2)],
        },
        "long_int_weights2": {
            "cosine": [-1.0 for i in range(long_intWarray_size_2)],
            "sine": [0.0 for i in range(long_intWarray_size_2)],
        },
        "cosine_weights": {
            "cosine": [(1.0, meas_len_1)],
            "sine": [(0.0, meas_len_1)],
        },
        "sine_weights": {
            "cosine": [(0.0, meas_len_1)],
            "sine": [(1.0, meas_len_1)],
        },
    },
    "mixers": {
        "mixer_NV": [
            {"intermediate_frequency": NV_IF_freq, "lo_frequency": NV_LO_freq, "correction": IQ_imbalance(0.0, 0.0)},
        ],
    },
}
