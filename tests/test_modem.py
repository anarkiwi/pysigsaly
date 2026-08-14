"""FSK modem tone plan and symbol round trip."""

import dataclasses

import numpy as np
import pytest

from pysigsaly import modem
from pysigsaly.params import DEFAULT, Params


def _symbols(params, n_frames, seed=0):
    """Random six-ary symbol block."""
    return np.random.default_rng(seed).integers(0, params.alphabet, (n_frames, params.n_channels), dtype=np.uint8)


def test_symbol_round_trip_is_exact(params):
    """Modulation then demodulation reproduces the symbols bit for bit."""
    symbols = _symbols(params, 300)
    assert np.array_equal(modem.demodulate(modem.modulate(symbols, params), params), symbols)


def test_round_trip_survives_int16_quantisation(params):
    """The link recording may be stored as 16-bit PCM without symbol errors."""
    symbols = _symbols(params, 120, seed=7)
    signal = np.round(modem.modulate(symbols, params) * 32767.0) / 32767.0
    assert np.array_equal(modem.demodulate(signal, params), symbols)


def test_modulated_signal_shape_and_headroom(params):
    """One 20 ms frame of samples per symbol frame, inside full scale."""
    signal = modem.modulate(_symbols(params, 40), params)
    assert signal.shape == (40 * params.frame_len,)
    assert np.max(np.abs(signal)) <= params.modem_peak


def test_historical_tone_plan_is_usable_but_not_orthogonal(params):
    """The 765/170/20 Hz plan decodes almost all symbols despite sub-orthogonal spacing."""
    historical = dataclasses.replace(params, historical_tones=True)
    symbols = _symbols(params, 200, seed=3)
    errors = np.mean(modem.demodulate(modem.modulate(symbols, historical), historical) != symbols)
    assert 0.0 < errors < 0.01
    assert historical.tone_table.max() < 3000.0


def test_tone_table_spacing(params):
    """Default tones are one symbol-rate apart and span 72 positions."""
    tones = params.tone_table
    assert tones.shape == (params.n_channels, params.alphabet)
    assert np.allclose(np.diff(tones.reshape(-1)), params.tone_spacing_hz)


def test_partial_trailing_frame_is_discarded(params):
    """Demodulation only reports whole frames."""
    signal = modem.modulate(_symbols(params, 10), params)
    assert modem.demodulate(signal[: -params.frame_len // 2], params).shape[0] == 9


def test_tone_plan_above_nyquist_rejected():
    """A sample rate too low for the tone plan is refused at construction."""
    with pytest.raises(ValueError):
        Params(sample_rate=2000)
    with pytest.raises(ValueError):
        Params(sample_rate=DEFAULT.sample_rate + 1)
