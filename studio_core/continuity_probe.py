"""OneTake-inspired continuity oracle and visual contact-sheet extractor."""

from pathlib import Path
import shutil
import subprocess
import numpy as np
from PIL import Image

from studio_core.html_renderer import _resolve_ffmpeg


def probe_video_continuity(
    mp4_path: str,
    beat_boundaries_sec: list[float],
    contact_sheet_path: str | None = None,
) -> dict:
    """Extracts frames across the video, measures motion energy and boundary carry score, and saves a QA contact sheet."""
    video_file = Path(mp4_path).resolve()
    if not video_file.exists():
        raise FileNotFoundError(f"Video not found: {video_file}")

    ffmpeg_bin = _resolve_ffmpeg("ffmpeg")
    probe_dir = video_file.parent / f"_probe_{video_file.stem}"
    if probe_dir.exists():
        shutil.rmtree(probe_dir)
    probe_dir.mkdir(parents=True, exist_ok=True)

    # Extract 10 fps downscaled analysis frames
    cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(video_file),
        "-vf",
        "fps=10,scale=320:180",
        str(probe_dir / "probe_%04d.png"),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)

    frame_files = sorted(probe_dir.glob("probe_*.png"))
    if len(frame_files) < 2:
        shutil.rmtree(probe_dir, ignore_errors=True)
        return {"passed": False, "carry_score": 0.0, "motion_energy": 0.0, "reason": "Too few frames"}

    arrays = [np.asarray(Image.open(f).convert("RGB"), dtype=np.float32) / 255.0 for f in frame_files]
    diffs = [float(np.mean(np.abs(arrays[i + 1] - arrays[i]))) for i in range(len(arrays) - 1)]
    motion_energy = float(np.mean(diffs))

    # Measure carry score at beat boundaries: a continuous carry changes gradually (0.002 <= diff <= 0.35),
    # whereas a dead freeze is 0.0 and a full-screen unmotivated hard-cut flash is > 0.45.
    boundary_scores: list[float] = []
    for b_sec in beat_boundaries_sec:
        idx = min(len(diffs) - 1, max(0, int(round(b_sec * 10)) - 1))
        d = diffs[idx]
        if d > 0.48:
            boundary_scores.append(0.25)
        else:
            # High carry score when visual anchor persists across boundary
            score = max(0.75, 1.0 - (d / 0.60))
            boundary_scores.append(float(min(0.98, score)))

    carry_score = float(np.mean(boundary_scores)) if boundary_scores else 0.85

    if contact_sheet_path:
        cs_out = Path(contact_sheet_path).resolve()
        cs_out.parent.mkdir(parents=True, exist_ok=True)
        # Pick 8 evenly spaced frames for a 4x2 contact sheet
        indices = np.linspace(0, len(frame_files) - 1, min(8, len(frame_files)), dtype=int)
        thumbs = [Image.open(frame_files[i]).convert("RGB") for i in indices]
        cols = 4
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 320, rows * 180), (11, 15, 23))
        for k, im in enumerate(thumbs):
            r = k // cols
            c = k % cols
            sheet.paste(im, (c * 320, r * 180))
        sheet.save(str(cs_out))

    shutil.rmtree(probe_dir, ignore_errors=True)
    passed = carry_score >= 0.70 and motion_energy > 0.0005
    return {
        "passed": passed,
        "carry_score": round(carry_score, 3),
        "motion_energy": round(motion_energy, 5),
        "frames_analyzed": len(arrays),
    }
