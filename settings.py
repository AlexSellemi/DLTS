# Stores global configurations

import signal_processing as sp
import numpy as np

# Oscilloscope settings (CH0 for signal, CH1 for temp)
SIG_CH = 0
TEMP_CH = 1

vpp0            = 4 
vpp1            = 4 
t               = 10e-6 
sr              = 100e6 
offset0         = -1.5
offset1         = 0 
IS_TRIGGER_OUT  = True

t_sig = 10e-6
tc = 20e-9
sig_samples = int((t_sig+tc)*sr)
temp_samples = 1
sig_ref_position = 5


# Temp parameters (Celsuis)
temp_min = 25
temp_max = 25
temp_step = 0.2


# Voltage parameters (from corresponding temp parameters above)
volt_max = 1
# volt_max = sp.temp_to_volt(temp_max)
volt_step = 0.01
# volt_step = sp.temp_to_volt(temp_step)


# Number of transients to acquire throughout temp scan
num_points = 1
# num_points = int((temp_max - temp_min) / temp_step)


# Number of averaged waveforms for manual mode
num_waveforms = 1