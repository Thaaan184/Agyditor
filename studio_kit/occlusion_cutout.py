"""Smart Two-Tier Subject Occlusion helper for AGY Local Video Studio.

Supports CPU-safe short burst mattes (Pop-Up anchor cutout, Flash Cutout strobe silhouette,
and 1s-3s hook sequences <= 90 frames) plus external alpha-matte directory ingestion
for long moving-subject 3D text orbits.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
MAX_CPU_FRAMES = 90


def compute_bottom_center_anchor(alpha_img: Image.Image) -> dict[str, Any]:
    """Compute normalized [ax, ay] bottom-center anchor from non-transparent subject bounds."""
    alpha = np.asarray(alpha_img.convert("L"))
    ys, xs = np.where(alpha > 20)
    h, w = alpha.shape
    if len(xs) == 0 or len(ys) == 0:
        return {"anchor": [0.5, 1.0], "bbox": [0, 0, w, h]}
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    cx = (x0 + x1) * 0.5 / max(1, w)
    by = (y1 + 1) / max(1, h)
    return {
        "anchor": [round(float(cx), 4), round(float(by), 4)],
        "bbox": [x0, y0, x1, y1],
        "size": [w, h],
    }


def make_white_flash_silhouette(cutout_rgba: Image.Image, blur_radius: float = 4.5) -> Image.Image:
    """Create blurred pure-white silhouette cutout matching Varo Flash Cutout (dHAx3HSVDLA)."""
    alpha = cutout_rgba.split()[-1]
    white = Image.new("RGBA", cutout_rgba.size, (255, 255, 255, 0))
    white.putalpha(alpha)
    if blur_radius > 0:
        white = white.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return white


def extract_frame_pil(video_path: pathlib.Path, time_s: float) -> Image.Image:
    cmd = [
        FFMPEG,
        "-v",
        "error",
        "-ss",
        f"{max(0.0, time_s):.4f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "-",
    ]
    raw = subprocess.check_output(cmd)
    from io import BytesIO

    return Image.open(BytesIO(raw)).convert("RGBA")


def run_cutout_image(rgba_img: Image.Image) -> Image.Image:
    from rembg import remove

    out = remove(rgba_img)
    return out.convert("RGBA")


def build_popup_bundle(video_or_img: pathlib.Path, out_dir: pathlib.Path, time_s: float = 0.0) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if video_or_img.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
        src_img = Image.open(video_or_img).convert("RGBA")
    else:
        src_img = extract_frame_pil(video_or_img, time_s)

    cutout = run_cutout_image(src_img)
    cutout_path = out_dir / "popup_cutout.png"
    cutout.save(cutout_path)

    anchor_meta = compute_bottom_center_anchor(cutout)
    flash_img = make_white_flash_silhouette(cutout, blur_radius=5.0)
    flash_path = out_dir / "flash_silhouette.png"
    flash_img.save(flash_path)

    meta = {
        "cutout": str(cutout_path),
        "flash_silhouette": str(flash_path),
        "anchor_info": anchor_meta,
    }
    (out_dir / "occlusion_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="AGY Smart Two-Tier Subject Occlusion Extractor")
    parser.add_argument("source", type=pathlib.Path, help="Input image or video file")
    parser.add_argument("out_dir", type=pathlib.Path, help="Output directory for cutout + flash silhouette")
    parser.add_argument("--time", type=float, default=0.0, help="Seek timestamp in seconds when source is video")
    args = parser.parse_args()

    meta = build_popup_bundle(args.source, args.out_dir, args.time)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
