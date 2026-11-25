"""Final Compositor & QA Proof Generator for Valorant Harbor 3K Vertical Edit.

Composites:
  - D:\\Clip\\Edit\\Valorant\\work\\layer_gameplay.mp4  (1080x1920 @ 60fps graded gameplay + FX + loupe + live killfeed)
  - D:\\Clip\\Edit\\Valorant\\work\\layer_overlays.mov  (1080x1920 @ 60fps RGBA self-hosted typography & SVG optics)
  - D:\\Clip\\Edit\\Valorant\\work\\audio_mix\\master_mix.wav (48 kHz stereo -16 LUFS 5-stem mix)
Into:
  - D:\\Clip\\Edit\\Valorant\\valorant_harbor_3k_vertical.mp4
And generates bounded QA evidence in D:\\Clip\\Edit\\Valorant\\qa\\:
  - qa_contact_sheet.jpg (12 critical moments across all 10 beats)
  - qa_loupe_closeup.png (full 1080x1920 frame at t=22.90s verifying Reyna 4.2x loupe, arrow, & killfeed)
  - qa_final_audio_arc.png (post-mux acoustic audit chart on final AAC MP4)
"""
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


def compose_final_mp4() -> dict[str, object]:
    gameplay = tm.WORK_DIR / "layer_gameplay.mp4"
    overlays = tm.WORK_DIR / "layer_overlays.mov"
    audio = tm.WORK_DIR / "audio_mix" / "master_mix.wav"
    for req in (gameplay, overlays, audio):
        if not req.exists():
            raise FileNotFoundError(f"Required intermediate missing: {req}")

    tm.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    tm.QA_DIR.mkdir(parents=True, exist_ok=True)
    final_mp4 = tm.FINAL_MP4_PATH

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

    # 12 key frames across Hook, WOOO, Bleep, Kill #1, Nice, Knife Whip, Stalk, Freeze A, Freeze B Loupe, Kill #3 Drop, 3K Counter, Gila Outro
    sample_times_s = [
        1.45,                     # 1. Hook + Opening Tag + "Ini To!"
        3.82,                     # 2. Mid Chaos + "WOOO!" snap-zoom
        tm.CENSOR_OUT_T0 + 0.16,  # 3. Comedic Bleep + shaking "an***g!"
        tm.KILL1_OUT_T + 0.08,    # 4. Kill #1 51m ADS HS through Sova Ult + Radial Impact
        14.15,                    # 5. "Kiri, kiri... Nice!"
        tm.KNIFE_WHIP_OUT_T,      # 6. Velocity Xenohunter Knife MotionTile Whip
        18.90,                    # 7. Arch Stalk + "Aish!"
        tm.FREEZE_OUT_T0 + 0.38,  # 8. Freeze Phase A: Chamber Target Bracket + deadpan serif
        tm.FREEZE_PHASE_B_T + 0.45,  # 9. Freeze Phase B: Reyna 4.2x Loupe + Leader + Live Row 2 Killfeed
        tm.KILL3_OUT_T + 0.04,    # 10. Kill #3 Chamber HS Flash Strobe + Double Killfeed
        tm.KILL3_OUT_T + 0.45,    # 11. 3K Rolling Slot Counter + 0.40S DOUBLE HS
        25.45,                    # 12. Outro "Wuh! Eh, gila To!!" Ghost Echo
    ]
    frame_indices = [max(0, min(tm.TOTAL_FRAMES - 1, int(round(t * tm.FPS)))) for t in sample_times_s]
    expr = "+".join(f"eq(n,{idx})" for idx in frame_indices)
    sheet_jpg = tm.QA_DIR / "qa_contact_sheet.jpg"
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

    # Full-resolution 1080x1920 close-up of the signature Reyna Loupe freeze frame (t = FREEZE_PHASE_B_T + 0.45s)
    loupe_png = tm.QA_DIR / "qa_loupe_closeup.png"
    loupe_t = tm.FREEZE_PHASE_B_T + 0.45
    subprocess.run(
        [
            FFMPEG, "-y", "-v", "error",
            "-ss", f"{loupe_t:.3f}",
            "-i", str(final_mp4),
            "-frames:v", "1", "-update", "1",
            str(loupe_png),
        ],
        check=True, capture_output=True, text=True,
    )

    # Post-mux acoustic audit on final AAC-encoded MP4
    arc_png = tm.QA_DIR / "qa_final_audio_arc.png"
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
        "final_mp4": str(final_mp4),
        "qa_contact_sheet": str(sheet_jpg),
        "qa_loupe_closeup": str(loupe_png),
        "qa_final_audio_arc": str(arc_png),
        "probe": probe,
        "acoustic_ok": verdict["ok"],
        "acoustic_failures": verdict["failures"],
        "loudness": verdict["metrics"]["loudness"],
        "band_pct": verdict["metrics"]["band_pct"],
        "detail_air_pct": verdict["metrics"]["detail_air_pct"],
        "pockets": verdict["metrics"]["pocket_checks"],
    }
    print("FINAL_COMPOSE_RESULT:", json.dumps(summary, indent=2))
    if not verdict["ok"]:
        raise RuntimeError(f"Final MP4 failed acoustic audit: {verdict['failures']}")
    return summary


if __name__ == "__main__":
    compose_final_mp4()
