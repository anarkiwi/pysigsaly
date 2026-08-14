"""Filter bank, rectifier and envelope resampling shared by analyser and synthesiser."""

from functools import lru_cache

import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt

EPS = 1e-12


@lru_cache(maxsize=8)
def band_sos(params):
    """Bandpass SOS sections for the analysis/synthesis bank, one per spectrum channel."""
    nyq = params.sample_rate / 2.0
    return tuple(
        butter(params.band_order, (low / nyq, min(high, 0.99 * nyq) / nyq), btype="bandpass", output="sos")
        for low, high in params.bands
    )


@lru_cache(maxsize=8)
def envelope_sos(params):
    """Lowpass SOS limiting envelope variation to under the 25 Hz cutoff."""
    return butter(params.envelope_order, params.envelope_cutoff_hz / (params.sample_rate / 2.0), output="sos")


@lru_cache(maxsize=8)
def pitch_sos(params):
    """Bandpass SOS isolating the fundamental region for autocorrelation."""
    nyq = params.sample_rate / 2.0
    low, high = params.pitch_band
    return butter(params.band_order, (low / nyq, high / nyq), btype="bandpass", output="sos")


def bank_filter(signal, sos_bank):
    """Apply each SOS section to signal, returning shape (n_bands, n_samples)."""
    return np.stack([sosfilt(sos, signal) for sos in sos_bank])


def frame_count(n_samples, params):
    """Whole 20 ms frames available in n_samples."""
    return int(n_samples) // params.frame_len


def frame_centres(n_frames, params):
    """Sample index at the centre of each frame."""
    return np.arange(n_frames) * params.frame_len + params.frame_len // 2


def normalise_rms(signal, params):
    """Scale to the reference RMS so the quantiser ladder has a fixed meaning."""
    rms = float(np.sqrt(np.mean(np.square(signal)))) if signal.size else 0.0
    if rms < EPS:
        return np.zeros_like(signal, dtype=float)
    return signal * (10.0 ** (params.input_rms_dbfs / 20.0) / rms)


def envelope_of_bands(bands, params):
    """Linear rectifier plus 25 Hz smoothing, decimated to the frame rate, shape (n_frames, n_bands)."""
    smoothed = np.abs(sosfiltfilt(envelope_sos(params), np.abs(bands), axis=-1))
    return smoothed[:, frame_centres(frame_count(bands.shape[-1], params), params)].T


def band_envelopes(signal, params):
    """Frame-rate band amplitudes of a signal, shape (n_frames, n_bands)."""
    return envelope_of_bands(bank_filter(signal, band_sos(params)), params)


def upsample_frames(frame_values, params, n_samples):
    """Hold-and-smooth frame-rate control signals up to the audio rate, shape (n_samples, ...)."""
    held = np.repeat(frame_values, params.frame_len, axis=0)
    smoothed = sosfiltfilt(envelope_sos(params), held, axis=0)
    if smoothed.shape[0] >= n_samples:
        return smoothed[:n_samples]
    pad = [(0, n_samples - smoothed.shape[0])] + [(0, 0)] * (smoothed.ndim - 1)
    return np.pad(smoothed, pad, mode="edge")


def to_db(amplitude):
    """Amplitude to dB with a floor that keeps silence finite."""
    return 20.0 * np.log10(np.asarray(amplitude, dtype=float) + EPS)
