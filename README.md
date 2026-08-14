# pysigsaly

Emulator of SIGSALY (Bell Labs "Project X", 1943-1946), the first digital secure voice system: a ten-band
channel vocoder plus vernier pitch reduces speech to twelve six-level parameters every 20 ms, a
never-reused six-ary key is added modulo 6 ("reentry"), and the result is sent as 12-channel 6-tone FSK.
Encoding writes a stereo WAV whose channel 0 is the enciphered radio link and channel 1 is the key record,
the pair the historical terminal got from its transmitter and its turntable. Implemented in numpy/scipy;
see [docs/architecture.md](docs/architecture.md) for the researched system specification and sources.

## Install

```
pip install -e .[dev]
```

## Use

```
pysigsaly encode speech.wav link.wav              # one-time pad from os.urandom
pysigsaly encode speech.wav link.wav --seed 1943  # reproducible non-secure test key
pysigsaly decode link.wav decoded.wav
pysigsaly demo outdir                             # synthesises an utterance, runs the whole chain
```

`--historical-tones` selects the 765 Hz / 170 Hz channel, 20 Hz step plan of patent US 3,897,591 in place
of the default orthogonal 50 Hz plan.

```python
from pysigsaly import DEFAULT, encode_signal, decode_signal, envelope_correlation

link = encode_signal(speech, DEFAULT)          # (n, 2): ciphertext, key record
decoded = decode_signal(link, DEFAULT)
envelope_correlation(speech, decoded, DEFAULT) # intelligibility proxy
```

## Example

espeak-ng reading "This is a secure voice conference between Washington and London", the enciphered link,
and the decoded output; regenerate with `examples/make_media.sh`.

| | |
|---|---|
| Clear input ([wav](examples/clear.wav)) | <video src="https://github.com/anarkiwi/pysigsaly/raw/main/examples/clear.mp4" controls width="380"></video> |
| Enciphered link, channel 0 ([wav](examples/link.wav)) | <video src="https://github.com/anarkiwi/pysigsaly/raw/main/examples/link.mp4" controls width="380"></video> |
| Decoded output ([wav](examples/decoded.wav)) | <video src="https://github.com/anarkiwi/pysigsaly/raw/main/examples/decoded.mp4" controls width="380"></video> |

Log envelope correlation of decoded against clear: 0.92.

## Parameters

| Parameter | Value |
|---|---|
| Audio sample rate | 8000 Hz (20 ms = 160 samples) |
| Frame rate | 50 frames/s |
| Parameter channels | 12: 10 spectrum + main and vernier pitch |
| Levels per channel | 6, companded (10 dB steps over 60 dB) |
| Analysis/synthesis bands | 150-2950 Hz: 150-350, 350-550, then 300 Hz bands |
| Envelope bandwidth | 25 Hz |
| Pitch range / levels | 80-320 Hz; 36 codes = 35 log-spaced pitches + reserved unvoiced code |
| Cipher | c = (p + k) mod 6, k uniform, single use |
| Symbol rate | 600 six-ary symbols/s (~1550 bit/s) |
| Modem | 12 channels x 6 tones, 20 ms symbols, 50 Hz spacing (historical plan optional) |

Constants live in `pysigsaly/params.py`; values that are inference rather than citation are flagged there
and in [docs/architecture.md](docs/architecture.md) section 10.3.

## Test

```
black --check . && pylint pysigsaly tests && pytest -n auto --cov=pysigsaly
```
