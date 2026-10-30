import collect_data as cd
import signal_processing as sp
import matplotlib.pyplot as plt
import plot as plot
import settings as stg

# Going to deprecate this soon

'''
Keep in mind that gain and digitization voltage affect apparent smoothness of waveform
Digitization voltage  = Vpp / 2^8
Max amplitude = |V_femto| = G * |V_sig|
Vpp / 256 = 0.01 * G * |V_sig|
Increasing gain makes signal more significant compared to noise (better strategy)
Decreasing Vpp makes noise less significant compared to signal
This could actually present a problem if the waveform amplitude changes over time
But overall this wouldn't be much of an issue with higher resolution
Also you want offset to be half of Vpp
'''

# Collect data
# avg_data1 = cd.collect(sr, num_waveforms)

# Or open existing data
# avg_data = cd.open("/Users/admin/Documents/VSCode/DLTS/DLTS", "Data1", "mac")
avg_data1 = cd.open("C:/Users/Andy/Documents/Alex-DLTS/DLTS_Code/DLTS", "Data4")
# avg_data2 = cd.open("C:/Users/Andy/Documents/Alex-DLTS/DLTS_Code/DLTS", "Data5")
# plt.plot(avg_data[0], avg_data[SIG_CH])
# plt.show()

# PROCESSING
decon_sig1 = sp.deconvolve_W(avg_data1, stg.SIG_CH, 1e-2)
# decon_sig2 = sp.deconvolve_W(avg_data2, SIG_CH, 1e-2)
# Plot deconvolved data
# plt.plot(decon_sig[0], decon_sig[1], label='Original Signal', color='red')
# plt.show()
cut_data1, fit_y1, params1 = sp.exp_fit2(decon_sig1)
# cut_data2, fit_y2, params2 = sp.exp_fit2(decon_sig2)

# PLOTTING
plot.plotter2(avg_data1, decon_sig1, cut_data1, fit_y1, params1, stg.WAV_CH, stg.SIG_CH)
# plot.plotter2(avg_data2, decon_sig2, cut_data2, fit_y2, params2, WAV_CH, SIG_CH)
plt.show()


'''
Temp reading: 

Currently the scope will gather a curve of temp (really voltage) vs. time, but we want a specific value instead for an entire trial of 100 averaged waveforms at the same temp
But also would be nice to get temp for a single trial or X trials in general
So I'm basically going to take (Temp[-1] + Temp[0]) / 2 as my reading for each trial, assuming a straight-ish line, then average these amounts for X trials  

'''