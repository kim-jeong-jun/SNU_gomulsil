# SNU_gomulsil<br>
for 고급물리실험<br>
AOM 켜기: turn_on_laser.py line 41-42 활성화<br>
Galvo Mirror 움직이기만 하도록 켜기 : turn_on_laser.py line 45-56 활성화<br>
Config 파일에서 galvo 전압 확인해야 합니다.<br> 
galvo_raster_config.py / #Galvo mirror setting / mirror_amp & mirror_frequency<br>
작동 멈출 때는 job.halt() + enter 로 동작 멈춰야 합니다.<br>

