"""Gameplay Base Layer Renderer (1080x1920 @ 60fps) for Valorant Harbor 3K Edit.

Produces D:\\Clip\\Edit\\Valorant\\work\\layer_gameplay.mp4 with:
- Clean CFR 60fps proxy decoded from 44.5s..75.5s of ShadowPlay DVR clip
- Exact piecewise time-remapping & 3-tap velocity shutter blur from timeline_map.py
- Breeze cinema LUT grading + subtle vignette
- Calibrated optical effects (MotionTileWhip, OpticalRadialMatch, FlashCutoutStrobe)
- 4.2x circular optical magnifying loupe on Reyna headshot spark (698, 356)
- Live Lanczos-upscaled Valorant killfeed re-dock pills free of FPS graph clutter
"""
from __future__ import annotations

import json
import math
import pathlib
import subprocess
import sys
import time
from collections import OrderedDict

import cv2
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projects.valorant_edit import timeline_map as tm  # noqa: E402

FFMPEG = str(ROOT / "bin" / "ffmpeg.exe")
FFPROBE = str(ROOT / "bin" / "ffprobe.exe")
PROXY_START_S = 44.5
PROXY_DUR_S = 31.0


def _build_breeze_lut() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build per-channel (B, G, R) cinema S-curve LUTs enhancing Breeze warmth & Glitchpop pop."""
    x = np.linspace(0.0, 1.0, 256, dtype=np.float32)
    # Gentle filmic S-curve: deeper crisp blacks, clean midtones, controlled highlight roll-off
    s = x + 0.055 * np.sin(2.0 * math.pi * (x - 0.5)) * (x * (1.0 - x) * 4.0)
    s = np.clip(s, 0.0, 1.0)
    # Subtle teal-shadow / warm-highlight separation (OpenCV BGR order)
    b_lut = np.clip(s * 0.99 + 0.014 * (1.0 - s) * s * 4.0, 0.0, 1.0)
    g_lut = np.clip(s * 1.005, 0.0, 1.0)
    r_lut = np.clip(s * 1.022 - 0.008 * (1.0 - s) ** 2, 0.0, 1.0)
    return (
        (b_lut * 255.0 + 0.5).astype(np.uint8),
        (g_lut * 255.0 + 0.5).astype(np.uint8),
        (r_lut * 255.0 + 0.5).astype(np.uint8),
    )


_LUT_B, _LUT_G, _LUT_R = _build_breeze_lut()
_LUT_BGR = np.stack([_LUT_B, _LUT_G, _LUT_R], axis=1).reshape(256, 1, 3)


def _build_vignette_mask(w: int, h: int) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xx / w - 0.5) * 2.0
    ny = (yy / h - 0.5) * 2.0
    r2 = nx * nx * 0.55 + ny * ny * 0.95
    vig = np.clip(1.0 - 0.22 * np.maximum(0.0, r2 - 0.35), 0.72, 1.0)
    return vig[:, :, None].astype(np.float32)


_VIG_MASK = _build_vignette_mask(tm.OUT_W, tm.OUT_H)


def apply_breeze_grade(frame_bgr: np.ndarray) -> np.ndarray:
    graded = cv2.LUT(frame_bgr, _LUT_BGR)
    # Subtle vibrance boost (+11% saturation in HSV) so red Vandal & blue Sova beam shine
    hsv = cv2.cvtColor(graded, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1].astype(np.float32) * 1.11
    hsv[:, :, 1] = np.clip(s, 0, 255).astype(np.uint8)
    graded = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    out = np.clip(graded.astype(np.float32) * _VIG_MASK, 0, 255).astype(np.uint8)
    return out


def extract_cfr_proxy(
    src_mp4: pathlib.Path = tm.SOURCE_CLIP_PATH,
    out_proxy: pathlib.Path | None = None,
    start_s: float = PROXY_START_S,
    dur_s: float = PROXY_DUR_S,
) -> pathlib.Path:
    """Decode ShadowPlay VFR source into a clean CFR 60fps H.264 intermediate on Drive D:."""
    proxy = out_proxy or (tm.WORK_DIR / "source_cfr60.mp4")
    proxy.parent.mkdir(parents=True, exist_ok=True)
    if proxy.exists() and proxy.stat().st_size > 1_000_000:
        return proxy
    subprocess.run(
        [
            FFMPEG, "-y", "-v", "error",
            "-ss", f"{start_s:.3f}",
            "-i", str(src_mp4),
            "-t", f"{dur_s:.3f}",
            "-an", "-r", str(tm.FPS), "-fps_mode", "cfr",
            "-c:v", "libx264", "-preset", "fast", "-crf", "11", "-pix_fmt", "yuv420p",
            str(proxy),
        ],
        check=True, capture_output=True, text=True,
    )
    return proxy


class SlidingFrameReader:
    """Memory-safe sequential frame reader with 64-frame LRU cache over CFR proxy."""

    def __init__(self, video_path: pathlib.Path, cache_size: int = 64):
        self.cap = cv2.VideoCapture(str(video_path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video proxy: {video_path}")
        self.total = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.pos = 0
        self.cache_size = cache_size
        self.cache: OrderedDict[int, np.ndarray] = OrderedDict()

    def get(self, idx: int) -> np.ndarray:
        i = max(0, min(self.total - 1, int(idx)))
        if i in self.cache:
            self.cache.move_to_end(i)
            return self.cache[i]

        if i < self.pos or (i - self.pos) > 30:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            self.pos = i

        frame = None
        while self.pos <= i:
            ok, f = self.cap.read()
            if not ok:
                break
            cur = self.pos
            self.pos += 1
            self.cache[cur] = f
            if len(self.cache) > self.cache_size:
                self.cache.popitem(last=False)
            if cur == i:
                frame = f

        if frame is None:
            if self.cache:
                return next(reversed(self.cache.values()))
            raise RuntimeError(f"Failed reading frame {i} from proxy")
        return frame

    def close(self) -> None:
        self.cap.release()


def render_loupe_inset(
    src_bgr: np.ndarray,
    center_xy: tuple[float, float],
    *,
    radius_px: int = tm.LOUPE_RADIUS_PX,
    zoom_factor: float = tm.LOUPE_ZOOM_FACTOR,
) -> tuple[np.ndarray, np.ndarray]:
    """Crop & 4.2x upscale raw source pixels around Reyna headshot spark into a circular loupe."""
    h, w = src_bgr.shape[:2]
    d = int(radius_px * 2)
    # Source span needed so zoomed pixels cleanly fill diameter d
    src_span = max(24.0, (d / 2.5) / (zoom_factor / 2.5))  # = d / zoom_factor
    half = src_span * 0.5
    cx, cy = float(center_xy[0]), float(center_xy[1])
    x0 = max(0.0, min(w - src_span, cx - half))
    y0 = max(0.0, min(h - src_span, cy - half))

    # Subpixel affine zoom straight from raw 1366x768 source frame
    scale = d / src_span
    M = np.array([[scale, 0.0, -x0 * scale], [0.0, scale, -y0 * scale]], dtype=np.float32)
    patch = cv2.warpAffine(src_bgr, M, (d, d), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)

    # Tactile optical sharpening so distant Reyna silhouette + orange headshot spark pop sharply
    blur = cv2.GaussianBlur(patch, (0, 0), 1.4)
    patch = cv2.addWeighted(patch, 1.55, blur, -0.55, 4.0)
    # Slight vibrance lift inside loupe glass
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1].astype(np.float32) * 1.22, 0, 255).astype(np.uint8)
    patch = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # Anti-aliased circular mask
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32)
    dist = np.hypot(xx - (radius_px - 0.5), yy - (radius_px - 0.5))
    mask = np.clip((radius_px - dist) * 1.2, 0.0, 1.0)
    mask_u8 = (mask * 255.0 + 0.5).astype(np.uint8)
    return patch, mask_u8


def apply_optical_effect(frame_bgr: np.ndarray, effect: str | None, u: float) -> np.ndarray:
    """Apply calibrated studio_kit v2 optical FX in OpenCV matching exact shader semantics."""
    if not effect:
        return frame_bgr
    h, w = frame_bgr.shape[:2]
    u = max(0.0, min(1.0, float(u)))

    if effect == "motion_tile_whip":
        # Mirror-tiled horizontal whip pan with 7-tap directional velocity blur
        vel = math.sin(u * math.pi) ** 1.3
        shift_x = (u - 0.5) * 420.0 * vel
        blur_span = 110.0 * vel
        acc = np.zeros((h, w, 3), dtype=np.float32)
        taps = 7
        for i in range(taps):
            k = (i / (taps - 1)) - 0.5
            M = np.array([[1.0, 0.0, shift_x + blur_span * k], [0.0, 1.0, 0.0]], dtype=np.float32)
            shifted = cv2.warpAffine(frame_bgr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
            acc += shifted.astype(np.float32)
        return np.clip(acc / taps, 0, 255).astype(np.uint8)

    if effect == "optical_radial_match":
        # Radial zoom blur + RGB chromatic split + subtle cyan impact pop (Kill #1 through Sova Ult)
        env = math.sin(u * math.pi) * math.exp(-1.4 * u)
        if env < 0.01:
            return frame_bgr
        cx, cy = w * 0.5, h * 0.5
        acc = np.zeros((h, w, 3), dtype=np.float32)
        taps = 5
        for i in range(taps):
            f = i / (taps - 1)
            sc = 1.0 + env * 0.085 * f
            M = cv2.getRotationMatrix2D((cx, cy), env * 1.4 * (f - 0.5), sc)
            acc += cv2.warpAffine(frame_bgr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        out = acc / taps
        # Radial RGB chromatic split (R zooms out slightly, B zooms in slightly)
        chroma = env * 0.022
        Mr = cv2.getRotationMatrix2D((cx, cy), 0.0, 1.0 + chroma)
        Mb = cv2.getRotationMatrix2D((cx, cy), 0.0, 1.0 - chroma)
        r_ch = cv2.warpAffine(out[:, :, 2], Mr, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        b_ch = cv2.warpAffine(out[:, :, 0], Mb, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        out[:, :, 2] = r_ch
        out[:, :, 0] = b_ch
        # Crisp brief cyan-white flash on first 2-3 frames of impact
        flash = max(0.0, 1.0 - u * 5.0)
        if flash > 0.0:
            out[:, :, 0] += 36.0 * flash
            out[:, :, 1] += 30.0 * flash
            out[:, :, 2] += 18.0 * flash
        return np.clip(out, 0, 255).astype(np.uint8)

    if effect == "flash_cutout_strobe":
        # Punchy 2-frame Glitchpop crimson/cyan exposure strobe + chromatic kick (Kill #3 Chamber HS)
        env = math.exp(-4.5 * u)
        cx, cy = w * 0.5, h * 0.5
        sc = 1.0 + 0.055 * math.sin(u * math.pi)
        M = cv2.getRotationMatrix2D((cx, cy), 0.0, sc)
        base = cv2.warpAffine(frame_bgr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101).astype(np.float32)
        chroma = env * 0.026
        Mr = cv2.getRotationMatrix2D((cx, cy), 0.0, 1.0 + chroma)
        Mb = cv2.getRotationMatrix2D((cx, cy), 0.0, 1.0 - chroma)
        base[:, :, 2] = cv2.warpAffine(base[:, :, 2], Mr, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        base[:, :, 0] = cv2.warpAffine(base[:, :, 0], Mb, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        # 2-frame controlled highlight flash + Glitchpop crimson rim tint
        if u < 0.14:
            gain = 1.38 if u < 0.07 else 1.18
            base *= gain
            base[:, :, 2] += 26.0 * (1.0 - u / 0.14)
            base[:, :, 0] += 18.0 * (1.0 - u / 0.14)
        return np.clip(base, 0, 255).astype(np.uint8)

    return frame_bgr


def _build_killfeed_plate(src_bgr: np.ndarray, rect: tuple[int, int, int, int], scale: float = 2.25) -> tuple[np.ndarray, np.ndarray]:
    """Crop clean real Valorant killfeed pixels, upscale Lanczos, mount on dark tactical glass pill."""
    x0, y0, x1, y1 = rect
    crop = src_bgr[y0:y1, x0:x1]
    uw = int(round((x1 - x0) * scale))
    uh = int(round((y1 - y0) * scale))
    up = cv2.resize(crop, (uw, uh), interpolation=cv2.INTER_LANCZOS4)
    # Mild crisp sharpening so player names & headshot icons are crystal-clear on mobile
    bl = cv2.GaussianBlur(up, (0, 0), 1.0)
    up = cv2.addWeighted(up, 1.32, bl, -0.32, 0.0)

    pad_x, pad_y = 14, 12
    pw, ph = uw + pad_x * 2, uh + pad_y * 2
    plate = np.full((ph, pw, 3), (11, 9, 9), dtype=np.uint8)  # #09090B in BGR
    plate[pad_y : pad_y + uh, pad_x : pad_x + uw] = up
    # Crisp 2px top Glitchpop crimson accent edge + subtle 1px border
    plate[0:3, :, :] = (84, 46, 255)  # #FF2E54 in BGR
    plate[-1:, :, :] = (48, 48, 56)
    plate[:, 0:1, :] = (48, 48, 56)
    plate[:, -1:, :] = (48, 48, 56)

    # Rounded corner alpha mask
    alpha = np.full((ph, pw), 235, dtype=np.uint8)
    alpha[pad_y : pad_y + uh, pad_x : pad_x + uw] = 255
    return plate, alpha


def _blend_rgba_patch(
    dst: np.ndarray,
    patch: np.ndarray,
    alpha_u8: np.ndarray,
    x: int,
    y: int,
    opacity: float = 1.0,
) -> None:
    if opacity <= 0.005:
        return
    h, w = dst.shape[:2]
    ph, pw = patch.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(w, x + pw), min(h, y + ph)
    if x1 <= x0 or y1 <= y0:
        return
    px0, py0 = x0 - x, y0 - y
    px1, py1 = px0 + (x1 - x0), py0 + (y1 - y0)
    a = (alpha_u8[py0:py1, px0:px1].astype(np.float32) / 255.0) * float(opacity)
    a3 = a[:, :, None]
    roi = dst[y0:y1, x0:x1].astype(np.float32)
    blended = roi * (1.0 - a3) + patch[py0:py1, px0:px1].astype(np.float32) * a3
    dst[y0:y1, x0:x1] = np.clip(blended, 0, 255).astype(np.uint8)


def _pop_spring(local_t: float, dur: float = 0.22) -> float:
    if local_t <= 0.0:
        return 0.0
    if local_t >= dur:
        return 1.0
    u = local_t / dur
    if u < 0.68:
        e = 1.0 - (1.0 - u / 0.68) ** 3
        return 1.06 * e
    e2 = (u - 0.68) / 0.32
    return 1.06 - 0.06 * (e2 * e2 * (3.0 - 2.0 * e2))


def _crop_vertical_frame(src_bgr: np.ndarray, out_t: float) -> np.ndarray:
    cam = tm.get_camera_state(out_t)
    left, top, _, _, eff_scale = tm.get_crop_box(out_t)
    tx = -left * eff_scale + cam["shake_x"]
    ty = -top * eff_scale + cam["shake_y"]
    M = np.array([[eff_scale, 0.0, tx], [0.0, eff_scale, ty]], dtype=np.float32)
    return cv2.warpAffine(
        src_bgr,
        M,
        (tm.OUT_W, tm.OUT_H),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REFLECT_101,
    )


def render_gameplay_layer(out_mp4: pathlib.Path | None = None) -> pathlib.Path:
    tm.WORK_DIR.mkdir(parents=True, exist_ok=True)
    target = out_mp4 or (tm.WORK_DIR / "layer_gameplay.mp4")
    proxy = extract_cfr_proxy()
    reader = SlidingFrameReader(proxy, cache_size=64)

    # Pre-grab exact special reference plates from the CFR proxy BEFORE sequential playback
    freeze_src_idx = int(round((71.75 - PROXY_START_S) * tm.FPS))
    kf_reyna_idx = int(round((71.95 - PROXY_START_S) * tm.FPS))
    kf_double_idx = int(round((72.45 - PROXY_START_S) * tm.FPS))

    freeze_src_bgr = reader.get(freeze_src_idx).copy()
    loupe_patch, loupe_mask = render_loupe_inset(
        freeze_src_bgr,
        tm.REYNA_SRC_XY,
        radius_px=tm.LOUPE_RADIUS_PX,
        zoom_factor=tm.LOUPE_ZOOM_FACTOR,
    )
    kf_single_plate, kf_single_alpha = _build_killfeed_plate(reader.get(kf_reyna_idx), tm.KILLFEED_REYNA_RECT, scale=2.25)
    kf_double_plate, kf_double_alpha = _build_killfeed_plate(reader.get(kf_double_idx), tm.KILLFEED_DOUBLE_RECT, scale=2.25)

    # Precompute freeze spotlight mask around Chamber & Reyna on 1080x1920 canvas
    freeze_mid = 0.5 * (tm.FREEZE_OUT_T0 + tm.FREEZE_OUT_T1)
    ch_x, ch_y = tm.project_source_to_canvas(*tm.CHAMBER_SRC_XY, freeze_mid)
    ry_x, ry_y = tm.project_source_to_canvas(*tm.REYNA_SRC_XY, freeze_mid)
    yy, xx = np.mgrid[0 : tm.OUT_H, 0 : tm.OUT_W].astype(np.float32)
    spot_ch = np.exp(-((xx - ch_x) ** 2 + (yy - ch_y) ** 2) / (2.0 * (125.0 ** 2)))[:, :, None]
    spot_ry = np.exp(-((xx - ry_x) ** 2 + (yy - ry_y) ** 2) / (2.0 * (145.0 ** 2)))[:, :, None]

    # Reset reader cleanly for sequential pass
    reader.close()
    reader = SlidingFrameReader(proxy, cache_size=64)

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
    freeze_base_graded: np.ndarray | None = None

    try:
        for f_idx in range(tm.TOTAL_FRAMES):
            out_t = f_idx / float(tm.FPS)
            st = tm.map_out_to_src(out_t)
            cam = tm.get_camera_state(out_t)

            if st["is_freeze"]:
                if freeze_base_graded is None:
                    freeze_base_graded = apply_breeze_grade(_crop_vertical_frame(freeze_src_bgr, freeze_mid))
                frame = freeze_base_graded.copy()
                # Dim & desaturate background while keeping Chamber / Reyna bright in optical spotlight
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)[:, :, None].astype(np.float32)
                f32 = frame.astype(np.float32)
                dimmed = (f32 * (1.0 - cam["desat"]) + gray * cam["desat"]) * cam["dim"]
                spot = spot_ch if out_t < tm.FREEZE_PHASE_B_T else np.maximum(spot_ch * 0.65, spot_ry)
                frame = np.clip(dimmed * (1.0 - spot) + f32 * spot, 0, 255).astype(np.uint8)

                # Phase B: Pop in the 4.2x Circular Magnifying Loupe on Reyna!
                if out_t >= tm.FREEZE_PHASE_B_T:
                    sc = _pop_spring(out_t - tm.FREEZE_PHASE_B_T, dur=0.20)
                    if sc > 0.02:
                        d_cur = max(8, int(round(tm.LOUPE_RADIUS_PX * 2 * sc)))
                        p_cur = cv2.resize(loupe_patch, (d_cur, d_cur), interpolation=cv2.INTER_LINEAR)
                        m_cur = cv2.resize(loupe_mask, (d_cur, d_cur), interpolation=cv2.INTER_LINEAR)
                        lx = int(round(tm.LOUPE_CANVAS_XY[0] - d_cur * 0.5))
                        ly = int(round(tm.LOUPE_CANVAS_XY[1] - d_cur * 0.5))
                        # Soft drop shadow behind glass loupe
                        sh_patch = np.zeros_like(p_cur)
                        _blend_rgba_patch(frame, sh_patch, m_cur, lx + 8, ly + 14, opacity=0.52)
                        _blend_rgba_patch(frame, p_cur, m_cur, lx, ly, opacity=1.0)
            else:
                src_idx = int(round((st["src_t"] - PROXY_START_S) * tm.FPS))
                if st["speed"] >= 1.40:
                    # 3-tap shutter motion blur blend across adjacent source frames during velocity ramps
                    f_m1 = reader.get(src_idx - 1).astype(np.float32)
                    f_0 = reader.get(src_idx).astype(np.float32)
                    f_p1 = reader.get(src_idx + 1).astype(np.float32)
                    src_bgr = np.clip(f_m1 * 0.25 + f_0 * 0.50 + f_p1 * 0.25, 0, 255).astype(np.uint8)
                else:
                    src_bgr = reader.get(src_idx)
                frame = apply_breeze_grade(_crop_vertical_frame(src_bgr, out_t))

            # Optical FX passes (MotionTileWhip, OpticalRadialMatch, FlashCutoutStrobe)
            if cam["effect"]:
                frame = apply_optical_effect(frame, cam["effect"], cam["effect_u"])

            # Live Re-Docked Valorant Killfeed Pills (zero Client FPS artifacts)
            if tm.FREEZE_PHASE_B_T <= out_t < tm.KILL3_OUT_T:
                u_kf = min(1.0, (out_t - tm.FREEZE_PHASE_B_T) / 0.18)
                ease_kf = 1.0 - (1.0 - u_kf) ** 3
                dx = int(round((1.0 - ease_kf) * 90.0))
                _blend_rgba_patch(frame, kf_single_plate, kf_single_alpha, tm.KILLFEED_DEST_X + dx, tm.KILLFEED_DEST_Y, opacity=ease_kf)
            elif tm.KILL3_OUT_T <= out_t <= tm.TOTAL_DURATION_S - 0.12:
                sc_kf = _pop_spring(out_t - tm.KILL3_OUT_T, dur=0.18)
                fade_end = min(1.0, max(0.0, (tm.TOTAL_DURATION_S - 0.12 - out_t) / 0.25))
                if sc_kf > 0.1:
                    kw = int(round(kf_double_plate.shape[1] * (0.94 + 0.06 * sc_kf)))
                    kh = int(round(kf_double_plate.shape[0] * (0.94 + 0.06 * sc_kf)))
                    kp = cv2.resize(kf_double_plate, (kw, kh), interpolation=cv2.INTER_LINEAR)
                    ka = cv2.resize(kf_double_alpha, (kw, kh), interpolation=cv2.INTER_LINEAR)
                    _blend_rgba_patch(frame, kp, ka, tm.KILLFEED_DEST_X, tm.KILLFEED_DEST_Y, opacity=fade_end)

            assert proc.stdin is not None
            proc.stdin.write(frame.tobytes())
    finally:
        reader.close()
        if proc.stdin:
            proc.stdin.close()
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"FFmpeg encode failed ({rc}): {stderr}")

    elapsed = time.perf_counter() - t_start
    probe = json.loads(subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate,nb_frames",
        "-of", "json", str(target),
    ], text=True))
    print(f"GAMEPLAY_LAYER_OK: {target} ({tm.TOTAL_FRAMES} frames in {elapsed:.1f}s) | probe={json.dumps(probe)}")
    return target


if __name__ == "__main__":
    render_gameplay_layer()
