"""Frozen parameter set for the SIGSALY emulator (docs/architecture.md section 10.2)."""

from dataclasses import dataclass
from typing import Tuple

import numpy as np

# 150-2950 Hz, ten nearly equal bands [1]; only bands 1, 2 and 10 are labelled, 3-9 inferred (doc 2.1.2).
SIGSALY_BANDS: Tuple[Tuple[float, float], ...] = (
    (150.0, 350.0),
    (350.0, 550.0),
    (550.0, 850.0),
    (850.0, 1150.0),
    (1150.0, 1450.0),
    (1450.0, 1750.0),
    (1750.0, 2050.0),
    (2050.0, 2350.0),
    (2350.0, 2650.0),
    (2650.0, 2950.0),
)

# Dudley's telephone-band vocoder [8]; its 0-250 Hz band is raised off DC to stay realisable.
DUDLEY_BANDS: Tuple[Tuple[float, float], ...] = ((60.0, 250.0),) + tuple(
    (250.0 + 300.0 * i, 550.0 + 300.0 * i) for i in range(9)
)


def articulation_bands(n_bands: int = 10, low: float = 150.0, high: float = 2950.0):
    """Equal-articulation (mel-warped) alternative bank, the layout implied by [3]."""
    mel = 2595.0 * np.log10(1.0 + np.array([low, high]) / 700.0)
    edges = 700.0 * (10.0 ** (np.linspace(mel[0], mel[1], n_bands + 1) / 2595.0) - 1.0)
    return tuple((float(a), float(b)) for a, b in zip(edges[:-1], edges[1:]))


@dataclass(frozen=True)
class Params:
    """Emulator constants. Historically inferred values are flagged per field."""

    sample_rate: int = 8000  # free parameter; 20 ms = 160 samples exactly
    frame_rate: int = 50  # [1][5]
    alphabet: int = 6  # six levels per channel [1]
    bands: Tuple[Tuple[float, float], ...] = SIGSALY_BANDS
    band_order: int = 4  # design choice; no source gives filter order
    envelope_cutoff_hz: float = 25.0  # [1][5][8][14]
    envelope_order: int = 2
    input_rms_dbfs: float = -20.0  # analogue of the constant-output amplifier [7]
    env_top_dbfs: float = -18.0  # ladder ceiling, just above the input RMS reference
    env_range_db: float = 60.0  # six 10 dB steps; no source publishes the original boundaries
    max_gain_db: float = 40.0  # synthesis gain clamp
    f0_min: float = 80.0  # [7]
    f0_max: float = 320.0  # [7]
    pitch_band: Tuple[float, float] = (60.0, 900.0)  # analysis band for autocorrelation
    pitch_window_frames: int = 3
    pitch_peak_ratio: float = 0.85  # accept the shortest lag within this fraction of the best peak
    voicing_nacf: float = 0.35  # normalised autocorrelation peak threshold
    voicing_floor_db: float = -45.0  # relative to the loudest frame
    tone_base_hz: float = 200.0  # lowest tone of the orthogonal plan
    historical_tones: bool = False  # True selects the 765 Hz / 170 Hz / 20 Hz plan [9][12]
    hist_base_hz: float = 765.0  # [9]
    hist_channel_hz: float = 170.0  # [9]
    hist_step_hz: float = 20.0  # [9][12]
    modem_peak: float = 0.9
    metric_floor_db: float = 60.0  # envelope metric ignores levels this far under the loudest frame

    def __post_init__(self):
        if self.sample_rate % self.frame_rate:
            raise ValueError("sample_rate must be a multiple of frame_rate")
        if self.tone_table.max() >= self.sample_rate / 2:
            raise ValueError("tone plan exceeds Nyquist")

    @property
    def frame_len(self) -> int:
        """Samples per 20 ms frame."""
        return self.sample_rate // self.frame_rate

    @property
    def n_spectrum(self) -> int:
        """Spectrum channel count."""
        return len(self.bands)

    @property
    def n_channels(self) -> int:
        """Total parameter channels: spectrum plus main and vernier pitch."""
        return self.n_spectrum + 2

    @property
    def pitch_main(self) -> int:
        """Index of the main pitch channel."""
        return self.n_spectrum

    @property
    def pitch_vernier(self) -> int:
        """Index of the vernier pitch channel."""
        return self.n_spectrum + 1

    @property
    def pitch_levels(self) -> int:
        """Combined pitch codes, one of which is reserved for unvoiced."""
        return self.alphabet**2

    @property
    def tone_spacing_hz(self) -> float:
        """Minimum orthogonal tone spacing for a 20 ms symbol, 1/T."""
        return float(self.frame_rate)

    @property
    def tone_table(self) -> np.ndarray:
        """Tone frequency per (channel, level), shape (n_channels, alphabet)."""
        chan = np.arange(self.n_channels)[:, None]
        level = np.arange(self.alphabet)[None, :]
        if self.historical_tones:
            return self.hist_base_hz + chan * self.hist_channel_hz + level * self.hist_step_hz
        return self.tone_base_hz + (chan * self.alphabet + level) * self.tone_spacing_hz

    @property
    def env_thresholds_db(self) -> np.ndarray:
        """Five companding thresholds delimiting six levels, equal dB steps."""
        step = self.env_range_db / self.alphabet
        floor_db = self.env_top_dbfs - self.env_range_db
        return floor_db + step * np.arange(1, self.alphabet)

    @property
    def env_levels_db(self) -> np.ndarray:
        """Mid-tread reconstruction level per quantiser step."""
        step = self.env_range_db / self.alphabet
        floor_db = self.env_top_dbfs - self.env_range_db
        return floor_db + step * (np.arange(self.alphabet) + 0.5)


DEFAULT = Params()
