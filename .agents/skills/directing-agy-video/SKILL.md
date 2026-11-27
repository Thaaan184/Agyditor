---
name: directing-agy-video
description: >-
  Master end-to-end production runbook and continuous reference-learning protocol for AGY Local Video Studio
  (studio_kit/). Use at the start of any new chat room when planning, editing, grading, sound-designing,
  or rendering videos across 16:9 or 9:16, AND whenever the user shares new YouTube/video editing references
  or style insights to upgrade studio capabilities.
---

# Directing AGY Video Production & Absorbing New Insights

## When to Activate
- **Mode A (Video Production / Editing):** Whenever the user asks to edit raw footage, build a short/reel, produce a long-form explainer or cinematic essay, add captions/motion graphics, or mix sound/color.
- **Mode B (Reference Study / Insight Ingestion):** Whenever the user shares reference links (YouTube, Shorts, Reels, breakdowns) and asks to learn their pacing, transitions, typography, grading, or sound design for future edits.

For the full file index of `studio_kit/` modules, 6 starter Motifs, 5 `.cube` LUTs, 293 indexed SFX assets (CC0, Pixabay, 24 Multiply Sound tonal WAVs, and 120 creator gaming/meme SFX), and v1-v5 study guides, read [references/studio-catalog.md](./references/studio-catalog.md).

---

## Mode A: End-to-End Video Production Runbook

Execute steps strictly in order. Do not skip directly to pixel rendering.

1. **Align Brief (`/grill-me` Light Check):**
   - Clarify missing decisions before cutting: target platform (`universal_vertical`, `yt_shorts`, `tiktok`, `ig_reels`, `youtube_16x9`), narrative arc/mood, footage/music source, and whether the user wants a live WeftCut timeline or direct rendered MP4.
2. **Route Editorial Context (`studio_kit/context_router.py`):**
   - Match the brief to one primary profile (`cinematic-essay`, `podcast-collage-short`, `creator-editorial`, `kinetic-reel-typography`, `narrative-film`, `mograph-pro`, `gaming-montage`, `gaming-comedic`, `talking-head-reel`).
   - Load `.agents/skills/managing-video-brand/SKILL.md` and `DESIGN.md` to lock `ENERGY / RHYTHM / MOTION` dials and font/palette tokens.
3. **Author & Validate Beat Sheet (`studio_kit/beat_sheet.py`):**
   - Draft declarative `beat_sheet.json` with concrete `visual_subject`, `narrative_purpose`, `broll_justification`, `motion_vector`, `transition_in`, `target_platform`, `emphasis_words`/`typography_mode`, `silence_pockets`, and `sound_cues` with explicit `visual_cause` or `contrast_rule`.
   - Validate via `validate_beat_sheet(...)`. Resolve all hard errors and inspect context warnings (Flow-of-Motion clash, Transition Restraint `>55%`, flat text streak on explanatory profiles, or `>60%` highlight overuse).
4. **Audio-First 5-Stem Mix (`studio_kit/sound_engine.py`):**
   - Select real BGM matching context/request (or let clean native game/dialogue audio breathe); NEVER synthesize fake BGM from raw `np.sin` or white-noise loops.
   - Auto-detect musical key (`detect_musical_key`) before placing tonal hits (`add_tonal_sfx`), and strictly avoid tonal/drone overuse that causes buzzing ear fatigue (limit tonal accents to 1-2 brief climax beats). For comedic gaming beats, pick restrained, context-matched accents from `studio_kit/sfx/meme_pack/` (`meme/*`) and `add_filter_sweep` (LPF muffle) instead of clichéd spam.
   - Anchor scenes with filtered `ambience` room-tone bedrock, layer transitions across Sub/Mid/Air (`50-240 ms` pre-lap), carve speech frequencies under voice, use `Great Hall` reverb tails (`T60 = 2.6s`) instead of abrupt music chops, and honor `silence_pockets`.
5. **Clean-Plate Color Grade & Spatial Narrative Typography (`color_grade.py`, `tactile_scene_kit.html`, `safe_zones.py`):**
   - Grade raw footage FIRST via `color_grade.py` (`HSV Ch-2 Density` `.cube` LUT + planar `gbrp` halation when fitting) BEFORE compositing crisp text/UI overlays.
   - Apply **Spatial Typography Topology** rather than parking every line at one static bottom Y coordinate: vary anchors across upper-left (`@wirilett`), directional spatial shifts (`camera_2d_canvas` `-83ms` pre-beat lead), chest-safe `narrative_cluster`, `explainer_visual_diagram`, or raw cropped HUD callouts to mirror emotional pacing.
   - Run live Playwright `safe_zones.audit_html_safe_zones(...)` (`0` collisions required).
6. **Assemble & Render:**
   - Render via `studio_kit/narrative_composer.py`, `WeftCut MCP` (`driving-weftcut`), `OneTake`, or `HyperFrames` using Windows Chrome GPU flags (`--use-gl=angle --use-angle=d3d11 --enable-webgl --ignore-gpu-blocklist`) on drive `D:`.
7. **Dual Verification Before Handoff:**
   - Run `studio_kit/acoustic_audit.py` under the matching loudness/spectral profile.
   - Generate contact sheet + `audio_arc` and visually inspect EVERY proof sheet via `read_file` to catch contrast issues, framing crops, or motion glitches before replying.

---

## Mode B: Absorbing New Editing References & Insights (Continuous Growth)

Whenever the user brings new reference videos or editing tastes in any chat room:

1. **Scope & Clarify:** Confirm which craft dimension to deepen (pacing, transitions, color, sound, typography, B-roll, camera) and whether any rule should be strict vs. context-dependent.
2. **Download & Extract Evidence Locally:**
   - Save study assets under `references/<topic>_study/` using `bin/yt-dlp.exe`, `faster-whisper` (if captions missing), `librosa`/FFmpeg audio stats, and contact sheets (`full`, `dense`, `hook60`, `mid60`).
   - Visually inspect ALL generated contact sheets via `read_file` before writing conclusions. Never invent timestamps or mechanics.
3. **Integrate Into Existing `studio_kit/` (No Orphan Scripts):**
   - Add reusable motion math to `studio_kit/motion_primitives.js` (and sync across all 6 `studio_kit/motifs/*/motion_primitives.js`), camera/shader passes to `keyframe_rig.js`/`optical_stage.js`, overlays to `tactile_scene_kit.html`, routing to `context_router.py`, guards to `beat_sheet.py`/`safe_zones.py`/`acoustic_audit.py`, and audio assets to `sound_palette_index.json`.
4. **Prove Visually & Test:**
   - Render compact proof sheets and inspect them via `read_file`. Fix any visual flaw immediately.
   - Write a clean study guide under `references/<topic>_study/` (if Indonesian, pass `humanizer-indonesia/scripts/metrik.py --preset semiformal` 9/9 `LULUS` with zero em/en dashes).
   - Update [references/studio-catalog.md](./references/studio-catalog.md) and `DESIGN.md` / `video-design-tokens.json` (do NOT bloat `GEMINI.md` with verbose API lists).
   - Add automated regression tests in `tests/test_option_a_stack.py` and confirm `pytest` passes 100%.
