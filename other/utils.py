import numpy as np
import scipy.signal as ss
from scipy.signal import firwin, filtfilt, welch
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
