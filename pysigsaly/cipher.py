"""Reentry: the modulo-six one-time pad of the X System [1]."""

import numpy as np


def reentry(plain, key, params):
    """Encipher: c = (p + k) mod N."""
    return np.mod(np.asarray(plain, dtype=np.uint8) + np.asarray(key, dtype=np.uint8), params.alphabet).astype(np.uint8)


def dereentry(cipher, key, params):
    """Decipher: p = (c - k) mod N, computed additively to stay inside uint8."""
    complement = params.alphabet - np.asarray(key, dtype=np.uint8)
    return np.mod(np.asarray(cipher, dtype=np.uint8) + complement, params.alphabet).astype(np.uint8)
