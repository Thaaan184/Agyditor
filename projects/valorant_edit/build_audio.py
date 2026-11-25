"""5-Stem Cinema & Comedic Audio Builder for Valorant Harbor 3K Vertical Edit.

Reads timing strictly from timeline_map.py, remaps original game+comms audio with
pitch-preserved atempo, surgically censors profanity at CENSOR_SRC_SPAN, generates
a clean local 124 BPM dark tactical groove (zero 100-350 Hz mud), mixes all 5 buses
via studio_kit/sound_engine.py, exports real waveform bars, and runs acoustic_audit.py.
"""
from __future__ import annotations

import json
import math
import pathlib
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np
import soundfile as sf
from scipy import signal

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.valorant_edit import timeline_map as tm  # noqa: E402
from studio_kit.acoustic_audit import audit_media  # noqa: E402
from studio_kit.sound_engine import (  # noqa: E402
    SR,
    SoundEngine5Stem,
    _biquad_peaking,
    _hp,
    _lp,
    _stereo_lfilter_or_sos,
    extract_waveform_bars,
    load_stereo,
)

FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
BEAT_SHEET_PATH = ROOT / "projects" / "valorant_edit" / "beat_sheet.json"


def _atempo_chain(speed: float) -> str:
    """Build valid FFmpeg atempo filter chain for any positive speed factor."""
    factors: list[float] = []
    rem = float(speed)
    while rem > 2.0:
        factors.append(2.0)
        rem /= 2.0
    while rem < 0.5:
        factors.append(0.5)
        rem /= 0.5
    factors.append(rem)
    return ",".join(f"atempo={f:.6f}" for f in factors)


def _stretch_slice(slc: np.ndarray, speed: float, target_n: int) -> np.ndarray:
    """Pitch-preserved FFmpeg atempo stretch matching exact target_n stereo samples."""
    if abs(speed - 1.0) < 1e-4:
        out = slc.copy()
    else:
        with tempfile.TemporaryDirectory() as td:
            in_w = pathlib.Path(td) / "in.wav"
            out_w = pathlib.Path(td) / "out.wav"
            sf.write(str(in_w), slc.astype(np.float32), SR, subtype="PCM_24")
            subprocess.run(
                [
                    FFMPEG, "-y", "-v", "error",
                    "-i", str(in_w),
                    "-af", _atempo_chain(speed),
                    "-ac", "2", "-ar", str(SR),
                    str(out_w),
                ],
                check=True, capture_output=True, text=True,
            )
            out = load_stereo(out_w)

    if len(out) > target_n:
        out = out[:target_n].copy()
    elif len(out) < target_n:
        out = np.pad(out, ((0, target_n - len(out)), (0, 0)))
    return out


def extract_source_audio_window(out_wav: pathlib.Path) -> pathlib.Path:
    """Extract clean 48 kHz stereo PCM audio for source 45.00..75.00s."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            FFMPEG, "-y", "-v", "error",
            "-ss", "45.0", "-i", str(tm.SOURCE_CLIP_PATH),
            "-t", "30.2", "-vn", "-ac", "2", "-ar", str(SR),
            "-c:a", "pcm_s24le",
            str(out_wav),
        ],
        check=True, capture_output=True, text=True,
    )
    return out_wav


def build_remapped_source_audio(src_wav: pathlib.Path) -> np.ndarray:
    """Remap source game+comms audio strictly along timeline_map.TIME_SEGMENTS + censor."""
    raw_src = load_stereo(src_wav)
    total_n = int(round(tm.TOTAL_DURATION_S * SR))
    out = np.zeros((total_n, 2), dtype=np.float64)

    for seg in tm.TIME_SEGMENTS:
        o0 = int(round(seg["out0"] * SR))
        o1 = min(total_n, int(round(seg["out1"] * SR)))
        n_seg = max(0, o1 - o0)
        if n_seg == 0:
            continue

        if seg["is_freeze"]:
            # Brief 55ms natural decay tail from end of preceding audio into freeze silence
            tail_n = min(n_seg, int(0.055 * SR))
            if o0 >= tail_n and tail_n > 8:
                prev_tail = out[o0 - tail_n : o0].copy()
                decay = np.exp(-np.linspace(0.0, 6.0, tail_n))[:, None]
                out[o0 : o0 + tail_n] = prev_tail * decay * 0.45
            continue

        s0 = max(0, int(round((seg["src0"] - 45.0) * SR)))
        s1 = min(len(raw_src), int(round((seg["src1"] - 45.0) * SR)))
        slc = raw_src[s0:s1].copy()
        if len(slc) < 16:
            continue

        stretched = _stretch_slice(slc, float(seg["speed"]), n_seg)
        # Smooth 8ms edge crossfades to prevent clicks at segment boundaries
        fade_n = min(n_seg // 4, int(0.008 * SR))
        if fade_n > 1:
            stretched[:fade_n] *= np.linspace(0.0, 1.0, fade_n)[:, None]
            stretched[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)[:, None]

        # Slightly tuck ultra-fast 2.15x velocity section so whoosh + groove breathe cleanly
        if seg["speed"] >= 2.0:
            stretched *= 0.68

        out[o0:o1] += stretched

    # Surgical profanity duck (-46 dB) covering exact 50ms-verified CENSOR_SRC_SPAN (55.04..55.58s)
    c0_t = tm.map_src_to_out(tm.CENSOR_SRC_SPAN[0])
    c1_t = tm.map_src_to_out(tm.CENSOR_SRC_SPAN[1])
    ci0 = max(0, int(round(c0_t * SR)))
    ci1 = min(total_n, int(round(c1_t * SR)))
    if ci1 > ci0:
        fn = min((ci1 - ci0) // 4, int(0.012 * SR))
        duck = 10.0 ** (-46.0 / 20.0)
        env = np.full(ci1 - ci0, duck, dtype=np.float64)
        if fn > 1:
            env[:fn] = np.linspace(1.0, duck, fn)
            env[-fn:] = np.linspace(duck, 1.0, fn)
        out[ci0:ci1] *= env[:, None]

    # Voice + weapon conditioning: clear 100-350 Hz mud, lift vocal clarity & headshot air
    out = np.stack([_hp(out[:, c], 95.0) for c in (0, 1)], axis=1)
    out = _stereo_lfilter_or_sos(out, _biquad_peaking(210.0, 1.05, -4.5))
    out = _stereo_lfilter_or_sos(out, _biquad_peaking(2900.0, 0.85, +3.0))
    out = _stereo_lfilter_or_sos(out, _biquad_peaking(7200.0, 0.75, +2.4))

    # Normalize active RMS to -20.5 dBFS for commanding game+comms presence
    active = np.abs(out.mean(axis=1)) > 0.008
    rms = float(np.sqrt(np.mean(out[active] ** 2))) if np.any(active) else 0.05
    out *= (10.0 ** (-20.5 / 20.0)) / max(rms, 1e-6)
    return out


def generate_tactical_groove(dur_s: float, bpm: float = 124.0, seed: int = 42) -> np.ndarray:
    """Synthesize a crisp, dark Valorant-inspired 124 BPM tactical groove with zero mud."""
    n = int(round(dur_s * SR))
    beat_s = 60.0 / bpm
    step_s = beat_s * 0.25  # 16th note
    n_steps = int(math.ceil(dur_s / step_s)) + 2
    rng = np.random.default_rng(seed)

    kick_bus = np.zeros((n, 2), dtype=np.float64)
    bass_bus = np.zeros((n, 2), dtype=np.float64)
    perc_bus = np.zeros((n, 2), dtype=np.float64)
    stab_bus = np.zeros((n, 2), dtype=np.float64)

    # Syncopated dark trap-house kick & rim pattern (16 steps per bar)
    kick_pat = {0, 6, 10, 14}
    rim_pat = {4, 12}
    bass_notes = [46.25, 46.25, 55.00, 41.20]  # F#1, F#1, A1, E1 (sub-clean)

    for step in range(n_steps):
        t0 = step * step_s
        i0 = int(round(t0 * SR))
        if i0 >= n:
            break
        s16 = step % 16
        bar = (step // 16) % 4

        # 1. Punchy sub kick (< 95 Hz body + crisp 4.5 kHz beater click)
        if s16 in kick_pat:
            kd = int(0.14 * SR)
            tk = np.arange(kd) / SR
            f_env = 40.0 + 78.0 * np.exp(-tk * 38.0)
            phase = 2.0 * math.pi * np.cumsum(f_env) / SR
            body = np.sin(phase) * np.exp(-tk * 22.0) * (1.0 - np.exp(-tk * 450.0))
            click = rng.standard_normal(kd) * np.exp(-tk * 220.0) * 0.24
            click = _hp(click, 3400.0)
            hit = np.stack([body * 0.75 + click, body * 0.75 + click], axis=1)
            m = min(kd, n - i0)
            kick_bus[i0 : i0 + m] += hit[:m]

        # 2. Clean sub bass pulse on bar shifts & syncopation (LP < 98 Hz, zero mud)
        if s16 in (0, 3, 6, 10):
            bd = int(step_s * 2.2 * SR)
            tb = np.arange(bd) / SR
            f0 = bass_notes[bar]
            env = np.exp(-tb * 7.5) * np.minimum(1.0, tb / 0.008)
            sub_sig = (np.sin(2.0 * math.pi * f0 * tb) * 0.75 + np.sin(4.0 * math.pi * f0 * tb) * 0.22) * env
            sub_sig = _lp(sub_sig, 96.0)
            m = min(bd, n - i0)
            bass_bus[i0 : i0 + m, 0] += sub_sig[:m] * 0.45
            bass_bus[i0 : i0 + m, 1] += sub_sig[:m] * 0.45

        # 3. Crisp 16th-note metallic tactical hats (5k-14k Hz air detail)
        if s16 % 2 == 0 or s16 in (7, 15):
            hd = int((0.042 if s16 in (2, 10) else 0.024) * SR)
            th = np.arange(hd) / SR
            vel = 0.26 if s16 % 4 == 2 else (0.16 if s16 % 2 == 0 else 0.11)
            hat = rng.standard_normal(hd) * np.exp(-th * (58.0 if s16 in (2, 10) else 110.0))
            hat = _hp(hat, 5200.0) * vel
            pan = 0.22 if (step % 2 == 0) else -0.22
            m = min(hd, n - i0)
            perc_bus[i0 : i0 + m, 0] += hat[:m] * math.sqrt(0.5 * (1.0 - pan))
            perc_bus[i0 : i0 + m, 1] += hat[:m] * math.sqrt(0.5 * (1.0 + pan))

        # 4. Dry tactical rimshot on beats 2 & 4 (800-5500 Hz, crisp mid-air)
        if s16 in rim_pat:
            rd = int(0.065 * SR)
            tr = np.arange(rd) / SR
            rim = (
                np.sin(2.0 * math.pi * 1180.0 * tr) * np.exp(-tr * 65.0) * 0.45
                + _hp(rng.standard_normal(rd), 2400.0) * np.exp(-tr * 85.0) * 0.42
            )
            m = min(rd, n - i0)
            perc_bus[i0 : i0 + m, 0] += rim[:m] * 0.36
            perc_bus[i0 : i0 + m, 1] += rim[:m] * 0.38

        # 5. Dark F#m tactical synth pluck on bar downbeats (HPF 520 Hz -> zero mud!)
        if s16 == 0:
            sd = int(beat_s * 1.8 * SR)
            ts = np.arange(sd) / SR
            env = np.exp(-ts * 3.4) * np.minimum(1.0, ts / 0.012)
            # F#4 (370), A4 (440), C#5 (554.37), E5 (659.25)
            l_ch = (
                np.sin(2.0 * math.pi * 370.0 * ts) * 0.25
                + np.sin(2.0 * math.pi * 554.37 * ts) * 0.22
                + np.sin(2.0 * math.pi * 659.25 * ts) * 0.14
            ) * env
            r_ch = (
                np.sin(2.0 * math.pi * 371.4 * ts) * 0.25
                + np.sin(2.0 * math.pi * 440.0 * ts) * 0.22
                + np.sin(2.0 * math.pi * 661.2 * ts) * 0.14
            ) * env
            m = min(sd, n - i0)
            stab_bus[i0 : i0 + m, 0] += _hp(l_ch, 480.0)[:m] * 0.26
            stab_bus[i0 : i0 + m, 1] += _hp(r_ch, 480.0)[:m] * 0.26

    mix = kick_bus + bass_bus + perc_bus + stab_bus
    # Enforce zero mud pocket in 120-340 Hz so acoustic_audit stays super tight
    mix = _stereo_lfilter_or_sos(mix, _biquad_peaking(215.0, 0.9, -6.5))
    mix = _stereo_lfilter_or_sos(mix, _biquad_peaking(6800.0, 0.8, +2.6))

    # Build-up low-pass sweep during silent arch stalk (19.6s .. FREEZE_OUT_T0)
    sw0 = int(19.6 * SR)
    sw1 = min(n, int(tm.FREEZE_OUT_T0 * SR))
    if sw1 > sw0:
        lp_ver = np.stack([_lp(mix[sw0:sw1, c], 620.0) for c in (0, 1)], axis=1)
        u = np.linspace(0.0, 1.0, sw1 - sw0)[:, None] ** 1.3
        mix[sw0:sw1] = mix[sw0:sw1] * (1.0 - 0.82 * u) + lp_ver * (0.82 * u)

    return mix


def build_audio_mix() -> dict[str, Any]:
    tm.WORK_DIR.mkdir(parents=True, exist_ok=True)
    tm.QA_DIR.mkdir(parents=True, exist_ok=True)
    audio_out_dir = tm.WORK_DIR / "audio_mix"
    audio_out_dir.mkdir(parents=True, exist_ok=True)

    src_wav = extract_source_audio_window(tm.WORK_DIR / "source_audio_45_75.wav")
    remapped_voice = build_remapped_source_audio(src_wav)

    groove = generate_tactical_groove(tm.TOTAL_DURATION_S + 2.0, bpm=124.0)
    groove_wav = tm.WORK_DIR / "tactical_groove_124bpm.wav"
    sf.write(str(groove_wav), np.clip(groove, -0.95, 0.95).astype(np.float32), SR, subtype="PCM_24")

    sheet = json.loads(BEAT_SHEET_PATH.read_text(encoding="utf-8"))
    proj = SoundEngine5Stem(dur_s=tm.TOTAL_DURATION_S, profile="comedic-dry", t60=0.95)

    # Bus 1: Remapped original Valorant + Discord comms directly on voice bus (drives 9-band BGM carving!)
    n_v = min(len(remapped_voice), proj.n)
    proj.voice[:n_v] += remapped_voice[:n_v]

    # Bus 5: Tactical groove BGM with reversed lead-in, hard stop into freeze, slam back on unfreeze, Great Hall tail exit
    proj.add_music_bed(
        groove_wav,
        segments=[
            {
                "start_s": 0.0,
                "end_s": tm.FREEZE_OUT_T0,
                "src_offset_s": 0.0,
                "lead_in_reverse": True,
                "lead_in_dur_s": 0.55,
            },
            {
                "start_s": tm.FREEZE_OUT_T1,
                "end_s": 24.85,
                "src_offset_s": tm.FREEZE_OUT_T1,
                "lead_in_reverse": False,
                "hall_tail": True,
            },
        ],
        gain_db=-17.2,
        reverse_lead_in_s=0.55,
        hall_exit_at_s=24.85,
    )

    # Apply beat_sheet silence_pockets, room-tone bed, comedic foley, and 2 hero 3-band kill impacts
    proj.apply_beat_sheet_cues(sheet)

    plan = proj.render_mix(audio_out_dir, target_lufs=-16.0, target_peak_db=-4.8, export_stems=True)

    # Export real audio waveform bars (10 bars/s) for overlay_stage.html
    master_arr = load_stereo(plan["master_wav"])
    bars = extract_waveform_bars(master_arr, 0.0, tm.TOTAL_DURATION_S, bars=270)
    wf_payload = {
        "duration_s": tm.TOTAL_DURATION_S,
        "bars_count": len(bars),
        "bars": bars,
    }
    wf_path = tm.WORK_DIR / "audio_waveform.json"
    wf_path.write_text(json.dumps(wf_payload, indent=2), encoding="utf-8")

    # Also write a compact QA listening clip (censor window + freeze & climax) for direct human/agent audio inspection
    seg_a = master_arr[int(6.8 * SR) : int(12.2 * SR)]
    gap = np.zeros((int(0.45 * SR), 2), dtype=np.float64)
    seg_b = master_arr[int(20.8 * SR) : int(min(tm.TOTAL_DURATION_S, 26.95) * SR)]
    qa_listen = np.concatenate([seg_a, gap, seg_b], axis=0)
    qa_listen_wav = tm.QA_DIR / "qa_listen_censor_and_climax.wav"
    sf.write(str(qa_listen_wav), np.clip(qa_listen, -0.99, 0.99).astype(np.float32), SR, subtype="PCM_16")

    verdict = audit_media(
        plan["master_wav"],
        beat_sheet_path=BEAT_SHEET_PATH,
        out_png=tm.QA_DIR / "qa_audio_arc.png",
        profile="mograph_sfx",
        has_bgm=True,
    )
    print("AUDIO_BUILD_RESULT:", json.dumps({
        "ok": verdict["ok"],
        "lufs_i": verdict["metrics"]["loudness"]["lufs_i"],
        "peak_dbfs": verdict["metrics"]["loudness"]["peak_dbfs"],
        "lra": verdict["metrics"]["loudness"]["lra"],
        "mud_100_350": verdict["metrics"]["band_pct"]["mud_100_350"],
        "detail_air": verdict["metrics"]["detail_air_pct"],
        "dead_zero": verdict["metrics"]["dynamics"]["dead_digital_zero_pct"],
        "pockets": verdict["metrics"]["pocket_checks"],
        "failures": verdict["failures"],
        "warnings": verdict["warnings"],
    }, indent=2))
    if not verdict["ok"]:
        raise RuntimeError(f"Acoustic gate failed: {verdict['failures']}")
    return {"plan": plan, "verdict": verdict, "waveform_json": str(wf_path), "qa_listen_wav": str(qa_listen_wav)}


if __name__ == "__main__":
    build_audio_mix()
