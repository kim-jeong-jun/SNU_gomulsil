import time
import datetime
from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from qm import QuantumMachinesManager
from configuration_class import *
import matplotlib.pyplot as plt
from qualang_tools.loops import from_array
import numpy as np 

simulate = False
run_raster = True

N = 1_000_000

from qm.qua import *
from qm import SimulationConfig
from configuration_class import config

# 스캔 파라미터
nx, ny       = 256, 256              # 해상도
x_min, x_max = 0, +0.5            # 전압 범위 [V]
y_min, y_max = 0, +0.5
pix_time     = 200*u.ms                   # 한 픽셀 dwell time [ns]

with program() as raster:
    i = declare(int)
    j = declare(int)
    x_amp = declare(fixed)
    y_amp = declare(fixed)


    with for_(i, 0, i < ny, i + 1):
        # 한 줄이 시작될 때 Y 전압을 먼저 업데이트
        assign(y_amp, y_min + (y_max - y_min) * i / (ny - 1))
        play("dc_pulse" * amp(y_amp), "scan_y")

        with for_(j, 0, j < nx, j + 1):
            assign(x_amp, x_min + (x_max - x_min) * j / (nx - 1))
            play("dc_pulse" * amp(x_amp), "scan_x")
            wait(pix_time - 4, "scan_x")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

###########################
# Run or Simulate Program #
###########################

qm = qmm.open_qm(config)
qmm.clear_all_job_results()
job = qm.execute(raster)        
job.halt()
