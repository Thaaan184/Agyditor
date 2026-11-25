"""V2 Transparent RGBA Overlay Renderer (1080x1920 @ 60fps) with blank-frame fast skip.

Renders projects/valorant_edit/overlay_stage_v2.html (zero AI-slop cards, pure kinetic
typography + _S5mVxnVbcU sky 3K & crimson brush slash) to layer_overlays_v2.mov.
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

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.valorant_edit import render_overlays as ro1  # noqa: E402
from projects.valorant_edit import timeline_map as tm  # noqa: E402

FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")


def _blank_transparent_png(w: int, h: int) -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), (0, 0, 0, 0)).save(buf, format="PNG", compress_level=1)
    return buf.getvalue()


def render_overlays_v2(out_mov: pathlib.Path | None = None) -> pathlib.Path:
    tm.WORK_DIR.mkdir(parents=True, exist_ok=True)
    tm.export_v2_stage_config()
    target = out_mov or (tm.WORK_DIR / "layer_overlays_v2.mov")
    blank_png = _blank_transparent_png(tm.OUT_W, tm.OUT_H)

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), ro1.DualRootHandler)
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
    required_fonts = {"Oswald", "Inter Tight", "Instrument Serif"}
    active_count = 0
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
            page.goto(f"http://127.0.0.1:{port}/projects/valorant_edit/overlay_stage_v2.html", wait_until="networkidle")
            page.wait_for_function("() => window.__ready === true", timeout=20000)

            loaded_fonts = set(page.evaluate("() => window.__loadedFonts || []"))
            missing = required_fonts - loaded_fonts
            if missing:
                raise RuntimeError(f"V2 self-hosted fonts missing: {sorted(missing)} (loaded={sorted(loaded_fonts)})")
            print(f"V2_FONTS_VERIFIED: {sorted(loaded_fonts)}")

            # Fast pre-flight JS check across full timeline
            for k in range(28):
                page.evaluate("(t) => window.__seek(t)", min(tm.TOTAL_DURATION_S, k * 1.0))
            if errs:
                raise RuntimeError(f"V2 pre-flight JS errors: {errs}")

            for idx in range(tm.TOTAL_FRAMES):
                t_frame = idx * dt
                is_act = page.evaluate("(t) => window.__isFrameActive(t)", t_frame)
                assert proc.stdin is not None
                if not is_act:
                    proc.stdin.write(blank_png)
                else:
                    active_count += 1
                    page.evaluate("(t) => window.__seek(t)", t_frame)
                    proc.stdin.write(page.screenshot(type="png", omit_background=True))

            if errs:
                raise RuntimeError(f"V2 overlay runtime errors: {errs}")
            browser.close()
    finally:
        if proc.stdin:
            proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        rc = proc.wait()
        httpd.shutdown()
        if rc != 0:
            raise RuntimeError(f"FFmpeg V2 overlay encode failed ({rc}): {stderr}")

    elapsed = time.perf_counter() - t0
    probe = json.loads(subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "stream=codec_name,pix_fmt,width,height,nb_frames",
        "-of", "json", str(target),
    ], text=True))
    print(f"OVERLAY_V2_OK: {target} ({active_count}/{tm.TOTAL_FRAMES} active frames in {elapsed:.1f}s) | probe={json.dumps(probe)}")
    return target


if __name__ == "__main__":
    render_overlays_v2()
