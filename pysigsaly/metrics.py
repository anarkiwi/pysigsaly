"""Intelligibility proxy: correlation of ten-band log envelope trajectories."""

import numpy as np

from .dsp import EPS, band_envelopes, normalise_rms, to_db


def log_envelope_trajectory(signal, params):
    """Frame-rate log band envelopes, floored where level differences are inaudible."""
    trajectory = to_db(band_envelopes(normalise_rms(np.asarray(signal, dtype=float), params), params))
    return np.maximum(trajectory, trajectory.max() - params.metric_floor_db)


def envelope_correlation(reference, test, params):
    """Pearson correlation of two log envelope trajectories over their common length."""
    ref = log_envelope_trajectory(reference, params)
    tst = log_envelope_trajectory(test, params)
    n_frames = min(ref.shape[0], tst.shape[0])
    ref, tst = ref[:n_frames], tst[:n_frames]
    ref = ref - ref.mean(axis=0)
    tst = tst - tst.mean(axis=0)
    return float(np.sum(ref * tst) / (np.sqrt(np.sum(ref**2) * np.sum(tst**2)) + EPS))
