# Approximation: fh = 0.35 / tr, where tr is rise time and fh is high frequency 3db cutoff
# Model frequency response transfer function as a low-pass (high-cut) filter
# wh = 2*pi*fh
# A(iw) = G * wh / iw + wh
# Take the inverse fourier transform of this to get h(t):
# h(t) = G * wh * exp(-wh*t) * u(t)

