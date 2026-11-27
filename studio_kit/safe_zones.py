"""Platform UI Safe-Zone Guard & DOM Collision Auditor for AGY Local Video Studio.

Prevents captions, narrative typography, waveform pills, or CTAs from being buried
behind native platform chrome on YouTube Shorts, TikTok, Instagram Reels, or YouTube 16:9.

Coordinates are expressed in normalized [0..1] viewport fractions so rules scale
identically across 1080x1920, 540x960 previews, and 1920x1080 landscape renders.
"""
from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw

# Normalized danger zones (x0, y0, x1, y1) representing native platform UI overlays
PLATFORM_DANGER_ZONES: dict[str, dict[str, Any]] = {
    "yt_shorts": {
        "aspect": "9x16",
        "safe_box": {"left": 0.055, "right": 0.843, "top": 0.115, "bottom": 0.771},
        "zones": [
            {"name": "top_nav", "box": (0.0, 0.0, 1.0, 0.115)},
            {"name": "right_action_rail", "box": (0.843, 0.435, 1.0, 0.880)},
            {"name": "bottom_meta_bar", "box": (0.0, 0.771, 1.0, 1.0)},
        ],
    },
    "tiktok": {
        "aspect": "9x16",
        "safe_box": {"left": 0.055, "right": 0.833, "top": 0.130, "bottom": 0.708},
        "zones": [
            {"name": "top_nav", "box": (0.0, 0.0, 1.0, 0.130)},
            {"name": "right_action_rail", "box": (0.833, 0.405, 1.0, 0.865)},
            {"name": "bottom_caption_bar", "box": (0.0, 0.708, 1.0, 1.0)},
        ],
    },
    "ig_reels": {
        "aspect": "9x16",
        "safe_box": {"left": 0.055, "right": 0.843, "top": 0.125, "bottom": 0.719},
        "zones": [
            {"name": "top_header", "box": (0.0, 0.0, 1.0, 0.125)},
            {"name": "right_action_rail", "box": (0.843, 0.520, 1.0, 0.885)},
            {"name": "bottom_handle_bar", "box": (0.0, 0.719, 1.0, 1.0)},
        ],
    },
    "universal_vertical": {
        "aspect": "9x16",
        # Strict union safe zone across YT Shorts + TikTok + IG Reels simultaneously!
        "safe_box": {"left": 0.055, "right": 0.830, "top": 0.135, "bottom": 0.702},
        "zones": [
            {"name": "top_platform_header", "box": (0.0, 0.0, 1.0, 0.135)},
            {"name": "right_action_buttons", "box": (0.830, 0.405, 1.0, 0.885)},
            {"name": "bottom_caption_ui", "box": (0.0, 0.702, 1.0, 1.0)},
        ],
    },
    "youtube_16x9": {
        "aspect": "16x9",
        "safe_box": {"left": 0.060, "right": 0.940, "top": 0.080, "bottom": 0.885},
        "zones": [
            {"name": "top_hover_title", "box": (0.0, 0.0, 1.0, 0.080)},
            {"name": "bottom_player_scrubber", "box": (0.0, 0.885, 1.0, 1.0)},
        ],
    },
}

DEFAULT_AUDIT_SELECTORS = [
    "#speaker-pill",
    "#ab-corner",
    "#wave-anchor",
    "#nle-track-box",
    "#luda-micro-cap",
    "#luda-act-tag",
    "#maciek-anchor",
    "#social-anchor",
    "#narrative-cluster-box",
    "#explainer-content-box",
]


def _overlap_area(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ix0 = max(a[0], b[0])
    iy0 = max(a[1], b[1])
    ix1 = min(a[2], b[2])
    iy1 = min(a[3], b[3])
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    return (ix1 - ix0) * (iy1 - iy0)


def check_rect_against_platform(
    rect_px: dict[str, float],
    width: int,
    height: int,
    *,
    platform: str = "universal_vertical",
    tolerance_px: float = 4.0,
) -> dict[str, Any]:
    """Check a single DOM bounding box {x, y, width, height} against platform UI danger zones."""
    spec = PLATFORM_DANGER_ZONES.get(platform)
    if not spec:
        raise ValueError(f"Unknown platform '{platform}'. Choose from {list(PLATFORM_DANGER_ZONES)}")

    w_el = max(0.0, float(rect_px.get("width", 0.0)))
    h_el = max(0.0, float(rect_px.get("height", 0.0)))
    if w_el < 2.0 or h_el < 2.0:
        return {"safe": True, "violations": []}

    # Shrink by tiny anti-aliasing tolerance
    x0 = (float(rect_px["x"]) + tolerance_px) / max(1, width)
    y0 = (float(rect_px["y"]) + tolerance_px) / max(1, height)
    x1 = (float(rect_px["x"]) + w_el - tolerance_px) / max(1, width)
    y1 = (float(rect_px["y"]) + h_el - tolerance_px) / max(1, height)
    el_box = (x0, y0, x1, y1)
    el_area = max(1e-9, (x1 - x0) * (y1 - y0))

    violations: list[dict[str, Any]] = []
    for z in spec["zones"]:
        ov = _overlap_area(el_box, z["box"])
        if ov > 0.0:
            pct = round(100.0 * ov / el_area, 1)
            if pct >= 1.5:
                violations.append({
                    "zone": z["name"],
                    "overlap_pct": pct,
                    "element_norm": [round(v, 3) for v in el_box],
                })

    # Edge-clip check (left/right margin safety)
    sb = spec["safe_box"]
    if x0 < sb["left"] - 0.015:
        violations.append({"zone": "left_edge_margin", "overlap_pct": round((sb["left"] - x0) * 100, 1)})
    if x1 > 0.965:
        violations.append({"zone": "right_edge_clip", "overlap_pct": round((x1 - 0.965) * 100, 1)})

    return {"safe": len(violations) == 0, "violations": violations}


def audit_html_safe_zones(
    page: Any,
    timestamps: list[float],
    *,
    width: int,
    height: int,
    platform: str = "universal_vertical",
    selectors: list[str] | None = None,
) -> dict[str, Any]:
    """Run live Playwright bounding-box checks across timeline timestamps to guarantee zero UI overlap."""
    sels = selectors or DEFAULT_AUDIT_SELECTORS
    all_violations: list[dict[str, Any]] = []
    checked_elements = 0

    for t in timestamps:
        page.evaluate("(tt) => window.__seek(tt)", float(t))
        rects = page.evaluate(
            """(selList) => {
                const out = [];
                for (const sel of selList) {
                    const el = document.querySelector(sel);
                    if (!el) continue;
                    // Check element and ancestor layer opacity
                    let cur = el;
                    let visible = true;
                    while (cur && cur !== document.body) {
                        const cs = getComputedStyle(cur);
                        if (parseFloat(cs.opacity) < 0.08 || cs.display === 'none' || cs.visibility === 'hidden') {
                            visible = false;
                            break;
                        }
                        cur = cur.parentElement;
                    }
                    if (!visible) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width > 2 && r.height > 2) {
                        out.push({ selector: sel, x: r.x, y: r.y, width: r.width, height: r.height });
                    }
                }
                return out;
            }""",
            sels,
        )
        for item in rects:
            checked_elements += 1
            chk = check_rect_against_platform(item, width, height, platform=platform)
            if not chk["safe"]:
                all_violations.append({
                    "t_s": round(float(t), 3),
                    "selector": item["selector"],
                    "violations": chk["violations"],
                })

    return {
        "ok": len(all_violations) == 0,
        "platform": platform,
        "checked_elements": checked_elements,
        "violations": all_violations,
    }


def draw_platform_ui_ghost(image: Image.Image, *, platform: str = "universal_vertical") -> Image.Image:
    """Overlay translucent native platform UI ghost chrome & danger bounds for visual proof."""
    spec = PLATFORM_DANGER_ZONES[platform]
    base = image.convert("RGBA")
    w, h = base.size
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # 1. Translucent red danger bands
    for z in spec["zones"]:
        x0, y0, x1, y1 = [int(round(v * d_sz)) for v, d_sz in zip(z["box"], (w, h, w, h))]
        d.rectangle([x0, y0, x1, y1], fill=(220, 38, 38, 42), outline=(248, 113, 113, 150), width=2)

    # 2. Ghost platform icons on 9x16 so viewer literally sees where TikTok/Reels/Shorts UI lives
    if spec["aspect"] == "9x16":
        rx = int(w * 0.915)
        r_rad = max(14, int(w * 0.036))
        for ry_frac, lbl in ((0.47, "LIKE"), (0.55, "CMT"), (0.63, "SHR"), (0.71, "AUD")):
            ry = int(h * ry_frac)
            d.ellipse([rx - r_rad, ry - r_rad, rx + r_rad, ry + r_rad], fill=(255, 255, 255, 55), outline=(255, 255, 255, 130), width=2)
            d.text((rx - 14, ry + r_rad + 3), lbl, fill=(255, 255, 255, 165))
        # Bottom username & caption ghost bars
        bx0 = int(w * 0.06)
        d.rounded_rectangle([bx0, int(h * 0.74), int(w * 0.45), int(h * 0.765)], radius=6, fill=(255, 255, 255, 65))
        d.rounded_rectangle([bx0, int(h * 0.78), int(w * 0.76), int(h * 0.802)], radius=6, fill=(255, 255, 255, 48))
        d.rounded_rectangle([bx0, int(h * 0.815), int(w * 0.62), int(h * 0.835)], radius=6, fill=(255, 255, 255, 42))
        d.text((bx0, int(h * 0.712)), "PLATFORM UI DANGER ZONE (SHORTS / TIKTOK / REELS)", fill=(254, 202, 202, 210))

    # 3. Crisp emerald safe-box border
    sb = spec["safe_box"]
    d.rectangle(
        [int(w * sb["left"]), int(h * sb["top"]), int(w * sb["right"]), int(h * sb["bottom"])],
        outline=(34, 197, 94, 190),
        width=2,
    )
    return Image.alpha_composite(base, ov).convert("RGB")
