# Run automatic data acquisition mode

import NI_USB5133_Communication_v2 as scope5133
import niscope
import collect_data as cd
import signal_processing as sp
import matplotlib.pyplot as plt
import plot as plot
import numpy as np
import settings as stg
import matplotlib.pyplot as plt

# Set up scope session
NI5133 = niscope.Session('Dev1')  

# Collect data
waveforms, tc_values = cd.collect_auto(NI5133)

# data0 = cd.collect_manual(NI5133, 1)

print(tc_values)
plt.plot(waveforms[0])
plt.plot(waveforms[len(waveforms)//2])
plt.plot(waveforms[-1])
plt.show()

# Now have to reformat the data so it's in a [t][T][I] structure for the 2D best fit func
# re_wf = []
# data = []

# # Create time axis
# dt = 1/stg.sr
# time = np.arange(np.size(waveforms)) * dt

# # Create temp axis
# data[1] = 

    
