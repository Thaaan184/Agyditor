"""Context-Adaptive Editorial Style Matrix & Auto-Router (Class-Up v4).

Routes any video brief or named profile to its empirically calibrated editorial spec
derived from 21 analyzed reference films (Luda, Gaku Lange, Herman Huang, Maciek Sulima,
marksoy, Jacob Nordin, Andrew, Multiply Sound, Faide, Windah, MILYHYA).

Core principle: Never force one loudness target, visual ground, or pacing template onto
mismatched genres. Every style locks its own framing, pacing rhythm, color grade,
typography hierarchy, transition restraint, and audio loudness/LRA window.
"""
from __future__ import annotations

import json
import re
from typing import Any

CONTEXT_PROFILES: dict[str, dict[str, Any]] = {
    "cinematic-essay": {
        "reference_creators": ["Luda (NFm2Xjx61Q8, g_UpY8VNwa0)", "Jacob Nordin (I66_LmOTlSk)"],
        "dials": {"ENERGY": 1, "RHYTHM": 3, "MOTION": 2},
        "aspect_defaults": {"landscape": "2.39:1_anamorphic_in_16x9", "vertical": "rounded_letterbox_in_9x16"},
        "pacing": {
            "cuts_per_min_range": [4.0, 15.0],
            "median_shot_s": [1.8, 9.5],
            "shot_cv_min": 0.45,
            "transition_restraint_max_ratio": 0.25,
            "rule": "Let contemplative holds breathe (5-10s) contrasted with tight montage clusters (1.5-2.0s). Avoid flashy plugin wipes.",
        },
        "color_grade": {
            "preset": "luda_filmic_warm",
            "halation": True,
            "vignette": True,
            "clean_plate_before_gfx": True,
        },
        "typography": {
            "caption_style": "luda_bare_crimson_micro",
            "chapter_style": "edge_micro_act_tag",
            "behind_subject_titles": True,
            "palette": ["#000000", "#F5F5F5", "#DC2626"],
        },
        "audio": {
            "audit_profile": "cinematic_essay",
            "sound_palette": "organic-cinema",
            "target_lufs": -19.5,
            "lra_target_lu": [6.0, 12.0],
            "tonal_sfx_key_match": True,
            "music_guidance": "Sparse intimate piano, strings, or ambient score matching emotional seasons; prefer real context song over synthetic pad.",
        },
    },
    "podcast-collage-short": {
        "reference_creators": ["marksoy (MoVlt-ptxIk)"],
        "dials": {"ENERGY": 3, "RHYTHM": 3, "MOTION": 3},
        "aspect_defaults": {"landscape": "16x9", "vertical": "9x16"},
        "pacing": {
            "cuts_per_min_range": [10.0, 20.0],
            "median_shot_s": [1.5, 3.5],
            "shot_cv_min": 0.35,
            "transition_restraint_max_ratio": 0.45,
            "rule": "Alternate clean talking-head speaker with full-bleed mixed-media collage cards every 1.5-3.2s directly on spoken emphasis.",
        },
        "color_grade": {
            "preset": "collage_punch_clean",
            "halation": False,
            "vignette": False,
            "clean_plate_before_gfx": True,
        },
        "typography": {
            "caption_style": "minimal_lowercase_speaker_plus_collage_cards",
            "collage_themes": ["cream_serif", "cobalt_grid", "newspaper_circle", "dark_highlighter"],
            "palette": ["#ECEAD8", "#0B1A8A", "#DC2626", "#18181B"],
        },
        "audio": {
            "audit_profile": "podcast_collage_short",
            "sound_palette": "kinetic-street",
            "target_lufs": -11.0,
            "lra_target_lu": [2.2, 4.0],
            "tonal_sfx_key_match": True,
            "music_guidance": "Tight modern groove or trending short-form beat ducked under crisp foreground vocal.",
        },
    },
    "creator-editorial": {
        "reference_creators": [
            "Gaku Lange (EWqrpI1IAyI, RAWhQycgvNY, SmsNAtaLR9I)",
            "Herman Huang (FZS0olGLPIw)",
            "Andrew (pdLEHfkwgV8)",
        ],
        "dials": {"ENERGY": 2, "RHYTHM": 3, "MOTION": 3},
        "aspect_defaults": {"landscape": "16x9", "vertical": "9x16"},
        "pacing": {
            "cuts_per_min_range": [8.0, 22.0],
            "median_shot_s": [1.7, 3.8],
            "shot_cv_min": 0.40,
            "transition_restraint_max_ratio": 0.35,
            "rule": "Show first, explain second. Cut on motion (motion-to-motion) along matched directional vectors; insert neutral palate cleansers before direction shifts.",
        },
        "color_grade": {
            "preset": "gaku_filmic_teal",
            "halation": True,
            "vignette": True,
            "clean_plate_before_gfx": True,
        },
        "typography": {
            "caption_style": "tactile_editorial_plus_social_bubbles",
            "overlays": ["cutting_mat", "nle_wave_badges", "music_dip_ui", "social_bubble"],
            "palette": ["#F4EFE6", "#1B3B2B", "#18181B", "#22C55E", "#D97706"],
        },
        "audio": {
            "audit_profile": "narrative_voice_film",
            "sound_palette": "organic-cinema",
            "target_lufs": -15.5,
            "lra_target_lu": [2.5, 5.5],
            "tonal_sfx_key_match": True,
            "music_guidance": "Warm lo-fi/editorial groove matching topic energy; dip music cleanly into transitions rather than hard chopping.",
        },
    },
    "kinetic-reel-typography": {
        "reference_creators": ["Maciek Sulima (yRsK2JyfMGM)"],
        "dials": {"ENERGY": 3, "RHYTHM": 3, "MOTION": 3},
        "aspect_defaults": {"landscape": "16x9", "vertical": "9x16"},
        "pacing": {
            "cuts_per_min_range": [6.0, 18.0],
            "median_shot_s": [1.4, 4.0],
            "shot_cv_min": 0.30,
            "transition_restraint_max_ratio": 0.40,
            "rule": "Split one S-curve across outgoing (accelerate out) and incoming (decelerate in) text elements along a single predictable axis.",
        },
        "color_grade": {
            "preset": "editorial_tungsten_clean",
            "halation": False,
            "vignette": True,
            "clean_plate_before_gfx": True,
        },
        "typography": {
            "caption_style": "maciek_asymmetric_3tier",
            "motion_primitive": "splitSCurveHandoff",
            "palette": ["#FAF7F0", "#F59E0B", "#18181B"],
        },
        "audio": {
            "audit_profile": "narrative_voice_film",
            "sound_palette": "editorial-clean",
            "target_lufs": -15.0,
            "lra_target_lu": [2.5, 4.8],
            "tonal_sfx_key_match": True,
            "music_guidance": "Clean rhythmic underscore or trending Reel track locked to typography swap beats.",
        },
    },
    "narrative-film": {
        "reference_creators": ["Andrew (pdLEHfkwgV8)", "Herman Huang (tzfzkTAQsnE)"],
        "dials": {"ENERGY": 2, "RHYTHM": 3, "MOTION": 2},
        "aspect_defaults": {"landscape": "16x9", "vertical": "9x16"},
        "pacing": {
            "cuts_per_min_range": [8.0, 20.0],
            "median_shot_s": [1.2, 4.0],
            "shot_cv_min": 0.25,
            "transition_restraint_max_ratio": 0.35,
            "rule": "Causal storytelling with honest A/B sound proof, physical craft cards, and NLE waveform strips.",
        },
        "color_grade": {
            "preset": "editorial_tungsten_clean",
            "halation": False,
            "vignette": True,
            "clean_plate_before_gfx": True,
        },
        "typography": {
            "caption_style": "tactile_craft_pill",
            "palette": ["#F4EFE6", "#1B3B2B", "#18181B", "#22C55E"],
        },
        "audio": {
            "audit_profile": "narrative_voice_film",
            "sound_palette": "organic-cinema",
            "target_lufs": -16.0,
            "lra_target_lu": [2.5, 6.8],
            "tonal_sfx_key_match": True,
            "music_guidance": "Context-matched musical bed carved around dialogue with Great Hall exits.",
        },
    },
    "gaming-montage": {
        "reference_creators": ["Faide"],
        "dials": {"ENERGY": 3, "RHYTHM": 3, "MOTION": 3},
        "aspect_defaults": {"landscape": "16x9", "vertical": "wide_fov_blurred_fill_9x16"},
        "pacing": {
            "cuts_per_min_range": [18.0, 45.0],
            "median_shot_s": [0.8, 2.2],
            "shot_cv_min": 0.25,
            "transition_restraint_max_ratio": 0.50,
            "rule": "Velocity speed-ramps locked to song beat onsets; box-less minimal callouts only on climax.",
        },
        "color_grade": {
            "preset": "neutral_rec709",
            "halation": False,
            "vignette": False,
            "clean_plate_before_gfx": True,
        },
        "typography": {
            "caption_style": "rolling_slot_boxless_hit",
            "palette": ["#F8FAFC", "#F59E0B"],
        },
        "audio": {
            "audit_profile": "mograph_sfx",
            "sound_palette": "gaming-montage",
            "target_lufs": -14.0,
            "lra_target_lu": [2.4, 5.0],
            "tonal_sfx_key_match": True,
            "music_guidance": "High-energy song chosen by user/context drives every velocity ramp and kill hit.",
        },
    },
    "gaming-comedic": {
        "reference_creators": ["Windah Basudara", "MILYHYA"],
        "dials": {"ENERGY": 3, "RHYTHM": 3, "MOTION": 2},
        "aspect_defaults": {"landscape": "16x9", "vertical": "wide_fov_blurred_fill_9x16"},
        "pacing": {
            "cuts_per_min_range": [14.0, 35.0],
            "median_shot_s": [1.0, 3.0],
            "shot_cv_min": 0.25,
            "transition_restraint_max_ratio": 0.30,
            "rule": "Cut-and-play around dead air, sudden BGM hard-cut before punchlines, expressive snap-zooms.",
        },
        "color_grade": {
            "preset": "neutral_rec709",
            "halation": False,
            "vignette": False,
            "clean_plate_before_gfx": True,
        },
        "typography": {
            "caption_style": "ghost_echo_or_apple_safezone",
            "palette": ["#F8FAFC", "#FACC15", "#EF4444"],
        },
        "audio": {
            "audit_profile": "narrative_voice_film",
            "sound_palette": "comedic-dry",
            "target_lufs": -15.5,
            "lra_target_lu": [2.8, 6.0],
            "tonal_sfx_key_match": False,
            "music_guidance": "Light comedic BGM with explicit silence pockets before punchlines and single dry stinger.",
        },
    },
}

_KEYWORD_ROUTING: list[tuple[str, tuple[str, ...]]] = [
    ("cinematic-essay", ("essay", "dokumenter", "documentary", "film pendek", "short film", "luda", "monolog", "storytelling sinematik", "cinematic", "reflective", "anamorphic", "letterbox")),
    ("podcast-collage-short", ("podcast", "collage", "kolase", "clipping", "marksoy", "interview clip", "diary of a ceo", "koran", "newspaper", "mixed media")),
    ("kinetic-reel-typography", ("kinetic", "typography", "tipografi", "maciek", "reels caption", "animated title", "judul gerak", "split s-curve")),
    ("gaming-comedic", ("windah", "milyhya", "lucu", "komedi", "comedic", "funny gaming", "troll")),
    ("gaming-montage", ("montage", "faide", "clutch", "valorant", "apex", "frag", "highlight game", "velocity")),
    ("creator-editorial", ("tutorial", "breakdown", "youtube", "gaku", "herman", "edukasi", "explainer", "review", "workflow", "vlog")),
]


def route_context(brief_or_profile: str, *, aspect: str | None = None) -> dict[str, Any]:
    """Select the highest-fit editorial profile and concrete studio settings for any request."""
    raw = (brief_or_profile or "").strip()
    key = raw.lower()
    chosen = "creator-editorial"
    reason = "Defaulted to creator-editorial balanced storytelling baseline."

    if key in CONTEXT_PROFILES:
        chosen = key
        reason = f"Exact profile match '{key}'."
    else:
        best_hits = 0
        for profile_name, kws in _KEYWORD_ROUTING:
            hits = sum(1 for kw in kws if re.search(rf"\b{re.escape(kw)}\b", key))
            if hits > best_hits:
                best_hits = hits
                chosen = profile_name
                reason = f"Matched {hits} context signal(s) for '{profile_name}'."

    spec = json.loads(json.dumps(CONTEXT_PROFILES[chosen]))
    spec["profile"] = chosen
    spec["routing_reason"] = reason
    if aspect:
        spec["selected_aspect"] = aspect
    return spec


def list_profiles() -> list[str]:
    return list(CONTEXT_PROFILES.keys())


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Route a video brief to its calibrated AGY editorial context.")
    ap.add_argument("brief", nargs="?", default="cinematic documentary essay")
    ap.add_argument("--aspect", default=None)
    args = ap.parse_args()
    print(json.dumps(route_context(args.brief, aspect=args.aspect), indent=2))
