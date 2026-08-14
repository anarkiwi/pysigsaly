"""Channel vocoder analyser and synthesiser operating on twelve six-ary parameter channels."""

import numpy as np

from .dsp import band_envelopes, band_sos, bank_filter, envelope_of_bands, normalise_rms, to_db, upsample_frames
from .pitch import track_f0
from .quantiser import dequantise_pitch, dequantise_spectrum, quantise_pitch, quantise_spectrum


def analyse(signal, params):
    """Speech to per-frame six-ary symbols, shape (n_frames, n_channels)."""
    signal = normalise_rms(np.asarray(signal, dtype=float), params)
    spectrum = quantise_spectrum(band_envelopes(signal, params), params)
    main, vernier = quantise_pitch(*track_f0(signal, params), params)
    return np.concatenate([spectrum, main[:, None], vernier[:, None]], axis=1).astype(np.uint8)


def excitation(f0, voiced, params, n_samples, rng):
    """Phase-continuous band-limited buzz crossfaded with hiss under the voicing flag."""
    f0_up = np.power(2.0, upsample_frames(np.log2(f0), params, n_samples))
    voiced_up = np.clip(upsample_frames(voiced.astype(float), params, n_samples), 0.0, 1.0)
    phase = 2.0 * np.pi * np.cumsum(f0_up) / params.sample_rate
    harmonic = np.arange(1, int(params.sample_rate / 2 / params.f0_min) + 1)[:, None]
    active = harmonic * f0_up[None, :] < params.sample_rate / 2
    buzz = np.sum(np.cos(harmonic * phase[None, :]) * active, axis=0) * np.sqrt(2.0 / active.sum(axis=0))
    return buzz * voiced_up + rng.standard_normal(n_samples) * (1.0 - voiced_up)


def synthesise(symbols, params, rng=None):
    """Six-ary symbols back to speech through the matched synthesis filter bank."""
    rng = np.random.default_rng() if rng is None else rng
    symbols = np.asarray(symbols, dtype=np.uint8)
    n_samples = symbols.shape[0] * params.frame_len
    target_db = to_db(dequantise_spectrum(symbols[:, : params.n_spectrum], params))
    f0, voiced = dequantise_pitch(symbols[:, params.pitch_main], symbols[:, params.pitch_vernier], params)
    bands = bank_filter(excitation(f0, voiced, params, n_samples, rng), band_sos(params))
    gain_db = np.minimum(target_db - to_db(envelope_of_bands(bands, params)), params.max_gain_db)
    gain = np.power(10.0, upsample_frames(gain_db, params, n_samples) / 20.0)
    return normalise_rms(np.sum(bands.T * gain, axis=1), params)
