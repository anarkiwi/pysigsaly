"""Shared fixtures: parameter set, synthetic utterance and key registry isolation."""

import numpy as np
import pytest

from pysigsaly import key
from pysigsaly.params import DEFAULT
from pysigsaly.synth import synth_utterance


@pytest.fixture(name="params")
def params_fixture():
    """Default emulator parameters."""
    return DEFAULT


@pytest.fixture(name="utterance", scope="session")
def utterance_fixture():
    """Synthetic voiced/unvoiced utterance with frame-rate F0 and voicing truth."""
    return synth_utterance(DEFAULT)


@pytest.fixture(name="rng")
def rng_fixture():
    """Deterministic generator for excitation noise."""
    return np.random.default_rng(20230715)


@pytest.fixture(autouse=True)
def _isolate_key_registry():
    """Each test starts with no key records issued."""
    key.reset_registry()
    yield
    key.reset_registry()
