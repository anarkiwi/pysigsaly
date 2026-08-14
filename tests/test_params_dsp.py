"""Parameter presets, filter bank helpers and WAV input handling."""

import dataclasses

import numpy as np
from scipy.io import wavfile

from pysigsaly import dsp, terminal
from pysigsaly.params import DUDLEY_BANDS, articulation_bands
from pysigsaly.vocoder import analyse


def test_band_table_covers_the_stated_span(params):
    """Ten contiguous bands from 150 to 2950 Hz."""
    edges = np.array(params.bands)
    assert edges.shape == (10, 2)
    assert edges[0, 0] == 150.0 and edges[-1, 1] == 2950.0
    assert np.array_equal(edges[1:, 0], edges[:-1, 1])


def test_alternative_band_presets_are_usable(params):
    """Dudley and equal-articulation banks analyse without error."""
    for bands in (DUDLEY_BANDS, articulation_bands()):
        edges = np.array(bands)
        assert np.all(np.diff(edges[:, 0]) > 0) and np.all(edges[:, 1] > edges[:, 0])
        alternative = dataclasses.replace(params, bands=tuple(bands))
        symbols = analyse(np.random.default_rng(0).standard_normal(4000), alternative)
        assert symbols.shape[1] == alternative.n_channels


def test_envelope_and_level_ladders_are_consistent(params):
    """Five thresholds delimit six mid-tread reconstruction levels."""
    assert params.env_thresholds_db.size == params.alphabet - 1
    assert params.env_levels_db.size == params.alphabet
    assert np.all(np.diff(params.env_levels_db) > 0)
    assert np.all(params.env_levels_db[:-1] < params.env_thresholds_db)


def test_normalise_rms_handles_silence(params):
    """Digital silence stays silent instead of dividing by zero."""
    assert not np.any(dsp.normalise_rms(np.zeros(100), params))


def test_upsample_frames_matches_the_requested_length(params, utterance):
    """Control signals are held and smoothed to an exact sample count."""
    envelopes = dsp.band_envelopes(utterance[0], params)
    n_samples = envelopes.shape[0] * params.frame_len
    assert dsp.upsample_frames(envelopes, params, n_samples - 10).shape == (n_samples - 10, params.n_spectrum)
    assert dsp.upsample_frames(envelopes, params, n_samples + 10).shape == (n_samples + 10, params.n_spectrum)


def test_read_wav_converts_rate_and_format(params, utterance, tmp_path):
    """Float and stereo inputs at another rate are resampled to mono."""
    signal = utterance[0]
    path = tmp_path / "float.wav"
    wavfile.write(path, params.sample_rate * 2, np.stack([signal, signal], axis=1).astype(np.float32))
    loaded = terminal.read_wav(path, params)
    assert loaded.ndim == 1
    assert abs(loaded.size - signal.size // 2) <= 2
