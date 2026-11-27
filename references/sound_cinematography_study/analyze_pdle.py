"""Deep acoustic, narrative transcript, cut-cadence, and multi-stage visual breakdown
of pdLEHfkwgV8.mp4 for reverse-any-video & zero-waste storytelling analysis.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import librosa
import numpy as np
from faster_whisper import WhisperModel

ROOT = pathlib.Path(r"d:\Files\Project Iseng\AGY Video Editor")
STUDY = ROOT / "references" / "sound_cinematography_study"
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")
MP4 = STUDY / "pdLEHfkwgV8.mp4"

sys.path.insert(0, str(ROOT / "studio_kit"))
import acoustic_audit  # noqa: E402


def main() -> None:
    pr = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", str(MP4)],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(pr.stdout)
    dur = float(info["format"]["duration"])
    vstream = next(s for s in info["streams"] if s["codec_type"] == "video")

    # 1. Measure acoustic + visual cuts via acoustic_audit
    met = acoustic_audit.measure_audio_metrics(MP4, check_cuts=True)
    arc_png = acoustic_audit.render_audio_arc_png(met, STUDY / "audio_arc_pdLEHfkwgV8.png", title="pdLEHfkwgV8")

    # 2. Extract 48kHz wav for faster-whisper + onset alignment near cuts
    wav = STUDY / "_tmp_pdle.wav"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(MP4), "-vn", "-ac", "1", "-ar", "48000", str(wav)], check=True)
    y, sr = librosa.load(str(wav), sr=48000, mono=True)

    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs_it, _ = model.transcribe(str(wav), word_timestamps=True)
    segments = []
    words = []
    for seg in segs_it:
        segments.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
        for w in seg.words:
            words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})

    wav.unlink(missing_ok=True)

    # Pause gaps > 0.35s
    pauses = []
    for a, b in zip(words, words[1:]):
        gap = round(b["s"] - a["e"], 2)
        if gap >= 0.35:
            pauses.append({"at": a["e"], "gap_s": gap, "after": a["w"], "before": b["w"]})

    # Onsets near visual cuts
    cuts = met["_series"]["cuts"]
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=1200)
    onsets = librosa.frames_to_time(onset_frames, sr=sr, hop_length=1200)
    cut_onsets = []
    for c in cuts[:40]:
        if len(onsets):
            near = float(onsets[np.argmin(np.abs(onsets - c))])
            cut_onsets.append({"cut_s": c, "nearest_onset_s": round(near, 3), "offset_ms": round((near - c) * 1000.0, 1)})

    # 3. Extract 3 rich visual contact sheets across the full duration (Hook/Start, Middle, End)
    third = dur / 3.0
    for name, ss, span in (
        ("sheet_pdLEHfkwgV8_part1_hook.jpg", 0.0, min(third, dur)),
        ("sheet_pdLEHfkwgV8_part2_mid.jpg", third, min(third, dur - third)),
        ("sheet_pdLEHfkwgV8_part3_end.jpg", 2 * third, max(5.0, dur - 2 * third)),
    ):
        fps_samp = 24.0 / max(span, 1.0)
        subprocess.run(
            [
                FFMPEG, "-y", "-v", "error", "-ss", f"{ss:.2f}", "-t", f"{span:.2f}", "-i", str(MP4),
                "-vf", f"fps={fps_samp:.4f},scale=384:-1,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.75,tile=6x4",
                "-frames:v", "1", "-q:v", "2", str(STUDY / name),
            ],
            check=True,
        )

    clean_met = {k: v for k, v in met.items() if k != "_series"}
    report = {
        "video": "pdLEHfkwgV8",
        "res": f"{vstream['width']}x{vstream['height']}",
        "fps": vstream["r_frame_rate"],
        "dur_s": round(dur, 2),
        "acoustic": clean_met,
        "cuts": cuts,
        "cut_onsets_sample": cut_onsets,
        "pauses_gt_350ms": pauses,
        "segments": segments,
        "full_transcript": " ".join(s["text"] for s in segments),
        "arc_png": str(arc_png),
    }
    (STUDY / "pdLEHfkwgV8_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("PDLE_ANALYSIS_OK", json.dumps({
        "dur_s": report["dur_s"],
        "res": report["res"],
        "loudness": clean_met["loudness"],
        "band_pct": clean_met["band_pct"],
        "detail_air_pct": clean_met["detail_air_pct"],
        "dynamics": clean_met["dynamics"],
        "cuts_count": len(cuts),
        "shot_cv": clean_met["shot_cv"],
        "pauses_count": len(pauses),
    }, indent=2))


if __name__ == "__main__":
    main()
