'''
package for NI USB-5133 Oscilloscope communication

Yueyun Chen

20220410 v1 single sequence acquisition
20220413 v2 add continuous acquisition


# Channels: CH 0, CH 1, PFI 1 (8 bits resolution, 100Ms/s sampling rate, and 4MB onboard memory for each input channel)

# IO limits:
    # each acquisition is limited to ~4e6 points due to onboard memory <=> ~40 ms at 100Ms/sec
    # 7 ms to use fetch_into to read 1e4 points, 7 ms to use fetch to read 1e4 points (TDS3034 needs ~150 ms to read 1e4 pts)
    # 60 ms to use fetch_into to read 1e6 points, 100 ms to use fetch to read 1e6 points
    
# Continuous IO limits:
    # 1.25 Msa/s sampling rate and 3 Msa per fetch is the sweet point for continuous data logging
    # total amount of data expected to acquire needs to be smaller than 2GB, which roughly corresponds to 800 sec acquisition time under the conditions above
    # 3Msa per fetch gives you the abilibity to fetch as fast as possible (minimize the number of fetches) while preventing the data to be overwriten, so this number should not be changed under any circumstances
    # 1.25 Msa/s is the fastest sampling rate the IO can handle without any data being overwritten under an arbitrarily long acquisition time
    
# Vertical configurations: 
    # range: vertical voltage range, float, 0.04, 0.1, 0.2, 0.4, 1.0, 2.0, 4.0, 10, 20, 40
    # offset: vertical voltage range, float, +/-0.4 for range<1.0, +/-4.0 for range<10, +/-25 for range=10, +/-20 for range=20, +/-10 for range=40
    # coupling: niscope.VerticalCoupling.DA/AC/GND
    
# Horizontal configurations:
    # min_sample_rate: sampling rate, float
    # min_num_pts: number of points to acquire, int, 1 to 4e6
    # num_records: has to be 1 for NI5133??
'''

# python package version: niscope 1.4.1
# LabVIEW driver version: NI-SCOPE 21.0.0
import niscope
import numpy as np
import time
import pandas as pd
from matplotlib import pyplot as plt

'''
# determine the number of samples per acquisition
# inputs: 
    t, acquisition period
    sr, sampling rate
    tc, compensation time to ensure the full signal is acquired
# return:
    number of samples
'''
def num_pts(t,sr,tc):

    pts = (t+tc)*sr

    return int(pts)

'''
# determine the vertical voltage configuration
# inputs: 
    vpp, expected peak-to-peak voltage
# optional inputs:
    offset, expected offset voltage: default, 0; other options, any float
# ouput:
    appropriate voltage configuration for NI5133: tuple of (vpp,offset)
'''
def volt_config(vpp,offset=0):
    
    offset_tuple = (0.4, 4, 25, 20, 10)
    vpp_tuple = ((0.04, 0.1, 0.2, 0.4), (1.0, 2.0, 4.0), (10), (20), (40))
    
    # check   it's too high or too low
    if vpp/2+abs(offset) > 30:
        print('Caution! Input voltage is too high.')
        if offset>10:
            return (40,10)
        elif offset<-10:
            return (40,-10)
        else:
            return (40,offset)
    elif vpp <= 0.01:
        print('Input voltage is too low, consider increase preamp\'s gain to boost performance')
    
    # flatten tuple
    def flatten_tuple(data):
        if isinstance(data, tuple):
            if len(data) == 0:
                return ()
            else:
                return flatten_tuple(data[0]) + flatten_tuple(data[1:])
        else:
            return (data,)
    
    # iterative to find the proper setting
    i = 0
    while i<len(offset_tuple):
        if offset_tuple[i] >= abs(offset):
            for vpp_level in flatten_tuple(vpp_tuple[i:]):
                if vpp_level >= vpp:
                    return (vpp_level,offset)
        i += 1

'''
# configurate NI5133 for a single sequence acquisition
    20 ns extra acquisition time by default to compensate for trigger delay
# inputs:
    session, currently active NI5133 session
    vpp0,vpp1, expected peak-to-peak voltage for channel 0 and 1
    t, acquisition period
# optional inputs:
    sr, sampling rate (samples/sec): default, 100e6; other options, 0<sr<=100e6
    tc, compensation time (sec) to ensure the full signal is acquired: default, 20e-9; other options, tc>=0
    offset0,offset1, expected offset voltage for channel 0 and 1
    trigger_out, bool for sending start trigger through PFI 1 or not: default, True; other options, False
# return:
    number of samples per channel for this acquisition  
'''
def config5133_single(session,vpp0,vpp1,t,sr=100e6,tc=20e-9,offset0=0,offset1=0,trigger_out=True):
    
    # do not allow onboard memory overwrite
    session.allow_more_records_than_memory = False
    
    # calculate number of samples to acquire per channel and proper voltage setting for each channel
    samples = num_pts(t,sr,tc)
    (volt_range_ch0,volt_offset_ch0) = volt_config(vpp0,offset0)
    (volt_range_ch1,volt_offset_ch1) = volt_config(vpp1,offset1)
    
    # check if number of samples is too high for a single acquisition
    if samples > 4194303:
        print('insufficient onboard memory, points of acquisition set to maximum: 4194303')
        samples = int(4194303)
    
    # configure vertical parameters
    session.channels[0].configure_vertical(range=volt_range_ch0, coupling=niscope.VerticalCoupling.DC, offset=volt_offset_ch0, probe_attenuation=1, enabled=True)
    session.channels[1].configure_vertical(range=volt_range_ch1, coupling=niscope.VerticalCoupling.DC, offset=volt_offset_ch1, probe_attenuation=1, enabled=True)
    
    # configure horizontal parameters
    session.configure_horizontal_timing(min_sample_rate=sr, min_num_pts=samples, ref_position=0, num_records=1, enforce_realtime=True) # configure horizontal parameters: sampling rate, number of points to acquire per acquisition, position of reference event in the waveform in percentage, number of acquisitions to record, enforce realtime or not
    
    # If user wants to configure this internally:
    # configure trigger: immediately triggered after session initiation
    session.configure_trigger_immediate()

    # If user wants to configure this internally:
    # session.configure_trigger_edge(trigger_source="0", level=0.1, trigger_coupling=niscope.TriggerCoupling.DC)

    # configure trigger output
    if trigger_out == True:
        session.exported_start_trigger_output_terminal = 'VAL_PFI_1'
    else: 
        session.exported_start_trigger_output_terminal = 'VAL_NO_SOURCE'
    session.exported_advance_trigger_output_terminal = 'VAL_NO_SOURCE'
    session.exported_ref_trigger_output_terminal = 'VAL_NO_SOURCE'
    
    # return number of samples per channel per acquisition
    return samples

'''
# initiate NI5133 single sequence acquisition and read out the acquired waveform
# inputs:
    session, currently active NI5133 session
    samples, number of samples per channel to acquire
# optional inputs:
    fetch, bool for reading data or not: default, True; other options, False
# return:
    tuple of waveform data (int8 numpy array) and waveform information (pandas data frame), or None
'''
def ini5133_single(session,samples,fetch=True):
    
    # initiate acquisition
    session.initiate()
    
    # if not fetching, return None
    if fetch == False:
        return None
    
    # create numpy array buffer for dual channel numpy.int8 data logging
    wf_buffer = np.ndarray((2,samples), dtype=np.int8)
    
    # read waveform data and related info
    wf_info_ch0 = session.channels[0].fetch_into(wf_buffer[0],num_records=1)[0]
    wf_info_ch1 = session.channels[1].fetch_into(wf_buffer[1],num_records=1)[0]
    
    # create a list of useful waveform info
    wf_info = pd.DataFrame([[wf_info_ch0.channel,wf_info_ch0.record,samples,wf_info_ch0.gain,wf_info_ch0.offset,wf_info_ch0.x_increment,wf_info_ch0.relative_initial_x,wf_info_ch0.absolute_initial_x],\
                            [wf_info_ch1.channel,wf_info_ch1.record,samples,wf_info_ch1.gain,wf_info_ch1.offset,wf_info_ch1.x_increment,wf_info_ch1.relative_initial_x,wf_info_ch1.absolute_initial_x]],\
                columns = ['channel','record','samples','y_increment','y_offset','x_increment','relative_initial_x','absolute_initial_x'])
    
    return (wf_buffer,wf_info)
    
'''
# construct waveform using waveform buffer and waveform info (based on exe5133_single return now)
# inputs:
    wf_buffer, int 8 numpy array of voltage data
    wf_info, pandas data frame of related waveform information
# optional inputs:
    binning, binning how many points together: default, 1; other options: positive integers
    include_remainder, include the last few redundant points in the original data: default, True; other options, False
# return:
    float64 numpy array of waveforms, array([time_array,volt_ch0_array,volt_ch1_array])
'''
def waveform_construct(wf_buffer,wf_info,binning=1,include_remainder=True):
    
    # extract number of samples per channel, y_incre, y_offset, x_incre
    samples = wf_info.at[0,'samples']
    x_incre = wf_info.at[0,'x_increment']
    y_incre_ch0 = wf_info.at[0,'y_increment']
    y_offset_ch0 = wf_info.at[0,'y_offset']
    y_incre_ch1 = wf_info.at[1,'y_increment']
    y_offset_ch1 = wf_info.at[1,'y_offset']
    
    if binning == 1:
        # if no binning required, scale the whole waveform
        time_ch = np.arange(0,samples,1,dtype=np.float64)*x_incre
        volt_ch0 = wf_buffer[0]*y_incre_ch0 + y_offset_ch0
        volt_ch1 = wf_buffer[1]*y_incre_ch1 + y_offset_ch1
    else:
        # when binning required, get number of complete bins and number of samples left
        bin_num = int(samples//binning)
        bin_mod = int(samples % binning)
        
        if bin_mod == 0:
            # when total number of samples is evenly divisible by bin size, bin the samples
            time_ave_ch = np.arange(0,samples,binning,dtype=np.float64)*x_incre
            wf_ave_ch0 = np.average(wf_buffer[0].reshape(bin_num,binning),axis=1)
            wf_ave_ch1 = np.average(wf_buffer[1].reshape(bin_num,binning),axis=1)
        else:
            # when it's not evenly divisible, bin the divisible part and append the average of the last few samples
            time_ave_ch = np.arange(0,samples,binning,dtype=np.float64)*x_incre
            wf_ave_ch0 = np.append(np.average(wf_buffer[0][:-bin_mod].reshape(bin_num,binning),axis=1),np.average(wf_buffer[0][-bin_mod:]))
            wf_ave_ch1 = np.append(np.average(wf_buffer[1][:-bin_mod].reshape(bin_num,binning),axis=1),np.average(wf_buffer[1][-bin_mod:]))
            
            if include_remainder == False:
                # if the remaider samples are not desired, toss them
                time_ave_ch = time_ave_ch[:-1]
                wf_ave_ch0 = wf_ave_ch0[:-1]
                wf_ave_ch1 = wf_ave_ch1[:-1]
        
        # scale the binned waveform
        time_ch = time_ave_ch
        volt_ch0 = wf_ave_ch0*y_incre_ch0 + y_offset_ch0
        volt_ch1 = wf_ave_ch1*y_incre_ch1 + y_offset_ch1

    return np.array([time_ch,volt_ch0,volt_ch1],dtype=np.float64)

'''
# save waveform buffer and waveform info into two separate files (based on exe5133_single return now)
    wf_buffer saved as path\\YYYYMMDD_HHMMSS_prefix_wf.bin
    wf_info saved as path\\YYYYMMDD_HHMMSS_prefix_wfinfo.xlsx
# inputs:
    wf_buffer, int 8 numpy array of voltage data
    wf_info, pandas data frame of related waveform information
# optional inputs:
    path, saving folder: default, 'C:\\Users\\Public\\Documents'
    prefix, file name prefix: default, 'NI5133_Acquisition'
    indicator, bool for print uppon saving: default, True; other options, False  
# retun:
    N/A
'''
def waveform_save(wf_buffer,wf_info,path='C:\\Users\\Public\\Documents',prefix='NI5133_Acquisition',indicator=True, return_ts= False):
    
    # get time 
    ts = time.strftime('%Y%m%d_%H%M%S',time.localtime())
    path_prefix = f'{path}\\{ts}_{prefix}'
    
    # save waveform buffer as binary
    wf_buffer.astype('int8').tofile(f'{path_prefix}_wf.bin')
    
    # save waveform info as text
    wf_info.to_excel(f'{path_prefix}_wfinfo.xlsx',index=False)
    
    # print saved files' names
    if indicator == True:
        print(f'waveform data saved as {path_prefix}_wf.bin')
        print(f'waveform info saved as {path_prefix}_wfinfo.xlsx')
    
    if return_ts == True:
        return ts

'''
# open a previously saved waveform data (int8) and related info (based on exe5133_single return now)
    assuming suffix '_wf.bin' for binary waveform data and '_wfinfo.xlsx' for waveform info
# inputs:
    path, saving folder
    prefix, file name  (time stamp and) prefix
# return:
    tuple of waveform data (int8 numpy array) and waveform information (pandas)
'''
def waveform_open(path,prefix, os):
    
    # load waveform info into pandas data frame, get number of samples per channel and total number of channels
    if os == "mac":
        wf_info = pd.read_excel(f'{path}/{prefix}_wfinfo.xlsx')
    elif os == "windows":
        wf_info = pd.read_excel(f'{path}\\{prefix}_wfinfo.xlsx')
    samples = int(wf_info.at[0,'samples'])
    channels = int(wf_info.shape[0])
    
    # load waveform data into numpy array, reshape
    if os == "mac":
        wf_buffer = np.fromfile(f'{path}/{prefix}_wf.bin',dtype='int8')
    elif os == "windows":
        wf_buffer = np.fromfile(f'{path}\\{prefix}_wf.bin',dtype='int8')
    wf_buffer = wf_buffer.reshape(channels,samples)
    
    return (wf_buffer,wf_info)

'''
# plot the aquired waveform (based on exe5133_single return now)
# inputs:
    wf, constructed numpy array of waveform
# return:
    N/A
'''
def waveform_plot(wf):
    
    # time axis auto scaling 
    if wf[0][-1] <100e-6:
        wf[0] = wf[0]*1e6
        unit = 'us'
    elif wf[0][-1] <100e-3:
        wf[0] = wf[0]*1e3
        unit = 'ms'
    else:
        unit = 's'
    
    plt.plot(wf[0],wf[1],label='CH 0')
    plt.plot(wf[0],wf[2],label='CH 1')
    plt.legend()
    
    plt.xlabel(f'time ({unit})')
    plt.ylabel('voltage (V)')
    plt.show()
    
    return

'''
# routine for NI USB5133 single sequence acquisition: initiate, read, save, plot, and return constructed waveform
# inputs:
    session, currently active NI5133 session
    samples, number of samples per channel to acquire
# optional inputs:
    save, bool: default, True; other options, False
    path, saving folder: default, 'C:\\Users\\Public\\Documents'
    prefix, file name prefix: default, 'NI5133_Acquisition'
    plot, bool: default, True; other options, False
    binning, binning how many points together: default, 1; other options: positive integers
    include_remainder, include the last few redundant points in the original data: default, True; other options, False
    wf_return, what kind of waveform data to return: default, 'waveform'; other options, 'binary', or None
# return:
    float64 numpy array of waveforms, or None
'''
def exe5133_single(session,samples,save=True,path='C:\\Users\\Public\\Documents',prefix='NI5133_Acquisition',plot=True,binning=1,include_remainder=True,wf_return='waveform'):
    
    # only initiate session and return None if no fetching required
    if save == False and plot == False and wf_return == None:
        return ini5133_single(session,samples,fetch=False)
    
    # fetch data otherwise
    (wf_buffer,wf_info) = ini5133_single(session,samples,fetch=True)
    
    # save data if required
    if save == True:
        ts = waveform_save(wf_buffer,wf_info,path=path,prefix=prefix,indicator=True, return_ts= True)
    
    # construct waveform if required
    if plot == True or wf_return == 'waveform':
        wf = waveform_construct(wf_buffer,wf_info,binning=binning,include_remainder=include_remainder)
        
    # plot if required
    if plot == True:
        waveform_plot(wf)
        
    # return desired data
    if wf_return == 'waveform' :   
        return wf
    elif wf_return == 'binary':
        return (wf_buffer,wf_info)
    elif wf_return == 'binary w/ ts':
        return (wf_buffer, wf_info, ts)
    else:
        return None
    
'''
# configurate NI5133 for a continuous acquisition
    20 ns extra acquisition time by default to compensate for trigger delay
    needs 3M samples per fetch to maximize compatible sampling rate
    total expected data size needs to be lower than 2GB
# inputs:
    session, currently active NI5133 session
    vpp0,vpp1, expected peak-to-peak voltage for channel 0 and 1
    t, acquisition period
# optional inputs:
    sr, sampling rate (samples/sec): default, 1.25e6; other options, 0<sr<=1.25e6
    tc, compensation time (sec) to ensure the full signal is acquired: default, 20e-9; other options, tc>=0
    offset0,offset1, expected offset voltage for channel 0 and 1
    trigger_out, bool for sending start trigger through PFI 1 or not: default, True; other options, False
# return:
    number of samples per channel for this acquisition  
'''
def config5133_continuous(session,vpp0,vpp1,t,sr=1.25e6,tc=20e-9,offset0=0,offset1=0,trigger_out=True):
    
    # allow onboard memory overwrite not allowed: device not supported, workaround is set min_num_pts to 1 and use software trigger
    session.allow_more_records_than_memory = False
    
    # check if sampling rate is appropriate 
    if sr > 1.25e6:
        print('sampling rate is too high, set to 1.25e6 to allow continuous data reading')
        sr = 1.25e6
    
    # calculate number of samples to acquire per channel and proper voltage setting for each channel
    samples = num_pts(t,sr,tc)
    (volt_range_ch0,volt_offset_ch0) = volt_config(vpp0,offset0)
    (volt_range_ch1,volt_offset_ch1) = volt_config(vpp1,offset1)
    
    # check if expected data size is appropriate 
    if samples*2 > 2e9:
        print('expected data size exceeds 2GB limit, total sample per channel is lowered to 1e9 to accommodate that')
        samples = int(1e9)
    
    # configure vertical parameters
    session.channels[0].configure_vertical(range=volt_range_ch0, coupling=niscope.VerticalCoupling.DC, offset=volt_offset_ch0, probe_attenuation=1, enabled=True)
    session.channels[1].configure_vertical(range=volt_range_ch1, coupling=niscope.VerticalCoupling.DC, offset=volt_offset_ch1, probe_attenuation=1, enabled=True)
    
    # configure horizontal parameters
    session.configure_horizontal_timing(min_sample_rate=sr, min_num_pts=1, ref_position=0, num_records=1, enforce_realtime=True) # configure horizontal parameters: sampling rate, number of points to acquire per acquisition, position of reference event in the waveform in percentage, number of acquisitions to record, enforce realtime or not
    
    # configure trigger: software trigger means continuous acquisition after session initiation until aborted
    session.configure_trigger_software()
    
    # configure trigger output
    if trigger_out == True:
        session.exported_start_trigger_output_terminal = 'VAL_PFI_1'
    else: 
        session.exported_start_trigger_output_terminal = 'VAL_NO_SOURCE'
    session.exported_advance_trigger_output_terminal = 'VAL_NO_SOURCE'
    session.exported_ref_trigger_output_terminal = 'VAL_NO_SOURCE'
    
    # return number of samples per channel per acquisition
    return samples

'''
# initiate NI5133 continuous acquisition and read out the acquired waveform
    fixed 3M samples per fetch to maximize compatible sampling rate
# inputs:
    session, currently active NI5133 session
    samples, number of samples per channel to acquire
# optional inputs:
    fetch, bool for reading data or not: default, True; other options, False
# return:
    tuple of waveform data (int8 numpy array) and waveform information (pandas data frame), or None
'''
def ini5133_continuous(session,samples,fetch=True):
    
    # if not fetching, initiate acquisition and return None
    if fetch == False:
        session.initiate()
        return None
    
    # create numpy array buffer for dual channel numpy.int8 data logging
    wf_buffer = np.ndarray((2,samples), dtype=np.int8)
    
    # create index iteration variables
    cur_index = 0
    sample_per_fetch = int(3e6)
    
    # initiate acquisition
    session.initiate()
    
    # read waveform data and related info for the first fetch
    wf_info_ch0 = session.channels[0].fetch_into(wf_buffer[0][cur_index:cur_index + sample_per_fetch],relative_to=niscope.FetchRelativeTo.READ_POINTER,num_records=1,timeout=-1)[0]
    wf_info_ch1 = session.channels[1].fetch_into(wf_buffer[1][cur_index:cur_index + sample_per_fetch],relative_to=niscope.FetchRelativeTo.READ_POINTER,num_records=1,timeout=-1)[0]
    cur_index += sample_per_fetch
    
    # for all additional fetches, discard the waveform info
    while cur_index < samples:
        session.channels[0].fetch_into(wf_buffer[0][cur_index:cur_index + sample_per_fetch],relative_to=niscope.FetchRelativeTo.READ_POINTER,num_records=1,timeout=-1)
        session.channels[1].fetch_into(wf_buffer[1][cur_index:cur_index + sample_per_fetch],relative_to=niscope.FetchRelativeTo.READ_POINTER,num_records=1,timeout=-1)
        cur_index += sample_per_fetch
    
    # abort acquisition when finished
    session.abort()
    
    # create a list of useful waveform info
    wf_info = pd.DataFrame([[wf_info_ch0.channel,wf_info_ch0.record,samples,wf_info_ch0.gain,wf_info_ch0.offset,wf_info_ch0.x_increment,wf_info_ch0.relative_initial_x,wf_info_ch0.absolute_initial_x],\
                            [wf_info_ch1.channel,wf_info_ch1.record,samples,wf_info_ch1.gain,wf_info_ch1.offset,wf_info_ch1.x_increment,wf_info_ch1.relative_initial_x,wf_info_ch1.absolute_initial_x]],\
                columns = ['channel','record','samples','y_increment','y_offset','x_increment','relative_initial_x','absolute_initial_x'])
    
    return (wf_buffer,wf_info)

'''
# routine for NI USB5133 continuous acquisition: initiate, read, save, plot, and return constructed waveform
# inputs:
    session, currently active NI5133 session
    samples, number of samples per channel to acquire
# optional inputs:
    save, bool: default, True; other options, False
    path, saving folder: default, 'C:\\Users\\Public\\Documents'
    prefix, file name prefix: default, 'NI5133_Acquisition'
    plot, bool: default, True; other options, False
    binning, binning how many points together: default, 1; other options: positive integers
    include_remainder, include the last few redundant points in the original data: default, True; other options, False
    wf_return, what kind of waveform data to return: default, 'waveform'; other options, 'binary', or None
# return:
    float64 numpy array of waveforms, or None
'''
def exe5133_continuous(session,samples,save=True,path='C:\\Users\\Public\\Documents',prefix='NI5133_Acquisition', plot=True,binning=1,include_remainder=True,wf_return='waveform'):
    
    # only initiate session and return None if no fetching required
    if save == False and plot == False and wf_return == None:
        return ini5133_continuous(session,samples,fetch=False)
    
    # fetch data otherwise
    (wf_buffer,wf_info) = ini5133_continuous(session,samples,fetch=True)
    
    # save data if required
    if save == True:
        waveform_save(wf_buffer,wf_info,path=path,prefix=prefix,indicator=True)
    
    # construct waveform if required
    if plot == True or wf_return == 'waveform':
        wf = waveform_construct(wf_buffer,wf_info,binning=binning,include_remainder=include_remainder)
        
    # plot if required
    if plot == True:
        waveform_plot(wf)
        
    # return desired data
    if wf_return == 'waveform' :   
        return wf
    elif wf_return == 'binary':
        return (wf_buffer,wf_info)
    else:
        return None
   