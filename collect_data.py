# Contains all the functions used to collect transients and temperature data

import NI_USB5133_Communication_v2 as scope5133
import niscope
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
import settings as stg
import signal_processing as sp
import time

'''
HELPER FUNCTIONS
'''

def avg(waveforms):
    # Average all of the waveforms, create a master array to do so
    stacked = np.stack(waveforms)
    avg_data = np.mean(stacked, axis=0)
    return avg_data

def open(path, prefix):
    # I think each of these files are already averaged, so no need for averaging here?
    wf_buffer, wf_info = scope5133.waveform_open(path, prefix)
    avg_data = scope5133.waveform_construct(wf_buffer, wf_info)
    print(avg_data.shape)
    return avg_data


# Modifies session settings to collect temp_samples points from TEMP_CH only. Meant for brief instantaneous value acquisition
def config_temp_read(session):

    session.channels[stg.TEMP_CH].channel_enabled = True
    session.channels[stg.SIG_CH].channel_enabled = False

    session.configure_horizontal_timing(min_sample_rate=stg.sr, min_num_pts=stg.temp_samples, ref_position=0, num_records=1, enforce_realtime=True)

    session.configure_trigger_immediate()


# Modifies session settings to collect sig_samples points from SIG_CH only. Meant for capturing a transient across a longer time window
def config_sig_read(session):

    session.channels[stg.TEMP_CH].channel_enabled = False
    session.channels[stg.SIG_CH].channel_enabled = True

    session.configure_horizontal_timing(min_sample_rate=stg.sr, min_num_pts=stg.sig_samples, ref_position=stg.sig_ref_position, num_records=1, enforce_realtime=True)

    session.configure_trigger_edge(
        trigger_source      = "0", 
        level               = -1, 
        slope               = niscope.TriggerSlope.NEGATIVE, 
        trigger_coupling    = niscope.TriggerCoupling.DC
    )


# Sample from a specific channel. Uses horizontal/vertical configs that are set at time of call
def sample(session, channel, buffer):
    
    session.initiate()
    
    session.channels[channel].fetch_into(
        buffer,
        num_records = 1,
    )
    session.abort()
    return buffer


'''
AUTOMATIC DATA COLLECTION

Collects many transients at temp data points within a specified range and at a specified increment

Data structure:
waveforms[i] = ith transient data (raw voltages)
tc_values[i] = thermocouple reading during ith transient
'''

def collect_auto(session):

    waveforms = []
    tc_values = []

    # General purpose configuration
    num_samples = scope5133.config5133_single(
        session, 
        vpp0        = stg.vpp0, 
        vpp1        = stg.vpp1, 
        t           = stg.t, 
        sr          = stg.sr, 
        offset0     = stg.offset0, 
        offset1     = stg.offset1, 
        trigger_out = stg.IS_TRIGGER_OUT
    )

    # Allocate buffers
    temp_buffer = np.zeros(stg.temp_samples, dtype=float)
    sig_buffer = np.zeros(stg.sig_samples, dtype=float)


    # Get current temp (this is currently just a raw voltage)
    print("Starting:")
    t0 = time.perf_counter()
    config_temp_read(session)
    t1 = time.perf_counter()
    print("Time to config temp read: ", t1-t0)

    t2 = time.perf_counter()
    curr_tc_read = sample(session, stg.TEMP_CH, temp_buffer).copy()[0]
    t3 = time.perf_counter()
    print("Time to read temp: ", t3-t2)


    print(curr_tc_read)
    prev_tc_saved = curr_tc_read

    point_count = 0
    while((prev_tc_saved < stg.volt_max)):
        t6 = time.perf_counter()
        curr_tc_read = sample(session, stg.TEMP_CH, temp_buffer).copy()[0]
        t7 = time.perf_counter()
        print("Time to read temp: ", t7-t6)

        if ((curr_tc_read - prev_tc_saved) > stg.volt_step):
            # Acquire transient
            t4 = time.perf_counter()
            config_sig_read(session)
            waveforms.append(sample(session, stg.SIG_CH, sig_buffer).copy())
            tc_values.append(curr_tc_read)
            prev_tc_saved = curr_tc_read
            # print("ADDING: ", curr_tc_read)
            config_temp_read(session)
            point_count += 1
            t5 = time.perf_counter()
            print("Time to get sig: ", t5-t4)

    session.close()
    return waveforms, tc_values


'''
MANUAL DATA COLLECTION

Acquires a single transient, with the option to average multiple waveforms

This was how I originally collected data 

Data Structure:
    data[0] --> t
    data[1] --> CH0
    data[2] --> CH1
    waveforms[i] = data
'''

def collect_manual(session, num_waveforms):

    # NI5133 = niscope.Session('Dev1')  
    # Configure oscilloscope session
    num_samples = scope5133.config5133_single(
        session, 
        vpp0        = 4, 
        vpp1        = 4, 
        t           = 10e-6, 
        sr          = stg.sr, 
        offset0     = -1.5, 
        offset1     = 0, 
        trigger_out = True
    )
   

    session.configure_trigger_edge(
        trigger_source      = "0", 
        level               = -0.1, 
        slope               = niscope.TriggerSlope.NEGATIVE, 
        trigger_coupling    = niscope.TriggerCoupling.DC
    )

  
    waveforms = []
    for i in range(num_waveforms):
        waveforms.append(scope5133.exe5133_single(session, num_samples, plot=False))

    session.close()

    # Average all of the data arrays in waveforms, create a master array to do so
    avg_data = avg(waveforms)

    return avg_data
