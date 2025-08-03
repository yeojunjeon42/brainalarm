import numpy as np
import pywt
from scipy.fftpack import fft, ifft

def generate_surrogate(signal, num_surrogates=1000, max_iter=100):
    """
    Generate surrogate signals using IAAFT.
    """
    N = len(signal)
    sorted_signal = np.sort(signal)
    surrogates = []

    orig_spectrum = np.abs(fft(signal))
    for _ in range(num_surrogates):
        surr = np.random.permutation(signal)
        for _ in range(max_iter):
            surr_spectrum = np.abs(fft(surr))
            surr_phase = np.angle(fft(surr))
            surr = np.real(ifft(orig_spectrum * np.exp(1j * surr_phase)))
            surr = sorted_signal[np.argsort(np.argsort(surr))]
        surrogates.append(surr)
    return np.array(surrogates)

def modwt(signal, wavelet, level):
    """
    Perform MODWT using pywt SWT (stationary wavelet transform).
    """
    coeffs = pywt.swt(signal, wavelet, level=level)
    return coeffs

def imodwt(coeffs, wavelet):
    """
    Inverse MODWT using pywt ISWT.
    """
    return pywt.iswt(coeffs, wavelet)

def suBAR(signal, wavelet='sym4', level=5, num_surrogates=1000, alpha=0.05):
    """
    SuBAR implementation for single-channel EEG artifact removal.
    """
    coeffs = modwt(signal, wavelet, level)
    surrogates = generate_surrogate(signal, num_surrogates)
    
    # Decompose each surrogate
    surrogate_coeffs = [modwt(s, wavelet, level) for s in surrogates]

    # Initialize filtered coefficients
    filtered_coeffs = []

    for j in range(level):
        # Gather wavelet coefficients for all surrogates at level j
        w_sur = np.array([surr[j][1] for surr in surrogate_coeffs])  # detail coefficients

        # Mean and std over surrogates
        w_mean = np.mean(w_sur, axis=0)
        w_std = np.std(w_sur, axis=0)

        # Threshold using Chebyshev’s inequality (95% default)
        threshold = w_mean + np.sqrt(1/alpha) * w_std

        # Compare and filter
        w_orig = coeffs[j][1]
        w_filtered = np.where(np.abs(w_orig) > threshold, w_mean, w_orig)

        filtered_coeffs.append((coeffs[j][0], w_filtered))  # (approx, detail)

    # Reconstruct cleaned signal
    cleaned_signal = imodwt(filtered_coeffs, wavelet)
    return cleaned_signal