"""Extract ffprobe stats, faster-whisper transcripts, and 5x4 contact sheets for study v2."""
from __future__ import annotations

import json
import pathlib
import subprocess

from faster_whisper import WhisperModel

ROOT = pathlib.Path(r"d:\Files\Project Iseng\AGY Video Editor")
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")


def main() -> None:
    model = WhisperModel("small", device="cpu", compute_type="int8")
    targets = [
        ("depth_optical_study", ["tP8QuxWBliA", "xCueXSWn-pk", "gsS7uvyhYvI", "5kLbhiIc63w"]),
        ("transitions_study_v2", ["9c9PVAQXiLU", "AkvzW2O0UeA", "dHAx3HSVDLA", "uSFLQ5bfKps"]),
    ]
    summary = {}
    for folder, ids in targets:
        base = ROOT / "references" / folder
        for vid in ids:
            mp4 = base / f"{vid}.mp4"
            wav = base / f"{vid}.wav"
            sheet = base / f"sheet_{vid}.jpg"
            probe = json.loads(
                subprocess.check_output(
                    [
                        FFPROBE,
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration:stream=codec_type,width,height,r_frame_rate",
                        "-of",
                        "json",
                        str(mp4),
                    ],
                    text=True,
                )
            )
            vstream = next(s for s in probe["streams"] if s["codec_type"] == "video")
            dur = float(probe["format"]["duration"])
            subprocess.run(
                [FFMPEG, "-y", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                check=True,
                capture_output=True,
            )
            segs, info = model.transcribe(str(wav), beam_size=1, word_timestamps=True)
            words = []
            txt_parts = []
            for seg in segs:
                txt_parts.append(seg.text.strip())
                if seg.words:
                    for w in seg.words:
                        words.append({"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)})

            step = max(dur / 20.0, 0.05)
            vf = (
                f"fps=1/{step:.4f},scale=270:480,"
                "drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.75,"
                "tile=5x4:padding=4:margin=4:color=#0B0F17"
            )
            subprocess.run(
                [FFMPEG, "-y", "-i", str(mp4), "-vf", vf, "-frames:v", "1", "-q:v", "2", str(sheet)],
                check=True,
                capture_output=True,
            )
            full_text = " ".join(txt_parts).strip()
            summary[vid] = {
                "folder": folder,
                "w": vstream["width"],
                "h": vstream["height"],
                "fps": vstream["r_frame_rate"],
                "dur": round(dur, 2),
                "lang": info.language,
                "text": full_text,
                "words": words,
            }
            print(f"DONE {vid}: {dur:.2f}s {vstream['width']}x{vstream['height']} @{vstream['r_frame_rate']} lang={info.language} | {full_text[:120]}")

    (ROOT / "references" / "study_v2_meta.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
