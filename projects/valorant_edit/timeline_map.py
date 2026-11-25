"""Deterministic single source of truth for the Valorant Harbor 3K vertical edit.

All video frame sampling, audio time-remapping, precision censoring, camera motion,
optical effects, Reyna magnifying loupe projection, and kinetic HTML/SVG subtitles
consume this module so A/V and pixel overlays stay locked to 0 ms / 0 px drift.
"""
from __future__ import annotations

import json
import math
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = ROOT / "projects" / "valorant_edit"
SOURCE_CLIP_PATH = pathlib.Path(r"D:\Clip\Valorant\Valorant 2026.11.25 - 01.10.25.02.DVR.mp4")

# User-specified render/output root on Drive D:
OUTPUT_ROOT = pathlib.Path(r"D:\Clip\Edit\Valorant")
WORK_DIR = OUTPUT_ROOT / "work"
QA_DIR = OUTPUT_ROOT / "qa"
FINAL_MP4_PATH = OUTPUT_ROOT / "valorant_harbor_3k_vertical.mp4"

SRC_W = 1366
SRC_H = 768
OUT_W = 1080
OUT_H = 1920
FPS = 60

# Exact verified pixel coordinates in 1366x768 source frame at src_t = 71.75s
CHAMBER_SRC_XY = (674.0, 376.0)
REYNA_SRC_XY = (698.0, 356.0)
LOUPE_CANVAS_XY = (760.0, 620.0)
LOUPE_RADIUS_PX = 172
LOUPE_ZOOM_FACTOR = 4.2

# Exact clean Valorant killfeed crop rectangles (free of Client FPS graphs)
KILLFEED_REYNA_RECT = (995, 94, 1354, 119)
KILLFEED_DOUBLE_RECT = (988, 94, 1354, 148)
KILLFEED_DEST_X = 126
KILLFEED_DEST_Y = 248

# Exact verified source window for "anjing" profanity censor (50ms voice-band verified)
CENSOR_SRC_SPAN = (55.04, 55.58)

# Raw piecewise time segments covering exact 45.00s..75.00s source footage
_RAW_SEGMENTS: list[dict[str, Any]] = [
    {"id": "b01_hook", "beat_id": "b01_hook", "src0": 45.00, "src1": 47.40, "speed": 1.00, "is_freeze": False},
    {"id": "b02_mid_chaos", "beat_id": "b02_mid_chaos", "src0": 47.40, "src1": 51.00, "speed": 1.45, "is_freeze": False},
    {"id": "b03_comms_bleep", "beat_id": "b03_comms_bleep", "src0": 51.00, "src1": 55.65, "speed": 1.00, "is_freeze": False},
    {"id": "b04a_pre", "beat_id": "b04_kill1_sova", "src0": 55.65, "src1": 57.02, "speed": 1.00, "is_freeze": False},
    {"id": "b04b_hitstop", "beat_id": "b04_kill1_sova", "src0": 57.02, "src1": 57.32, "speed": 0.45, "is_freeze": False},
    {"id": "b04c_recover", "beat_id": "b04_kill1_sova", "src0": 57.32, "src1": 58.10, "speed": 1.00, "is_freeze": False},
    {"id": "b05a_glide", "beat_id": "b05_nice_comms", "src0": 58.10, "src1": 59.90, "speed": 1.25, "is_freeze": False},
    {"id": "b05b_nice", "beat_id": "b05_nice_comms", "src0": 59.90, "src1": 61.60, "speed": 1.00, "is_freeze": False},
    {"id": "b06_velocity_whip", "beat_id": "b06_velocity_whip", "src0": 61.60, "src1": 67.60, "speed": 2.15, "is_freeze": False},
    {"id": "b07a_aish", "beat_id": "b07_arch_stalk", "src0": 67.60, "src1": 70.30, "speed": 1.35, "is_freeze": False},
    {"id": "b07b_stalk", "beat_id": "b07_arch_stalk", "src0": 70.30, "src1": 71.75, "speed": 1.00, "is_freeze": False},
    {"id": "b08_lucky_freeze", "beat_id": "b08_lucky_freeze", "src0": 71.75, "src1": 71.75, "speed": 0.00, "is_freeze": True, "freeze_dur": 1.75},
    {"id": "b09a_live", "beat_id": "b09_kill3_drop", "src0": 71.75, "src1": 72.12, "speed": 1.00, "is_freeze": False},
    {"id": "b09b_hitstop", "beat_id": "b09_kill3_drop", "src0": 72.12, "src1": 72.32, "speed": 0.45, "is_freeze": False},
    {"id": "b09c_recover", "beat_id": "b09_kill3_drop", "src0": 72.32, "src1": 72.60, "speed": 1.00, "is_freeze": False},
    {"id": "b10_gila_outro", "beat_id": "b10_gila_outro", "src0": 72.60, "src1": 75.00, "speed": 1.00, "is_freeze": False},
]


def _build_segments() -> list[dict[str, Any]]:
    built: list[dict[str, Any]] = []
    cursor = 0.0
    for seg in _RAW_SEGMENTS:
        if seg["is_freeze"]:
            dur = float(seg["freeze_dur"])
        else:
            dur = (float(seg["src1"]) - float(seg["src0"])) / float(seg["speed"])
        item = {
            **seg,
            "out0": round(cursor, 6),
            "out1": round(cursor + dur, 6),
            "dur": round(dur, 6),
        }
        built.append(item)
        cursor += dur
    return built


TIME_SEGMENTS: list[dict[str, Any]] = _build_segments()
TOTAL_DURATION_S: float = round(TIME_SEGMENTS[-1]["out1"], 6)
TOTAL_FRAMES: int = int(round(TOTAL_DURATION_S * FPS))


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    if abs(edge1 - edge0) < 1e-9:
        return 1.0 if x >= edge1 else 0.0
    u = _clamp01((x - edge0) / (edge1 - edge0))
    return u * u * (3.0 - 2.0 * u)


def _ease_out_expo(u: float) -> float:
    u = _clamp01(u)
    return 1.0 if u >= 1.0 else 1.0 - math.pow(2.0, -10.0 * u)


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def map_out_to_src(out_t: float) -> dict[str, Any]:
    """Map an output timestamp [0, TOTAL_DURATION_S] to exact source time and metadata."""
    t = max(0.0, min(TOTAL_DURATION_S, float(out_t)))
    for seg in TIME_SEGMENTS:
        if t <= seg["out1"] + 1e-9:
            span = max(1e-9, seg["dur"])
            local_u = _clamp01((t - seg["out0"]) / span)
            if seg["is_freeze"]:
                src_t = seg["src0"]
            else:
                src_t = seg["src0"] + local_u * (seg["src1"] - seg["src0"])
            return {
                "src_t": round(src_t, 6),
                "speed": seg["speed"],
                "is_freeze": seg["is_freeze"],
                "segment_id": seg["id"],
                "beat_id": seg["beat_id"],
                "local_u": round(local_u, 6),
            }
    last = TIME_SEGMENTS[-1]
    return {
        "src_t": last["src1"],
        "speed": last["speed"],
        "is_freeze": False,
        "segment_id": last["id"],
        "beat_id": last["beat_id"],
        "local_u": 1.0,
    }


def map_src_to_out(src_t: float, *, after_freeze: bool = False) -> float:
    """Map a source clip timestamp [45.0, 75.0] to exact output timeline seconds."""
    s = max(45.0, min(75.0, float(src_t)))
    for seg in TIME_SEGMENTS:
        if seg["is_freeze"]:
            if abs(s - seg["src0"]) < 1e-6:
                return seg["out1"] if after_freeze else seg["out0"]
            continue
        if seg["src0"] - 1e-9 <= s <= seg["src1"] + 1e-9:
            if abs(s - 71.75) < 1e-6 and after_freeze and seg["id"] == "b07b_stalk":
                continue
            span = max(1e-9, seg["src1"] - seg["src0"])
            u = _clamp01((s - seg["src0"]) / span)
            return round(seg["out0"] + u * seg["dur"], 6)
    return TOTAL_DURATION_S


# Exact computed milestone output times derived straight from source events
CENSOR_OUT_T0 = map_src_to_out(CENSOR_SRC_SPAN[0])
CENSOR_OUT_T1 = map_src_to_out(CENSOR_SRC_SPAN[1])
KILL1_OUT_T = map_src_to_out(57.05)
KNIFE_WHIP_OUT_T = map_src_to_out(66.15)
FREEZE_OUT_T0 = next(s["out0"] for s in TIME_SEGMENTS if s["id"] == "b08_lucky_freeze")
FREEZE_OUT_T1 = next(s["out1"] for s in TIME_SEGMENTS if s["id"] == "b08_lucky_freeze")
FREEZE_PHASE_B_T = round(FREEZE_OUT_T0 + 0.75, 4)
KILL3_OUT_T = map_src_to_out(72.15, after_freeze=True)

SILENCE_POCKETS: list[dict[str, Any]] = [
    {
        "id": "pocket_bleep_censor",
        "t0": round(CENSOR_OUT_T0 - 0.03, 3),
        "t1": round(CENSOR_OUT_T1 + 0.04, 3),
        "fade_ms": 18.0,
        "duck_music_db": -52.0,
        "duck_ambience_db": -16.0,
        "duck_transitions_db": -46.0,
    },
    {
        "id": "pocket_reyna_lucky_freeze",
        "t0": round(FREEZE_OUT_T0, 3),
        "t1": round(FREEZE_OUT_T1, 3),
        "fade_ms": 22.0,
        "duck_music_db": -54.0,
        "duck_ambience_db": -14.0,
        "duck_transitions_db": -48.0,
    },
]

# Verified comms subtitles + comedic freeze callouts (zero em/en dashes, safe-zone y=1440)
SUBTITLE_CUES: list[dict[str, Any]] = [
    {
        "id": "sub_ini_to",
        "t0": round(map_src_to_out(46.15), 3),
        "t1": round(map_src_to_out(47.20), 3),
        "text": "Ini To!",
        "style": "normal",
        "anim": "apple_follower",
        "y_px": 1445,
    },
    {
        "id": "sub_wooo",
        "t0": round(map_src_to_out(49.15), 3),
        "t1": round(map_src_to_out(50.25), 3),
        "text": "WOOO!",
        "style": "emphasis",
        "anim": "pop_overshoot",
        "y_px": 1430,
    },
    {
        "id": "sub_mana_backup",
        "t0": round(map_src_to_out(53.45), 3),
        "t1": round(CENSOR_OUT_T0 - 0.03, 3),
        "text": "To, mana backup-nya To,",
        "style": "normal",
        "anim": "apple_follower",
        "y_px": 1445,
    },
    {
        "id": "sub_censor_bleep",
        "t0": round(CENSOR_OUT_T0 - 0.02, 3),
        "t1": round(CENSOR_OUT_T1 + 0.16, 3),
        "text": "an***g!",
        "style": "scream",
        "anim": "censor_shake",
        "y_px": 1425,
    },
    {
        "id": "sub_sova_ult",
        "t0": round(map_src_to_out(55.92), 3),
        "t1": round(KILL1_OUT_T - 0.05, 3),
        "text": "I AM THE HUNTER!",
        "style": "sova_alert",
        "anim": "apple_follower",
        "y_px": 1455,
    },
    {
        "id": "sub_kiri_nice",
        "t0": round(map_src_to_out(58.45), 3),
        "t1": round(map_src_to_out(60.75), 3),
        "text": "Kiri, kiri... Nice!",
        "style": "emphasis",
        "anim": "apple_follower",
        "y_px": 1445,
    },
    {
        "id": "sub_headshot_tuh",
        "t0": round(map_src_to_out(60.85), 3),
        "t1": round(map_src_to_out(61.95), 3),
        "text": "Headshot tuh.",
        "style": "normal",
        "anim": "apple_follower",
        "y_px": 1445,
    },
    {
        "id": "sub_aish",
        "t0": round(map_src_to_out(68.20), 3),
        "t1": round(map_src_to_out(69.50), 3),
        "text": "Aish!",
        "style": "emphasis",
        "anim": "pop_overshoot",
        "y_px": 1435,
    },
    {
        "id": "sub_freeze_chamber",
        "t0": round(FREEZE_OUT_T0 + 0.05, 3),
        "t1": round(FREEZE_PHASE_B_T - 0.02, 3),
        "text": "Niatnya nembak Chamber...",
        "style": "deadpan_serif",
        "anim": "apple_follower",
        "y_px": 1445,
    },
    {
        "id": "sub_freeze_reyna",
        "t0": round(FREEZE_PHASE_B_T, 3),
        "t1": round(FREEZE_OUT_T1, 3),
        "text": "EH REYNA DI BELAKANG IKUT KENA?!",
        "style": "lucky_punch",
        "anim": "pop_overshoot",
        "y_px": 1430,
    },
    {
        "id": "sub_gila_to",
        "t0": round(map_src_to_out(72.85, after_freeze=True), 3),
        "t1": round(TOTAL_DURATION_S - 0.12, 3),
        "text": "Wuh! Eh, gila To!!",
        "style": "hype_echo",
        "anim": "ghost_echo",
        "y_px": 1430,
    },
]


def _pulse(t: float, t0: float, t1: float) -> float:
    if t < t0 or t > t1:
        return 0.0
    u = _clamp01((t - t0) / max(1e-6, t1 - t0))
    return math.sin(u * math.pi)


def get_camera_state(out_t: float) -> dict[str, Any]:
    """Evaluate deterministic dynamic 9:16 crop center, zoom, impact shake, dimming, and optical FX."""
    t = max(0.0, min(TOTAL_DURATION_S, float(out_t)))
    cx = SRC_W * 0.5  # 683.0
    cy = SRC_H * 0.5  # 384.0
    zoom = 1.00
    shake_x = 0.0
    shake_y = 0.0
    dim = 1.0
    desat = 0.0
    effect: str | None = None
    effect_u = 0.0

    # Opening hook subtle pull-out (1.06 -> 1.00)
    if t < 1.20:
        zoom = _lerp(1.06, 1.00, _ease_out_expo(t / 1.20))

    # Snap-zoom on "WOOO!" gasp
    wooo_t = map_src_to_out(49.25)
    if wooo_t <= t <= wooo_t + 0.55:
        p = _pulse(t, wooo_t, wooo_t + 0.55)
        zoom = max(zoom, 1.0 + 0.13 * p)
        shake_x += 7.0 * math.sin(t * 78.0) * p

    # Comedic snap-zoom + tension tighten on censored "an***g!"
    if CENSOR_OUT_T0 - 0.04 <= t <= CENSOR_OUT_T1 + 0.14:
        p = _pulse(t, CENSOR_OUT_T0 - 0.04, CENSOR_OUT_T1 + 0.14)
        zoom = max(zoom, 1.0 + 0.20 * (p ** 0.65))
        shake_x += 10.0 * math.sin(t * 95.0) * p
        shake_y += 6.0 * math.cos(t * 112.0) * p

    # Kill #1 (51m ADS HS through Sova ult): slight left-shifted pan to show blue ult beam + OpticalRadialMatch
    if KILL1_OUT_T - 0.55 <= t <= KILL1_OUT_T + 0.85:
        p_pan = _pulse(t, KILL1_OUT_T - 0.55, KILL1_OUT_T + 0.85)
        cx = _lerp(cx, 648.0, p_pan)
    if KILL1_OUT_T - 0.02 <= t <= KILL1_OUT_T + 0.34:
        u = _clamp01((t - (KILL1_OUT_T - 0.02)) / 0.36)
        effect = "optical_radial_match"
        effect_u = u
        decay = math.exp(-5.5 * u)
        zoom = max(zoom, 1.0 + 0.16 * math.sin(u * math.pi))
        shake_x += 15.0 * math.sin(u * 36.0) * decay
        shake_y += 11.0 * math.cos(u * 42.0) * decay

    # Xenohunter Knife Whip transition during velocity ramp
    if KNIFE_WHIP_OUT_T - 0.14 <= t <= KNIFE_WHIP_OUT_T + 0.18:
        u = _clamp01((t - (KNIFE_WHIP_OUT_T - 0.14)) / 0.32)
        effect = "motion_tile_whip"
        effect_u = u

    # Arch stalk slow push-in toward Chamber & arch opening before freeze
    b07b_t0 = next(s["out0"] for s in TIME_SEGMENTS if s["id"] == "b07b_stalk")
    if b07b_t0 <= t < FREEZE_OUT_T0:
        u = _smoothstep(b07b_t0, FREEZE_OUT_T0, t)
        cx = _lerp(683.0, 665.0, u)
        cy = _lerp(384.0, 376.0, u)
        zoom = _lerp(1.00, 1.15, u)

    # Signature Freeze-Frame (b08_lucky_freeze): locked exact camera framing for pixel-true loupe & arrows
    if FREEZE_OUT_T0 <= t <= FREEZE_OUT_T1:
        cx = 665.0
        cy = 376.0
        zoom = 1.15
        u_in = _smoothstep(FREEZE_OUT_T0, FREEZE_OUT_T0 + 0.12, t)
        u_out = 1.0 - _smoothstep(FREEZE_OUT_T1 - 0.08, FREEZE_OUT_T1, t)
        env = u_in * u_out
        dim = _lerp(1.0, 0.56, env)
        desat = _lerp(0.0, 0.48, env)

    # Post-freeze live snap + Kill #3 Chamber HS FlashCutoutStrobe + impact punch
    if FREEZE_OUT_T1 < t <= KILL3_OUT_T + 0.55:
        u_rel = _smoothstep(FREEZE_OUT_T1, KILL3_OUT_T + 0.55, t)
        cx = _lerp(665.0, 683.0, u_rel)
        cy = _lerp(376.0, 384.0, u_rel)
        zoom = _lerp(1.15, 1.02, u_rel)
    if KILL3_OUT_T - 0.01 <= t <= KILL3_OUT_T + 0.28:
        u = _clamp01((t - (KILL3_OUT_T - 0.01)) / 0.29)
        effect = "flash_cutout_strobe"
        effect_u = u
        decay = math.exp(-6.0 * u)
        zoom = max(zoom, 1.08 + 0.14 * math.sin(u * math.pi))
        shake_x += 18.0 * math.sin(u * 40.0) * decay
        shake_y += 14.0 * math.cos(u * 46.0) * decay

    # Final outro gentle settle showing Jett stepping out on the left
    b10_t0 = next(s["out0"] for s in TIME_SEGMENTS if s["id"] == "b10_gila_outro")
    if t >= b10_t0:
        u = _smoothstep(b10_t0, TOTAL_DURATION_S, t)
        cx = _lerp(683.0, 645.0, u)
        zoom = _lerp(1.04, 1.00, u)

    return {
        "cx": round(cx, 4),
        "cy": round(cy, 4),
        "zoom": round(zoom, 5),
        "shake_x": round(shake_x, 3),
        "shake_y": round(shake_y, 3),
        "dim": round(dim, 4),
        "desat": round(desat, 4),
        "effect": effect,
        "effect_u": round(effect_u, 5),
    }


def get_crop_box(out_t: float) -> tuple[float, float, float, float, float]:
    """Return exact (left, top, crop_w, crop_h, eff_scale) in source coordinates for out_t."""
    cam = get_camera_state(out_t)
    base_scale = OUT_H / float(SRC_H)  # 2.5
    eff_scale = base_scale * cam["zoom"]
    crop_w = OUT_W / eff_scale
    crop_h = OUT_H / eff_scale
    left = max(0.0, min(SRC_W - crop_w, cam["cx"] - crop_w * 0.5))
    top = max(0.0, min(SRC_H - crop_h, cam["cy"] - crop_h * 0.5))
    return left, top, crop_w, crop_h, eff_scale


def project_source_to_canvas(src_x: float, src_y: float, out_t: float) -> tuple[float, float]:
    """Project an exact 1366x768 source pixel (src_x, src_y) onto 1080x1920 canvas pixels."""
    cam = get_camera_state(out_t)
    left, top, _, _, eff_scale = get_crop_box(out_t)
    x_canvas = (float(src_x) - left) * eff_scale + cam["shake_x"]
    y_canvas = (float(src_y) - top) * eff_scale + cam["shake_y"]
    return round(x_canvas, 2), round(y_canvas, 2)


def export_stage_config(path: str | pathlib.Path | None = None) -> pathlib.Path:
    """Export unified JSON timing & pixel projection config for overlay_stage.html."""
    target = pathlib.Path(path) if path else (WORK_DIR / "stage_config.json")
    target.parent.mkdir(parents=True, exist_ok=True)

    freeze_mid = round(0.5 * (FREEZE_OUT_T0 + FREEZE_OUT_T1), 4)
    chamber_xy = project_source_to_canvas(*CHAMBER_SRC_XY, freeze_mid)
    reyna_xy = project_source_to_canvas(*REYNA_SRC_XY, freeze_mid)

    cfg = {
        "width": OUT_W,
        "height": OUT_H,
        "fps": FPS,
        "duration_s": TOTAL_DURATION_S,
        "total_frames": TOTAL_FRAMES,
        "milestones": {
            "censor_t0": CENSOR_OUT_T0,
            "censor_t1": CENSOR_OUT_T1,
            "kill1_t": KILL1_OUT_T,
            "knife_whip_t": KNIFE_WHIP_OUT_T,
            "freeze_t0": FREEZE_OUT_T0,
            "freeze_phase_b_t": FREEZE_PHASE_B_T,
            "freeze_t1": FREEZE_OUT_T1,
            "kill3_t": KILL3_OUT_T,
        },
        "chamber": {
            "src_xy": list(CHAMBER_SRC_XY),
            "target_canvas_xy": list(chamber_xy),
            "phase_a_t0": FREEZE_OUT_T0,
            "phase_a_t1": FREEZE_OUT_T1,
        },
        "loupe": {
            "src_xy": list(REYNA_SRC_XY),
            "target_canvas_xy": list(reyna_xy),
            "center_xy": list(LOUPE_CANVAS_XY),
            "radius_px": LOUPE_RADIUS_PX,
            "zoom_factor": LOUPE_ZOOM_FACTOR,
            "t0": FREEZE_PHASE_B_T,
            "t1": FREEZE_OUT_T1,
        },
        "killfeed_dest": {
            "x": KILLFEED_DEST_X,
            "y": KILLFEED_DEST_Y,
            "single_t0": FREEZE_PHASE_B_T,
            "double_t0": KILL3_OUT_T,
            "end_t": round(TOTAL_DURATION_S - 0.15, 3),
        },
        "subtitles": SUBTITLE_CUES,
        "silence_pockets": SILENCE_POCKETS,
    }
    target.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return target


if __name__ == "__main__":
    p = export_stage_config()
    print(f"STAGE_CONFIG_OK: {p} | duration={TOTAL_DURATION_S:.3f}s ({TOTAL_FRAMES} frames)")
    print(f"Milestones: censor=[{CENSOR_OUT_T0:.3f},{CENSOR_OUT_T1:.3f}] kill1={KILL1_OUT_T:.3f} freeze=[{FREEZE_OUT_T0:.3f},{FREEZE_OUT_T1:.3f}] kill3={KILL3_OUT_T:.3f}")
