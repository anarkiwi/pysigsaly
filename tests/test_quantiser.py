"""Companded spectrum stepper and vernier pitch pair."""

import numpy as np

from pysigsaly import quantiser


def test_spectrum_levels_span_the_ladder(params):
    """Amplitudes from below the floor to above the ceiling map monotonically onto 0..5."""
    amplitudes = np.power(10.0, np.linspace(-90.0, 0.0, 400) / 20.0)
    levels = quantiser.quantise_spectrum(amplitudes, params)
    assert levels.dtype == np.uint8
    assert levels.min() == 0 and levels.max() == params.alphabet - 1
    assert np.all(np.diff(levels.astype(int)) >= 0)


def test_spectrum_dequantiser_is_within_half_a_step(params):
    """Reconstruction error inside the ladder is bounded by half a step."""
    step = params.env_range_db / params.alphabet
    inside = np.linspace(params.env_top_dbfs - params.env_range_db + 0.1, params.env_top_dbfs - 0.1, 200)
    amplitudes = np.power(10.0, inside / 20.0)
    recovered = quantiser.dequantise_spectrum(quantiser.quantise_spectrum(amplitudes, params), params)
    assert np.max(np.abs(20.0 * np.log10(recovered) - inside)) <= step / 2.0 + 1e-6


def test_pitch_vernier_round_trip(params):
    """Every voiced pitch is recovered to better than half a log step."""
    f0 = np.geomspace(params.f0_min, params.f0_max, 300)
    voiced = np.ones_like(f0, dtype=bool)
    main, vernier = quantiser.quantise_pitch(f0, voiced, params)
    assert main.max() < params.alphabet and vernier.max() < params.alphabet
    recovered, flags = quantiser.dequantise_pitch(main, vernier, params)
    assert flags.all()
    step = np.log2(params.f0_max / params.f0_min) / (params.pitch_levels - 2)
    assert np.max(np.abs(np.log2(recovered / f0))) <= step / 2.0 + 1e-9


def test_pitch_uses_all_thirty_five_voiced_codes(params):
    """The vernier pair delivers 36 levels, one reserved for unvoiced."""
    f0 = np.geomspace(params.f0_min, params.f0_max, 2000)
    main, vernier = quantiser.quantise_pitch(f0, np.ones_like(f0, dtype=bool), params)
    codes = np.unique(params.alphabet * main.astype(int) + vernier.astype(int))
    assert codes.size == params.pitch_levels - 1
    assert codes.min() == 1 and codes.max() == params.pitch_levels - 1


def test_unvoiced_uses_the_reserved_zero_code(params):
    """Unvoiced frames send 0 on both pitch channels."""
    main, vernier = quantiser.quantise_pitch(np.full(5, 150.0), np.zeros(5, dtype=bool), params)
    assert not main.any() and not vernier.any()
    _, flags = quantiser.dequantise_pitch(main, vernier, params)
    assert not flags.any()


def test_pitch_outside_the_search_range_is_clamped(params):
    """F0 beyond 80-320 Hz saturates at the ladder ends."""
    f0 = np.array([10.0, 1000.0])
    main, vernier = quantiser.quantise_pitch(f0, np.ones(2, dtype=bool), params)
    codes = params.alphabet * main.astype(int) + vernier.astype(int)
    assert codes.tolist() == [1, params.pitch_levels - 1]
