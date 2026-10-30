import numpy as np
import matplotlib.pyplot as plt
import signal_processing as sp

def plotter1(avg_data, decon, cut_data, fit_y, params, WAV_CH, SIG_CH):

    # Rescale time axis for ease of reading (does not modify avg_data[0] but generates a copy)
    t, unit = sp.rescale(avg_data[0])
    t_cut, unused = sp.rescale(cut_data[0])

    # Unpack fit parameters (including rescaling time constant)
    A, f1, c = params
    T1_arr = np.array([1/f1])
    T1_arr = sp.rescale(T1_arr)
    T1 = T1_arr[0]

    # Plot full averaged data
    # plt.plot(avg_data[0], avg_data[WAV_CH], label='Waveform', color='orange')
    plt.plot(t, avg_data[SIG_CH], label='Signal', color='blue')

    # Plot deconvolved data
    plt.plot(t, decon[1], label='Original Signal', color='red')

    # Plot exponential fit of deconvolved data
    plt.plot(t_cut, fit_y, label=f'A={A:.4f}, T1={T1[0]:.4f}{unit}, c={c:.4f}', color='green')

    # Plot residual
    residual = fit_y - cut_data[1]
    plt.plot(t_cut, residual, label='Residual', color='purple')

    plt.xlabel(f'Time ({unit})')
    plt.ylabel('Voltage (V)')
    plt.legend()
    plt.show()

def plotter2(avg_data, decon, cut_data, fit_y, params, WAV_CH, SIG_CH):

    # Rescale time axis for ease of reading (does not modify avg_data[0] but generates a copy)
    t, unit = sp.rescale(avg_data[0])
    t_cut, unused = sp.rescale(cut_data[0])

    # Unpack fit parameters (including rescaling time constant)
    A, f1, B, f2, c = params
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
    plt.plot(t_cut, fit_y, label=f'A={A:.4f}, T1={T1[0]:.4f}{unit}, \n B={B:.4f}, T2={T2[0]:.4f}{unit} \n c={c:.4f}', color='green')

    # Plot residual
    residual = fit_y - cut_data[1]
    plt.plot(t_cut, residual, label='Residual', color='purple')

    plt.xlabel(f'Time ({unit})')
    plt.ylabel('Voltage (V)')
    plt.ylim(-10, 1)
    plt.legend()