"""12-channel six-tone FSK modem on the 20 ms frame grid."""

from functools import lru_cache

import numpy as np

from .dsp import frame_count


@lru_cache(maxsize=8)
def _bases(params):
    """Synthesis cosine basis (n_tones, frame_len) and analysis DFT basis (frame_len, n_tones)."""
    freqs = params.tone_table.reshape(-1)
    time = np.arange(params.frame_len) / params.sample_rate
    phase = 2.0 * np.pi * np.outer(freqs, time)
    return np.cos(phase), np.exp(-1j * phase).T


def modulate(symbols, params):
    """Symbols (n_frames, n_channels) to a real baseband multiplex."""
    symbols = np.asarray(symbols, dtype=np.intp)
    n_frames = symbols.shape[0]
    tones = np.zeros((n_frames, params.n_channels * params.alphabet))
    channels = np.arange(params.n_channels) * params.alphabet
    tones[np.arange(n_frames)[:, None], channels[None, :] + symbols] = 1.0
    signal = tones @ _bases(params)[0]
    return (signal * (params.modem_peak / params.n_channels)).reshape(-1)


def demodulate(signal, params):
    """Per-frame magnitude argmax over each channel's six candidate tones."""
    n_frames = frame_count(np.size(signal), params)
    frames = np.asarray(signal, dtype=float)[: n_frames * params.frame_len].reshape(n_frames, params.frame_len)
    magnitudes = np.abs(frames @ _bases(params)[1])
    return np.argmax(magnitudes.reshape(n_frames, params.n_channels, params.alphabet), axis=2).astype(np.uint8)
