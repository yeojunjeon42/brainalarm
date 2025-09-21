import numpy as np
from scipy.signal import firwin, filtfilt, welch
# import pywt
from scipy.fftpack import fft, ifft
#fir
def filter_bandpass(data, hl, fs, numtaps=101):
    """
    FIR bandpass filter using firwin.
    - lowcut, highcut: 주파수 대역 (Hz)
    - fs: 샘플링 주파수 (Hz)
    - numtaps: 필터 계수 수 (길이)
    """
    nyq = 0.5 * fs
    taps = firwin(numtaps, [hl[0] / nyq, hl[1] / nyq], pass_zero=False, window='blackman')
    filtered_data = filtfilt(taps, [1.0], data)
    return filtered_data


def filter_notch(data, notch_freq, fs, quality_factor=30, numtaps=101):
    nyq = 0.5 * fs
    freq_bw = notch_freq / quality_factor
    f1 = (notch_freq - freq_bw/2) / nyq
    f2 = (notch_freq + freq_bw/2) / nyq
    taps = firwin(numtaps,[f1, f2],pass_zero='bandstop', window='blackman')
    filtered_data = filtfilt(taps, [1.0],data)
    return filtered_data

def reduce_similar_positions(positions, threshold):
    """
    positions: 1D numpy array of positions (e.g., [1, 3, 4, 10, 11, 30])
    threshold: max distance to consider two positions as 'similar'
    
    Returns:
        reduced list of positions
    """
    if len(positions) == 0:
        return []

    # 정렬된 상태에서 비교
    positions = np.sort(positions)
    reduced = [positions[0]]

    for pos in positions[1:]:
        if pos - reduced[-1] > threshold:
            reduced.append(pos)

    return np.array(reduced)

def num_zerocross(x, normalize=False, axis=-1):
    x = np.asarray(x)
    nzc = np.diff(np.signbit(x), axis=axis).sum(axis=axis)
    if normalize:
        nzc = nzc / x.shape[axis]
    return nzc

def petrosian_fd(x, axis=-1):
    x = np.asarray(x)
    N = x.shape[axis]
    # Number of sign changes in the first derivative of the signal
    nzc_deriv = num_zerocross(np.diff(x, axis=axis), axis=axis)
    pfd = np.log10(N) / (np.log10(N) + np.log10(N / (N + 0.4 * nzc_deriv)))
    return pfd

def spectral_entropy(x,fs,axis=-1):
    x = np.asarray(x)
    # Compute and normalize power spectrum
    _, psd = welch(x, fs, axis=axis)
    psd_norm = psd / psd.sum(axis=axis, keepdims=True)
    se = (psd_norm * np.log2(psd_norm)).sum(axis=axis)*(-1)
    se /= np.log2(psd_norm.shape[axis])
    return se

def standard_deviation(x):
    return np.std(x, ddof=1)

def hjorth_activity(x):
    return np.var(x)

def hjorth_mobility(x):
    dx = np.diff(x)
    return np.std(dx) / np.std(x)

def hjorth_complexity(x):
    dx = np.diff(x)
    ddx = np.diff(dx)
    return np.std(ddx) / np.std(dx) / hjorth_mobility(x)

def lrssv(x):
    return np.log10(np.sqrt(np.sum((x[1:] - x[:-1])**2)))

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

# def suBAR(signal, wavelet='sym4', level=5, num_surrogates=1000, alpha=0.05):
#     """
#     SuBAR implementation for single-channel EEG artifact removal.
#     """
#     coeffs = modwt(signal, wavelet, level)
#     surrogates = generate_surrogate(signal, num_surrogates)
    
#     # Decompose each surrogate
#     surrogate_coeffs = [modwt(s, wavelet, level) for s in surrogates]

#     # Initialize filtered coefficients
#     filtered_coeffs = []

#     for j in range(level):
#         # Gather wavelet coefficients for all surrogates at level j
#         w_sur = np.array([surr[j][1] for surr in surrogate_coeffs])  # detail coefficients

#         # Mean and std over surrogates
#         w_mean = np.mean(w_sur, axis=0)
#         w_std = np.std(w_sur, axis=0)

#         # Threshold using Chebyshev’s inequality (95% default)
#         threshold = w_mean + np.sqrt(1/alpha) * w_std

#         # Compare and filter
#         w_orig = coeffs[j][1]
#         w_filtered = np.where(np.abs(w_orig) > threshold, w_mean, w_orig)

#         filtered_coeffs.append((coeffs[j][0], w_filtered))  # (approx, detail)

#     # Reconstruct cleaned signal
#     cleaned_signal = imodwt(filtered_coeffs, wavelet)
#     return cleaned_signal
