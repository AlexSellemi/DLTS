import NI_USB5133_Communication_v2 as scope5133
import niscope
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np

sr = 100e6
num_waveforms = 100
WAV_CH = 1 + 1
SIG_CH = 0 + 1

# current session
NI5133 = niscope.Session('Dev1')  
#  t = 20e-6
# configure current session
num_samples = scope5133.config5133_single(NI5133, vpp0=4, vpp1=4, t=10e-6, sr=sr, offset0=0, offset1=-2, trigger_out=True)
NI5133.configure_trigger_edge(trigger_source="0", level=0.1, slope=niscope.TriggerSlope.NEGATIVE, trigger_coupling=niscope.TriggerCoupling.DC)

# execute acquisition
# data[0] --> t
# data[1] --> CH0
# data[2] --> CH1
# waveforms[i] = data
waveforms = []
for i in range(num_waveforms):
    waveforms.append(scope5133.exe5133_single(NI5133, num_samples, plot=False))

# end session
NI5133.close()

# PROCESSING ------------------------------------------------------------------------------------------

# Calculate averages
# y_avg = data.mean()
# x_avg = (1/sr) * num_samples * 0.5

# Average all of the waveforms, create a master array to do so
stacked = np.stack(waveforms)
avg_data = np.mean(stacked, axis=0)

# Maybe save this for LATER:
# Data rescaling (DO THIS BEFORE cutting data)
if avg_data[0][-1] < 100e-6:
    avg_data[0] *= 1e6
    unit = 'us'
elif avg_data[0][-1] < 100e-3:
    avg_data[0] *= 1e3
    unit = 'ms'
else:
    unit = 's'

# Use rise times of Femto to determine which portion of the data to cut off, just gonna say 1us now to be safe for 10e3, 10e4
# Although this is already automatically done by the np.argmin! 
x_min = np.argmin(avg_data[SIG_CH]) + 100

# Plot vertical line at peak
# plt.axvline(x=data[0, x_min], color='red')

# Cut the transient data so it starts at the peak
# Also zero the transient on x and y
# CH0 is useless at this point, may just end up cutting it out altogether
cut_data = avg_data[:, x_min:].copy()
cut_data[0] -= avg_data[0, x_min]
cut_data[SIG_CH] -= cut_data[SIG_CH].max() # if you use data instead of cut_data then fwd current will be included

# Models the expected transient format so it can be passed into curve_fit
# Vertical offset c not necessary due to adjustment of cut_data
# fe = 1/Te --> rate of emission
# def exp_func(t, a, f1, b, f2):
def exp_func(t, a, f1):
    return -a*np.exp(-f1*t) #-b*np.exp(-f2*t)

low_bounds = [0,0] #0,0]
high_bounds = [np.inf, np.inf] #, np.inf, np.inf]
params, cv = curve_fit(exp_func, cut_data[0], cut_data[SIG_CH], bounds=(low_bounds, high_bounds))
# a, f1, b, f2 = params
a, f1 = params

fit_y = -a*np.exp(-f1*cut_data[0]) #-b*np.exp(-f2*cut_data[0])

# PLOTTING ------------------------------------------------------------------------------------------
# Plot original data
# plt.plot(avg_data[0], avg_data[WAV_CH], label='Waveform')
# plt.plot(avg_data[0], avg_data[SIG_CH], label='Signal')
plt.ylim(-1, 0.1)

# Plot cut data
plt.plot(cut_data[0], cut_data[SIG_CH], label='Transient')

# Plot best fit curve
# plt.plot(cut_data[0], fit_y, color='red', label=f'Tau1 = {1/f1:0.4g} {unit}, Tau2 = {1/f2:0.4g} {unit}')
plt.plot(cut_data[0], fit_y, color='red', label=f'Tau1 = {1/f1:0.4g} {unit}')

# Plot residual
residual = fit_y - cut_data[SIG_CH]
plt.plot(cut_data[0], residual, color='green', label='Residual')

plt.xlabel(f'Time ({unit})')
plt.ylabel('Voltage (V)')
plt.legend()
plt.show()

# Problem with the current method of creating cut data is that it wastes resolution! Though now that I have it triggering on the falling edge of the waveform it's not as much of a problem
# Things to do:
# Add 2nd exponential to model
# Average a bunch of trials at the same temperature (can improve resolution, effective # of bits enob)

# Figure out why switching WAV_CH and SIG_CH truncates the transient...want to have flexibility with which scope inputs are used