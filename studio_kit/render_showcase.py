"""Render the 1080x1920 @ 60fps studio showcase MP4 with GPU Chrome,
linear-light sub-frame shutter blur, CC0 SFX mixing, and EBU R128 loudness check.
"""
from __future__ import annotations

import functools
import http.server
import io
import os
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
DURATION_S = 8.5
TOTAL_FRAMES = int(round(DURATION_S * FPS))

# Linear-light shutter integration windows around rapid transitions and kinetic rolls
FAST_MOTION_WINDOWS = (
    (2.20, 2.70),  # Smooth Mask Reveal + Occlusion Wipe
    (4.52, 4.86),  # Angled Split + Counter-Zoom
    (4.74, 5.56),  # Rolling Cylinder peak blur & col stagger
    (6.50, 6.80),  # Cutout Frame Hold Slide-In
    (7.28, 7.82),  # Ghost Echo 20% kinetic swap
)

_TO_LINEAR = np.array([(i / 255.0) ** 2.2 for i in range(256)], dtype=np.float32)


def is_fast_window(t: float) -> bool:
    for start, end in FAST_MOTION_WINDOWS:
        if start <= t <= end:
            return True
    return False


def render_video_stream(out_video: Path) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(KIT))

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(KIT), **kwargs)

        def log_message(self, format, *args):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    port = httpd.server_address[1]
    srv_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    srv_thread.start()

    ffmpeg_cmd = [
        FFMPEG,
        "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out_video),
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    t0_wall = time.perf_counter()
    dt = 1.0 / FPS

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                channel="chrome",
                headless=True,
                args=[
                    "--use-gl=angle",
                    "--use-angle=d3d11",
                    "--enable-webgl",
                    "--ignore-gpu-blocklist",
                ],
            )
            page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(f"http://127.0.0.1:{port}/demo_showcase.html", wait_until="networkidle")
            page.wait_for_function("() => window.__ready === true", timeout=15000)

            fonts_loaded = page.evaluate(
                "() => Array.from(document.fonts).filter(f => f.status === 'loaded').length"
            )
            if fonts_loaded < 5:
                raise RuntimeError(f"Expected >= 5 bundled @font-face faces loaded, got {fonts_loaded}")

            for frame_idx in range(TOTAL_FRAMES):
                t_frame = frame_idx * dt
                if is_fast_window(t_frame):
                    sub_samples = 4
                    acc = None
                    for s in range(sub_samples):
                        t_sub = max(0.0, min(DURATION_S, t_frame + ((s + 0.5) / sub_samples - 0.5) * dt))
                        page.evaluate("(t) => window.__seek(t)", t_sub)
                        img_bytes = page.screenshot(type="jpeg", quality=97)
                        arr = np.asarray(Image.open(io.BytesIO(img_bytes)).convert("RGB"), dtype=np.uint8)
                        lin = _TO_LINEAR[arr]
                        acc = lin if acc is None else (acc + lin)
                    avg_lin = np.clip(acc / float(sub_samples), 0.0, 1.0)
                    rgb_out = (np.power(avg_lin, 1.0 / 2.2) * 255.0 + 0.5).astype(np.uint8)
                    proc.stdin.write(rgb_out.tobytes())
                else:
                    page.evaluate("(t) => window.__seek(t)", t_frame)
                    img_bytes = page.screenshot(type="jpeg", quality=97)
                    arr = np.asarray(Image.open(io.BytesIO(img_bytes)).convert("RGB"), dtype=np.uint8)
                    proc.stdin.write(arr.tobytes())

            if errors:
                raise RuntimeError(f"Browser page errors: {errors}")
            browser.close()
    finally:
        if proc.stdin:
            proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        rc = proc.wait()
        httpd.shutdown()
        if rc != 0:
            raise RuntimeError(f"FFmpeg video encode failed ({rc}):\n{stderr}")

    elapsed = time.perf_counter() - t0_wall
    print(f"VIDEO_RENDER_OK: {TOTAL_FRAMES} frames rendered in {elapsed:.2f}s -> {out_video}")


def mix_audio_and_mux(video_only: Path, final_mp4: Path) -> None:
    sfx = KIT / "sfx"
    click = str(sfx / "click.ogg")
    whoosh = str(sfx / "whoosh.ogg")
    pop = str(sfx / "pop.ogg")
    impact = str(sfx / "impact.ogg")
    tick = str(sfx / "tick.ogg")

    raw_audio = RENDERS / "_showcase_audio_mix.wav"
    norm_audio = RENDERS / "_showcase_audio_norm.wav"

    # Explicit asplit per reused SFX stream + brief room-tone bed + cue-locked hits
    filter_complex = ";".join([
        "anullsrc=channel_layout=stereo:sample_rate=48000:duration=8.5[silence]",
        "sine=frequency=58:sample_rate=48000:duration=0.45,aformat=channel_layouts=stereo,afade=t=in:st=0:d=0.03,afade=t=out:st=0.06:d=0.39,volume=0.22,adelay=4550|4550[sub_hit]",
        "[0:a]aresample=48000,aformat=channel_layouts=stereo,adelay=120|120,volume=0.55[s_open]",
        "[1:a]aresample=48000,aformat=channel_layouts=stereo,asplit=3[w1][w2][w3]",
        "[w1]adelay=2240|2240,volume=0.80[s_wipe1]",
        "[w2]adelay=6520|6520,volume=0.76[s_slide3]",
        "[w3]adelay=7300|7300,volume=0.68[s_echo4]",
        "[2:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[p1][p2]",
        "[p1]adelay=2500|2500,volume=0.66[s_pop2]",
        "[p2]adelay=5500|5500,volume=0.72[s_lock3]",
        "[3:a]aresample=48000,aformat=channel_layouts=stereo,adelay=4560|4560,volume=0.88[s_imp2]",
        "[4:a]aresample=48000,aformat=channel_layouts=stereo,asplit=3[t1][t2][t3]",
        "[t1]adelay=4820|4820,volume=0.44[s_tick1]",
        "[t2]adelay=4980|4980,volume=0.42[s_tick2]",
        "[t3]adelay=5140|5140,volume=0.40[s_tick3]",
        "[silence][sub_hit][s_open][s_wipe1][s_pop2][s_imp2][s_tick1][s_tick2][s_tick3][s_lock3][s_slide3][s_echo4]"
        "amix=inputs=12:duration=first:normalize=0,atrim=0:8.5[mixed]"
    ])

    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", click, "-i", whoosh, "-i", pop, "-i", impact, "-i", tick,
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
            "-af", "acompressor=threshold=-20dB:ratio=4:attack=1:release=90:makeup=7.5dB,loudnorm=I=-15.8:TP=-4.4:LRA=5,alimiter=limit=0.60:level=disabled:attack=1:release=40",
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
            "-shortest",
            "-movflags", "+faststart",
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
    # Exact frame indices across all 4 scenes and 3 peak-velocity transitions (@ 60fps)
    frames = [27, 108, 145, 163, 213, 279, 294, 348, 398, 444, 474, 496]
    select_expr = "+".join(f"eq(n,{idx})" for idx in frames)
    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", str(final_mp4),
            "-vf", f"select='{select_expr}',scale=360:640,tile=4x3:padding=8:margin=8:color=#0B0F17",
            "-frames:v", "1",
            "-q:v", "2",
            str(sheet_jpg),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    RENDERS.mkdir(parents=True, exist_ok=True)
    video_only = RENDERS / "_showcase_video.mp4"
    final_mp4 = RENDERS / "baseline_showcase.mp4"
    sheet_jpg = RENDERS / "showcase_sheet.jpg"

    if "--audio-only" in sys.argv and final_mp4.exists():
        subprocess.run(
            [FFMPEG, "-y", "-i", str(final_mp4), "-an", "-c:v", "copy", str(video_only)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        render_video_stream(video_only)

    mix_audio_and_mux(video_only, final_mp4)
    if video_only.exists():
        video_only.unlink()
    extract_contact_sheet(final_mp4, sheet_jpg)

    ebur = subprocess.run(
        [FFMPEG, "-i", str(final_mp4), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    probe = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,r_frame_rate", "-of", "json", str(final_mp4)],
        capture_output=True,
        text=True,
        check=True,
    )
    print("FFPROBE:", probe.stdout.strip())
    for line in ebur.stderr.splitlines():
        if any(k in line for k in ("Integrated loudness:", "I:", "Threshold:", "Peak:")):
            print("LOUDNESS:", line.strip())
    print("CONTACT_SHEET:", sheet_jpg)


if __name__ == "__main__":
    main()
