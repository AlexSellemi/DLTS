import collect_data as cd
import signal_processing as sp
import matplotlib.pyplot as plt
import plot

# Oscilloscope parameters
sr = 100e6
num_waveforms = 100
WAV_CH = 1 + 1
SIG_CH = 0 + 1

# Collect data
# avg_data = cd.collect(sr, num_waveforms)

# Or open existing data
avg_data = cd.open("/Users/admin/Documents/VSCode/DLTS/DLTS", "Data1", "mac")

# PROCESSING
decon = sp.deconvolve_W(avg_data, SIG_CH, 1e-2)
# Plot deconvolved data
# plt.plot(decon[0], decon[1], label='Original Signal', color='red')
cut_data, fit_y, params = sp.exp_fit(decon)

# PLOTTING
plot.plotter2(avg_data, decon, cut_data, fit_y, params, WAV_CH, SIG_CH)