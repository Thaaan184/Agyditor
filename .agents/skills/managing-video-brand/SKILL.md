---
name: managing-video-brand
description: >-
  Provides the single source of truth for video brand identity, motion dials (ENERGY, RHYTHM, MOTION),
  typography, color tokens, and skill/SFX routing across WeftCut Motifs, HyperFrames compositions, OneTake films,
  Three.js 3D scenes, Barty-Bart sound/explainer packs, claude-shorts, ghost-editor, and motion-video-director.
  Use whenever planning a video, styling subtitles, authoring Motifs, or composing scenes.
---

# Managing Video Brand & Anti-Slop Dials

## When to use this skill
- Before designing any motion graphic, WeftCut Motif overlay, HyperFrames/Three.js composition, OneTake film, or dynamic subtitle style.
- When configuring `antislop` dials (`ENERGY`, `RHYTHM`, `MOTION`) for a new video project or preset.

## Workflow
1. Read [resources/video-design-tokens.json](resources/video-design-tokens.json) for active color palettes, local bundled `@font-face` font files (`studio_kit/fonts/`), Mixed-Voice typography ratios, and calibrated curves (`studio_kit/motion_primitives.js`).
2. Select or auto-route the target editorial context via `studio_kit/context_router.py` and [resources/style-profiles.md](resources/style-profiles.md):
   - `cinematic-essay` (`Luda` / `Jacob Nordin`): `2.39:1` or vertical rounded-letterbox in `#000000` with bare crimson micro captions, `luda_filmic_warm` + halation clean-plate grade, wide dynamic range (`-19.5 LUFS`, `LRA 6-12 LU`), key-matched tonal drones/hits.
   - `podcast-collage-short` (`marksoy`): Punchy `-11 LUFS` vertical cuts alternating clean talking head with mixed-media collage cards (`cream_serif`, `cobalt_grid`, `newspaper_circle`, `dark_highlighter`).
   - `creator-editorial` (`Gaku Lange` / `Herman Huang` / `Andrew`): Show-First `-15.5 LUFS` breakdowns, Flow-of-Motion directional cuts, Transition Restraint, `gaku_filmic_teal` clean-plate grade, cutting mat, NLE waveforms, and organic social bubbles.
   - `kinetic-reel-typography` (`Maciek Sulima`): `splitSCurveHandoff` single-axis handoffs + 3-tier asymmetric captions (`lead` / `HERO` / `tail`).
   - `narrative-film`: Show-first storytelling anchored in natural footage, craft paper/cutting-mat diagrams, and authentic NLE waveform strips via `studio_kit/narrative_composer.py`.
   - `mograph-pro`: Continuous kinetic editorial (`ENERGY 2`, `RHYTHM 3`, `MOTION 3`) via OneTake, HyperFrames, Three.js (`threejs-*`), and `studio_kit/motifs/kinetic-3d-spatial`.
   - `gaming-montage` & `gaming-comedic` (`Faide` / `Windah` / `MILYHYA`): Beat-synced velocity ramps or cut-and-play sudden BGM cut-outs via WeftCut MCP + `claude-shorts` + starter Motifs.
   - `talking-head-reel` & `promo-editorial`: Vertical talking-head / reel layouts (`ghost-editor` + `motion-video-director` 100% free local audio override).
3. Verify every visual and audio choice against the active profile (`references/transitions_study/TRANSITIONS_GUIDE.md`, `references/text_motion_study/TEXT_MOTION_GUIDE.md`, `references/sound_cinematography_study/SOUND_CINEMA_ARCHITECTURE.md`, `references/editorial_classup_study/EDITORIAL_CLASSUP_GUIDE.md`, and `references/narrative_typography_study/NARRATIVE_TYPOGRAPHY_SAFEZONE_GUIDE.md`) and document a one-line reason per `antislop` R-31. Keep every vertical overlay inside `studio_kit/safe_zones.py` (`universal_vertical`: `top >= 13.5%`, `bottom <= 70.2%`, `right <= 83.0%`) and `16:9` inside `youtube_16x9`, pick context-fit narrative typography (`narrative_cluster`, `camera_2d_canvas`, or `explainer_visual_diagram` without `>60%` highlight overuse or unrequested loud text on quiet cinema), never default to unrequested dark-carbon neon grids or abstract 3D blobs when footage or tactile surfaces tell the story better, ensure zero fallback to Windows system fonts (`Segoe UI`), enable `180-360` deg shutter/directional blur on rapid text moves, validate `studio_kit/beat_sheet.py` (`visual_subject`, `visual_cause`, zero-waste B-roll) before rendering, mix audio across the 5-stem `studio_kit/sound_engine.py` (room-tone bed, 3-band spectrum stacking, adaptive voice carving, Great Hall tails, silence pockets), pass `studio_kit/acoustic_audit.py` under the matching profile (`cinematic_essay`, `podcast_collage_short`, `narrative_voice_film`, or `mograph_sfx`), inspect peak-motion contact sheets + `audio_arc`, never place web app navigation bars inside a frame, and never require paid voiceover APIs.
