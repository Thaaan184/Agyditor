"""Analyze audio dynamics, frequency carving, negative space, shot cuts, transcripts,
and extract visual + spectral contact sheets for the 6 sound & cinematography references.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess

import librosa
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from faster_whisper import WhisperModel

ROOT = pathlib.Path(r"d:\Files\Project Iseng\AGY Video Editor")
STUDY = ROOT / "references" / "sound_cinematography_study"
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")

VIDEOS = [
    ("PLZRzKMxsqE", "short"),
    ("YKGhX9Dxycg", "short"),
    ("MlaidhI2034", "short"),
    ("6V8zYYzxPCA", "short"),
    ("UYq0o9Klf8I", "short"),
    ("tzfzkTAQsnE", "long"),
]


def band_energy_shares(y: np.ndarray, sr: int) -> dict[str, float]:
    n_fft = min(len(y), 65536)
    freqs = np.fft.rfftfreq(len(y), 1.0 / sr)
    mag2 = np.abs(np.fft.rfft(y)) ** 2
    total = float(mag2.sum()) + 1e-12
    bands = {
        "sub_20_90": (20, 90),
        "mud_100_350": (100, 350),
        "voice_350_2500": (350, 2500),
        "detail_2500_8000": (2500, 8000),
        "air_8000_18000": (8000, 18000),
    }
    return {
        k: round(100.0 * float(mag2[(freqs >= lo) & (freqs < hi)].sum()) / total, 2)
        for k, (lo, hi) in bands.items()
    }


def detect_cuts(mp4: pathlib.Path) -> list[float]:
    cmd = [
        FFMPEG, "-i", str(mp4),
        "-vf", "select='gt(scene,0.28)',showinfo",
        "-f", "null", "-",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    pts = []
    for line in res.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            pts.append(round(float(m.group(1)), 3))
    return pts


def get_loudness_stats(mp4: pathlib.Path) -> dict[str, float]:
    res = subprocess.run(
        [FFMPEG, "-nostats", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    txt = res.stderr
    def _find(pat: str) -> float | None:
        ms = re.findall(pat, txt)
        return float(ms[-1]) if ms else None

    return {
        "lufs_i": _find(r"I:\s+([-\d.]+)\s+LUFS"),
        "lra": _find(r"LRA:\s+([-\d.]+)\s+LU"),
        "peak_dbfs": _find(r"Peak:\s+([-\d.]+)\s+dBFS"),
    }


def plot_audio_story(vid: str, y: np.ndarray, sr: int, cuts: list[float], word_spans: list[tuple[float, float]], out_png: pathlib.Path) -> dict[str, float]:
    hop = int(sr * 0.025)
    rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    db = 20.0 * np.log10(np.maximum(rms, 1e-6))

    active_med = float(np.median(db[db > -55])) if np.any(db > -55) else -30.0
    quiet_18db_pct = round(100.0 * float(np.mean(db < (active_med - 15.0))), 1)
    silence_pct = round(100.0 * float(np.mean(db < -48.0)), 1)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onsets = librosa.frames_to_time(librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop), sr=sr, hop_length=hop)

    # Low vs High instantaneous ratio
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    sub_e = (S[(freqs >= 25) & (freqs < 120)] ** 2).sum(axis=0) + 1e-9
    mid_e = (S[(freqs >= 350) & (freqs < 3000)] ** 2).sum(axis=0) + 1e-9
    air_e = (S[(freqs >= 3000) & (freqs < 14000)] ** 2).sum(axis=0) + 1e-9

    fig, axes = plt.subplots(2, 1, figsize=(13, 6.2), sharex=True, gridspec_kw={"height_ratios": [1.1, 1.3]})
    fig.patch.set_facecolor("#0B0F17")
    for ax in axes:
        ax.set_facecolor("#101726")
        ax.tick_params(colors="#CBD5E1", labelsize=8)
        for sp in ax.spines.values():
            sp.set_color("#1E293B")

    # Top: Loudness arc + cuts + dialogue bands
    axes[0].plot(times, db, color="#38BDF8", linewidth=1.2, label="RMS dBFS")
    axes[0].axhline(active_med, color="#94A3B8", linestyle="--", linewidth=0.8, alpha=0.6)
    axes[0].axhline(active_med - 15.0, color="#FACC15", linestyle=":", linewidth=0.9, alpha=0.7, label="Quiet contrast (-15dB)")
    for s, e in word_spans:
        axes[0].axvspan(s, e, color="#22C55E", alpha=0.14)
    for c in cuts:
        axes[0].axvline(c, color="#EF4444", linewidth=0.9, alpha=0.75)
    axes[0].set_ylim(-65, 2)
    axes[0].set_ylabel("dBFS", color="#F8FAFC", fontsize=9)
    axes[0].set_title(f"{vid} Acoustic Arc (Green=Voice, Red=Visual Cut) | Quiet<-15dB: {quiet_18db_pct}% | Silence<-48dB: {silence_pct}%", color="#F8FAFC", fontsize=10)
    axes[0].legend(loc="lower right", fontsize=7, facecolor="#0B0F17", labelcolor="#F8FAFC")

    # Bottom: Sub vs Voice vs Detail bands over time
    t_spec = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)
    axes[1].plot(t_spec, 10 * np.log10(sub_e), color="#F97316", linewidth=1.1, label="Sub 25-120Hz")
    axes[1].plot(t_spec, 10 * np.log10(mid_e), color="#22C55E", linewidth=1.1, alpha=0.85, label="Voice/Body 350-3kHz")
    axes[1].plot(t_spec, 10 * np.log10(air_e), color="#A855F7", linewidth=1.0, alpha=0.85, label="Foley/Air 3k-14kHz")
    for c in cuts:
        axes[1].axvline(c, color="#EF4444", linewidth=0.7, alpha=0.55)
    axes[1].set_ylabel("Band dB", color="#F8FAFC", fontsize=9)
    axes[1].set_xlabel("Time (s)", color="#F8FAFC", fontsize=9)
    axes[1].legend(loc="lower right", fontsize=7, facecolor="#0B0F17", labelcolor="#F8FAFC")

    plt.tight_layout()
    fig.savefig(out_png, dpi=130)
    plt.close(fig)

    # Check onset-to-cut timing alignment
    pre_lap_ms = []
    for c in cuts:
        if len(onsets) == 0:
            continue
        diffs = (onsets - c) * 1000.0
        nearest = diffs[np.argmin(np.abs(diffs))]
        if abs(nearest) <= 350:
            pre_lap_ms.append(round(float(nearest), 1))

    return {
        "active_med_db": round(active_med, 1),
        "quiet_15db_pct": quiet_18db_pct,
        "silence_48db_pct": silence_pct,
        "onset_count": int(len(onsets)),
        "near_cut_onset_offsets_ms": pre_lap_ms[:16],
    }


def main() -> None:
    model = WhisperModel("small", device="cpu", compute_type="int8")
    report = {}

    for vid, kind in VIDEOS:
        mp4 = STUDY / f"{vid}.mp4"
        wav = STUDY / f"{vid}.wav"
        probe = json.loads(
            subprocess.check_output(
                [FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(mp4)],
                text=True,
            )
        )
        vstream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        dur = float(probe["format"]["duration"])

        subprocess.run([FFMPEG, "-y", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "44100", str(wav)], check=True, capture_output=True)
        y, sr = librosa.load(str(wav), sr=44100, mono=True)

        segs, info = model.transcribe(str(wav), beam_size=1, word_timestamps=True)
        words = []
        txt_parts = []
        for s in segs:
            txt_parts.append(s.text.strip())
            if s.words:
                for w in s.words:
                    words.append({"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)})

        # Speech gap analysis (gaps >= 0.4s between words)
        gaps = []
        for i in range(1, len(words)):
            g = words[i]["s"] - words[i - 1]["e"]
            if g >= 0.35:
                gaps.append(round(g, 2))

        cuts = detect_cuts(mp4)
        shot_durs = []
        pts_all = [0.0] + cuts + [dur]
        for i in range(1, len(pts_all)):
            d = pts_all[i] - pts_all[i - 1]
            if d > 0.08:
                shot_durs.append(round(d, 2))
        cv_shots = round(float(np.std(shot_durs) / max(1e-5, np.mean(shot_durs))), 2) if len(shot_durs) > 1 else 0.0

        loud = get_loudness_stats(mp4)
        bands = band_energy_shares(y, sr)
        dyn = plot_audio_story(vid, y, sr, cuts, [(w["s"], w["e"]) for w in words], STUDY / f"audio_arc_{vid}.png")

        # Extract visual contact sheets
        if kind == "short":
            step = max(dur / 20.0, 0.05)
            vf = (
                f"fps=1/{step:.4f},scale=270:480,"
                "drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.75,"
                "tile=5x4:padding=4:margin=4:color=#0B0F17"
            )
            subprocess.run([FFMPEG, "-y", "-i", str(mp4), "-vf", vf, "-frames:v", "1", "-q:v", "2", str(STUDY / f"sheet_{vid}.jpg")], check=True, capture_output=True)
        else:
            # Longform cinematography & B-roll sheet: 24 frames across full duration + 16 frames across opening 28s hook!
            step = max(dur / 24.0, 0.2)
            vf_full = (
                f"fps=1/{step:.4f},scale=384:216,"
                "drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=15:fontcolor=yellow:box=1:boxcolor=black@0.75,"
                "tile=4x6:padding=4:margin=4:color=#0B0F17"
            )
            subprocess.run([FFMPEG, "-y", "-i", str(mp4), "-vf", vf_full, "-frames:v", "1", "-q:v", "2", str(STUDY / f"sheet_{vid}_full.jpg")], check=True, capture_output=True)

            vf_hook = (
                "fps=16/28,scale=384:216,"
                "drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=15:fontcolor=yellow:box=1:boxcolor=black@0.75,"
                "tile=4x4:padding=4:margin=4:color=#0B0F17"
            )
            subprocess.run([FFMPEG, "-y", "-t", "28", "-i", str(mp4), "-vf", vf_hook, "-frames:v", "1", "-q:v", "2", str(STUDY / f"sheet_{vid}_hook.jpg")], check=True, capture_output=True)

        full_text = " ".join(txt_parts).strip()
        report[vid] = {
            "kind": kind,
            "res": f"{vstream['width']}x{vstream['height']}",
            "fps": vstream["r_frame_rate"],
            "dur": round(dur, 2),
            "lang": info.language,
            "loudness": loud,
            "band_pct": bands,
            "dynamics": dyn,
            "cuts_count": len(cuts),
            "shot_avg_s": round(float(np.mean(shot_durs)), 2) if shot_durs else round(dur, 2),
            "shot_cv": cv_shots,
            "speech_gaps_gt_035s": gaps[:20],
            "transcript": full_text,
        }
        print(
            f"ANALYZED {vid}: dur={dur:.1f}s I={loud['lufs_i']} LRA={loud['lra']} PK={loud['peak_dbfs']} "
            f"quiet15={dyn['quiet_15db_pct']}% mud={bands['mud_100_350']}% cuts={len(cuts)} cv={cv_shots} | {full_text[:95]}"
        )

    (STUDY / "sound_study_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SOUND_STUDY_ALL_OK")


if __name__ == "__main__":
    main()
