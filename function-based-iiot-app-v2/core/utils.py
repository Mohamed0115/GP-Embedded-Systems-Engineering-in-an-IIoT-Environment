import numpy as np

def compute_fft(data, sr):
    """Compute single-sided FFT amplitude spectrum.
    
    Removes DC offset (mean) before FFT to eliminate the 0 Hz spike.
    Multiplies by 2 for single-sided spectrum (except DC and Nyquist).
    
    Args:
        data: array of calibrated physical values (g, mm/s, etc.)
        sr: sample rate in Hz
    Returns:
        freq: array of frequency bins in Hz
        fft_vals: array of peak amplitude values in same unit as input data
    """
    n = len(data)
    if n == 0: return [], []
    # Remove DC offset to eliminate the 0 Hz spike
    data_centered = data - np.mean(data)
    freq = np.fft.rfftfreq(n, d=1/sr)
    fft_vals = np.abs(np.fft.rfft(data_centered)) / n
    # Multiply by 2 for single-sided spectrum (energy from negative freqs)
    # DC (index 0) and Nyquist (last index if n is even) stay as-is
    fft_vals[1:-1] *= 2
    return freq, fft_vals

def compute_rms(data):
    """Compute Root Mean Square of the data array."""
    if len(data) == 0: return 0.0
    return np.sqrt(np.mean(np.square(data)))

def convert_fft_units(freq, fft_vals, from_unit, to_unit):
    """Convert FFT amplitude values between acceleration (g) and velocity (mm/s).
    
    Uses the physics relationship in frequency domain:
        Velocity(f) = Acceleration(f) / (2 * pi * f)
    with unit conversion: 1g = 9806.65 mm/s²
    
    So:  mm/s = g * 9806.65 / (2 * pi * f)
    And: g    = mm/s * (2 * pi * f) / 9806.65
    
    Args:
        freq: array of frequency bins (Hz)
        fft_vals: array of FFT amplitudes in 'from_unit'
        from_unit: current unit string, e.g. "g" or "mm/s"
        to_unit: target unit string
    Returns:
        converted: array of FFT amplitudes in 'to_unit'
    """
    freq = np.array(freq, dtype=float)
    fft_vals = np.array(fft_vals, dtype=float)
    converted = fft_vals.copy()
    
    if from_unit == to_unit:
        return converted
    
    # Constant: 1g = 9806.65 mm/s²
    G_TO_MMS2 = 9806.65
    
    if from_unit == "g" and to_unit == "mm/s":
        # Velocity = Acceleration / (2*pi*f) => mm/s = g * 9806.65 / (2*pi*f)
        for i in range(len(freq)):
            if freq[i] > 0:
                converted[i] = fft_vals[i] * G_TO_MMS2 / (2.0 * np.pi * freq[i])
            else:
                converted[i] = 0.0  # DC bin has no velocity meaning
                
    elif from_unit == "mm/s" and to_unit == "g":
        # Acceleration = Velocity * (2*pi*f) => g = mm/s * (2*pi*f) / 9806.65
        for i in range(len(freq)):
            if freq[i] > 0:
                converted[i] = fft_vals[i] * (2.0 * np.pi * freq[i]) / G_TO_MMS2
            else:
                converted[i] = 0.0
    
    return converted
