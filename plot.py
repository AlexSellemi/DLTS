import numpy as np
import matplotlib.pyplot as plt
import signal_processing as sp

def plotter(avg_data, cut_data, fit_y, params, unit, WAV_CH, SIG_CH):

    a, f1, b, f2, = params
    # Plot full averaged data

    plt.plot(avg_data[0], avg_data[WAV_CH], label='Waveform', color='orange')
    plt.plot(avg_data[0], avg_data[SIG_CH], label='Signal', color='blue')

    # Plot vertical line at peak
    plt.axvline(x=cut_data[0, 0], color='black', ls='--')

    # Plot cut averaged data
    # plt.plot(cut_data[0], cut_data[SIG_CH], label='Transient')

    # Plot best fit curve
    plt.plot(cut_data[0], fit_y, color='red', label=f'Tau1 = {1/f1:0.4g} {unit}, Tau2 = {1/f2:0.4g} {unit}')
    # plt.plot(cut_data[0], fit_y, color='red', label=f'Tau1 = {1/f1:0.4g} {unit}')

    # Plot residual
    residual = fit_y - cut_data[SIG_CH]
    plt.plot(cut_data[0], residual, color='green', label='Residual')

    plt.xlabel(f'Time ({unit})')
    plt.ylabel('Voltage (V)')
    plt.ylim(-2, 0.2)
    plt.legend()
    plt.show()

def plotter2(avg_data, decon, cut_data, fit_y, params, WAV_CH, SIG_CH):

    # Rescale time axis for ease of reading (does not modify avg_data[0] but generates a copy)
    t, unit = sp.rescale(avg_data[0])
    t_cut, unused = sp.rescale(cut_data[0])

    # Unpack fit parameters (including rescaling time constant)
    A, B, f1, f2, c = params
    T1_arr = np.array([1/f1])
    T1_arr = sp.rescale(T1_arr)
    T1 = T1_arr[0]

    T2_arr = np.array([1/f2])
    T2_arr = sp.rescale(T2_arr)
    T2 = T2_arr[0]

    # Plot full averaged data
    # plt.plot(avg_data[0], avg_data[WAV_CH], label='Waveform', color='orange')
    plt.plot(t, avg_data[SIG_CH], label='Signal', color='blue')

    # Plot deconvolved data
    plt.plot(t, decon[1], label='Original Signal', color='red')

    # Plot exponential fit of deconvolved data
    plt.plot(t_cut, fit_y, label=f'T1={T1}{unit}, T2={T2}{unit}', color='green')

    # Plot residual
    residual = fit_y - cut_data[1]
    plt.plot(t_cut, residual, label='Residual', color='purple')

    plt.xlabel(f'Time ({unit})')
    plt.ylabel('Voltage (V)')
    plt.legend()
    plt.show()