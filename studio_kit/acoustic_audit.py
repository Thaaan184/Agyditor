"""Profile-Aware Post-Render Acoustic, Spectral Balance, & Contrast Auditor.

Differentiates warm voice-led storytelling mixes (e.g. pdLEHfkwgV8 warm chest voice + acoustic bed)
from dense electronic SFX motion-graphics mixes (e.g. unbroken / MlaidhI2034) so genuine intimate
narration is never falsely penalized as mud while hollow/boxy slop fails immediately.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import Any

import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")


PROFILE_THRESHOLDS: dict[str, dict[str, float]] = {
    "mograph_sfx": {
        "lufs_min": -18.5,
        "lufs_max": -13.0,
        "peak_max_dbfs": -3.5,
        "lra_min_lu": 2.4,
        "mud_max_pct": 35.0,
        "voice_min_pct": 5.0,
        "detail_air_min_pct": 4.0,
        "quiet15_min_pct": 5.0,
        "dead_zero_max_pct": 35.0,
    },
    "narrative_voice_film": {
        "lufs_min": -18.5,
        "lufs_max": -13.0,
        "peak_max_dbfs": -3.5,
        "lra_min_lu": 2.2,
        "mud_max_pct": 48.0,
        "voice_min_pct": 18.0,
        "detail_air_min_pct": 2.5,
        "quiet15_min_pct": 4.5,
        "dead_zero_max_pct": 28.0,
    },
    "cinematic_essay": {
        "lufs_min": -24.0,
        "lufs_max": -16.5,
        "peak_max_dbfs": -3.0,
        "lra_min_lu": 4.5,
        "mud_max_pct": 55.0,
        "voice_min_pct": 12.0,
        "detail_air_min_pct": 2.0,
        "quiet15_min_pct": 6.0,
        "dead_zero_max_pct": 35.0,
    },
    "podcast_collage_short": {
        "lufs_min": -14.5,
        "lufs_max": -8.0,
        "peak_max_dbfs": -1.0,
        "lra_min_lu": 2.0,
        "mud_max_pct": 42.0,
        "voice_min_pct": 20.0,
        "detail_air_min_pct": 3.5,
        "quiet15_min_pct": 3.0,
        "dead_zero_max_pct": 25.0,
    },
}


def measure_audio_metrics(
    media_path: str | pathlib.Path,
    *,
    beat_sheet: dict[str, Any] | None = None,
    check_cuts: bool = False,
) -> dict[str, Any]:
    path = pathlib.Path(media_path)
    if not path.exists():
        raise FileNotFoundError(f"Media not found: {path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = pathlib.Path(tmpdir) / "audit.wav"
        dec = subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "48000", str(wav_path)],
            capture_output=True, text=True, check=False,
        )
        if dec.returncode != 0 or not wav_path.exists():
            raise RuntimeError(f"Audio decode failed for {path}: {dec.stderr}")

        ebur = subprocess.run(
            [FFMPEG, "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
            capture_output=True, text=True, check=False,
        ).stderr

        def _extract_last(pattern: str) -> float | None:
            matches = re.findall(pattern, ebur)
            return float(matches[-1]) if matches else None

        lufs_i = _extract_last(r"I:\s+([-\d.]+)\s+LUFS")
        lra = _extract_last(r"LRA:\s+([-\d.]+)\s+LU")
        peak_dbfs = _extract_last(r"Peak:\s+([-\d.]+)\s+dBFS")

        y, sr = librosa.load(str(wav_path), sr=48000, mono=True)

    dur = float(len(y) / sr)
    freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
    mag2 = np.abs(np.fft.rfft(y)) ** 2
    total = float(mag2.sum()) + 1e-12
    band_pct = {
        k: round(100.0 * float(mag2[(freqs >= lo) & (freqs < hi)].sum()) / total, 2)
        for k, (lo, hi) in (
            ("sub_20_90", (20, 90)),
            ("mud_100_350", (100, 350)),
            ("voice_350_2500", (350, 2500)),
            ("detail_2500_8000", (2500, 8000)),
            ("air_8000_18000", (8000, 18000)),
        )
    }
    detail_air_pct = round(band_pct["detail_2500_8000"] + band_pct["air_8000_18000"], 2)

    hop = int(sr * 0.025)
    rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    db = 20.0 * np.log10(np.maximum(rms, 1e-6))

    interior = (times >= 0.18) & (times <= max(0.25, dur - 0.18))
    db_int = db[interior] if np.any(interior) else db
    times_int = times[interior] if np.any(interior) else times

    active_mask = db_int > -55.0
    active_med = float(np.median(db_int[active_mask])) if np.any(active_mask) else -35.0
    quiet_15db_pct = round(100.0 * float(np.mean(db_int < (active_med - 15.0))), 1)
    silence_48db_pct = round(100.0 * float(np.mean(db_int < -48.0)), 1)

    in_pocket = np.zeros_like(times_int, dtype=bool)
    pockets = (beat_sheet or {}).get("silence_pockets", [])
    pocket_results = []
    for p in pockets:
        t0, t1 = float(p["t0"]), float(p["t1"])
        mask = (times_int >= t0) & (times_int <= t1)
        in_pocket |= mask
        before_mask = (times >= max(0.0, t0 - 1.2)) & (times < max(0.05, t0 - 0.04))
        if np.any(mask) and np.any(before_mask):
            pocket_min = float(np.min(db_int[mask]))
            before_med = float(np.median(db[before_mask]))
            drop = round(before_med - pocket_min, 2)
            pocket_results.append({"t0": t0, "t1": t1, "drop_db": drop, "min_db": round(pocket_min, 2)})

    non_pocket_db = db_int[~in_pocket] if np.any(~in_pocket) else db_int
    dead_zero_pct = round(100.0 * float(np.mean(non_pocket_db < -68.0)), 1)

    cuts: list[float] = []
    shot_cv: float | None = None
    if check_cuts:
        sc = subprocess.run(
            [FFMPEG, "-i", str(path), "-vf", "select='gt(scene,0.28)',showinfo", "-f", "null", "-"],
            capture_output=True, text=True, check=False,
        ).stderr
        for line in sc.splitlines():
            m = re.search(r"pts_time:([\d.]+)", line)
            if m:
                cuts.append(round(float(m.group(1)), 3))
        if len(cuts) >= 2:
            lens = np.diff([0.0] + cuts + [dur])
            shot_cv = round(float(np.std(lens) / max(np.mean(lens), 1e-6)), 3)

    return {
        "file": str(path),
        "duration_s": round(dur, 3),
        "loudness": {"lufs_i": lufs_i, "lra": lra, "peak_dbfs": peak_dbfs},
        "band_pct": band_pct,
        "detail_air_pct": detail_air_pct,
        "dynamics": {
            "active_med_db": round(active_med, 2),
            "quiet_15db_pct": quiet_15db_pct,
            "silence_48db_pct": silence_48db_pct,
            "dead_digital_zero_pct": dead_zero_pct,
            "p10_db": round(float(np.percentile(db_int, 10)), 2),
            "p90_db": round(float(np.percentile(db_int, 90)), 2),
        },
        "pocket_checks": pocket_results,
        "cuts_count": len(cuts) if check_cuts else None,
        "shot_cv": shot_cv,
        "_series": {"times": times, "db": db, "y": y, "sr": sr, "cuts": cuts},
    }


def evaluate_acoustic_gate(
    metrics: dict[str, Any],
    *,
    profile: str = "narrative_voice_film",
    thresholds: dict[str, float] | None = None,
    has_bgm: bool = True,
) -> dict[str, Any]:
    base = PROFILE_THRESHOLDS.get(profile, PROFILE_THRESHOLDS["narrative_voice_film"])
    t = {**base, **(thresholds or {})}
    failures: list[str] = []
    warnings: list[str] = []

    ld = metrics["loudness"]
    bands = metrics["band_pct"]
    dyn = metrics["dynamics"]

    if ld["lufs_i"] is None or not (t["lufs_min"] <= ld["lufs_i"] <= t["lufs_max"]):
        failures.append(f"LUFS {ld['lufs_i']} out of target window [{t['lufs_min']}, {t['lufs_max']}].")
    if ld["peak_dbfs"] is None or ld["peak_dbfs"] > t["peak_max_dbfs"]:
        failures.append(f"True peak {ld['peak_dbfs']} dBFS exceeds headroom ceiling {t['peak_max_dbfs']} dBFS.")
    if ld["lra"] is not None and ld["lra"] < t["lra_min_lu"]:
        failures.append(f"LRA {ld['lra']} LU too flat/over-compressed (< {t['lra_min_lu']} LU).")
    if bands["mud_100_350"] > t["mud_max_pct"]:
        failures.append(f"Low-mid mud {bands['mud_100_350']}% exceeds max {t['mud_max_pct']}% for profile '{profile}'.")
    if bands["voice_350_2500"] < t["voice_min_pct"]:
        failures.append(f"Mid/voice body {bands['voice_350_2500']}% below {t['voice_min_pct']}% for profile '{profile}'.")
    if metrics["detail_air_pct"] < t["detail_air_min_pct"]:
        failures.append(
            f"Clarity & air (2.5-18 kHz) is {metrics['detail_air_pct']}% (< {t['detail_air_min_pct']}%; muffled/lacks foley texture)."
        )
    if dyn["quiet_15db_pct"] < t["quiet15_min_pct"]:
        warnings.append(
            f"Quiet contrast (< active -15 dB) is only {dyn['quiet_15db_pct']}% (< {t['quiet15_min_pct']}%); add deliberate breath/silence pockets."
        )
    if has_bgm and dyn["dead_digital_zero_pct"] > t["dead_zero_max_pct"]:
        failures.append(
            f"Dead digital vacuum {dyn['dead_digital_zero_pct']}% (> {t['dead_zero_max_pct']}%); room-tone / bed dropped out."
        )

    for pk in metrics.get("pocket_checks", []):
        if pk["drop_db"] < 8.0:
            failures.append(
                f"Silence pocket [{pk['t0']}, {pk['t1']}] only dropped {pk['drop_db']} dB (< 8.0 dB contrast required)."
            )

    clean = {k: v for k, v in metrics.items() if k != "_series"}
    return {"ok": len(failures) == 0, "profile": profile, "failures": failures, "warnings": warnings, "metrics": clean}


def render_audio_arc_png(
    metrics: dict[str, Any],
    out_png: str | pathlib.Path,
    *,
    beat_sheet: dict[str, Any] | None = None,
    title: str | None = None,
) -> pathlib.Path:
    s = metrics["_series"]
    y, sr, times, db = s["y"], s["sr"], s["times"], s["db"]
    hop = int(sr * 0.025)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

    def _band_db(lo: int, hi: int) -> np.ndarray:
        idx = (freqs >= lo) & (freqs < hi)
        val = np.sqrt(np.mean(S[idx] ** 2, axis=0)) if np.any(idx) else np.zeros(S.shape[1])
        return 20.0 * np.log10(np.maximum(val, 1e-6))

    sub_b = _band_db(20, 120)
    mid_b = _band_db(350, 3000)
    air_b = _band_db(3000, 16000)
    t_stft = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)

    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 6.4), sharex=True)
    fig.patch.set_facecolor("#0B0F17")
    for ax in (ax1, ax2):
        ax.set_facecolor("#111827")

    dyn = metrics["dynamics"]
    ld = metrics["loudness"]
    head = title or pathlib.Path(metrics["file"]).name
    ax1.plot(times, db, color="#38BDF8", lw=1.4, label="RMS dBFS")
    ax1.axhline(dyn["active_med_db"], color="#94A3B8", ls="--", lw=0.9, label=f"Active med {dyn['active_med_db']} dB")
    ax1.axhline(dyn["active_med_db"] - 15.0, color="#FACC15", ls=":", lw=0.9, label="Contrast (-15 dB)")
    for p in (beat_sheet or {}).get("silence_pockets", []):
        ax1.axvspan(float(p["t0"]), float(p["t1"]), color="#EF4444", alpha=0.22, label="Silence pocket")
    for c in s.get("cuts", []):
        ax1.axvline(c, color="#F87171", lw=0.7, alpha=0.55)
    ax1.set_ylim(-68, 0)
    ax1.set_ylabel("dBFS")
    ax1.set_title(
        f"{head} | {ld['lufs_i']} LUFS, LRA {ld['lra']} LU, Peak {ld['peak_dbfs']} dBFS | Mud {metrics['band_pct']['mud_100_350']}% | Air+Detail {metrics['detail_air_pct']}%",
        fontsize=10.5,
    )
    handles, labels = ax1.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax1.legend(by_label.values(), by_label.keys(), loc="lower right", fontsize=8)

    ax2.plot(t_stft, sub_b, color="#FB923C", lw=1.1, label="Sub 20-120 Hz")
    ax2.plot(t_stft, mid_b, color="#4ADE80", lw=1.1, label="Voice/Body 350-3k Hz")
    ax2.plot(t_stft, air_b, color="#C084FC", lw=1.1, label="Foley/Air 3k-16k Hz")
    for p in (beat_sheet or {}).get("silence_pockets", []):
        ax2.axvspan(float(p["t0"]), float(p["t1"]), color="#EF4444", alpha=0.14)
    ax2.set_ylabel("Band dB")
    ax2.set_xlabel("Time (s)")
    ax2.legend(loc="lower right", fontsize=8)

    plt.tight_layout()
    out_p = pathlib.Path(out_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_p, dpi=115)
    plt.close()
    return out_p


def audit_media(
    media_path: str | pathlib.Path,
    *,
    beat_sheet_path: str | pathlib.Path | None = None,
    out_png: str | pathlib.Path | None = None,
    profile: str | None = None,
    has_bgm: bool = True,
    check_cuts: bool = False,
) -> dict[str, Any]:
    sheet = json.loads(pathlib.Path(beat_sheet_path).read_text(encoding="utf-8")) if beat_sheet_path else None
    eff_profile = profile or (sheet or {}).get("audio_audit_profile", "narrative_voice_film")
    metrics = measure_audio_metrics(media_path, beat_sheet=sheet, check_cuts=check_cuts)
    verdict = evaluate_acoustic_gate(metrics, profile=eff_profile, has_bgm=has_bgm)
    if out_png:
        png = render_audio_arc_png(metrics, out_png, beat_sheet=sheet)
        verdict["arc_png"] = str(png)
    return verdict


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Profile-aware post-render acoustic, spectral, and contrast auditor.")
    ap.add_argument("media")
    ap.add_argument("--beat-sheet", default=None)
    ap.add_argument("--profile", default=None, choices=sorted(PROFILE_THRESHOLDS.keys()))
    ap.add_argument("--out-png", default=None)
    ap.add_argument("--no-bgm", action="store_true")
    ap.add_argument("--check-cuts", action="store_true")
    ap.add_argument("--advisory", action="store_true")
    args = ap.parse_args()

    res = audit_media(
        args.media,
        beat_sheet_path=args.beat_sheet,
        out_png=args.out_png,
        profile=args.profile,
        has_bgm=not args.no_bgm,
        check_cuts=args.check_cuts,
    )
    print(json.dumps(res, indent=2))
    if not args.advisory and not res["ok"]:
        sys.exit(1)
