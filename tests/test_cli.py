"""End to end command line encode, decode and demo."""

import numpy as np
import pytest
from scipy.io import wavfile

from pysigsaly import metrics, terminal
from pysigsaly.cli import main


def test_encode_then_decode_files(params, utterance, tmp_path):
    """A speech WAV survives the CLI round trip."""
    signal = utterance[0]
    clear, link, decoded = (tmp_path / name for name in ("clear.wav", "link.wav", "decoded.wav"))
    terminal.write_wav(clear, signal, params)
    assert main(["encode", str(clear), str(link), "--seed", "201"]) == 0
    rate, data = wavfile.read(link)
    assert rate == params.sample_rate and data.ndim == 2 and data.shape[1] == 2
    assert main(["decode", str(link), str(decoded)]) == 0
    assert metrics.envelope_correlation(signal, terminal.read_wav(decoded, params), params) > 0.9


def test_demo_writes_three_files(tmp_path, capsys):
    """The demo path needs no input audio."""
    assert main(["demo", str(tmp_path / "out"), "--seed", "202"]) == 0
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["clear.wav", "decoded.wav", "link.wav"]
    assert "envelope correlation" in capsys.readouterr().out


def test_demo_with_historical_tone_plan(tmp_path):
    """The historical tone plan is selectable end to end."""
    assert main(["demo", str(tmp_path / "hist"), "--seed", "203", "--historical-tones"]) == 0


def test_decode_rejects_a_mono_recording(params, utterance, tmp_path):
    """Decoding needs both the ciphertext and key channels."""
    mono = tmp_path / "mono.wav"
    terminal.write_wav(mono, utterance[0], params)
    with pytest.raises(ValueError):
        main(["decode", str(mono), str(tmp_path / "out.wav")])


def test_decode_rejects_a_rate_mismatch(params, tmp_path):
    """A link recording at the wrong rate is refused."""
    bad = tmp_path / "bad.wav"
    wavfile.write(bad, params.sample_rate * 2, np.zeros((100, 2), dtype=np.int16))
    with pytest.raises(ValueError):
        main(["decode", str(bad), str(tmp_path / "out.wav")])
