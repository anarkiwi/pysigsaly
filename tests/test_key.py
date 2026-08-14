"""Key material: uniformity, reproducibility and single use."""

import numpy as np
import pytest
from scipy.stats import chisquare

from pysigsaly import key


@pytest.mark.parametrize("seed", [None, 42])
def test_key_is_uniform_over_the_alphabet(params, seed):
    """Both key sources are unbiased on {0..5}."""
    keystream = key.make_key(6000, params, seed)
    assert keystream.shape == (6000, params.n_channels)
    assert keystream.dtype == np.uint8
    counts = np.bincount(keystream.reshape(-1), minlength=params.alphabet)
    assert counts.size == params.alphabet
    assert chisquare(counts).pvalue > 0.01


def test_seeded_key_is_reproducible(params):
    """The threshing machine test key repeats for a given seed."""
    assert np.array_equal(key.make_key(200, params, 7), key.make_key(200, params, 7))
    assert not np.array_equal(key.make_key(200, params, 7), key.make_key(200, params, 8))


def test_unseeded_keys_differ(params):
    """Two one-time pads are distinct."""
    assert not np.array_equal(key.make_key(500, params), key.make_key(500, params))


def test_key_record_is_single_use(params):
    """Registering the same key record twice is refused."""
    keystream = key.make_key(50, params, 3)
    key.register_key(keystream)
    with pytest.raises(key.KeyReuseError):
        key.register_key(keystream)
    key.reset_registry()
    key.register_key(keystream)


def test_urandom_key_rejection_sampling_covers_short_requests(params):
    """A single-frame request still fills completely."""
    keystream = key.urandom_key(1, params)
    assert keystream.shape == (1, params.n_channels)
    assert keystream.max() < params.alphabet
