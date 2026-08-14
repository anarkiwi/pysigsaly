"""Six-level companded steppers for the spectrum channels and the vernier pitch pair."""

import numpy as np

from .dsp import to_db


def quantise_spectrum(envelopes, params):
    """Companded six-level codes for band amplitudes, shape preserved."""
    return np.searchsorted(params.env_thresholds_db, to_db(envelopes)).astype(np.uint8)


def dequantise_spectrum(levels, params):
    """Mid-tread amplitude for each spectrum code."""
    return np.power(10.0, params.env_levels_db[np.asarray(levels, dtype=np.intp)] / 20.0)


def _log_position(f0, params):
    """Fractional position of F0 within the log-spaced pitch range."""
    span = np.log2(params.f0_max / params.f0_min)
    return np.clip(np.log2(np.maximum(f0, params.f0_min) / params.f0_min) / span, 0.0, 1.0)


def quantise_pitch(f0, voiced, params):
    """Main and vernier pitch codes; code 0/0 is the reserved unvoiced value."""
    steps = params.pitch_levels - 1
    code = np.where(voiced, 1 + np.rint(_log_position(f0, params) * (steps - 1)).astype(np.intp), 0)
    return (code // params.alphabet).astype(np.uint8), (code % params.alphabet).astype(np.uint8)


def dequantise_pitch(main, vernier, params):
    """Recover F0 and voicing from the vernier pair; the vernier is the base-N residual digit [11]."""
    code = params.alphabet * np.asarray(main, dtype=np.intp) + np.asarray(vernier, dtype=np.intp)
    voiced = code > 0
    position = np.maximum(code - 1, 0) / (params.pitch_levels - 2)
    return params.f0_min * np.power(params.f0_max / params.f0_min, position), voiced
