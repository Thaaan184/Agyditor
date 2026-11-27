"""Render the 1080x1920 @ 60fps studio v2 showcase MP4 demonstrating 3D space,
keyframed DoF, Three.js r186 extrusion/cylinder + SpotLight, signature trim glow nib,
and GLSL v2 optical transition shaders with -16 LUFS CC0 SFX.
"""
from __future__ import annotations

import http.server
import io
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "studio_kit"
BIN = ROOT / "bin"
FFMPEG = str(BIN / "ffmpeg.exe")
FFPROBE = str(BIN / "ffprobe.exe")
RENDERS = KIT / "renders"

WIDTH = 1080
HEIGHT = 1920
FPS = 60
DURATION_S = 9.0
TOTAL_FRAMES = int(round(DURATION_S * FPS))

FAST_WINDOWS = (
    (2.16, 2.68),  # Motion Tile Mirror Whip
    (4.90, 5.28),  # Flash Cutout Strobe
    (6.90, 7.28),  # Optical Radial Match
)

_TO_LINEAR = np.array([(i / 255.0) ** 2.2 for i in range(256)], dtype=np.float32)


def is_fast_window(t: float) -> bool:
    for a, b in FAST_WINDOWS:
        if a <= t <= b:
            return True
    return False


def render_video_stream(out_video: Path) -> None:
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(KIT), **kwargs)

        def log_message(self, format, *args):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    ffmpeg_cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_video),
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    t0 = time.perf_counter()
    dt = 1.0 / FPS
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=True,
                args=["--use-gl=angle", "--use-angle=d3d11", "--enable-webgl", "--ignore-gpu-blocklist"],
            )
            page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
            errs: list[str] = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.goto(f"http://127.0.0.1:{port}/demo_showcase_v2.html", wait_until="networkidle")
            page.wait_for_function("() => window.__ready === true", timeout=20000)

            for idx in range(TOTAL_FRAMES):
                t_frame = idx * dt
                if is_fast_window(t_frame):
                    acc = None
                    for s in range(4):
                        t_sub = max(0.0, min(DURATION_S, t_frame + ((s + 0.5) / 4 - 0.5) * dt))
                        page.evaluate("(t) => window.__seek(t)", t_sub)
                        buf = page.screenshot(type="jpeg", quality=96)
                        arr = np.asarray(Image.open(io.BytesIO(buf)).convert("RGB"), dtype=np.uint8)
                        lin = _TO_LINEAR[arr]
                        acc = lin if acc is None else (acc + lin)
                    avg = np.clip(acc * 0.25, 0.0, 1.0)
                    proc.stdin.write((np.power(avg, 1.0 / 2.2) * 255.0 + 0.5).astype(np.uint8).tobytes())
                else:
                    page.evaluate("(t) => window.__seek(t)", t_frame)
                    buf = page.screenshot(type="jpeg", quality=96)
                    arr = np.asarray(Image.open(io.BytesIO(buf)).convert("RGB"), dtype=np.uint8)
                    proc.stdin.write(arr.tobytes())

            if errs:
                raise RuntimeError(f"Browser runtime errors: {errs}")
            browser.close()
    finally:
        if proc.stdin:
            proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        rc = proc.wait()
        httpd.shutdown()
        if rc != 0:
            raise RuntimeError(f"FFmpeg encode failed ({rc}):\n{stderr}")

    print(f"V2_VIDEO_RENDER_OK: {TOTAL_FRAMES} frames in {time.perf_counter() - t0:.2f}s -> {out_video}")


def mix_audio_and_mux(video_only: Path, final_mp4: Path) -> None:
    sfx = KIT / "sfx"
    raw_audio = RENDERS / "_v2_audio_mix.wav"
    norm_audio = RENDERS / "_v2_audio_norm.wav"

    filter_complex = ";".join([
        "anullsrc=channel_layout=stereo:sample_rate=48000:duration=9.0[silence]",
        "sine=frequency=55:sample_rate=48000:duration=0.45,aformat=channel_layouts=stereo,afade=t=in:st=0:d=0.02,afade=t=out:st=0.06:d=0.39,volume=0.22,adelay=4950|4950[sub_hit]",
        "[0:a]aresample=48000,aformat=channel_layouts=stereo,adelay=80|80,volume=0.55[s_open]",
        "[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=3[w1][w2][w3]",
        "[w1]adelay=2220|2220,volume=0.82[s_whip1]",
        "[w2]adelay=5220|5220,volume=0.60[s_nib]",
        "[w3]adelay=6960|6960,volume=0.84[s_radial]",
        "[2:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[p1][p2]",
        "[p1]adelay=2580|2580,volume=0.72[s_pop2]",
        "[p2]adelay=7280|7280,volume=0.76[s_dolly]",
        "[3:a]aresample=48000,aformat=channel_layouts=stereo,adelay=4940|4940,volume=0.90[s_imp]",
        "[4:a]aresample=48000,aformat=channel_layouts=stereo,asplit=3[t1][t2][t3]",
        "[t1]adelay=4960|4960,volume=0.45[s_tk1]",
        "[t2]adelay=5080|5080,volume=0.45[s_tk2]",
        "[t3]adelay=5190|5190,volume=0.45[s_tk3]",
        "[5:a]aresample=48000,aformat=channel_layouts=stereo,adelay=6550|6550,volume=0.52[s_riser]",
        "[silence][sub_hit][s_open][s_whip1][s_pop2][s_imp][s_tk1][s_tk2][s_tk3][s_nib][s_riser][s_radial][s_dolly]"
        "amix=inputs=13:duration=first:normalize=0,atrim=0:9.0[mixed]"
    ])

    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", str(sfx / "click.ogg"),
            "-i", str(sfx / "whoosh.ogg"),
            "-i", str(sfx / "pop.ogg"),
            "-i", str(sfx / "impact.ogg"),
            "-i", str(sfx / "tick.ogg"),
            "-i", str(sfx / "riser.ogg"),
            "-filter_complex", filter_complex,
            "-map", "[mixed]",
            "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
            str(raw_audio),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", str(raw_audio),
            "-af", "acompressor=threshold=-20dB:ratio=4:attack=1:release=90:makeup=7.0dB,loudnorm=I=-16.0:TP=-4.5:LRA=5,alimiter=limit=0.59:level=disabled:attack=1:release=40",
            "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
            str(norm_audio),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", str(video_only),
            "-i", str(norm_audio),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(final_mp4),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    for tmp in (raw_audio, norm_audio):
        if tmp.exists():
            tmp.unlink()


def extract_contact_sheet(final_mp4: Path, sheet_jpg: Path) -> None:
    frames = [18, 66, 138, 146, 158, 225, 298, 306, 360, 424, 465, 515]
    expr = "+".join(f"eq(n,{idx})" for idx in frames)
    subprocess.run(
        [
            FFMPEG, "-y", "-i", str(final_mp4),
            "-vf", f"select='{expr}',scale=360:640,tile=4x3:padding=8:margin=8:color=#0B0F17",
            "-frames:v", "1", "-q:v", "2",
            str(sheet_jpg),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    video_only = RENDERS / "_v2_video.mp4"
    final_mp4 = RENDERS / "showcase_v2_depth_optics.mp4"
    sheet_jpg = RENDERS / "showcase_v2_sheet.jpg"

    if "--audio-only" in sys.argv and final_mp4.exists():
        subprocess.run([FFMPEG, "-y", "-i", str(final_mp4), "-an", "-c:v", "copy", str(video_only)], check=True, capture_output=True)
    else:
        render_video_stream(video_only)

    mix_audio_and_mux(video_only, final_mp4)
    if video_only.exists():
        video_only.unlink()
    extract_contact_sheet(final_mp4, sheet_jpg)

    ebur = subprocess.run([FFMPEG, "-i", str(final_mp4), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, check=True)
    probe = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,r_frame_rate", "-of", "json", str(final_mp4)], capture_output=True, text=True, check=True)
    print("FFPROBE:", probe.stdout.strip())
    lines = [l.strip() for l in ebur.stderr.splitlines() if "Integrated loudness:" in l or l.strip().startswith("I:") or l.strip().startswith("Peak:")]
    for l in lines[-4:]:
        print("LOUDNESS:", l)
    print("CONTACT_SHEET:", sheet_jpg)


if __name__ == "__main__":
    main()
