# -*- coding: utf-8 -*-
"""
Created on Fri Apr 18 18:15:04 2025

@author: user
"""

"""
        HELLO QUA
A simple sandbox to showcase different QUA functionalities during the installation.
"""

import time
from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from qm import QuantumMachinesManager
from configuration_jjkim import *
import matplotlib.pyplot as plt

#%%
################### 
# The QUA program #
###################
time = 10 * u.ms
cycle = time // 4
wait_cycle = cycle 
total_cycle = cycle + wait_cycle
#Checking configuration parameters 
#galvo_raster_config.py / #Galvo mirror setting / mirror_amp & mirror_frequency<br>

with program() as hello_QUA:
    # a = declare(fixed)

    a = declare(int)
    b = declare(int)
#AOM 켜기: turn_on_laser.py line 41-42 활성화<
    with infinite_loop_():
        # Trigger pulses
        with for_(a, 0, a<10, a+1):
            play("laser_ON", "AOM", duration=cycle+(a*0)) ## AOM 
        # play("Sync", "TCSPC")  ## TCSPC Sync
        # # play("laser_ON", "Trigger") ## SR400 Trigger
# Galvo Mirror 움직이기만 하도록 켜기 : turn_on_laser.py line 45-46 활성화<br>
        # ## Galvo mirror  pulse 0.2V 1Hz
#        play("const", "mirror_x", duration = total_cycle) ## Galvo mirror1
 #       play("const", "mirror_y", duration = total_cycle) ## Galvo mirror2
        
        # with for_(b, 0, b<10, b+1):
        #     wait(wait_cycle+(b*0), "AOM", "TCSPC")

        
#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port)

###########################
# Run or Simulate Program #
###########################


qm = qmm.open_qm(config)
job = qm.execute(hello_QUA)

    
    # time.sleep(0.5)
    # job.halt()
