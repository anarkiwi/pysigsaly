"""SIGSALY (Bell Labs Project X, 1943) secure voice terminal emulator."""

from .cipher import dereentry, reentry
from .key import KeyReuseError, make_key
from .metrics import envelope_correlation
from .params import DEFAULT, Params
from .terminal import decode_file, decode_signal, decode_symbols, encode_file, encode_signal, encode_symbols
from .vocoder import analyse, synthesise

__all__ = [
    "DEFAULT",
    "KeyReuseError",
    "Params",
    "analyse",
    "decode_file",
    "decode_signal",
    "decode_symbols",
    "dereentry",
    "encode_file",
    "encode_signal",
    "encode_symbols",
    "envelope_correlation",
    "make_key",
    "reentry",
    "synthesise",
]
