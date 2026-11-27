"""Story-Causal & Zero-Waste Beat-Sheet Pre-Render Contract (v2).

Enforces narrative causality and antislop rules BEFORE any heavy render:
1. Concrete `visual_subject` per beat (bans generic dark-tech 3D blobs/neon grids without real subject).
2. Explicit one-line `narrative_purpose` and `broll_justification` for every cutaway/B-roll.
3. Spoken/on-screen copy checked against antislop-copywriting rules (zero em/en dashes or AI buzzwords).
4. Causal audio linking: every sound_cues item MUST specify `visual_cause` (exact on-screen action
   producing the sound) OR explicit `contrast_rule` (`silent_ab_proof`, `room_tone_bed`,
   `music_dip_transition`, `emotional_realism_contrast`).
5. Asymmetric shot pacing (shot CV >= 0.20 when >= 3 beats) & dynamic contrast pockets (>= 8s).
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any

import numpy as np

VALID_PROFILES = {
    "mograph-pro",
    "gaming-montage",
    "gaming-comedic",
    "talking-head-reel",
    "promo-editorial",
    "cinematic-doc",
    "narrative-film",
    "cinematic-essay",
    "podcast-collage-short",
    "creator-editorial",
    "kinetic-reel-typography",
}

VALID_PALETTES = {
    "editorial-clean",
    "kinetic-street",
    "organic-cinema",
    "comedic-dry",
    "gaming-montage",
}

VALID_AUDIT_PROFILES = {
    "narrative_voice_film",
    "mograph_sfx",
    "cinematic_essay",
    "podcast_collage_short",
}

VALID_SHOT_TYPES = {
    "a_roll",
    "b_roll",
    "kinetic_card",
    "tactile_diagram",
    "ui_demo",
    "silence_contrast",
    "visual_proof",
    "collage_card",
    "letterbox_cinema",
    "match_cut_split",
    "freeze_roto",
    "clean_plate_grow",
    "narrative_cluster",
    "camera_2d_typo",
    "explainer_diagram",
    "chapter_slam",
}

VALID_PLATFORMS = {
    "universal_vertical",
    "yt_shorts",
    "tiktok",
    "ig_reels",
    "youtube_16x9",
}

OPPOSING_MOTION_PAIRS = {
    ("pan_left", "pan_right"),
    ("pan_right", "pan_left"),
    ("push_in", "pull_out"),
    ("pull_out", "push_in"),
    ("tilt_up", "tilt_down"),
    ("tilt_down", "tilt_up"),
}

VALID_CONTRAST_RULES = {
    "silent_ab_proof",
    "room_tone_bed",
    "music_dip_transition",
    "emotional_realism_contrast",
}

BANNED_BUZZWORDS = (
    "revolutionary",
    "seamless",
    "cutting-edge",
    "next-level",
    "ai-powered",
    "game-changer",
    "game changer",
    "elevate",
    "unlock the power",
    "supercharge",
    "effortless",
    "in today's fast-paced",
    "let's dive in",
)

BANNED_ABSTRACT_SLOP = (
    "wireframe prism",
    "amber prism",
    "octahedron",
    "floating cube",
    "neon orb",
    "glowing sphere",
    "cyberpunk grid",
    "abstract polygon",
)

FORBIDDEN_DASHES = ("\u2014", "\u2013")


def _check_clean_copy(text: str, field_name: str, errors: list[str], warnings: list[str] | None = None) -> None:
    if not text:
        return
    for dash in FORBIDDEN_DASHES:
        if dash in text:
            errors.append(f"antislop R-02 violation in {field_name}: contains forbidden unicode dash ({repr(dash)})")
    lower = text.lower()
    for word in BANNED_BUZZWORDS:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            errors.append(f"antislop R-16 violation in {field_name}: contains banned buzzword '{word}'")
    if warnings is not None:
        if re.search(r"\bnot just\b.{2,45}\bit'?s\b", lower) or re.search(r"\bbukan (hanya|sekadar)\b.{2,45}\bmelainkan\b", lower):
            warnings.append(f"antislop-copywriting warning in {field_name}: negative parallelism cliche detected.")


def validate_beat_sheet(
    sheet: dict[str, Any],
    *,
    strict_cv: bool = True,
    require_silence_over_s: float = 8.0,
) -> dict[str, Any]:
    """Validate story causality, visual subject concreteness, and SFX motivation."""
    errors: list[str] = []
    warnings: list[str] = []

    title = str(sheet.get("title", "")).strip()
    if not title:
        errors.append("Missing top-level 'title'.")
    _check_clean_copy(title, "title", errors)

    profile = sheet.get("profile")
    if profile not in VALID_PROFILES:
        errors.append(f"Invalid 'profile' ({profile}); expected one of {sorted(VALID_PROFILES)}.")

    palette = sheet.get("sound_palette")
    if palette not in VALID_PALETTES:
        errors.append(f"Invalid 'sound_palette' ({palette}); expected one of {sorted(VALID_PALETTES)}.")

    audit_profile = sheet.get("audio_audit_profile", "narrative_voice_film")
    if audit_profile not in VALID_AUDIT_PROFILES:
        errors.append(f"Invalid 'audio_audit_profile' ({audit_profile}); expected {sorted(VALID_AUDIT_PROFILES)}.")

    beats = sheet.get("beats", [])
    if not isinstance(beats, list) or not beats:
        errors.append("'beats' must be a non-empty list.")
        return {"ok": False, "errors": errors, "warnings": warnings, "metrics": {}}

    durations: list[float] = []
    prev_end = -1.0
    for idx, beat in enumerate(beats):
        bid = str(beat.get("id", f"beat_{idx}"))
        t0 = float(beat.get("t_start", -1))
        t1 = float(beat.get("t_end", -1))
        if t0 < 0 or t1 <= t0:
            errors.append(f"Beat '{bid}' has invalid time span [{t0}, {t1}].")
        if idx > 0 and t0 < prev_end - 0.05:
            warnings.append(f"Beat '{bid}' overlaps prior beat end by {prev_end - t0:.2f}s.")
        prev_end = max(prev_end, t1)
        durations.append(max(0.0, t1 - t0))

        stype = beat.get("shot_type")
        if stype not in VALID_SHOT_TYPES:
            errors.append(f"Beat '{bid}' invalid shot_type '{stype}'.")

        visual_subj = str(beat.get("visual_subject", "")).strip()
        if len(visual_subj) < 8:
            errors.append(
                f"Story causality gate failed on '{bid}': missing concrete 'visual_subject' (footage clip, UI screen, or physical object)."
            )
        else:
            low_sub = visual_subj.lower()
            for slop_term in BANNED_ABSTRACT_SLOP:
                if slop_term in low_sub:
                    errors.append(
                        f"antislop R-22 violation on '{bid}': abstract placeholder visual '{slop_term}' without concrete story subject."
                    )

        purpose = str(beat.get("narrative_purpose", "")).strip()
        if len(purpose) < 12:
            errors.append(f"Zero-waste gate failed on '{bid}': 'narrative_purpose' too vague or missing.")
        _check_clean_copy(purpose, f"{bid}.narrative_purpose", errors)

        if stype == "b_roll":
            just = str(beat.get("broll_justification", "")).strip()
            if len(just) < 12:
                errors.append(
                    f"Zero-waste B-roll gate failed on '{bid}': b_roll requires 'broll_justification' proving why it isn't filler."
                )
            _check_clean_copy(just, f"{bid}.broll_justification", errors)

        on_screen = beat.get("on_screen_copy", "")
        if isinstance(on_screen, list):
            for ci, line in enumerate(on_screen):
                _check_clean_copy(str(line), f"{bid}.on_screen_copy[{ci}]", errors, warnings)
        else:
            _check_clean_copy(str(on_screen), f"{bid}.on_screen_copy", errors, warnings)

        audio_intent = beat.get("audio_intent", {})
        if not isinstance(audio_intent, dict) or not str(audio_intent.get("strategy", "")).strip():
            errors.append(f"Beat '{bid}' missing explicit audio_intent.strategy.")

    # Monotony anti-slop guard: reject 4+ consecutive identical shot_type + near-identical duration
    if len(beats) >= 4:
        streak = 1
        for idx in range(1, len(beats)):
            same_type = beats[idx].get("shot_type") == beats[idx - 1].get("shot_type")
            same_dur = abs(durations[idx] - durations[idx - 1]) < 0.08
            streak = streak + 1 if (same_type and same_dur) else 1
            if streak >= 4:
                errors.append(
                    f"Rhythm monotony failure at '{beats[idx].get('id')}': 4+ consecutive identical shot_type & duration beats."
                )
                break

    # Gaku Lange Flow-of-Motion check: warn when opposing motion vectors collide without static_reset palate cleanser
    for idx in range(1, len(beats)):
        mv_prev = str(beats[idx - 1].get("motion_vector", "")).strip()
        mv_curr = str(beats[idx].get("motion_vector", "")).strip()
        if mv_prev and mv_curr and (mv_prev, mv_curr) in OPPOSING_MOTION_PAIRS:
            warnings.append(
                f"Flow-of-Motion clash between '{beats[idx - 1].get('id')}' ({mv_prev}) and '{beats[idx].get('id')}' ({mv_curr}): insert a 'static_reset' palate cleanser or match direction."
            )

    # Herman Huang Transition Restraint check: warn when >55% of beats use flashy non-hard transitions
    if len(beats) >= 5:
        flashy = sum(1 for b in beats if str(b.get("transition_in", "")).strip().lower() not in ("", "hard", "cut", "none"))
        if flashy / len(beats) > 0.55:
            warnings.append(
                f"Transition restraint warning: {flashy}/{len(beats)} beats use stylized transitions (>55%); reserve transitions for earned chapter shifts."
            )

    # Platform target check
    target_plat = sheet.get("target_platform")
    if target_plat and target_plat not in VALID_PLATFORMS:
        errors.append(f"Invalid target_platform '{target_plat}'. Must be one of {sorted(VALID_PLATFORMS)}.")

    # Context-aware Narrative Typography Balance check (RhVB8WPLJAI / BWRdNeNkph4):
    # - Never forces hype highlights on quiet cinematic-essay beats.
    # - Warns if 3+ consecutive text-heavy beats in explanatory/short profiles have zero emphasis/visual mode.
    # - Warns against highlight OVERUSE (>60% of words highlighted in a beat ruins hierarchy!).
    plain_text_streak = 0
    for beat in beats:
        bid = str(beat.get("id", "beat"))
        raw_copy = beat.get("on_screen_copy", "")
        copy_str = " ".join(str(x) for x in raw_copy) if isinstance(raw_copy, list) else str(raw_copy or "")
        words = [w for w in re.split(r"\s+", re.sub(r"<[^>]+>", "", copy_str).strip()) if w]
        emph = beat.get("emphasis_words") or []
        if isinstance(emph, str):
            emph = [emph]
        has_visual_typo = bool(
            emph
            or beat.get("typography_mode")
            or beat.get("shot_type") in ("narrative_cluster", "camera_2d_typo", "explainer_diagram", "chapter_slam", "tactile_diagram", "collage_card")
            or ("<em>" in copy_str or "<span" in copy_str)
        )
        if len(words) >= 5 and len(emph) / len(words) > 0.60:
            warnings.append(
                f"Typography highlight overuse on '{bid}': {len(emph)}/{len(words)} words highlighted (>60%); highlight only 1-2 key anchor words."
            )
        if profile in ("creator-editorial", "podcast-collage-short", "kinetic-reel-typography") and len(words) >= 6 and not has_visual_typo:
            plain_text_streak += 1
            if plain_text_streak == 3:
                warnings.append(
                    f"Flat text warning around '{bid}': 3+ consecutive text-heavy beats lack emphasis_words or visual typography_mode."
                )
        else:
            plain_text_streak = 0

    total_dur = max((float(b.get("t_end", 0)) for b in beats), default=0.0)
    shot_cv = float(np.std(durations) / max(np.mean(durations), 1e-6)) if len(durations) >= 3 else 0.0
    if len(durations) >= 3 and shot_cv < 0.20:
        msg = f"Rhythm check failed: shot length CV is {shot_cv:.2f} (< 0.20 implies uniform PPT cadence)."
        if strict_cv:
            errors.append(msg)
        else:
            warnings.append(msg)

    pockets = sheet.get("silence_pockets", [])
    has_silence_beat = any(b.get("shot_type") == "silence_contrast" for b in beats)
    valid_pockets = [p for p in pockets if float(p.get("t1", 0)) - float(p.get("t0", 0)) >= 0.22]
    if total_dur >= require_silence_over_s and not (valid_pockets or has_silence_beat):
        errors.append(
            f"Dynamic contrast gate failed: timeline is {total_dur:.1f}s (>= {require_silence_over_s}s) without any silence_pockets (>= 0.22s) or silence_contrast beat."
        )

    cues = sheet.get("sound_cues", [])
    for ci, cue in enumerate(cues):
        cid = str(cue.get("id", f"cue_{ci}"))
        if cue.get("raw_sine") or cue.get("tone_hz"):
            errors.append(f"Sound anti-slop failure on '{cid}': raw sine wave beeps are forbidden.")

        vis_cause = str(cue.get("visual_cause", "")).strip()
        contrast_rule = cue.get("contrast_rule")
        if not vis_cause and contrast_rule not in VALID_CONTRAST_RULES:
            errors.append(
                f"Audio causality failure on '{cid}': SFX requires concrete 'visual_cause' naming what moves/acts on screen, or valid 'contrast_rule'."
            )

        layers = cue.get("layers", [])
        intensity = cue.get("intensity", "normal")
        if intensity == "hero" and len(layers) < 2:
            errors.append(
                f"Spectrum layering gate failed on hero cue '{cid}': dramatic hits/whooshes require >= 2 frequency layers."
            )
        cue_profile = cue.get("palette")
        if cue_profile and cue_profile != palette and cue_profile != "universal-room":
            if not cue.get("emotional_realism_note"):
                errors.append(
                    f"Sound coherence gate failed on '{cid}': palette '{cue_profile}' clashes with '{palette}' without an 'emotional_realism_note'."
                )
        for li, lay in enumerate(layers):
            role = lay.get("spectrum_role")
            if role and role not in ("sub_low", "mid_body", "high_air", "full_spectrum", "room_bed"):
                errors.append(f"Invalid spectrum_role '{role}' in '{cid}.layers[{li}]'.")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "total_duration_s": round(total_dur, 3),
            "beat_count": len(beats),
            "shot_cv": round(shot_cv, 3),
            "silence_pockets_count": len(valid_pockets),
            "hero_cues_count": sum(1 for c in cues if c.get("intensity") == "hero"),
            "causal_sfx_count": sum(1 for c in cues if str(c.get("visual_cause", "")).strip()),
        },
    }


def validate_beat_sheet_file(path: str | pathlib.Path) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return validate_beat_sheet(data)


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Validate an AGY studio beat_sheet JSON file.")
    ap.add_argument("beat_sheet")
    args = ap.parse_args()
    res = validate_beat_sheet_file(args.beat_sheet)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["ok"] else 1)
