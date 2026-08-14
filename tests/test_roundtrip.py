"""Full transmitter/receiver chain, key misalignment and wrong keys."""

import numpy as np
import pytest

from pysigsaly import cipher, key, metrics, modem, terminal
from pysigsaly.vocoder import analyse

INTELLIGIBLE = 0.9
DESTROYED = 0.2


def test_analysis_produces_twelve_six_ary_channels(params, utterance):
    """One 12-symbol frame per 20 ms of speech."""
    signal = utterance[0]
    symbols = analyse(signal, params)
    assert symbols.shape == (signal.size // params.frame_len, params.n_channels)
    assert symbols.dtype == np.uint8 and symbols.max() < params.alphabet


def test_encode_decode_recovers_the_envelope_trajectory(params, utterance, rng):
    """The decoded speech tracks the input's ten-band log envelopes."""
    signal = utterance[0]
    link = terminal.encode_signal(signal, params, seed=101)
    assert link.shape[1] == 2
    decoded = terminal.decode_signal(link, params, rng)
    assert metrics.envelope_correlation(signal, decoded, params) > INTELLIGIBLE


def test_link_carries_key_and_ciphertext_on_one_frame_grid(params, utterance):
    """Channel 0 demodulates to ciphertext, channel 1 to the key that made it."""
    signal = utterance[0]
    plain = analyse(signal, params)
    link = terminal.encode_signal(signal, params, seed=102)
    ciphertext = modem.demodulate(link[:, 0], params)
    keystream = modem.demodulate(link[:, 1], params)
    assert np.array_equal(cipher.dereentry(ciphertext, keystream, params), plain)


def test_key_offset_by_one_frame_destroys_the_output(params, utterance, rng):
    """A single frame of key slip leaves noise, not degraded speech."""
    signal = utterance[0]
    plain = analyse(signal, params)
    keystream = key.make_key(plain.shape[0], params, seed=103)
    ciphertext = cipher.reentry(plain, keystream, params)
    aligned = terminal.decode_symbols(ciphertext, keystream, params, np.random.default_rng(1))
    slipped = terminal.decode_symbols(ciphertext, np.roll(keystream, 1, axis=0), params, rng)
    assert metrics.envelope_correlation(signal, aligned, params) > INTELLIGIBLE
    assert metrics.envelope_correlation(signal, slipped, params) < DESTROYED


def test_wrong_key_yields_noise(params, utterance, rng):
    """An unrelated key record recovers nothing."""
    signal = utterance[0]
    plain = analyse(signal, params)
    ciphertext = cipher.reentry(plain, key.make_key(plain.shape[0], params, seed=104), params)
    decoded = terminal.decode_symbols(ciphertext, key.make_key(plain.shape[0], params, seed=105), params, rng)
    assert metrics.envelope_correlation(signal, decoded, params) < DESTROYED


def test_key_records_are_never_reused_in_a_run(params, utterance):
    """A second encode with the same test key is refused."""
    signal = utterance[0]
    terminal.encode_signal(signal, params, seed=106)
    with pytest.raises(key.KeyReuseError):
        terminal.encode_signal(signal, params, seed=106)


def test_successive_one_time_pads_differ(params, utterance):
    """Unseeded encodes consume fresh key material."""
    signal = utterance[0]
    first = modem.demodulate(terminal.encode_signal(signal, params)[:, 1], params)
    second = modem.demodulate(terminal.encode_signal(signal, params)[:, 1], params)
    assert not np.array_equal(first, second)
