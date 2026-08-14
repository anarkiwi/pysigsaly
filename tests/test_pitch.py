"""F0 tracking and voiced/unvoiced decision."""

import numpy as np
import pytest

from pysigsaly.pitch import track_f0
from pysigsaly.synth import synth_utterance


@pytest.mark.parametrize("f0", [90.0, 130.0, 200.0, 300.0])
def test_steady_harmonic_stack_is_tracked(params, f0):
    """A synthetic vowel at a known F0 is measured to within 2 percent."""
    signal, truth, voiced = synth_utterance(params, segments=((1.0, f0, f0),))
    estimate, flags = track_f0(signal, params)
    inner = slice(5, -5)
    assert voiced[inner].all() and flags[inner].mean() > 0.95
    assert np.median(np.abs(estimate[inner] - truth[inner]) / truth[inner]) < 0.02


def test_tracking_on_a_varying_utterance(params, utterance):
    """Voicing is right on most frames and voiced F0 error stays small."""
    signal, truth, voiced = utterance
    estimate, flags = track_f0(signal, params)
    assert (flags == voiced).mean() > 0.9
    both = flags & voiced
    error = np.abs(estimate[both] - truth[both]) / truth[both]
    assert np.median(error) < 0.02
    assert np.mean(error < 0.05) > 0.9


def test_noise_is_unvoiced(params):
    """A fricative-like segment is not declared voiced."""
    signal, _, _ = synth_utterance(params, segments=((0.6, 0.0, 0.0),))
    _, flags = track_f0(signal, params)
    assert flags.mean() < 0.1


def test_silence_gives_no_frames(params):
    """An input shorter than one frame yields empty tracks."""
    estimate, flags = track_f0(np.zeros(params.frame_len - 1), params)
    assert estimate.size == 0 and flags.size == 0
