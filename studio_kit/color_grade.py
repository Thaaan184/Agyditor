"""Open-Source Filmic Color Grading Engine for AGY Local Video Studio.

Implements the exact filmic grading workflow empirically studied from Gaku Lange
(-14_cGVgV20 HSV Channel-2 Density, f31-WqH7izk 8-Step Filmic Stack, PuoI9paASys
Clean-Plate Separation) and Luda (NFm2Xjx61Q8 Dehancer-style warm highlights /
cool shadows / lifted black floor):

1. Clean-Plate Rule: Grade base camera footage FIRST, then overlay crisp motion
   graphics & typography on top so text never gets tinted or blurred by halation.
2. HSV Channel-2 Gain ("Subtractive Film Density"): Raises HSV Saturation channel
   while gently deepening high-saturation value (luminance), producing rich filmic
   reds & teals instead of neon RGB clipping.
3. Filmic S-Curve + Lifted Black Floor (L5 ~ 4.5-7.0) + Soft Highlight Shoulder.
4. Split-Tone Shadows (cool teal/cyan) vs Highlights (warm amber/tungsten) +
   subtle green-axis magenta reduction.
5. Fast 33x33x33 standard .cube 3D LUT export for real-time FFmpeg `lut3d` filtering
   plus optional warm red-orange Halation bloom & lens edge vignette.
"""
from __future__ import annotations

import pathlib
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
LUT_DIR = ROOT / "studio_kit" / "luts"

GRADE_PRESETS: dict[str, dict[str, Any]] = {
    "luda_filmic_warm": {
        "description": "Anamorphic Dehancer-inspired film grade: lifted matte blacks (L5~5), true cyan-teal deep shadows, warm golden highlights, protected skin midtones, subtractive HSV density, specular-only halation.",
        "black_lift": 0.024,
        "highlight_rolloff": 0.92,
        "contrast": 1.13,
        "pivot": 0.45,
        "hsv_sat_gain": 1.16,
        "subtractive_density": 0.12,
        "reduce_magenta": 0.014,
        "shadow_tint_rgb": (-0.016, 0.010, 0.016),
        "highlight_tint_rgb": (0.028, 0.016, -0.024),
        "halation_strength": 0.11,
        "vignette_angle": "PI/4.8",
    },
    "gaku_filmic_teal": {
        "description": "Gaku Lange filmic Tokyo/street grade: HSV Ch-2 density boost, reduced magenta, crisp Kodak teal shadows, warm amber highlights, subtle specular halation.",
        "black_lift": 0.020,
        "highlight_rolloff": 0.94,
        "contrast": 1.16,
        "pivot": 0.45,
        "hsv_sat_gain": 1.20,
        "subtractive_density": 0.14,
        "reduce_magenta": 0.020,
        "shadow_tint_rgb": (-0.022, 0.012, 0.020),
        "highlight_tint_rgb": (0.022, 0.012, -0.020),
        "halation_strength": 0.10,
        "vignette_angle": "PI/5.4",
    },
    "editorial_tungsten_clean": {
        "description": "Balanced creator/studio look: warm tungsten skin & practical highlights, gentle lifted shadows, natural color density without heavy cast.",
        "black_lift": 0.018,
        "highlight_rolloff": 0.96,
        "contrast": 1.09,
        "pivot": 0.46,
        "hsv_sat_gain": 1.10,
        "subtractive_density": 0.08,
        "reduce_magenta": 0.012,
        "shadow_tint_rgb": (-0.006, 0.002, 0.010),
        "highlight_tint_rgb": (0.022, 0.008, -0.018),
        "halation_strength": 0.0,
        "vignette_angle": "PI/6.0",
    },
    "collage_punch_clean": {
        "description": "Crisp short-form interview look (marksoy reference): snappy midtone contrast, clean neutral whites, light HSV density boost, zero soft haze.",
        "black_lift": 0.008,
        "highlight_rolloff": 0.99,
        "contrast": 1.14,
        "pivot": 0.47,
        "hsv_sat_gain": 1.12,
        "subtractive_density": 0.05,
        "reduce_magenta": 0.008,
        "shadow_tint_rgb": (0.0, 0.0, 0.004),
        "highlight_tint_rgb": (0.008, 0.004, -0.004),
        "halation_strength": 0.0,
        "vignette_angle": None,
    },
    "neutral_rec709": {
        "description": "Clean Rec.709 pass-through with subtle safety toe/shoulder for gaming or screen recordings.",
        "black_lift": 0.0,
        "highlight_rolloff": 1.0,
        "contrast": 1.0,
        "pivot": 0.5,
        "hsv_sat_gain": 1.0,
        "subtractive_density": 0.0,
        "reduce_magenta": 0.0,
        "shadow_tint_rgb": (0.0, 0.0, 0.0),
        "highlight_tint_rgb": (0.0, 0.0, 0.0),
        "halation_strength": 0.0,
        "vignette_angle": None,
    },
}


def _rgb_to_hsv_vec(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin

    h = np.zeros_like(cmax)
    mask = delta > 1e-7
    rm = mask & (cmax == r)
    gm = mask & (cmax == g) & (~rm)
    bm = mask & (~rm) & (~gm)
    h[rm] = ((g[rm] - b[rm]) / delta[rm]) % 6.0
    h[gm] = ((b[gm] - r[gm]) / delta[gm]) + 2.0
    h[bm] = ((r[bm] - g[bm]) / delta[bm]) + 4.0
    h = (h / 6.0) % 1.0

    s = np.where(cmax > 1e-7, delta / np.maximum(cmax, 1e-7), 0.0)
    return h, s, cmax


def _hsv_to_rgb_vec(h: np.ndarray, s: np.ndarray, v: np.ndarray) -> np.ndarray:
    h6 = (h % 1.0) * 6.0
    i = np.floor(h6).astype(np.int32)
    f = h6 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))

    i_mod = i % 6
    r = np.select([i_mod == 0, i_mod == 1, i_mod == 2, i_mod == 3, i_mod == 4, i_mod == 5], [v, q, p, p, t, v])
    g = np.select([i_mod == 0, i_mod == 1, i_mod == 2, i_mod == 3, i_mod == 4, i_mod == 5], [t, v, v, q, p, p])
    b = np.select([i_mod == 0, i_mod == 1, i_mod == 2, i_mod == 3, i_mod == 4, i_mod == 5], [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1)


def apply_grade_array(rgb01: np.ndarray, preset_name: str) -> np.ndarray:
    """Apply the filmic grade math (S-curve + split-tone + HSV Ch-2 density) to [0..1] RGB array."""
    cfg = GRADE_PRESETS[preset_name]
    x = np.clip(rgb01.astype(np.float64), 0.0, 1.0)

    # 1. Filmic S-curve contrast around pivot + highlight roll-off + lifted matte black floor
    c = float(cfg["contrast"])
    piv = float(cfg["pivot"])
    if abs(c - 1.0) > 1e-4:
        # Smooth sigmoidal toe/shoulder contrast
        centered = x - piv
        curved = piv + centered * c / (1.0 + np.abs(centered) * (c - 1.0) * 0.85)
        x = np.clip(curved, 0.0, 1.0)

    # Soft shoulder compression above 0.72
    roll = float(cfg["highlight_rolloff"])
    if roll < 0.999:
        hi = np.maximum(0.0, x - 0.72)
        x = np.where(x > 0.72, 0.72 + hi * (roll - 0.72) / 0.28, x)

    # Lifted black toe
    lift = float(cfg["black_lift"])
    if lift > 0.0:
        x = lift + x * (1.0 - lift)

    # 2. White balance magenta reduction (slight emerald-green counterbalance)
    rm = float(cfg["reduce_magenta"])
    if rm > 0.0:
        x[..., 1] = np.clip(x[..., 1] + rm * (1.0 - np.abs(x[..., 1] - 0.5) * 1.4), 0.0, 1.0)

    # 3. Split-tone: non-overlapping deep shadow (<0.36) vs bright highlight (>0.56) so skin midtones stay pure
    lum = 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
    sh_w = np.clip(1.0 - lum / 0.36, 0.0, 1.0) ** 2.0
    hi_w = np.clip((lum - 0.56) / 0.44, 0.0, 1.0) ** 1.8
    sh_t = np.array(cfg["shadow_tint_rgb"], dtype=np.float64)
    hi_t = np.array(cfg["highlight_tint_rgb"], dtype=np.float64)
    x = np.clip(x + sh_w[..., None] * sh_t + hi_w[..., None] * hi_t, 0.0, 1.0)

    # 4. Gaku HSV Channel-2 Gain ("Subtractive Film Density")
    sat_gain = float(cfg["hsv_sat_gain"])
    sub_den = float(cfg["subtractive_density"])
    if abs(sat_gain - 1.0) > 1e-4 or sub_den > 1e-4:
        h, s, v = _rgb_to_hsv_vec(x)
        # Protect extreme highlights & deep blacks slightly from chromatic noise
        sat_protect = np.clip(v * 2.5, 0.0, 1.0) * np.clip((1.05 - v) * 2.5, 0.35, 1.0)
        s_new = np.clip(s * (1.0 + (sat_gain - 1.0) * sat_protect), 0.0, 1.0)
        # Subtractive film density: saturated colors absorb light & become deeper rather than glowing neon
        v_new = np.clip(v * (1.0 - sub_den * (s_new ** 1.4) * (1.0 - 0.35 * v)), 0.0, 1.0)
        x = _hsv_to_rgb_vec(h, s_new, v_new)

    return np.clip(x, 0.0, 1.0)


def generate_cube_lut(preset_name: str, out_path: pathlib.Path | None = None, *, size: int = 33) -> pathlib.Path:
    """Export a standard Adobe/FFmpeg .cube 3D LUT for real-time FFmpeg lut3d filtering."""
    if preset_name not in GRADE_PRESETS:
        raise ValueError(f"Unknown color grade preset '{preset_name}'. Choose from {list(GRADE_PRESETS)}")
    LUT_DIR.mkdir(parents=True, exist_ok=True)
    target = out_path or (LUT_DIR / f"{preset_name}.cube")

    lin = np.linspace(0.0, 1.0, size, dtype=np.float64)
    # .cube order: R varies fastest, then G, then B
    b_grid, g_grid, r_grid = np.meshgrid(lin, lin, lin, indexing="ij")
    rgb = np.stack([r_grid, g_grid, b_grid], axis=-1).reshape(-1, 3)
    graded = apply_grade_array(rgb, preset_name)

    lines = [
        f'TITLE "{preset_name}"',
        f"LUT_3D_SIZE {size}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]
    lines.extend(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}" for row in graded)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def ensure_all_luts() -> dict[str, pathlib.Path]:
    return {name: generate_cube_lut(name) for name in GRADE_PRESETS}


def _escape_ffmpeg_path(p: pathlib.Path) -> str:
    # Escape Windows drive colon and slashes safely for FFmpeg filter options
    return str(p.resolve()).replace("\\", "/").replace(":", "\\:")


def build_ffmpeg_grade_chain(
    preset_name: str,
    *,
    in_label: str = "base_raw",
    out_label: str = "base",
    enable_halation: bool | None = None,
    enable_vignette: bool | None = None,
) -> str:
    """Return an FFmpeg filtergraph segment grading clean video BEFORE motion graphics overlay."""
    if preset_name not in GRADE_PRESETS:
        raise ValueError(f"Unknown color grade preset '{preset_name}'")
    cfg = GRADE_PRESETS[preset_name]
    lut_path = LUT_DIR / f"{preset_name}.cube"
    if not lut_path.exists():
        generate_cube_lut(preset_name, lut_path)

    use_hal = (float(cfg["halation_strength"]) > 0.01) if enable_halation is None else bool(enable_halation)
    use_vig = (cfg["vignette_angle"] is not None) if enable_vignette is None else bool(enable_vignette)
    esc = _escape_ffmpeg_path(lut_path)

    if preset_name == "neutral_rec709" and not use_hal and not use_vig:
        return f"[{in_label}]null[{out_label}]"

    parts: list[str] = []
    cur = f"{in_label}_lut"
    parts.append(f"[{in_label}]format=rgb24,lut3d=file='{esc}'[{cur}]")

    if use_hal:
        hal_op = max(0.05, min(0.22, float(cfg["halation_strength"]) or 0.12))
        # Keep entire halation branch strictly in planar RGB (gbrp) so zero pixels never shift YUV chroma!
        parts.append(
            f"[{cur}]format=gbrp,split=2[{cur}_main][{cur}_hi];"
            f"[{cur}_hi]lutrgb=r='if(gt(val,208),min(255,(val-208)*4.5),0)':g='if(gt(val,216),min(255,(val-216)*1.9),0)':b='0',"
            f"format=gbrp,gblur=sigma=12[{cur}_bloom];"
            f"[{cur}_main][{cur}_bloom]blend=all_mode=screen:all_opacity={hal_op:.2f}[{cur}_hal]"
        )
        cur = f"{cur}_hal"

    vig_str = f",vignette=angle={cfg['vignette_angle'] or 'PI/5.2'}" if use_vig else ""
    parts.append(f"[{cur}]format=yuv420p{vig_str}[{out_label}]")
    return ";".join(parts)


if __name__ == "__main__":
    paths = ensure_all_luts()
    for k, v in paths.items():
        print(f"GENERATED LUT: {k:26s} -> {v.relative_to(ROOT)} ({v.stat().st_size} bytes)")
