import numpy as np

def compute_fft(data, sr):
    n = len(data)
    if n == 0: return [], []
    freq = np.fft.rfftfreq(n, d=1/sr)
    fft_vals = np.abs(np.fft.rfft(data)) / n
    return freq, fft_vals

def compute_rms(data):
    if len(data) == 0: return 0.0
    return np.sqrt(np.mean(np.square(data)))
