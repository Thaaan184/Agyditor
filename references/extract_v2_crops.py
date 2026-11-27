"""Dump full transcripts from study_v2_meta.json and extract key closeup frames."""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(r"d:\Files\Project Iseng\AGY Video Editor")
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
META = json.loads((ROOT / "references" / "study_v2_meta.json").read_text(encoding="utf-8"))

for vid, info in META.items():
    print(f"=== {vid} ({info['dur']}s {info['w']}x{info['h']} @{info['fps']}) ===")
    print(info["text"])
    print()

extracts = [
    (ROOT / "references/depth_optical_study/xCueXSWn-pk.mp4", 25.39, ROOT / "references/depth_optical_study/xCue_graph.jpg"),
    (ROOT / "references/depth_optical_study/xCueXSWn-pk.mp4", 50.78, ROOT / "references/depth_optical_study/xCue_cam.jpg"),
    (ROOT / "references/depth_optical_study/tP8QuxWBliA.mp4", 49.34, ROOT / "references/depth_optical_study/tP8_3d_light.jpg"),
    (ROOT / "references/transitions_study_v2/9c9PVAQXiLU.mp4", 0.90, ROOT / "references/transitions_study_v2/9c9_wipe1.jpg"),
    (ROOT / "references/transitions_study_v2/9c9PVAQXiLU.mp4", 6.10, ROOT / "references/transitions_study_v2/9c9_wipe2.jpg"),
]
for src, ts, dst in extracts:
    subprocess.run([FFMPEG, "-y", "-ss", str(ts), "-i", str(src), "-frames:v", "1", "-q:v", "2", str(dst)], check=True, capture_output=True)
print("EXTRACTS_OK")
