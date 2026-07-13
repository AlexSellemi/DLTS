import NI_USB5133_Communication_v2 as scope5133
import niscope
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np

def avg(waveforms):
    # Average all of the waveforms, create a master array to do so
    stacked = np.stack(waveforms)
    avg_data = np.mean(stacked, axis=0)
    return avg_data

def collect(sr, num_waveforms):

    # Start and configure oscilloscope current session
    NI5133 = niscope.Session('Dev1')  
    num_samples = scope5133.config5133_single(NI5133, vpp0=4, vpp1=4, t=10e-6, sr=sr, offset0=0, offset1=-2, trigger_out=True)
    NI5133.configure_trigger_edge(trigger_source="0", level=0.1, slope=niscope.TriggerSlope.NEGATIVE, trigger_coupling=niscope.TriggerCoupling.DC)

    '''
    execute acquisition:
    data[0] --> t
    data[1] --> CH0
    data[2] --> CH1
    waveforms[i] = data
    '''
    waveforms = []
    for i in range(num_waveforms):
        waveforms.append(scope5133.exe5133_single(NI5133, num_samples, plot=False))

    # end session
    NI5133.close()

    # Average all of the data arrays in waveforms, create a master array to do so
    avg_data = avg(waveforms)

    return avg_data

def open(path, prefix, os):
    # I think each of these files are already averaged, so no need for averaging here?
    wf_buffer, wf_info = scope5133.waveform_open(path, prefix, os)
    avg_data = scope5133.waveform_construct(wf_buffer, wf_info)
    return avg_data