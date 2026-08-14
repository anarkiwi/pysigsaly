"""Render a phrase with espeak-ng, run it through the terminal chain and write the example WAVs."""

import argparse
import os
import subprocess
import tempfile

from pysigsaly.metrics import envelope_correlation
from pysigsaly.params import DEFAULT
from pysigsaly.terminal import decode_signal, encode_signal, read_wav, write_wav

PHRASE = "This is a secure voice conference between Washington and London."


def espeak(phrase, path, voice="en-us", speed=145):
    """Synthesise a phrase to a WAV with espeak-ng."""
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-w", path, phrase], check=True, capture_output=True)


def main():
    """Write clear.wav, link.wav and decoded.wav next to this script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--phrase", default=PHRASE)
    parser.add_argument("--seed", type=int, default=19430715, help="non-secure test key; omit for a real pad")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as work:
        raw = os.path.join(work, "tts.wav")
        espeak(args.phrase, raw)
        clear = read_wav(raw, DEFAULT)
    link = encode_signal(clear, DEFAULT, args.seed)
    decoded = decode_signal(link, DEFAULT)
    for name, signal in (("clear.wav", clear), ("link.wav", link), ("decoded.wav", decoded)):
        write_wav(os.path.join(args.outdir, name), signal, DEFAULT)
    print(f"log envelope correlation: {envelope_correlation(clear, decoded, DEFAULT):.3f}")


if __name__ == "__main__":
    main()
