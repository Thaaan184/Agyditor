"""V2 Final Compositor & QA Proof Generator -> D:\\Clip\\Edit\\Valorant\\valorant_harbor_3k_v2.mp4."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.valorant_edit import timeline_map as tm  # noqa: E402
from studio_kit.acoustic_audit import audit_media  # noqa: E402

FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")
BEAT_SHEET_PATH = ROOT / "projects" / "valorant_edit" / "beat_sheet.json"


def compose_final_v2() -> dict[str, object]:
    gameplay = tm.WORK_DIR / "layer_gameplay_v2.mp4"
    overlays = tm.WORK_DIR / "layer_overlays_v2.mov"
    audio = tm.WORK_DIR / "audio_mix" / "master_mix.wav"
    for req in (gameplay, overlays, audio):
        if not req.exists():
            raise FileNotFoundError(f"Required V2 intermediate missing: {req}")

    tm.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    tm.QA_V2_DIR.mkdir(parents=True, exist_ok=True)
    final_mp4 = tm.FINAL_V2_MP4_PATH

    subprocess.run(
        [
            FFMPEG, "-y", "-v", "error",
            "-i", str(gameplay),
            "-i", str(overlays),
            "-i", str(audio),
            "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1:format=auto[v]",
            "-map", "[v]", "-map", "2:a:0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-shortest", "-movflags", "+faststart",
            str(final_mp4),
        ],
        check=True, capture_output=True, text=True,
    )

    sample_times_s = [
        1.45,                       # 1. Zoomed-out Wide Hook + centered safe "Ini To!"
        3.82,                       # 2. Dynamic zoom + "WOOO!"
        tm.CENSOR_OUT_T0 + 0.16,    # 3. Snap-zoom + shaking "AN***G!"
        tm.KILL1_OUT_T + 0.08,      # 4. Kill #1 Sova Ult Radial Impact (zero fake card!)
        14.15,                      # 5. Wide FOV + "Kiri, kiri... Nice!"
        tm.KNIFE_WHIP_OUT_T,        # 6. Full-bleed MotionTile Knife Whip
        18.90,                      # 7. Wide Arch Stalk + "Aish!"
        tm.FREEZE_OUT_T0 + 0.42,    # 8. Freeze Phase A: Chamber Punch-In + italic serif
        tm.FREEZE_PHASE_B_T + 0.45, # 9. Freeze Phase B: 3.85x Deep Reyna Zoom + raw killfeed
        tm.KILL3_OUT_T + 0.14,      # 10. Kill #3 _S5mVxnVbcU Crimson Slash + Double Killfeed + 3K sky
        tm.KILL3_OUT_T + 0.55,      # 11. Post-slash settle + Double Killfeed
        25.45,                      # 12. Wide Outro + "Wuh! Eh, gila To!!" safe zone
    ]
    frame_indices = [max(0, min(tm.TOTAL_FRAMES - 1, int(round(t * tm.FPS)))) for t in sample_times_s]
    expr = "+".join(f"eq(n,{idx})" for idx in frame_indices)
    sheet_jpg = tm.QA_V2_DIR / "qa_v2_contact_sheet.jpg"
    subprocess.run(
        [
            FFMPEG, "-y", "-v", "error",
            "-i", str(final_mp4),
            "-vf", f"select='{expr}',scale=360:640,tile=4x3:padding=8:margin=8:color=#09090B",
            "-frames:v", "1", "-update", "1", "-q:v", "2",
            str(sheet_jpg),
        ],
        check=True, capture_output=True, text=True,
    )

    reyna_png = tm.QA_V2_DIR / "qa_v2_reyna_zoom.png"
    subprocess.run(
        [
            FFMPEG, "-y", "-v", "error",
            "-ss", f"{tm.FREEZE_PHASE_B_T + 0.45:.3f}",
            "-i", str(final_mp4),
            "-frames:v", "1", "-update", "1",
            str(reyna_png),
        ],
        check=True, capture_output=True, text=True,
    )

    slash_png = tm.QA_V2_DIR / "qa_v2_kill3_slash.png"
    subprocess.run(
        [
            FFMPEG, "-y", "-v", "error",
            "-ss", f"{tm.KILL3_OUT_T + 0.14:.3f}",
            "-i", str(final_mp4),
            "-frames:v", "1", "-update", "1",
            str(slash_png),
        ],
        check=True, capture_output=True, text=True,
    )

    arc_png = tm.QA_V2_DIR / "qa_v2_audio_arc.png"
    verdict = audit_media(
        final_mp4,
        beat_sheet_path=BEAT_SHEET_PATH,
        out_png=arc_png,
        profile="mograph_sfx",
        has_bgm=True,
    )
    probe = json.loads(
        subprocess.check_output(
            [
                FFPROBE, "-v", "error",
                "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
                "-of", "json", str(final_mp4),
            ],
            text=True,
        )
    )
    summary = {
        "final_v2_mp4": str(final_mp4),
        "qa_v2_contact_sheet": str(sheet_jpg),
        "qa_v2_reyna_zoom": str(reyna_png),
        "qa_v2_kill3_slash": str(slash_png),
        "qa_v2_audio_arc": str(arc_png),
        "probe": probe,
        "acoustic_ok": verdict["ok"],
        "acoustic_failures": verdict["failures"],
        "loudness": verdict["metrics"]["loudness"],
        "band_pct": verdict["metrics"]["band_pct"],
        "detail_air_pct": verdict["metrics"]["detail_air_pct"],
        "pockets": verdict["metrics"]["pocket_checks"],
    }
    print("FINAL_V2_RESULT:", json.dumps(summary, indent=2))
    if not verdict["ok"]:
        raise RuntimeError(f"V2 MP4 failed acoustic audit: {verdict['failures']}")
    return summary


if __name__ == "__main__":
    compose_final_v2()
