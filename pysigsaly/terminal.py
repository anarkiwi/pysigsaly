"""Terminal chain: speech WAV to a stereo ciphertext/key WAV and back."""

from math import gcd

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

from .cipher import dereentry, reentry
from .key import make_key, register_key
from .modem import demodulate, modulate
from .vocoder import analyse, synthesise


def read_wav(path, params):
    """Read a WAV as mono float at the emulator sample rate."""
    rate, data = wavfile.read(path)
    data = np.asarray(data)
    if data.dtype.kind in "iu":
        data = data.astype(float) / float(np.iinfo(data.dtype).max)
    else:
        data = data.astype(float)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if rate != params.sample_rate:
        divisor = gcd(int(rate), params.sample_rate)
        data = resample_poly(data, params.sample_rate // divisor, int(rate) // divisor)
    return data


def write_wav(path, signal, params):
    """Write float samples in [-1, 1] as 16-bit PCM."""
    scaled = np.round(np.clip(np.asarray(signal, dtype=float), -1.0, 1.0) * 32767.0)
    wavfile.write(path, params.sample_rate, scaled.astype(np.int16))


def encode_symbols(signal, params, seed=None):
    """Analyse and encipher, returning ciphertext and the key record used."""
    plain = analyse(signal, params)
    key = make_key(plain.shape[0], params, seed)
    register_key(key)
    return reentry(plain, key, params), key


def encode_signal(signal, params, seed=None):
    """Speech to a two-channel array: FSK ciphertext and FSK key record."""
    cipher, key = encode_symbols(signal, params, seed)
    return np.stack([modulate(cipher, params), modulate(key, params)], axis=1)


def decode_symbols(cipher, key, params, rng=None):
    """Decipher and synthesise speech from symbol arrays."""
    n_frames = min(cipher.shape[0], key.shape[0])
    return synthesise(dereentry(cipher[:n_frames], key[:n_frames], params), params, rng)


def decode_signal(stereo, params, rng=None):
    """Demodulate both channels of the link recording and synthesise speech."""
    stereo = np.asarray(stereo, dtype=float)
    return decode_symbols(demodulate(stereo[:, 0], params), demodulate(stereo[:, 1], params), params, rng)


def encode_file(src, dst, params, seed=None):
    """Encode a speech WAV to a stereo ciphertext/key WAV."""
    write_wav(dst, encode_signal(read_wav(src, params), params, seed), params)


def decode_file(src, dst, params, rng=None):
    """Decode a stereo ciphertext/key WAV back to speech."""
    rate, data = wavfile.read(src)
    if data.ndim != 2 or data.shape[1] != 2:
        raise ValueError("expected a two-channel ciphertext/key recording")
    if rate != params.sample_rate:
        raise ValueError(f"link recording is {rate} Hz, expected {params.sample_rate} Hz")
    stereo = data.astype(float) / float(np.iinfo(data.dtype).max) if data.dtype.kind in "iu" else data.astype(float)
    write_wav(dst, decode_signal(stereo, params, rng), params)
