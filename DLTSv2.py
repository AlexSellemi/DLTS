import NI_USB5133_Communication_v2 as scope5133
import niscope
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
# import signal_processing

# Oscilloscope parameters
sr = 100e6
num_waveforms = 100
WAV_CH = 1 + 1
SIG_CH = 0 + 1

# Start and configure oscilloscope current session
NI5133 = niscope.Session('Dev1')  
#  t = 20e-6
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

# feed waveforms to signal_processing

# SIGNAL PROCESSING ------------------------------------------------------------------------------------------

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


# Use rise times of Femto to determine which portion of the data to cut off
# Although this is already automatically done by the np.argmin! 
x_min = np.argmin(avg_data[SIG_CH]) + 45

# Zero averaged data on y
avg_data[SIG_CH] -= avg_data[SIG_CH, x_min:].max()

# Waveform channel sorta useless at this point, may just end up cutting it out as well
# Cut the transient data so it starts at the peak
cut_data = avg_data[:, x_min:].copy()

# wrapper: fit_y = best_fit(data, x_min, SIG_CH)
# Models the expected transient format so it can be passed into curve_fit
# Vertical offset c not necessary due to adjustment of cut_data
# fe = 1/Te --> rate of emission
def exp_func(t, a, f1, b, f2, t2):
# def exp_func(t, a, f1):
    return -a*np.exp(-f1*t) + b*np.exp(-f2*(t-t2))

low_bounds = [0, 0, 0, 0, -np.inf]
high_bounds = [np.inf, np.inf, np.inf, np.inf, np.inf]
params, cv = curve_fit(exp_func, avg_data[0], avg_data[SIG_CH], bounds=(low_bounds, high_bounds))
a, f1, b, f2, t2 = params
# a, f1, = prams

fit_y = -a*np.exp(-f1*avg_data[0]) + b*np.exp(-f2*(avg_data[0]-t2))

# PLOTTING ------------------------------------------------------------------------------------------
# Plot full averaged data
# plt.plot(avg_data[0], avg_data[WAV_CH], label='Waveform', color='orange')
plt.plot(avg_data[0], avg_data[SIG_CH], label='Signal', color='blue')

# Plot vertical line at peak
plt.axvline(x=cut_data[0, 0], color='black', ls='--')

# Plot cut averaged data
# plt.plot(cut_data[0], cut_data[SIG_CH], label='Transient')

# Plot best fit curve
plt.plot(avg_data[0], fit_y, color='red', label=f'Tau1 = {1/f1:0.4g} {unit}, Tau2 = {1/f2:0.4g} {unit}')
# plt.plot(cut_data[0], fit_y, color='red', label=f'Tau1 = {1/f1:0.4g} {unit}')

# Plot residual
residual = fit_y - avg_data[SIG_CH]
plt.plot(avg_data[0], residual, color='green', label='Residual')

plt.xlabel(f'Time ({unit})')
plt.ylabel('Voltage (V)')
# plt.ylim(-1, 0.1)
plt.legend()
plt.show()