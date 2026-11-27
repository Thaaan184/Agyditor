"""Unified 5-Stem Acoustic Engine for AGY Local Video Studio.

Implements cinema sound design mechanics extracted from studio reference research:
1. Five distinct buses mixed at 48 kHz Stereo:
   - voice: Narration / dialogue (HPF cleanup + presence).
   - ambience: Filtered real room-tone bedrock (anti-digital-vacuum glue).
   - foley: Tactile physical actions (CC0 foley + physical materials, zero raw sine-beeps).
   - transitions_impacts: 2-to-3-layer Audio-Spectrum Cake (Sub + Mid + High Air) with J-cut pre-lap.
   - music: Underscore or external track with 9-band voice-pocket carving, reversed lead-in risers,
     and nested Great Hall (T60 = 2.6s) reverb tail exits before hard stops or loops.
2. Shared Stereo Convolution Room Bus (T60 = 1.05s) so foley & impacts inhabit one room.
3. Explicit silence_pockets for high-contrast drop-outs right before hook/punchline reveals.
4. Iterative FFmpeg ebur128 mastering targeting -16.0 LUFS & true peak <= -4.0 dBFS with
   corrective 180-320 Hz boxiness notch so mixes stay crisp without low-mid mud.
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import Any

import librosa
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = pathlib.Path(__file__).resolve().parent.parent
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
INDEX_PATH = ROOT / "studio_kit" / "sound_palette_index.json"
SR = 48000

# Import OneTake physical materials cleanly without altering OneTake source
ONETAKE_SCRIPTS = ROOT / ".agents" / "skills" / "onetake" / "scripts"
if str(ONETAKE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ONETAKE_SCRIPTS))
import sfx_palette as _ot  # noqa: E402


def _bp(x: np.ndarray, f_lo: float, f_hi: float, order: int = 2) -> np.ndarray:
    lo = max(25.0, min(f_lo, SR * 0.45))
    hi = max(lo + 40.0, min(f_hi, SR * 0.48))
    sos = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="bandpass", output="sos")
    return signal.sosfilt(sos, x)


def _hp(x: np.ndarray, f_cut: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, np.clip(f_cut, 20.0, SR * 0.45) / (SR / 2), btype="highpass", output="sos")
    return signal.sosfilt(sos, x)


def _lp(x: np.ndarray, f_cut: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, np.clip(f_cut, 80.0, SR * 0.48) / (SR / 2), btype="lowpass", output="sos")
    return signal.sosfilt(sos, x)


def _biquad_peaking(freq: float, q: float, gain_db: float) -> np.ndarray:
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * np.clip(freq, 25.0, SR * 0.46) / SR
    alpha = math.sin(w0) / (2.0 * max(q, 0.2))
    cos_w0 = math.cos(w0)
    b0 = 1.0 + alpha * a
    b1 = -2.0 * cos_w0
    b2 = 1.0 - alpha * a
    a0 = 1.0 + alpha / a
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha / a
    return np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]], dtype=np.float64)


def _stereo_lfilter_or_sos(sig: np.ndarray, sos: np.ndarray) -> np.ndarray:
    if sig.ndim == 1:
        return signal.sosfilt(sos, sig)
    return np.stack([signal.sosfilt(sos, sig[:, c]) for c in range(sig.shape[1])], axis=1)


def load_stereo(path: str | pathlib.Path) -> np.ndarray:
    y, _ = librosa.load(str(path), sr=SR, mono=False)
    arr = np.asarray(y, dtype=np.float64)
    if arr.ndim == 1:
        arr = np.stack([arr, arr], axis=1)
    else:
        arr = arr.T
        if arr.shape[1] == 1:
            arr = np.repeat(arr, 2, axis=1)
        else:
            arr = arr[:, :2]
    return arr


_PITCH_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_ENHARMONIC = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}
# Krumhansl-Schmuckler major & minor key profiles
_KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def normalize_musical_key(key_str: str) -> str:
    tok = (key_str or "C").strip().upper().split()[0].replace("MAJOR", "").replace("MINOR", "").replace("M", "")
    tok = tok.split("/")[0].split("_")[0]
    tok = _ENHARMONIC.get(tok, tok)
    return tok if tok in _PITCH_NAMES else "C"


def detect_musical_key(audio_or_path: np.ndarray | str | pathlib.Path, *, max_s: float = 45.0) -> dict[str, Any]:
    """Detect musical key (C..B major/minor) of ANY external song or underscore via chroma CQT."""
    if isinstance(audio_or_path, (str, pathlib.Path)):
        y, sr = librosa.load(str(audio_or_path), sr=22050, mono=True, duration=max_s)
    else:
        arr = np.asarray(audio_or_path, dtype=np.float64)
        mono = arr.mean(axis=1) if arr.ndim == 2 else arr
        mono = mono[: int(max_s * SR)]
        y = librosa.resample(mono.astype(np.float32), orig_sr=SR, target_sr=22050)
        sr = 22050

    if len(y) < sr // 2 or float(np.max(np.abs(y))) < 1e-5:
        return {"key": "C", "mode": "major", "confidence": 0.0}

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    vec = np.mean(chroma, axis=1)
    vec = (vec - np.mean(vec)) / (np.std(vec) + 1e-9)

    best_score = -9.0
    best_key = "C"
    best_mode = "major"
    for shift in range(12):
        for mode_name, prof in (("major", _KS_MAJOR), ("minor", _KS_MINOR)):
            rot = np.roll(prof, shift)
            rot = (rot - np.mean(rot)) / (np.std(rot) + 1e-9)
            corr = float(np.dot(vec, rot) / 12.0)
            if corr > best_score:
                best_score = corr
                best_key = _PITCH_NAMES[shift]
                best_mode = mode_name
    return {"key": best_key, "mode": best_mode, "confidence": round(best_score, 3)}


def extract_waveform_bars(arr: np.ndarray, t0: float, t1: float, bars: int = 44) -> list[float]:
    """Compute normalized peak-RMS envelope bars over [t0, t1] directly from a live stereo array."""
    i0 = max(0, int(round(t0 * SR)))
    i1 = min(len(arr), int(round(t1 * SR)))
    if i1 <= i0 or bars <= 0:
        return [0.0] * max(1, bars)
    mono = np.mean(np.abs(arr[i0:i1]), axis=1)
    edges = np.linspace(0, len(mono), bars + 1, dtype=int)
    vals = []
    for k in range(bars):
        seg = mono[edges[k] : edges[k + 1]]
        vals.append(float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0)
    mx = max(vals)
    if mx <= 1e-7:
        return [0.02] * bars
    # Gentle ^0.68 visual loudness curve so quiet transients stay legible alongside peaks
    return [round(float((v / mx) ** 0.68), 3) for v in vals]


def _pan_stereo(sig: np.ndarray, pan: float = 0.0, pan_to: float | None = None) -> np.ndarray:
    mono = sig.mean(axis=1) if sig.ndim == 2 else np.asarray(sig, dtype=np.float64)
    n = len(mono)
    p0 = float(np.clip(pan, -0.9, 0.9))
    p1 = p0 if pan_to is None else float(np.clip(pan_to, -0.9, 0.9))
    curve = np.linspace(p0, p1, n) if n else np.zeros(0)
    l_gain = np.sqrt(0.5 * (1.0 - curve))
    r_gain = np.sqrt(0.5 * (1.0 + curve))
    return np.stack([mono * l_gain, mono * r_gain], axis=1)


def _add_at(buf: np.ndarray, sig: np.ndarray, t_s: float, gain_db: float = 0.0, fade_ms: float = 6.0) -> None:
    if len(sig) == 0:
        return
    s = sig.copy() * (10.0 ** (gain_db / 20.0))
    fn = min(len(s) // 4, int(SR * fade_ms / 1000.0))
    if fn > 1:
        s[:fn] *= np.linspace(0.0, 1.0, fn)[:, None]
        s[-fn:] *= np.linspace(1.0, 0.0, fn)[:, None]
    i0 = int(round(t_s * SR))
    if i0 < 0:
        cut = min(len(s), -i0)
        s = s[cut:]
        i0 = 0
    if i0 >= len(buf) or len(s) == 0:
        return
    n = min(len(s), len(buf) - i0)
    buf[i0 : i0 + n] += s[:n]


def build_hall_impulse(t60: float = 2.6, cutoff_hz: float = 4200.0, seed: int = 19) -> np.ndarray:
    """Stereo Great Hall impulse response matching Herman Huang's seamless music exit."""
    rng = np.random.default_rng(seed)
    n = int(SR * t60 * 1.25)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-6.9 * t / t60)[:, None]
    ir = np.stack([_lp(ir[:, 0], cutoff_hz), _lp(ir[:, 1], cutoff_hz * 0.9)], axis=1)
    ir[: int(SR * 0.018)] *= 0.0
    for d, g in ((0.022, 0.55), (0.037, 0.42), (0.058, 0.30), (0.084, 0.22)):
        idx = int(d * SR)
        if idx + 2 < n:
            ir[idx : idx + 2] += g * rng.uniform(0.45, 1.0, (2, 2))
    ir /= np.abs(ir).sum(axis=0).max() + 1e-9
    return ir * 3.6


def carve_bed_under_voice(bed: np.ndarray, voice: np.ndarray, strength: float = 0.78) -> np.ndarray:
    """Apply Media-Use style 9-band spectral pocket carving + envelope ducking under VO."""
    if len(voice) == 0 or np.max(np.abs(voice)) < 1e-5:
        return bed.copy()

    n = len(bed)
    v_mono = voice[:n].mean(axis=1) if voice.ndim == 2 else voice[:n]
    b_mono = bed.mean(axis=1) if bed.ndim == 2 else bed

    # Measure spectral energy per third-octave center around human voice
    centers = [250.0, 400.0, 630.0, 1000.0, 1600.0, 2500.0, 4000.0]
    fft_n = min(len(v_mono), 262144)
    if fft_n < 1024:
        return bed.copy()
    freqs = np.fft.rfftfreq(fft_n, 1.0 / SR)
    vp = np.abs(np.fft.rfft(v_mono[:fft_n])) ** 2
    bp_spec = np.abs(np.fft.rfft(b_mono[:fft_n])) ** 2

    scores = []
    for fc in centers:
        lo, hi = fc / (2.0 ** (1 / 6)), fc * (2.0 ** (1 / 6))
        m = (freqs >= lo) & (freqs < hi)
        if np.any(m):
            v_pow = float(vp[m].mean())
            b_pow = float(bp_spec[m].mean())
            # Score balances where voice presence sits & music overlaps
            intel_weight = math.exp(-0.5 * (math.log2(fc / 1800.0) ** 2))
            scores.append((fc, (v_pow + 1e-12) * (b_pow + 1e-12) * intel_weight))
    scores.sort(key=lambda x: x[1], reverse=True)
    top_bands = scores[:3]

    carved = bed.copy()
    # Apply subtle EQ notch in dominant overlapping speech pockets ONLY when voice active
    env_win = int(SR * 0.04)
    v_abs = np.abs(v_mono)
    v_rms = np.sqrt(np.convolve(v_abs ** 2, np.ones(env_win) / env_win, mode="same") + 1e-12)
    v_db = 20.0 * np.log10(v_rms)
    active = np.clip((v_db - (-44.0)) / 18.0, 0.0, 1.0)
    # Fast attack, gentle 300ms release smoothing
    att = 1.0 - math.exp(-1.0 / (SR * 0.035))
    rel = 1.0 - math.exp(-1.0 / (SR * 0.320))
    smooth_env = np.zeros_like(active)
    cur = 0.0
    for idx in range(0, len(active), 128):
        target = float(active[idx])
        cur += (att * 128 if target > cur else rel * 128) * (target - cur)
        cur = min(1.0, max(0.0, cur))
        smooth_env[idx : idx + 128] = cur

    notched = carved.copy()
    for rank, (fc, _) in enumerate(top_bands):
        cut_db = -(4.5 + 3.5 * strength) * (1.0 - 0.18 * rank)
        sos = _biquad_peaking(fc, 1.35, cut_db)
        notched = _stereo_lfilter_or_sos(notched, sos)

    # Blend dry vs mid-carved track smoothly with speech activity, plus gentle gain duck (-4..-9 dB)
    duck_lin = 10.0 ** (-(4.0 + 5.5 * strength) / 20.0)
    blend = smooth_env[:, None]
    out = carved * (1.0 - blend) + notched * blend * (1.0 - blend * (1.0 - duck_lin))
    return out


def make_reversed_riser(audio_src: np.ndarray, sample_start_s: float, sample_dur_s: float, out_dur_s: float) -> np.ndarray:
    """Create a seamless musical riser by reversing a beat/chord slice with exponential swell."""
    i0 = max(0, int(sample_start_s * SR))
    n_src = max(int(0.25 * SR), int(sample_dur_s * SR))
    slc = audio_src[i0 : i0 + n_src].copy()
    if len(slc) < int(0.1 * SR):
        slc = audio_src[: min(len(audio_src), int(out_dur_s * SR))].copy()
    rev = slc[::-1]
    n_out = max(int(0.2 * SR), int(out_dur_s * SR))
    if len(rev) < n_out:
        rev = np.tile(rev, (n_out // len(rev) + 1, 1))
    rev = rev[-n_out:].copy()
    # Exponential rise + tail air HPF taper to prevent muddy rumble build
    t = np.linspace(0.0, 1.0, n_out)
    env = (t ** 2.1) * np.clip((1.0 - t) * 45.0, 0.0, 1.0)
    rev = _stereo_lfilter_or_sos(rev, signal.butter(2, 160.0 / (SR / 2), btype="highpass", output="sos"))
    return rev * env[:, None]


def generate_ambient_underscore(dur_s: float, *, root_hz: float = 98.0, bpm: float = 96.0, seed: int = 11) -> np.ndarray:
    """Rich organic offline underscore (warm harmonic drones + brushed pulse + Hall wash).

    Used strictly when no external BGM track is supplied, avoiding sterile single sines.
    """
    n = int(SR * dur_s)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)

    # Filtered velvet pad (root + 5th + warm octave + bright shimmer harmonic with stereo detune)
    pad_l = np.zeros(n)
    pad_r = np.zeros(n)
    for mult, amp, detune in ((1.0, 0.28, -0.35), (1.498, 0.24, +0.28), (2.0, 0.22, -0.45), (3.0, 0.16, +0.35), (4.0, 0.14, -0.25)):
        f_l = root_hz * mult + detune
        f_r = root_hz * mult - detune
        breath = 0.72 + 0.28 * np.sin(2.0 * math.pi * (bpm / 240.0) * t + mult)
        pad_l += np.sin(2.0 * math.pi * f_l * t) * amp * breath
        pad_r += np.sin(2.0 * math.pi * f_r * t) * amp * breath

    # Warm analog-like soft saturation + 1850 Hz damping so pad carries body while leaving 2.5-8 kHz airy
    pad = np.stack([_ot.sat(pad_l, 1.40), _ot.sat(pad_r, 1.40)], axis=1)
    pad = np.stack([_lp(_hp(pad[:, c], 48.0), 1850.0) for c in (0, 1)], axis=1)

    # Subtle rhythmic brushed pulse synced strictly to BPM grid
    beat_period = 60.0 / bpm
    pulse_l = np.zeros(n)
    pulse_r = np.zeros(n)
    b_t = 0.0
    beat_idx = 0
    while b_t + 0.2 < dur_s:
        idx = int(b_t * SR)
        if beat_idx % 2 == 0:
            sub_hit = _ot.sub(f=root_hz * 0.56, dur=0.30) * 0.26
            nn = min(len(sub_hit), n - idx)
            pulse_l[idx : idx + nn] += sub_hit[:nn]
            pulse_r[idx : idx + nn] += sub_hit[:nn]
        else:
            # Soft brushed shaker texture in high-mid stereo
            sh = _bp(rng.standard_normal(int(0.09 * SR)), 2800.0, 6200.0) * np.exp(-np.arange(int(0.09 * SR)) / (0.022 * SR))
            pan_v = 0.28 if beat_idx % 4 == 1 else -0.28
            sh_st = _pan_stereo(sh * 0.22, pan=pan_v)
            nn = min(len(sh_st), n - idx)
            pulse_l[idx : idx + nn] += sh_st[:nn, 0]
            pulse_r[idx : idx + nn] += sh_st[:nn, 1]
        b_t += beat_period
        beat_idx += 1

    bed = pad * 0.42 + np.stack([pulse_l, pulse_r], axis=1) * 0.65
    # Pass through subtle room glue so everything feels recorded in studio space
    hall = build_hall_impulse(t60=1.8, cutoff_hz=2800.0, seed=seed + 3)
    wet = np.stack([signal.fftconvolve(bed[:, c], hall[:, c])[:n] for c in (0, 1)], axis=1)
    combined = bed * 0.78 + wet * 0.26
    mx = float(np.max(np.abs(combined))) + 1e-9
    return (combined / mx) * 0.55


class SoundEngine5Stem:
    """Unified 5-Stem acoustic composer with shared convolution room & mastering gate."""

    def __init__(self, dur_s: float, *, profile: str = "editorial-clean", t60: float = 1.05):
        self.dur_s = float(dur_s)
        self.profile = profile
        self.n = int(round(self.dur_s * SR))
        self.pad_n = self.n + SR * 3  # room tail margin
        self.index = json.loads(INDEX_PATH.read_text(encoding="utf-8")) if INDEX_PATH.exists() else {"assets": []}
        self._by_id = {a["id"]: a for a in self.index.get("assets", [])}
        self._cache: dict[str, np.ndarray] = {}

        # Five explicit buses
        self.voice = np.zeros((self.pad_n, 2), dtype=np.float64)
        self.ambience = np.zeros((self.pad_n, 2), dtype=np.float64)
        self.foley = np.zeros((self.pad_n, 2), dtype=np.float64)
        self.transitions = np.zeros((self.pad_n, 2), dtype=np.float64)
        self.music = np.zeros((self.pad_n, 2), dtype=np.float64)

        # Shared convolution room wet accumulator
        self._room_wet = np.zeros((self.pad_n, 2), dtype=np.float64)
        self._hall_wet = np.zeros((self.pad_n, 2), dtype=np.float64)
        self.t60 = t60
        self.silence_pockets: list[dict[str, float]] = []
        self.music_dips: list[dict[str, float]] = []
        self.filter_sweeps: list[dict[str, Any]] = []
        self.active_music_key: str = "C"
        self.events_log: list[dict[str, Any]] = []

    def _resolve_asset(self, asset_id_or_query: str, *, spectrum_role: str | None = None) -> tuple[pathlib.Path, dict[str, Any]]:
        if asset_id_or_query in self._by_id:
            meta = self._by_id[asset_id_or_query]
            return ROOT / meta["rel_path"], meta

        # Direct path fallback
        cand_path = ROOT / asset_id_or_query
        if cand_path.exists():
            return cand_path, {"id": asset_id_or_query, "spectrum_role": spectrum_role or "full_spectrum"}

        # Query selection preferring active profile & spectrum role
        q = asset_id_or_query.lower()
        scored = []
        for a in self.index.get("assets", []):
            score = 0.0
            hay = f"{a['id']} {a['category']} {' '.join(a.get('tags', []))}".lower()
            if q in hay:
                score += 6.0
            elif any(tok in hay for tok in q.replace("-", " ").split()):
                score += 3.0
            if self.profile in a.get("profiles", []):
                score += 3.0
            elif "universal-room" in a.get("profiles", []):
                score += 1.5
            if spectrum_role and a.get("spectrum_role") == spectrum_role:
                score += 4.0
            if score > 0:
                scored.append((score, a))
        if not scored:
            raise KeyError(f"No asset matching '{asset_id_or_query}' (role={spectrum_role})")
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]
        return ROOT / best["rel_path"], best

    def _get_audio(self, path: pathlib.Path) -> np.ndarray:
        k = str(path.resolve())
        if k not in self._cache:
            self._cache[k] = load_stereo(path)
        return self._cache[k]

    def add_room_tone(
        self,
        asset_id_or_query: str = "se/ambience__fs-426767-apartment-room-tone-wav",
        *,
        gain_db: float = -34.0,
        hp_hz: float = 85.0,
        lp_hz: float = 6800.0,
    ) -> None:
        """Lay down a continuous physical room-tone bed so quiet pauses never flatline to -inf."""
        p, meta = self._resolve_asset(asset_id_or_query, spectrum_role="room_bed")
        seg = self._get_audio(p)
        tiled = np.tile(seg, (self.n // len(seg) + 2, 1))[: self.n]
        shaped = np.stack([_lp(_hp(tiled[:, c], hp_hz), lp_hz) for c in (0, 1)], axis=1)
        rms = float(np.sqrt(np.mean(shaped ** 2))) + 1e-9
        target_rms = 10.0 ** (gain_db / 20.0)
        _add_at(self.ambience, shaped * (target_rms / rms), 0.0, gain_db=0.0, fade_ms=80.0)
        self.events_log.append({"bus": "ambience", "asset": meta["id"], "gain_db": gain_db})

    def add_voice(self, wav_path: str | pathlib.Path, *, start_s: float, gain_db: float = 0.0, send: float = 0.08) -> float:
        sig = load_stereo(wav_path)
        # Clean sub-85 Hz rumble on dialogue and normalize gently to -16 dBFS active RMS
        cleaned = np.stack([_hp(sig[:, c], 85.0) for c in (0, 1)], axis=1)
        active = np.abs(cleaned.mean(axis=1)) > 0.008
        rms = float(np.sqrt(np.mean(cleaned[active] ** 2))) if np.any(active) else float(np.sqrt(np.mean(cleaned ** 2)))
        target = 10.0 ** ((-16.0 + gain_db) / 20.0)
        scaled = cleaned * (target / max(rms, 1e-6))
        _add_at(self.voice, scaled, start_s, gain_db=0.0, fade_ms=10.0)
        _add_at(self._room_wet, scaled * send, start_s, gain_db=0.0, fade_ms=10.0)
        dur = len(sig) / SR
        self.events_log.append({"bus": "voice", "file": str(wav_path), "t": start_s, "dur": round(dur, 3)})
        return dur

    def add_physical_foley(
        self,
        kind: str,
        *,
        t_s: float,
        gain_db: float = -8.0,
        pan: float = 0.0,
        pan_to: float | None = None,
        send: float = 0.25,
        freq: float | None = None,
        dur_s: float | None = None,
    ) -> None:
        """Synthesize room-matched acoustic material (air, wood, glass, sub, bubble) without raw sines."""
        if kind == "air":
            mono = _ot.air(dur=dur_s or 0.45, f0=freq or 280.0, f1=(freq or 280.0) * 9.0, q=1.4, shape=0.45)
        elif kind == "wood":
            mono = _ot.wood(f=freq or 185.0, dur=dur_s or 0.14)
        elif kind == "glass":
            mono = _ot.glass(f=freq or 740.0, dur=dur_s or 0.65, bright=0.95)
        elif kind == "sub":
            mono = _ot.sub(f=freq or 58.0, dur=dur_s or 0.55)
        elif kind == "bubble":
            mono = _ot.bubble(f=freq or 520.0, dur=dur_s or 0.22)
        else:
            raise ValueError(f"Unsupported physical material '{kind}'")

        st = _pan_stereo(mono, pan=pan, pan_to=pan_to)
        _add_at(self.foley, st, t_s, gain_db=gain_db, fade_ms=4.0)
        _add_at(self._room_wet, st * send, t_s, gain_db=0.0, fade_ms=4.0)
        self.events_log.append({"bus": "foley", "material": kind, "t": t_s, "gain_db": gain_db})

    def add_asset_cue(
        self,
        asset_query: str,
        *,
        t_s: float,
        bus: str = "foley",
        gain_db: float = -6.0,
        pre_lap_ms: float = 0.0,
        pan: float = 0.0,
        pan_to: float | None = None,
        send: float = 0.22,
        spectrum_role: str | None = None,
        hp_hz: float | None = None,
        lp_hz: float | None = None,
        max_dur_s: float | None = None,
        reverse: bool = False,
    ) -> None:
        p, meta = self._resolve_asset(asset_query, spectrum_role=spectrum_role)
        raw = self._get_audio(p).copy()
        if max_dur_s is not None:
            raw = raw[: int(max_dur_s * SR)]
        if reverse:
            raw = raw[::-1].copy()
        if hp_hz:
            raw = np.stack([_hp(raw[:, c], hp_hz) for c in (0, 1)], axis=1)
        if lp_hz:
            raw = np.stack([_lp(raw[:, c], lp_hz) for c in (0, 1)], axis=1)

        st = _pan_stereo(raw, pan=pan, pan_to=pan_to) if (pan != 0.0 or pan_to is not None) else raw
        # Peak normalize before gain placement for consistent predictable balance
        mx = float(np.max(np.abs(st))) + 1e-9
        st = st / mx
        target_t = max(0.0, t_s - pre_lap_ms / 1000.0)
        target_bus = self.transitions if bus == "transitions" else self.foley
        _add_at(target_bus, st, target_t, gain_db=gain_db, fade_ms=8.0)
        _add_at(self._room_wet, st * send * (10.0 ** (gain_db / 20.0)), target_t, gain_db=0.0, fade_ms=8.0)
        self.events_log.append({
            "bus": bus,
            "asset": meta["id"],
            "t": round(target_t, 3),
            "j_cut_ms": pre_lap_ms,
            "gain_db": gain_db,
        })

    def add_source_clip_audio(
        self,
        media_path: str | pathlib.Path,
        *,
        t_s: float,
        dur_s: float,
        src_start_s: float = 0.0,
        bus: str = "ambience",
        target_rms_db: float = -22.0,
        pre_lap_ms: float = 0.0,
        pan: float = 0.0,
        hp_hz: float = 90.0,
        lp_hz: float | None = None,
        fade_ms: float = 28.0,
        send: float = 0.14,
    ) -> float:
        """Extract genuine audio directly from a camera clip or WAV/MP4 onto a project bus."""
        src_p = pathlib.Path(media_path)
        if not src_p.is_absolute():
            src_p = ROOT / src_p
        cache_key = f"clip::{src_p.resolve()}"
        if cache_key not in self._cache:
            if src_p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm", ".m4v"):
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                    tmp_wav = pathlib.Path(tf.name)
                try:
                    subprocess.run(
                        [FFMPEG, "-y", "-v", "error", "-i", str(src_p), "-vn", "-ac", "2", "-ar", str(SR), str(tmp_wav)],
                        check=True, capture_output=True, text=True,
                    )
                    self._cache[cache_key] = load_stereo(tmp_wav)
                finally:
                    tmp_wav.unlink(missing_ok=True)
            else:
                self._cache[cache_key] = load_stereo(src_p)

        full = self._cache[cache_key]
        i0 = max(0, int(round(src_start_s * SR)))
        need = max(1, int(round(dur_s * SR)))
        slc = full[i0 : i0 + need].copy()
        if len(slc) < need:
            slc = np.pad(slc, ((0, need - len(slc)), (0, 0)))

        if hp_hz:
            slc = np.stack([_hp(slc[:, c], hp_hz) for c in (0, 1)], axis=1)
        if lp_hz:
            slc = np.stack([_lp(slc[:, c], lp_hz) for c in (0, 1)], axis=1)

        if bus == "voice":
            active = np.abs(slc.mean(axis=1)) > 0.008
            cur_rms = float(np.sqrt(np.mean(slc[active] ** 2))) if np.any(active) else float(np.sqrt(np.mean(slc ** 2)))
        else:
            cur_rms = float(np.sqrt(np.mean(slc ** 2)))
        scale = (10.0 ** (target_rms_db / 20.0)) / max(cur_rms, 1e-6)
        # Guard quiet source tracks from boosting pure hiss by > +24 dB
        scale = min(scale, 15.8)
        scaled = slc * scale
        if pan != 0.0:
            scaled = _pan_stereo(scaled, pan=pan)

        target_t = max(0.0, t_s - pre_lap_ms / 1000.0)
        bus_map = {
            "voice": self.voice,
            "ambience": self.ambience,
            "foley": self.foley,
            "transitions": self.transitions,
        }
        dest = bus_map.get(bus, self.ambience)
        _add_at(dest, scaled, target_t, gain_db=0.0, fade_ms=fade_ms)
        if send > 0.0:
            _add_at(self._room_wet, scaled * send, target_t, gain_db=0.0, fade_ms=fade_ms)
        self.events_log.append({
            "bus": bus,
            "asset": f"src:{src_p.name}",
            "t": round(target_t, 3),
            "dur": round(len(scaled) / SR, 3),
            "target_rms_db": target_rms_db,
        })
        return float(len(scaled) / SR)

    def add_layered_transition(
        self,
        *,
        t_s: float,
        low_asset: str | None = "se/impact__kenney-impact-impactsoft-heavy-000",
        mid_asset: str | None = "ge/whoosh-2",
        air_asset: str | None = "se/transition__fs-786514-swoosh-v2",
        pre_lap_ms: float = 110.0,
        pan: float = 0.0,
        pan_to: float | None = None,
        gain_db: float = -3.0,
        send: float = 0.28,
    ) -> None:
        """Herman Huang Technique 1: 3-Band Audio Spectrum Cake with non-overlapping EQs."""
        if low_asset:
            self.add_asset_cue(
                low_asset, t_s=t_s, bus="transitions", gain_db=gain_db - 2.5,
                pre_lap_ms=pre_lap_ms * 0.25, pan=0.0, send=send * 0.5,
                spectrum_role="sub_low", hp_hz=32.0, lp_hz=155.0, max_dur_s=0.9,
            )
        if mid_asset:
            self.add_asset_cue(
                mid_asset, t_s=t_s, bus="transitions", gain_db=gain_db - 1.5,
                pre_lap_ms=pre_lap_ms, pan=pan, pan_to=pan_to, send=send,
                spectrum_role="mid_body", hp_hz=260.0, lp_hz=2800.0, max_dur_s=1.1,
            )
        if air_asset:
            self.add_asset_cue(
                air_asset, t_s=t_s, bus="transitions", gain_db=gain_db - 2.0,
                pre_lap_ms=pre_lap_ms * 0.7, pan=pan, pan_to=pan_to, send=send * 1.1,
                spectrum_role="high_air", hp_hz=2600.0, lp_hz=15500.0, max_dur_s=0.85,
            )

    def add_music_bed(
        self,
        track_path: str | pathlib.Path | None = None,
        *,
        segments: list[dict[str, Any]] | None = None,
        gain_db: float = -15.5,
        reverse_lead_in_s: float = 0.9,
        hall_exit_at_s: float | None = None,
        loop_end_rise_s: float = 0.0,
        root_hz: float = 98.0,
        bpm: float = 96.0,
    ) -> None:
        """Load external music or generate offline underscore, shaped per segment + Hall exit."""
        if track_path and pathlib.Path(track_path).exists():
            src = load_stereo(track_path)
        else:
            src = generate_ambient_underscore(max(self.dur_s + 2.0, 12.0), root_hz=root_hz, bpm=bpm)

        # Detect musical key of the active song/underscore automatically for tonal SFX harmony
        key_info = detect_musical_key(src)
        self.active_music_key = key_info["key"]
        self.events_log.append({
            "bus": "music",
            "source": str(track_path) if track_path else "offline_underscore",
            "detected_key": key_info["key"],
            "detected_mode": key_info["mode"],
        })

        # Normalize music source gently before segment fades
        src_rms = float(np.sqrt(np.mean(src ** 2))) + 1e-9
        src = src * (10.0 ** (gain_db / 20.0) / src_rms)

        segs = segments or [{"start_s": 0.0, "end_s": self.dur_s, "src_offset_s": 0.0}]
        for seg in segs:
            t0 = float(seg["start_s"])
            t1 = float(seg["end_s"])
            if t1 <= t0:
                continue
            need_n = int((t1 - t0) * SR)
            off = int(float(seg.get("src_offset_s", 0.0)) * SR)
            tiled = np.tile(src, ((off + need_n) // len(src) + 2, 1))
            clip = tiled[off : off + need_n].copy()

            if seg.get("lead_in_reverse", reverse_lead_in_s > 0):
                riser_d = float(seg.get("lead_in_dur_s", reverse_lead_in_s))
                riser = make_reversed_riser(src, float(seg.get("src_offset_s", 0.0)), 1.2, riser_d)
                _add_at(self.music, riser * 0.85, max(0.0, t0 - riser_d * 0.82), gain_db=0.0, fade_ms=10.0)

            _add_at(self.music, clip, t0, gain_db=0.0, fade_ms=35.0)

            if seg.get("hall_tail", False) or (hall_exit_at_s is not None and abs(t1 - hall_exit_at_s) < 0.06):
                # Snap last beat into stereo Great Hall reverb bus
                beat_len = min(len(clip), int(0.45 * SR))
                _add_at(self._hall_wet, clip[-beat_len:] * 1.15, max(0.0, t1 - beat_len / SR), gain_db=0.0, fade_ms=15.0)

        if loop_end_rise_s > 0.1 and self.dur_s > loop_end_rise_s:
            # Final segment reverse riser easing cleanly back into frame 0.000s loop
            tail_riser = make_reversed_riser(src, 0.0, 1.3, loop_end_rise_s)
            _add_at(self.music, tail_riser * 0.9, self.dur_s - loop_end_rise_s, gain_db=0.0, fade_ms=12.0)

    def add_silence_pocket(
        self,
        t0: float,
        t1: float,
        *,
        fade_ms: float = 28.0,
        duck_music_db: float = -48.0,
        duck_ambience_db: float = -18.0,
        duck_transitions_db: float = -40.0,
    ) -> None:
        """Schedule intentional micro-silence / contrast pocket before a reveal or punchline."""
        self.silence_pockets.append({
            "t0": round(t0, 3),
            "t1": round(t1, 3),
            "fade_ms": fade_ms,
            "duck_music_db": duck_music_db,
            "duck_ambience_db": duck_ambience_db,
            "duck_transitions_db": duck_transitions_db,
        })

    def _apply_pocket_mask(self, buf: np.ndarray, key: str) -> np.ndarray:
        out = buf.copy()
        for pk in self.silence_pockets:
            i0 = max(0, int(pk["t0"] * SR))
            i1 = min(len(out), int(pk["t1"] * SR))
            if i1 <= i0:
                continue
            fn = min((i1 - i0) // 2, int(SR * pk["fade_ms"] / 1000.0))
            duck_lin = 10.0 ** (pk[key] / 20.0)
            env = np.full(i1 - i0, duck_lin, dtype=np.float64)
            if fn > 1:
                env[:fn] = np.linspace(1.0, duck_lin, fn)
                env[-fn:] = np.linspace(duck_lin, 1.0, fn)
            out[i0:i1] *= env[:, None]
        return out

    def add_music_dip(
        self,
        t0: float,
        t1: float,
        *,
        db: float = -10.0,
        fade_ms: float = 180.0,
    ) -> None:
        """Schedule a smooth NLE volume dip on the music bed without cutting the track dead."""
        self.music_dips.append({"t0": float(t0), "t1": float(t1), "db": float(db), "fade_ms": float(fade_ms)})

    def _apply_music_dips(self, buf: np.ndarray) -> np.ndarray:
        out = buf.copy()
        for dp in self.music_dips:
            i0 = max(0, int(dp["t0"] * SR))
            i1 = min(len(out), int(dp["t1"] * SR))
            if i1 <= i0:
                continue
            fn = min((i1 - i0) // 2, max(2, int(SR * dp["fade_ms"] / 1000.0)))
            dip_lin = 10.0 ** (dp["db"] / 20.0)
            env = np.full(i1 - i0, dip_lin, dtype=np.float64)
            env[:fn] = np.linspace(1.0, dip_lin, fn)
            env[-fn:] = np.linspace(dip_lin, 1.0, fn)
            out[i0:i1] *= env[:, None]
        return out

    def add_tonal_sfx(
        self,
        kind: str = "tonal_hit",
        *,
        t_s: float,
        key: str | None = None,
        auto_match_music: bool = True,
        gain_db: float = -7.5,
        pre_lap_ms: float = 0.0,
        pan: float = 0.0,
        pan_to: float | None = None,
        max_dur_s: float | None = None,
        fade_ms: float = 80.0,
        send: float = 0.22,
    ) -> str:
        """Place a key-matched tonal drone or hit from studio_kit/sfx/tonal_pack/ (Multiply Sound)."""
        want_key = normalize_musical_key(key) if key else (self.active_music_key if auto_match_music else "C")
        want_type = "tonal_drone" if "drone" in kind.lower() else "tonal_hit"
        matches = [
            a for a in self.index.get("assets", [])
            if a.get("tonal_type") == want_type and a.get("musical_key") == want_key
        ]
        if not matches:
            # Fallback to any tonal asset of the requested type if specific key missing
            matches = [a for a in self.index.get("assets", []) if a.get("tonal_type") == want_type]
        if not matches:
            raise KeyError(f"No tonal SFX found for kind='{want_type}', key='{want_key}'. Run build_sound_index.py.")

        chosen = matches[0]
        p = ROOT / chosen["rel_path"]
        raw = self._get_audio(p).copy()
        if max_dur_s is not None:
            raw = raw[: int(max_dur_s * SR)]
        # Light 42 Hz safety high-pass so tonal drones stay clean under voice/music
        raw = np.stack([_hp(raw[:, c], 42.0) for c in (0, 1)], axis=1)
        st = _pan_stereo(raw, pan=pan, pan_to=pan_to) if (pan != 0.0 or pan_to is not None) else raw
        mx = float(np.max(np.abs(st))) + 1e-9
        st = st / mx

        target_t = max(0.0, t_s - pre_lap_ms / 1000.0)
        dest_bus = self.ambience if want_type == "tonal_drone" else self.transitions
        _add_at(dest_bus, st, target_t, gain_db=gain_db, fade_ms=fade_ms)
        if send > 0.0:
            _add_at(self._room_wet, st * send * (10.0 ** (gain_db / 20.0)), target_t, gain_db=0.0, fade_ms=fade_ms)
        self.events_log.append({
            "bus": "ambience" if want_type == "tonal_drone" else "transitions",
            "asset": chosen["id"],
            "tonal_key": want_key,
            "t": round(target_t, 3),
            "gain_db": gain_db,
        })
        return str(chosen["id"])

    def add_filter_sweep(
        self,
        bus: str = "music",
        *,
        t0: float,
        t1: float,
        sweep_type: str = "lowpass_open",
        f_start: float = 420.0,
        f_end: float = 14000.0,
    ) -> None:
        """Schedule a Jacob Nordin style LP/HP filter sweep (e.g. muffled interior opening to bright exterior)."""
        self.filter_sweeps.append({
            "bus": bus,
            "t0": float(t0),
            "t1": float(t1),
            "sweep_type": sweep_type,
            "f_start": float(f_start),
            "f_end": float(f_end),
        })

    def _apply_filter_sweeps(self, buf: np.ndarray, bus_name: str) -> np.ndarray:
        sweeps = [sw for sw in self.filter_sweeps if sw["bus"] == bus_name]
        if not sweeps:
            return buf
        out = buf.copy()
        for sw in sweeps:
            i0 = max(0, int(sw["t0"] * SR))
            i1 = min(len(out), int(sw["t1"] * SR))
            if i1 - i0 < 512:
                continue
            seg = out[i0:i1]
            n_seg = len(seg)
            steps = 12
            edges = np.linspace(0, n_seg, steps + 1, dtype=int)
            freqs = np.geomspace(max(60.0, sw["f_start"]), min(18000.0, sw["f_end"]), steps)
            rendered = np.zeros_like(seg)
            w_acc = np.zeros((n_seg, 1), dtype=np.float64)
            is_hp = "highpass" in sw["sweep_type"].lower()
            for k in range(steps):
                a = max(0, edges[k] - 512)
                b = min(n_seg, edges[k + 1] + 512)
                fc = float(freqs[k])
                chunk = np.stack([(_hp if is_hp else _lp)(seg[a:b, c], fc, order=2) for c in (0, 1)], axis=1)
                win = np.hanning(b - a)[:, None] if (b - a) > 8 else np.ones((b - a, 1))
                rendered[a:b] += chunk * win
                w_acc[a:b] += win
            out[i0:i1] = rendered / np.maximum(w_acc, 1e-6)
        return out

    def apply_beat_sheet_cues(self, sheet: dict[str, Any]) -> None:
        """Declaratively execute beat-sheet silence_pockets and sound_cues onto 5-stem buses."""
        for pk in sheet.get("silence_pockets", []):
            self.add_silence_pocket(
                float(pk["t0"]),
                float(pk["t1"]),
                fade_ms=float(pk.get("fade_ms", 24.0)),
                duck_music_db=float(pk.get("duck_music_db", -52.0)),
                duck_ambience_db=float(pk.get("duck_ambience_db", -16.0)),
                duck_transitions_db=float(pk.get("duck_transitions_db", -48.0)),
            )

        for cue in sheet.get("sound_cues", []):
            t_s = float(cue.get("t_s", 0.0))
            bus = str(cue.get("bus", "foley"))
            pre_lap = float(cue.get("pre_lap_ms", 0.0))
            pan = float(cue.get("pan", 0.0))
            gain_db = float(cue.get("gain_db", -7.0))
            layers = cue.get("layers", [])

            if cue.get("contrast_rule") == "room_tone_bed" and layers:
                self.add_room_tone(
                    layers[0]["asset"],
                    gain_db=float(cue.get("gain_db", -37.0)),
                    hp_hz=float(cue.get("hp_hz", 90.0)),
                    lp_hz=float(cue.get("lp_hz", 6400.0)),
                )
                continue

            if cue.get("intensity") == "hero" and len(layers) >= 2:
                by_role = {lay.get("spectrum_role"): lay["asset"] for lay in layers if lay.get("asset")}
                self.add_layered_transition(
                    t_s=t_s,
                    low_asset=by_role.get("sub_low"),
                    mid_asset=by_role.get("mid_body"),
                    air_asset=by_role.get("high_air"),
                    pre_lap_ms=pre_lap or 90.0,
                    pan=pan,
                    gain_db=gain_db,
                )
                continue

            for lay in layers:
                if "material" in lay:
                    self.add_physical_foley(
                        lay["material"],
                        t_s=t_s,
                        gain_db=float(lay.get("gain_db", gain_db)),
                        pan=float(lay.get("pan", pan)),
                        freq=lay.get("freq"),
                        dur_s=lay.get("dur_s"),
                    )
                elif "asset" in lay:
                    self.add_asset_cue(
                        lay["asset"],
                        t_s=t_s,
                        bus=bus,
                        gain_db=float(lay.get("gain_db", gain_db)),
                        pre_lap_ms=float(lay.get("pre_lap_ms", pre_lap)),
                        pan=float(lay.get("pan", pan)),
                        pan_to=lay.get("pan_to", cue.get("pan_to")),
                        spectrum_role=lay.get("spectrum_role"),
                        hp_hz=lay.get("hp_hz", cue.get("hp_hz")),
                        lp_hz=lay.get("lp_hz", cue.get("lp_hz")),
                        max_dur_s=lay.get("max_dur_s", cue.get("max_dur_s")),
                        reverse=bool(lay.get("reverse", False)),
                    )

        for tc in sheet.get("tonal_cues", []):
            self.add_tonal_sfx(
                str(tc.get("kind", "tonal_hit")),
                t_s=float(tc["t_s"]),
                key=tc.get("key"),
                auto_match_music=bool(tc.get("auto_match_music", True)),
                gain_db=float(tc.get("gain_db", -7.5)),
                pre_lap_ms=float(tc.get("pre_lap_ms", 0.0)),
                pan=float(tc.get("pan", 0.0)),
                pan_to=tc.get("pan_to"),
                max_dur_s=tc.get("max_dur_s"),
                fade_ms=float(tc.get("fade_ms", 80.0)),
            )

        for sw in sheet.get("filter_sweeps", []):
            self.add_filter_sweep(
                str(sw.get("bus", "music")),
                t0=float(sw["t0"]),
                t1=float(sw["t1"]),
                sweep_type=str(sw.get("sweep_type", "lowpass_open")),
                f_start=float(sw.get("f_start", 420.0)),
                f_end=float(sw.get("f_end", 14000.0)),
            )

    def render_mix(
        self,
        out_dir: str | pathlib.Path,
        *,
        target_lufs: float = -16.0,
        target_peak_db: float = -4.2,
        export_stems: bool = True,
    ) -> dict[str, Any]:
        out_p = pathlib.Path(out_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        # 1. Apply music dips, EQ sweeps & silence pockets cleanly across non-voice beds
        music_shaped = self._apply_music_dips(self.music[: self.n])
        music_shaped = self._apply_filter_sweeps(music_shaped, "music")
        music_shaped = self._apply_pocket_mask(music_shaped, "duck_music_db")
        amb_shaped = self._apply_filter_sweeps(self.ambience[: self.n], "ambience")
        amb_shaped = self._apply_pocket_mask(amb_shaped, "duck_ambience_db")
        trans_shaped = self._apply_pocket_mask(self.transitions[: self.n], "duck_transitions_db")
        foley_shaped = self._apply_filter_sweeps(self.foley[: self.n], "foley")
        voice_shaped = self.voice[: self.n].copy()

        # 2. Adaptive 9-band FFT spectral voice-pocket carving on music bed
        has_voice = float(np.max(np.abs(voice_shaped))) > 1e-4
        if has_voice:
            music_shaped = carve_bed_under_voice(music_shaped, voice_shaped, strength=0.78)

        # 3. Shared Studio Room IR (T60 = 1.05s) + Great Hall Reverb Tail (T60 = 2.6s)
        room_ir = _ot.impulse(self.t60)
        hall_ir = build_hall_impulse(t60=2.6, cutoff_hz=4200.0)
        room_ret = np.stack([signal.fftconvolve(self._room_wet[:, c], room_ir[:, c])[: self.n] for c in (0, 1)], axis=1)
        hall_ret = np.stack([signal.fftconvolve(self._hall_wet[:, c], hall_ir[:, c])[: self.n] for c in (0, 1)], axis=1)
        hall_ret = self._apply_pocket_mask(hall_ret, "duck_transitions_db")

        # 4. Sum 5 stems + Corrective Anti-Mud Conditioning (tame 210 Hz accumulation + gentle 6.5 kHz air lift)
        raw_sum = voice_shaped + amb_shaped + foley_shaped + trans_shaped + music_shaped + room_ret * 0.72 + hall_ret * 0.88
        raw_sum = np.stack([_hp(raw_sum[:, c], 32.0) for c in (0, 1)], axis=1)
        raw_sum = _stereo_lfilter_or_sos(raw_sum, _biquad_peaking(215.0, 1.05, -3.2))
        raw_sum = _stereo_lfilter_or_sos(raw_sum, _biquad_peaking(6200.0, 0.8, +2.0))

        # Edge safety micro-fades (12ms)
        fn = min(self.n // 10, int(SR * 0.012))
        if fn > 1:
            raw_sum[:fn] *= np.linspace(0.0, 1.0, fn)[:, None]
            raw_sum[-fn:] *= np.linspace(1.0, 0.0, fn)[:, None]

        # Pre-normalize safely to prevent int16 clipping prior to FFmpeg ebur128 mastering
        pk = float(np.max(np.abs(raw_sum))) + 1e-9
        if pk > 0.85:
            raw_sum = raw_sum * (0.85 / pk)

        raw_wav = out_p / "_mix_raw.wav"
        master_wav = out_p / "master_mix.wav"
        sf.write(str(raw_wav), raw_sum.astype(np.float32), SR, subtype="PCM_24")

        # 5. Iterative ebur128 + true-peak ceiling limiter (matches sound_pass.py precision)
        def _measure_ebur(wav_file: pathlib.Path) -> tuple[float, float]:
            res = subprocess.run(
                [FFMPEG, "-nostats", "-i", str(wav_file), "-af", "ebur128=peak=true", "-f", "null", "-"],
                capture_output=True, text=True, check=True,
            ).stderr
            lufs_m = re.findall(r"I:\s+([-\d.]+)\s+LUFS", res)
            pk_m = re.findall(r"Peak:\s+([-\d.]+)\s+dBFS", res)
            return float(lufs_m[-1]), float(pk_m[-1])

        gain_db = 0.0
        lim_lin = 10.0 ** (target_peak_db / 20.0)
        final_lufs = -16.0
        final_peak = -4.2
        for _ in range(5):
            af = f"volume={gain_db:.2f}dB,alimiter=limit={lim_lin:.4f}:level=disabled:attack=1.5:release=60"
            subprocess.run(
                [FFMPEG, "-y", "-v", "error", "-i", str(raw_wav), "-af", af, "-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "2", str(master_wav)],
                check=True, capture_output=True, text=True,
            )
            final_lufs, final_peak = _measure_ebur(master_wav)
            if abs(final_lufs - target_lufs) <= 0.45 and final_peak <= target_peak_db + 0.25:
                break
            if final_peak > target_peak_db:
                lim_lin *= 0.90
            gain_db += target_lufs - final_lufs

        stems_paths: dict[str, str] = {}
        if export_stems:
            stems_dir = out_p / "stems"
            stems_dir.mkdir(exist_ok=True)
            for sname, arr in (
                ("stem_voice.wav", voice_shaped),
                ("stem_ambience.wav", amb_shaped),
                ("stem_foley.wav", foley_shaped + room_ret * 0.4),
                ("stem_transitions.wav", trans_shaped + room_ret * 0.32 + hall_ret * 0.35),
                ("stem_music.wav", music_shaped + hall_ret * 0.53),
            ):
                sp = stems_dir / sname
                sf.write(str(sp), np.clip(arr, -0.99, 0.99).astype(np.float32), SR, subtype="PCM_16")
                stems_paths[sname] = str(sp)

        if raw_wav.exists():
            raw_wav.unlink()

        plan = {
            "master_wav": str(master_wav),
            "duration_s": self.dur_s,
            "profile": self.profile,
            "lufs_i": final_lufs,
            "peak_dbfs": final_peak,
            "silence_pockets": self.silence_pockets,
            "stems": stems_paths,
            "weftcut_role_mapping": {
                "stem_voice.wav": "dialogue",
                "stem_ambience.wav": "ambience",
                "stem_foley.wav": "sfx",
                "stem_transitions.wav": "sfx",
                "stem_music.wav": "bgm",
            },
            "events": self.events_log,
        }
        plan_path = out_p / "weftcut_stem_plan.json"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        return plan
