"""V2 Gameplay Layer Renderer (1080x1920 @ 60fps) for Valorant Harbor 3K Edit.

Key V2 upgrades directly from user feedback & forensic analysis of 4JHCUuCAlC4,
1AXvJp95kX8, and _S5mVxnVbcU:
- Zoomed-out wide-FOV center gameplay over live blurred Breeze fill (top & bottom),
  scaling dynamically up/down during impacts, knife whips, and freeze reveals.
- Zero AI-slop dark rectangle cards or fake HUD widgets.
- _S5mVxnVbcU-inspired Chamber punch-in -> 3.85x deep horizontal whip-zoom directly
  onto tiny Reyna's headshot spark (698, 356) + raw cropped Valorant killfeed pixels
  (no card box) + crimson/gold Ace-style impact flash on Kill #3.
"""
from __future__ import annotations

import json
import math
import pathlib
import subprocess
import sys
import time

import cv2
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.valorant_edit import render_gameplay as rg1  # noqa: E402
from projects.valorant_edit import timeline_map as tm  # noqa: E402

FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")
PROXY_START_S = rg1.PROXY_START_S


def _build_blurred_backdrop(src_bgr: np.ndarray, dim: float = 0.44) -> np.ndarray:
    """Fast optical-bokeh full 1080x1920 live blurred fill matching source Breeze palette."""
    # Center-crop 9:16 slice at low res (270x480), blur heavily, upscale smoothly
    crop_w = int(round(tm.SRC_H * (tm.OUT_W / tm.OUT_H)))  # 432
    x0 = (tm.SRC_W - crop_w) // 2
    mid = src_bgr[:, x0 : x0 + crop_w]
    small = cv2.resize(mid, (180, 320), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(small, (0, 0), 14.0)
    up = cv2.resize(blurred, (tm.OUT_W, tm.OUT_H), interpolation=cv2.INTER_LINEAR)
    # Gently darken + keep warm contrast so foreground wide gameplay & text pop effortlessly
    return np.clip(up.astype(np.float32) * float(dim), 0, 255).astype(np.uint8)


def _apply_horizontal_smear(frame_bgr: np.ndarray, smear_px: float) -> np.ndarray:
    """Fast 7-tap directional horizontal streak smear inspired by _S5mVxnVbcU whip transitions."""
    if abs(smear_px) < 2.0:
        return frame_bgr
    h, w = frame_bgr.shape[:2]
    acc = np.zeros((h, w, 3), dtype=np.float32)
    taps = 7
    for i in range(taps):
        k = (i / (taps - 1)) - 0.5
        M = np.array([[1.0, 0.0, smear_px * k], [0.0, 1.0, 0.0]], dtype=np.float32)
        acc += cv2.warpAffine(frame_bgr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    return np.clip(acc / taps, 0, 255).astype(np.uint8)


def _crop_dynamic_layer(src_bgr: np.ndarray, st: dict[str, object]) -> tuple[np.ndarray, int]:
    """Render aspect-true zoomed-out or deep-zoomed foreground gameplay window of height win_h."""
    win_h = max(320, min(tm.OUT_H, int(round(float(st["win_h"])))))
    win_w = tm.OUT_W
    src_zoom = float(st["src_zoom"])
    cx = float(st["cx"])
    cy = float(st["cy"])
    shake_x = float(st["shake_x"])
    shake_y = float(st["shake_y"])

    # Guarantee 1:1 square pixels (zero stretching) while honoring zoomed-out wide FOV
    min_scale_h = win_h / float(tm.SRC_H)
    scale_w = (win_w / float(tm.SRC_W)) * src_zoom
    eff_scale = max(min_scale_h, scale_w)

    crop_w = win_w / eff_scale
    crop_h = win_h / eff_scale
    left = max(0.0, min(tm.SRC_W - crop_w, cx - crop_w * 0.5))
    top = max(0.0, min(tm.SRC_H - crop_h, cy - crop_h * 0.5))

    tx = -left * eff_scale + shake_x
    ty = -top * eff_scale + shake_y
    M = np.array([[eff_scale, 0.0, tx], [0.0, eff_scale, ty]], dtype=np.float32)
    fg = cv2.warpAffine(src_bgr, M, (win_w, win_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)

    # Breeze LUT + subtle vibrance
    fg = cv2.LUT(fg, rg1._LUT_BGR)
    hsv = cv2.cvtColor(fg, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1].astype(np.float32) * 1.12, 0, 255).astype(np.uint8)
    fg = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # Optional subtle desat/dim during Freeze Phase A or Reyna zoom spotlight boost
    fg_dim = float(st["fg_dim"])
    fg_desat = float(st["fg_desat"])
    if fg_desat > 0.01 or fg_dim < 0.995:
        gray = cv2.cvtColor(fg, cv2.COLOR_BGR2GRAY)[:, :, None].astype(np.float32)
        f32 = fg.astype(np.float32)
        fg = np.clip((f32 * (1.0 - fg_desat) + gray * fg_desat) * fg_dim, 0, 255).astype(np.uint8)

    # Deep Reyna headshot pop (Phase B): crisp unsharp mask + warm glow breath on Reyna spark
    rp = float(st["reyna_pulse"])
    if rp > 0.01:
        bl = cv2.GaussianBlur(fg, (0, 0), 1.4)
        sharp = cv2.addWeighted(fg, 1.42, bl, -0.42, 4.0)
        # Subtle radial highlight favoring center Reyna headshot spark
        yy, xx = np.mgrid[0:win_h, 0:win_w].astype(np.float32)
        nx = (xx / win_w - 0.5) * 2.0
        ny = (yy / win_h - 0.5) * 2.0
        spot = np.clip(1.0 - 0.38 * np.maximum(0.0, nx * nx + ny * ny - 0.18), 0.58, 1.0)[:, :, None]
        fg = np.clip(sharp.astype(np.float32) * (1.0 - rp + rp * spot), 0, 255).astype(np.uint8)

    # Kill #3 _S5mVxnVbcU Ace-style golden-crimson warm saturation burst
    csu = float(st["crimson_slash_u"])
    if 0.0 < csu < 0.75:
        kick = math.sin(min(1.0, csu / 0.75) * math.pi) * math.exp(-2.2 * csu)
        f32 = fg.astype(np.float32)
        f32[:, :, 2] *= (1.0 + 0.24 * kick)
        f32[:, :, 1] *= (1.0 + 0.08 * kick)
        f32[:, :, 0] *= (1.0 - 0.10 * kick)
        fg = np.clip(f32, 0, 255).astype(np.uint8)

    win_y0 = int(round(float(st["win_cy"]) - win_h * 0.5))
    win_y0 = max(0, min(tm.OUT_H - win_h, win_y0))
    return fg, win_y0


def _composite_window_soft(bg: np.ndarray, fg: np.ndarray, y0: int) -> np.ndarray:
    """Composite wide gameplay layer onto live blurred fill with silky top/bottom feather & shadow."""
    out = bg.copy()
    h, w = fg.shape[:2]
    if h >= tm.OUT_H - 4:
        return fg[: tm.OUT_H, : tm.OUT_W]

    # Subtle ambient drop shadow on blurred fill above/below the sharp gameplay layer (no ugly box border!)
    sh_h = 26
    if y0 > 0:
        sy0 = max(0, y0 - sh_h)
        grad = np.linspace(1.0, 0.58, y0 - sy0, dtype=np.float32)[:, None, None]
        out[sy0:y0] = np.clip(out[sy0:y0].astype(np.float32) * grad, 0, 255).astype(np.uint8)
    y1 = y0 + h
    if y1 < tm.OUT_H:
        sy1 = min(tm.OUT_H, y1 + sh_h)
        grad = np.linspace(0.58, 1.0, sy1 - y1, dtype=np.float32)[:, None, None]
        out[y1:sy1] = np.clip(out[y1:sy1].astype(np.float32) * grad, 0, 255).astype(np.uint8)

    # Silky 10px edge feather on top and bottom edges of foreground layer
    feather = min(10, h // 8)
    alpha = np.ones((h, 1, 1), dtype=np.float32)
    alpha[:feather, 0, 0] = np.linspace(0.0, 1.0, feather)
    alpha[-feather:, 0, 0] = np.linspace(1.0, 0.0, feather)
    roi = out[y0:y1].astype(np.float32)
    out[y0:y1] = np.clip(roi * (1.0 - alpha) + fg.astype(np.float32) * alpha, 0, 255).astype(np.uint8)
    return out


def _build_raw_killfeed_strip(src_bgr: np.ndarray, rect: tuple[int, int, int, int], scale: float = 2.15) -> tuple[np.ndarray, np.ndarray]:
    """Crop PURE real Valorant killfeed pixels only (ZERO dark rectangle card padding or web border!)."""
    x0, y0, x1, y1 = rect
    crop = src_bgr[y0:y1, x0:x1]
    uw = int(round((x1 - x0) * scale))
    uh = int(round((y1 - y0) * scale))
    up = cv2.resize(crop, (uw, uh), interpolation=cv2.INTER_LANCZOS4)
    bl = cv2.GaussianBlur(up, (0, 0), 0.9)
    up = cv2.addWeighted(up, 1.30, bl, -0.30, 0.0)
    alpha = np.full((uh, uw), 248, dtype=np.uint8)
    return up, alpha


def render_gameplay_v2(out_mp4: pathlib.Path | None = None) -> pathlib.Path:
    tm.WORK_DIR.mkdir(parents=True, exist_ok=True)
    target = out_mp4 or (tm.WORK_DIR / "layer_gameplay_v2.mp4")
    proxy = rg1.extract_cfr_proxy()
    reader = rg1.SlidingFrameReader(proxy, cache_size=64)

    freeze_src_idx = int(round((71.75 - PROXY_START_S) * tm.FPS))
    kf_reyna_idx = int(round((71.95 - PROXY_START_S) * tm.FPS))
    kf_double_idx = int(round((72.45 - PROXY_START_S) * tm.FPS))

    freeze_src_bgr = reader.get(freeze_src_idx).copy()
    kf_single_raw, kf_single_a = _build_raw_killfeed_strip(reader.get(kf_reyna_idx), tm.KILLFEED_REYNA_RECT, scale=2.15)
    kf_double_raw, kf_double_a = _build_raw_killfeed_strip(reader.get(kf_double_idx), tm.KILLFEED_DOUBLE_RECT, scale=2.15)

    reader.close()
    reader = rg1.SlidingFrameReader(proxy, cache_size=64)

    ffmpeg_cmd = [
        FFMPEG, "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{tm.OUT_W}x{tm.OUT_H}", "-r", str(tm.FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(target),
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    t_start = time.perf_counter()
    freeze_bg_cache: np.ndarray | None = None
    try:
        for f_idx in range(tm.TOTAL_FRAMES):
            out_t = f_idx / float(tm.FPS)
            st_t = tm.map_out_to_src(out_t)
            lst = tm.get_v2_layer_state(out_t)

            if st_t["is_freeze"]:
                src_bgr = freeze_src_bgr
                if freeze_bg_cache is None:
                    freeze_bg_cache = _build_blurred_backdrop(freeze_src_bgr, dim=0.38)
                bg = freeze_bg_cache
            else:
                src_idx = int(round((st_t["src_t"] - PROXY_START_S) * tm.FPS))
                if st_t["speed"] >= 1.40:
                    f_m1 = reader.get(src_idx - 1).astype(np.float32)
                    f_0 = reader.get(src_idx).astype(np.float32)
                    f_p1 = reader.get(src_idx + 1).astype(np.float32)
                    src_bgr = np.clip(f_m1 * 0.25 + f_0 * 0.50 + f_p1 * 0.25, 0, 255).astype(np.uint8)
                else:
                    src_bgr = reader.get(src_idx)
                bg = _build_blurred_backdrop(src_bgr, dim=float(lst["dim_bg"]))

            fg, win_y0 = _crop_dynamic_layer(src_bgr, lst)
            frame = _composite_window_soft(bg, fg, win_y0)

            # Directional horizontal whip smears (transition snap & Chamber -> Reyna deep zoom)
            if abs(float(lst["smear_x"])) >= 2.0:
                frame = _apply_horizontal_smear(frame, float(lst["smear_x"]))

            # Optical FX passes (MotionTileWhip, OpticalRadialMatch, FlashCutoutStrobe)
            if lst["effect"]:
                frame = rg1.apply_optical_effect(frame, str(lst["effect"]), float(lst["effect_u"]))

            # Pure Raw Cropped Live Killfeed (NO HTML card rectangle!) in clean upper blur band
            if tm.FREEZE_PHASE_B_T <= out_t < tm.KILL3_OUT_T:
                u_kf = min(1.0, (out_t - tm.FREEZE_PHASE_B_T) / 0.16)
                ease = 1.0 - (1.0 - u_kf) ** 3
                dx = int(round((1.0 - ease) * 80.0))
                kx = (tm.OUT_W - kf_single_raw.shape[1]) // 2 + dx
                ky = 190
                rg1._blend_rgba_patch(frame, np.zeros_like(kf_single_raw), kf_single_a, kx + 4, ky + 8, opacity=0.45 * ease)
                rg1._blend_rgba_patch(frame, kf_single_raw, kf_single_a, kx, ky, opacity=ease)
            elif tm.KILL3_OUT_T <= out_t <= tm.TOTAL_DURATION_S - 0.12:
                sc_kf = rg1._pop_spring(out_t - tm.KILL3_OUT_T, dur=0.18)
                fade_end = min(1.0, max(0.0, (tm.TOTAL_DURATION_S - 0.12 - out_t) / 0.25))
                if sc_kf > 0.1:
                    kx = (tm.OUT_W - kf_double_raw.shape[1]) // 2
                    ky = 298
                    rg1._blend_rgba_patch(frame, np.zeros_like(kf_double_raw), kf_double_a, kx + 4, ky + 8, opacity=0.48 * fade_end)
                    rg1._blend_rgba_patch(frame, kf_double_raw, kf_double_a, kx, ky, opacity=fade_end)

            assert proc.stdin is not None
            proc.stdin.write(frame.tobytes())
    finally:
        reader.close()
        if proc.stdin:
            proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"FFmpeg V2 gameplay encode failed ({rc}): {stderr}")

    elapsed = time.perf_counter() - t_start
    probe = json.loads(subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate,nb_frames",
        "-of", "json", str(target),
    ], text=True))
    print(f"GAMEPLAY_V2_OK: {target} ({tm.TOTAL_FRAMES} frames in {elapsed:.1f}s) | probe={json.dumps(probe)}")
    return target


if __name__ == "__main__":
    render_gameplay_v2()
