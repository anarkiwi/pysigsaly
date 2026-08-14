"""Frame-rate fundamental frequency and voicing decision by normalised autocorrelation."""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.signal import sosfiltfilt

from .dsp import EPS, frame_centres, frame_count, pitch_sos, to_db


def _windows(signal, params, n_frames):
    """Analysis windows centred on each frame, shape (n_frames, window)."""
    width = params.frame_len * params.pitch_window_frames
    padded = np.pad(signal, (width // 2, width - width // 2))
    return sliding_window_view(padded, width)[frame_centres(n_frames, params)]


def track_f0(signal, params):
    """Per-frame F0 in Hz and a boolean voiced flag."""
    n_frames = frame_count(signal.size, params)
    if n_frames == 0:
        return np.zeros(0), np.zeros(0, dtype=bool)
    windows = _windows(sosfiltfilt(pitch_sos(params), signal), params, n_frames)
    windows = windows - windows.mean(axis=1, keepdims=True)
    width = windows.shape[1]
    spectrum = np.fft.rfft(windows, n=2 * width, axis=1)
    acf = np.fft.irfft(spectrum * np.conj(spectrum), axis=1)[:, :width]
    acf *= width / (width - np.arange(width))
    nacf = acf / (acf[:, :1] + EPS)
    low = int(params.sample_rate / params.f0_max)
    high = min(int(np.ceil(params.sample_rate / params.f0_min)), width - 2)
    candidates = nacf[:, low : high + 1]
    strong = candidates >= params.pitch_peak_ratio * candidates.max(axis=1, keepdims=True)
    local = np.ones_like(strong)
    local[:, 1:-1] = (candidates[:, 1:-1] >= candidates[:, :-2]) & (candidates[:, 1:-1] >= candidates[:, 2:])
    lag = np.argmax(strong & local, axis=1) + low
    rows = np.arange(n_frames)
    prev, peak, nxt = nacf[rows, lag - 1], nacf[rows, lag], nacf[rows, lag + 1]
    curvature = prev - 2.0 * peak + nxt
    shift = np.where(np.abs(curvature) > EPS, 0.5 * (prev - nxt) / np.where(curvature == 0, EPS, curvature), 0.0)
    f0 = params.sample_rate / (lag + np.clip(shift, -0.5, 0.5))
    frame_db = to_db(np.sqrt(np.mean(np.square(windows), axis=1)))
    voiced = (peak > params.voicing_nacf) & (frame_db > frame_db.max() + params.voicing_floor_db)
    return np.clip(f0, params.f0_min, params.f0_max), voiced
