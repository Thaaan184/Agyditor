"""Headless Chrome GPU Transparent RGBA Overlay Renderer (1080x1920 @ 60fps).

Serves workspace assets (/studio_kit/, /projects/) alongside D:\\Clip\\Edit\\Valorant\\work (/work/),
launches Windows Chrome with ANGLE D3D11 WebGL flags, verifies all 4 self-hosted fonts load cleanly,
and pipes transparent RGBA frames to FFmpeg PNG-in-MOV (D:\\Clip\\Edit\\Valorant\\work\\layer_overlays.mov).
"""
from __future__ import annotations

import http.server
import io
import json
import pathlib
import subprocess
import sys
import threading
import time

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.valorant_edit import timeline_map as tm  # noqa: E402

FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")


class DualRootHandler(http.server.SimpleHTTPRequestHandler):
    """Serve /work/* from D:\\Clip\\Edit\\Valorant\\work and everything else from repo root."""

    def translate_path(self, path: str) -> str:
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean.startswith("/work/"):
            rel = clean[len("/work/") :].lstrip("/")
            return str(tm.WORK_DIR / rel)
        rel = clean.lstrip("/")
        return str(ROOT / rel)

    def log_message(self, format: str, *args: object) -> None:
        pass


def render_overlays_layer(out_mov: pathlib.Path | None = None) -> pathlib.Path:
    tm.WORK_DIR.mkdir(parents=True, exist_ok=True)
    tm.export_stage_config()
    target = out_mov or (tm.WORK_DIR / "layer_overlays.mov")

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), DualRootHandler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    ffmpeg_cmd = [
        FFMPEG, "-y", "-v", "error",
        "-f", "image2pipe", "-vcodec", "png", "-r", str(tm.FPS),
        "-i", "-",
        "-c:v", "copy",
        str(target),
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    t0 = time.perf_counter()
    dt = 1.0 / float(tm.FPS)
    required_fonts = {"Oswald", "Inter Tight", "Instrument Serif", "JetBrains Mono"}
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
            page = browser.new_page(viewport={"width": tm.OUT_W, "height": tm.OUT_H}, device_scale_factor=1)
            errs: list[str] = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.goto(f"http://127.0.0.1:{port}/projects/valorant_edit/overlay_stage.html", wait_until="networkidle")
            page.wait_for_function("() => window.__ready === true", timeout=20000)

            loaded_fonts = set(page.evaluate("() => window.__loadedFonts || []"))
            missing = required_fonts - loaded_fonts
            if missing:
                raise RuntimeError(f"Self-hosted fonts failed to load: {sorted(missing)} (loaded={sorted(loaded_fonts)})")
            print(f"FONTS_VERIFIED: {sorted(loaded_fonts)}")

            # Fast 0.1s pre-flight JS seek sweep across full timeline before piping frames
            for k in range(28):
                page.evaluate("(t) => window.__seek(t)", min(tm.TOTAL_DURATION_S, k * 1.0))
            if errs:
                raise RuntimeError(f"Pre-flight overlay JS errors: {errs}")

            for idx in range(tm.TOTAL_FRAMES):
                t_frame = idx * dt
                page.evaluate("(t) => window.__seek(t)", t_frame)
                png_bytes = page.screenshot(type="png", omit_background=True)
                assert proc.stdin is not None
                proc.stdin.write(png_bytes)

            if errs:
                raise RuntimeError(f"Overlay browser errors: {errs}")
            browser.close()
    finally:
        if proc.stdin:
            proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        rc = proc.wait()
        httpd.shutdown()
        if rc != 0:
            raise RuntimeError(f"FFmpeg overlay encode failed ({rc}): {stderr}")

    elapsed = time.perf_counter() - t0
    probe = json.loads(subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "stream=codec_name,pix_fmt,width,height,nb_frames",
        "-of", "json", str(target),
    ], text=True))
    print(f"OVERLAY_LAYER_OK: {target} ({tm.TOTAL_FRAMES} frames in {elapsed:.1f}s) | probe={json.dumps(probe)}")
    return target


if __name__ == "__main__":
    render_overlays_layer()
