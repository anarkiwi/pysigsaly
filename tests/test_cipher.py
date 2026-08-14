"""Reentry: exactness, ciphertext flatness and independence from the plaintext."""

import numpy as np
from scipy.stats import chi2_contingency, chisquare

from pysigsaly import cipher, key


def _skewed_plaintext(params, n_frames, seed=11):
    """Plaintext with the strong level-0 bias real vocoder output shows."""
    rng = np.random.default_rng(seed)
    weights = np.array([0.6, 0.15, 0.1, 0.07, 0.05, 0.03])
    return rng.choice(params.alphabet, size=(n_frames, params.n_channels), p=weights).astype(np.uint8)


def test_round_trip_recovers_plaintext(params):
    """Adding then subtracting the key modulo six is lossless."""
    plain = _skewed_plaintext(params, 500)
    keystream = key.make_key(plain.shape[0], params, seed=1)
    recovered = cipher.dereentry(cipher.reentry(plain, keystream, params), keystream, params)
    assert np.array_equal(recovered, plain)
    assert recovered.dtype == np.uint8


def test_all_symbol_pairs(params):
    """Every plaintext/key combination is exact and stays in the alphabet."""
    plain, keystream = np.meshgrid(np.arange(params.alphabet), np.arange(params.alphabet))
    plain = plain.astype(np.uint8)
    keystream = keystream.astype(np.uint8)
    ciphertext = cipher.reentry(plain, keystream, params)
    assert ciphertext.max() < params.alphabet
    assert np.array_equal(cipher.dereentry(ciphertext, keystream, params), plain)


def test_ciphertext_is_flat(params):
    """Skewed plaintext plus a uniform key gives a uniform ciphertext."""
    plain = _skewed_plaintext(params, 4000)
    ciphertext = cipher.reentry(plain, key.make_key(plain.shape[0], params, seed=2), params)
    counts = np.bincount(ciphertext.reshape(-1), minlength=params.alphabet)
    assert chisquare(counts).pvalue > 0.01
    assert chisquare(np.bincount(plain.reshape(-1), minlength=params.alphabet)).pvalue < 1e-6


def test_ciphertext_independent_of_plaintext(params):
    """The joint plaintext/ciphertext table shows no association."""
    plain = _skewed_plaintext(params, 4000, seed=5)
    ciphertext = cipher.reentry(plain, key.make_key(plain.shape[0], params, seed=6), params)
    table = np.histogram2d(plain.reshape(-1), ciphertext.reshape(-1), bins=[params.alphabet, params.alphabet])[0]
    assert chi2_contingency(table).pvalue > 0.01
    assert abs(np.corrcoef(plain.reshape(-1), ciphertext.reshape(-1))[0, 1]) < 0.05
