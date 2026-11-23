"""Deterministic seekable HTML/Canvas/SVG to 1080p MP4 renderer via Playwright Chromium and FFmpeg."""

from pathlib import Path
import shutil
import subprocess
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def _resolve_ffmpeg(binary_name: str = "ffmpeg") -> str:
    local_bin = ROOT / "bin" / f"{binary_name}.exe"
    if local_bin.exists():
        return str(local_bin)
    found = shutil.which(binary_name)
    if not found:
        raise FileNotFoundError(f"{binary_name} not found in {local_bin} or system PATH")
    return found


def render_seekable_html(
    html_path: str,
    output_mp4: str,
    duration_sec: float,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    audio_wav: str | None = None,
) -> dict:
    """Captures frame-by-frame deterministic states via window.__seek(t) and encodes MP4 via FFmpeg."""
    src_html = Path(html_path).resolve()
    if not src_html.exists():
        raise FileNotFoundError(f"HTML composition not found: {src_html}")

    out_file = Path(output_mp4).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = out_file.parent / f"frames_tmp_{out_file.stem}"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    total_frames = max(1, round(duration_sec * fps))

    with sync_playwright() as p:
        browser = None
        for ch in ("chrome", "msedge", None):
            try:
                browser = (
                    p.chromium.launch(headless=True, channel=ch)
                    if ch
                    else p.chromium.launch(headless=True)
                )
                break
            except Exception:
                continue
        if browser is None:
            raise RuntimeError("No Chromium, Chrome, or Edge browser available for Playwright")
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        page.goto(src_html.as_uri(), wait_until="load")

        for frame_idx in range(total_frames):
            t_sec = frame_idx / float(fps)
            page.evaluate(f"if (window.__seek) {{ window.__seek({t_sec:.6f}); }}")
            frame_file = frames_dir / f"frame_{frame_idx:05d}.png"
            page.screenshot(path=str(frame_file), type="png")

        browser.close()

    ffmpeg_bin = _resolve_ffmpeg("ffmpeg")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%05d.png"),
    ]
    if audio_wav and Path(audio_wav).exists():
        cmd.extend(["-i", str(Path(audio_wav).resolve()), "-c:a", "aac", "-b:a", "192k", "-shortest"])

    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-preset",
            "fast",
            str(out_file),
        ]
    )

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    shutil.rmtree(frames_dir, ignore_errors=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed: {proc.stderr}")

    return {
        "output_mp4": str(out_file),
        "frames_rendered": total_frames,
        "fps": fps,
        "width": width,
        "height": height,
    }
