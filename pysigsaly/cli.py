"""Command line interface: encode, decode and a self-contained demo."""

import argparse
import os

from dataclasses import replace

from .metrics import envelope_correlation
from .params import DEFAULT
from .synth import synth_utterance
from .terminal import decode_file, decode_signal, encode_signal, read_wav, write_wav


def _params(args):
    """Parameter set selected by the common command line options."""
    return replace(DEFAULT, sample_rate=args.sample_rate, historical_tones=args.historical_tones)


def _add_common(parser):
    """Options shared by every subcommand."""
    parser.add_argument("--sample-rate", type=int, default=DEFAULT.sample_rate)
    parser.add_argument("--historical-tones", action="store_true", help="use the 765/170/20 Hz tone plan")


def build_parser():
    """Top level argument parser."""
    parser = argparse.ArgumentParser(prog="pysigsaly", description="SIGSALY (Bell Labs Project X) emulator")
    subs = parser.add_subparsers(dest="command", required=True)

    encode = subs.add_parser("encode", help="speech WAV to stereo ciphertext/key WAV")
    encode.add_argument("input")
    encode.add_argument("output")
    encode.add_argument("--seed", type=int, default=None, help="non-secure 'threshing machine' test key")
    _add_common(encode)

    decode = subs.add_parser("decode", help="stereo ciphertext/key WAV back to speech")
    decode.add_argument("input")
    decode.add_argument("output")
    _add_common(decode)

    demo = subs.add_parser("demo", help="synthesise an utterance and run the full chain")
    demo.add_argument("outdir")
    demo.add_argument("--seed", type=int, default=None)
    _add_common(demo)
    return parser


def run_demo(args):
    """Write clear, link and decoded WAVs plus the envelope correlation."""
    params = _params(args)
    os.makedirs(args.outdir, exist_ok=True)
    clear, _, _ = synth_utterance(params)
    link = encode_signal(clear, params, args.seed)
    decoded = decode_signal(link, params)
    for name, signal in (("clear.wav", clear), ("link.wav", link), ("decoded.wav", decoded)):
        write_wav(os.path.join(args.outdir, name), signal, params)
    correlation = envelope_correlation(clear, decoded, params)
    print(f"wrote clear.wav, link.wav, decoded.wav to {args.outdir}")
    print(f"log envelope correlation: {correlation:.3f}")
    return correlation


def main(argv=None):
    """Entry point."""
    args = build_parser().parse_args(argv)
    params = _params(args)
    if args.command == "encode":
        write_wav(args.output, encode_signal(read_wav(args.input, params), params, args.seed), params)
    elif args.command == "decode":
        decode_file(args.input, args.output, params)
    else:
        run_demo(args)
    return 0
