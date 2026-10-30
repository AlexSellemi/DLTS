# Run manual data acquisiton mode (single new transient or open prev file)

import NI_USB5133_Communication_v2 as scope5133
import niscope
import collect_data as cd
import signal_processing as sp
import matplotlib.pyplot as plt
import plot as plot
import settings as stg

# Oscilloscope parameters
num_waveforms = 1
WAV_CH = 1 + 1
SIG_CH = 0 + 1

# User input params
NEW_TRIAL = False
file_path = "C:/Users/Andy/Documents/Alex-DLTS/DLTS_Code/DLTS/Data"
file_prefix = "Data4"

# Start new scope session
NI5133_manual = niscope.Session('Dev1')

if(NEW_TRIAL):
    avg_data = cd.collect_manual(NI5133_manual, num_waveforms)
else:
    avg_data = cd.open(file_path, file_prefix)

# Call functions to process data assuming 2D format
decon_sig = sp.deconvolve_W(avg_data, (stg.SIG_CH+1), 1e-2)
cut_data, fit_y, params = sp.exp_fit2(decon_sig)

# Call plotting functions
plot.plot(avg_data)
plot.plot(decon_sig)
plt.show()
