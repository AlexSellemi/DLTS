import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import convolve
import scipy.fft as sfft
import matplotlib.pyplot as plt

# Rescaling should only be performed on a copied time axis for plotting
def rescale(time):
    t = time.copy()
    if t[-1] < 100e-6:
        t *= 1e6
        unit = 'us'
    elif t[-1] < 100e-3:
        t *= 1e3
        unit = 'ms'
    else:
        unit = 's'
    return t, unit

# Fit exponential(s) to the appropriate part of the data
def exp_fit(data):

    # Analyze transient data from peak only, not before
    x_min = np.argmin(data[1])
    cut_data = data[:, x_min:].copy()

    # Exponential curve fit
    # fe = 1/Te
    def exponential(t, A, f1, B, f2, c):
        return -A*np.exp(-f1*t) - B*np.exp(-f2*t) + c

    low_bounds = [0, 0, 0, 0, 0]
    high = np.inf
    high_bounds = [high, high, high, high, high]
    params, cv = curve_fit(exponential, cut_data[0], cut_data[1], bounds=(low_bounds, high_bounds))
    A, f1, B, f2, c = params
    fit_y = -A*np.exp(-f1*cut_data[0]) - B*np.exp(-f2*cut_data[0]) + c

    return cut_data, fit_y, params

'''
Richardson-Lucy Method that I probably won't use b/c it's more useful for images
1. Start with some initial estimate (an array) of your actual signal 
2. Convolve that estimate with h(t)
3. Divide the observed signal by the array calculated in 2
4. Convolve the result from 3 with the flipped h(t). This is your correction factor
5. estimate *= correction, and repeat!
'''

def deconvolve_RL(data, SIG_CH):
    # use full data, not cut_data
    t = data[0].copy()
    d = data[SIG_CH].copy()
    print(d.shape)

    G = 10e3
    fh = 500000            # cutoff freq
    wh = 2 * np.pi * fh
    h = wh * np.exp(-wh*t) # omit gain for recovered input to be at same scale as output
    print(sum(h))
    h /= sum(h)
    h_flip = h[::-1]
    estimate = np.full(d.size, np.mean(d))

    for _ in range(15):
        a = convolve(estimate, h, mode='full')[:len(d)]
        a = np.clip(a, 0, None)              # do not want to accidentally divide by 0
        ratio = d / a
        correction = convolve(ratio, h_flip, mode='full')[len(h)-1 : len(h)-1 + len(d)]
        estimate *= correction

    h *= sum(h)
    return estimate, h

# Wiener deconvolution
def deconvolve_W(data, SIG_CH, K):
    t = data[0]
    d = data[SIG_CH].copy()

    # Pad data to avoid wraparound effects of fft
    pad = 50
    d_pad = np.pad(d, pad_width=pad, mode='edge')
    dt = t[1] - t[0]
    N = len(d_pad)
    f = sfft.fftfreq(N, d=dt)

    D = sfft.fft(d_pad)
    G = 10e3
    fh = 500000         # cutoff freq
    wh = 2 * np.pi * fh

    # Model H directly instead of taking fft(h(t)) because h(t) is poorly modeled on the time axis (it's mostly 0)
    H = wh / (wh + 1j * 2 * np.pi * f)

    # Wiener Method: Instead of dividing by H, multiply by H* / (H^2 + K)
    H_conj = np.conj(H)
    W = H_conj / (np.abs(H)**2 + K)
    X = D * W
    x = np.real(sfft.ifft(X))

    # Un-pad x
    x = x[pad:-pad]

    # Return deconvolved data as a 2D array with a time axis for ease of handling
    return np.vstack((t, x))