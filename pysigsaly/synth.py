"""Synthetic test utterance: voiced formant stacks with time-varying F0 plus noise-excited segments."""

import numpy as np
from scipy.signal import lfilter, sosfiltfilt

from .dsp import EPS, envelope_sos, frame_centres, frame_count, normalise_rms

# (duration s, start F0, end F0); zero F0 marks an unvoiced segment.
SEGMENTS = (
    (0.50, 110.0, 145.0),
    (0.25, 0.0, 0.0),
    (0.50, 200.0, 165.0),
    (0.20, 0.0, 0.0),
    (0.55, 130.0, 100.0),
)

VOICED_FORMANTS = ((700.0, 90.0), (1220.0, 110.0), (2600.0, 160.0))
UNVOICED_FORMANTS = ((2400.0, 700.0), (3300.0, 500.0))


def _resonate(signal, formants, params):
    """Cascade of two-pole resonators."""
    out = signal
    for freq, bandwidth in formants:
        radius = np.exp(-np.pi * bandwidth / params.sample_rate)
        omega = 2.0 * np.pi * freq / params.sample_rate
        out = lfilter([1.0 - radius], [1.0, -2.0 * radius * np.cos(omega), radius**2], out)
    return out


def _tracks(params, segments):
    """Sample-rate F0 and voicing tracks for the segment list."""
    counts = [int(round(duration * params.sample_rate)) for duration, _, _ in segments]
    f0_parts = [
        np.linspace(max(start, params.f0_min), max(end, params.f0_min), count)
        for count, (_, start, end) in zip(counts, segments)
    ]
    voiced_parts = [np.full(count, start > 0.0) for count, (_, start, _) in zip(counts, segments)]
    return np.concatenate(f0_parts), np.concatenate(voiced_parts)


def synth_utterance(params, seed=0, segments=SEGMENTS):
    """Return (signal, frame-rate F0 truth, frame-rate voicing truth)."""
    rng = np.random.default_rng(seed)
    f0_track, voiced_track = _tracks(params, segments)
    n_samples = f0_track.size
    phase = 2.0 * np.pi * np.cumsum(f0_track) / params.sample_rate
    harmonic = np.arange(1, int(params.sample_rate / 2 / params.f0_min) + 1)[:, None]
    active = harmonic * f0_track[None, :] < params.sample_rate / 2
    glottal = np.sum(np.cos(harmonic * phase[None, :]) * active / harmonic, axis=0)
    mix = np.clip(sosfiltfilt(envelope_sos(params), voiced_track.astype(float)), 0.0, 1.0)
    noise = rng.standard_normal(n_samples)
    signal = (
        _resonate(glottal, VOICED_FORMANTS, params) * mix
        + _resonate(noise, UNVOICED_FORMANTS, params) * (1.0 - mix) * 0.5
    )
    signal = normalise_rms(signal / (np.max(np.abs(signal)) + EPS), params)
    centres = frame_centres(frame_count(n_samples, params), params)
    return signal, f0_track[centres], voiced_track[centres]
