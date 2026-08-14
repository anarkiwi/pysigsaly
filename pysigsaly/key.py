"""Key material: uniform six-ary symbols, one-time or seeded 'threshing machine' test key [1]."""

import hashlib
import os

import numpy as np

_ISSUED = set()


class KeyReuseError(RuntimeError):
    """Raised when a key record is presented for a second encode in the same run."""


def urandom_key(n_frames, params):
    """One-time pad from os.urandom, unbiased by rejection sampling."""
    total = n_frames * params.n_channels
    limit = 256 - (256 % params.alphabet)
    out = np.empty(0, dtype=np.uint8)
    while out.size < total:
        draw = np.frombuffer(os.urandom(max(total - out.size, 1) * 2), dtype=np.uint8)
        out = np.concatenate([out, draw[draw < limit] % params.alphabet])
    return out[:total].reshape(n_frames, params.n_channels)


def threshing_key(n_frames, params, seed):
    """Reproducible pseudorandom key; NOT secure, the analogue of the wartime relay key generator [1]."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, params.alphabet, size=(n_frames, params.n_channels), dtype=np.uint8)


def make_key(n_frames, params, seed=None):
    """One-time pad by default; a seeded test key when seed is given."""
    if seed is None:
        return urandom_key(n_frames, params)
    return threshing_key(n_frames, params, seed)


def fingerprint(key):
    """Stable digest of a key record."""
    return hashlib.sha256(np.ascontiguousarray(key, dtype=np.uint8).tobytes()).digest()


def register_key(key):
    """Enforce single use of a key record within this process."""
    digest = fingerprint(key)
    if digest in _ISSUED:
        raise KeyReuseError("key record already used; one-time pads must never be reused")
    _ISSUED.add(digest)


def reset_registry():
    """Forget issued key records."""
    _ISSUED.clear()
