# AGY Local Video Studio: Calibrated Catalog (`studio_kit/` & `references/`)

Read this file on demand whenever you need exact module paths, exported function names, LUT presets, sound packs, Motif folders, or craft study guides without bloating `GEMINI.md`.

---

## 1. Core Python & JS Modules (`studio_kit/`)

| Module | Role & Key Exports |
|---|---|
| `studio_kit/context_router.py` | `route_context(brief)` auto-selects editorial profile (`cinematic-essay`, `podcast-collage-short`, `creator-editorial`, `kinetic-reel-typography`, `narrative-film`, `mograph-pro`, `gaming-montage`, `gaming-comedic`, `talking-head-reel`), loudness target, LUT preset, and typography mode. |
| `studio_kit/beat_sheet.py` | `validate_beat_sheet(sheet)` / `validate_beat_sheet_file(path)`: zero-waste pre-render gate (`visual_subject` anti-placeholder, `narrative_purpose`, `broll_justification`, `visual_cause`/`contrast_rule`, `shot_cv >= 0.20`, `VALID_PLATFORMS`, Flow-of-Motion vector check, Transition Restraint `<=55%`, context-aware flat-text & `>60%` highlight-overuse warnings). |
| `studio_kit/safe_zones.py` | `PLATFORM_DANGER_ZONES` (`yt_shorts`, `tiktok`, `ig_reels`, `universal_vertical`, `youtube_16x9`), `check_rect_against_platform(...)`, live Playwright `audit_html_safe_zones(...)`, and `draw_platform_ui_ghost(...)`. |
| `studio_kit/color_grade.py` | Clean-plate filmic grading BEFORE crisp text overlays. 5 generated `.cube` 3D LUTs in `studio_kit/luts/` (`luda_filmic_warm`, `gaku_filmic_teal`, `editorial_tungsten_clean`, `collage_punch_clean`, `neutral_rec709`) using `HSV Channel-2 Density` + planar RGB (`format=gbrp`) halation via `build_ffmpeg_grade_chain(...)`. |
| `studio_kit/sound_engine.py` | `SoundEngine5Stem`: 5 coherent buses (`voice`, `ambience` room-tone bedrock, tactile `foley`, 2-to-3-layer `transitions`, `music`), shared convolution Room IR (`T60 ~ 1.05s`), `Great Hall` tail exits (`T60 = 2.6s`), 9-band adaptive voice-pocket carving, `detect_musical_key(...)`, `add_tonal_sfx(...)`, `add_filter_sweep(...)`, and `silence_pockets`. |
| `studio_kit/sound_palette_index.json` | Indexed `173` free local audio files (`149` CC0/Pixabay + `24` copyright-free Multiply Sound key-matched tonal WAVs in `studio_kit/sfx/tonal_pack/`) locked across 5 palettes (`editorial-clean`, `kinetic-street`, `organic-cinema`, `comedic-dry`, `gaming-montage`). Rebuilt via `studio_kit/build_sound_index.py`. |
| `studio_kit/acoustic_audit.py` | `audit_media(path, beat_sheet_path, profile)`: post-render spectral & dynamic gate across 4 profiles (`cinematic_essay` `-24..-16.5 LUFS / LRA >= 4.5`, `podcast_collage_short` `-14.5..-8 LUFS`, `narrative_voice_film` `-18.5..-13 LUFS / mud <= 48% / voice >= 18%`, `mograph_sfx` `mud < 35% / detail+air >= 4%`). |
| `studio_kit/motion_primitives.js` | Pure `f(t)` closed-form curves & primitives (`window.AGYMotion` / `require`): `CURVES`, `spring`, `appleFollowerChar`, `ghostEchoPair`, `rollingSlotColumn`, `spatial3DCameraWord`, `foregroundOcclusionWipe`, `cutoutFrameHoldSlide`, `smoothMaskReveal`, `angledSplitZoom`, `splitSCurveHandoff`, `asymmetricCaptionLayout`, `matchCutSplitWipe`, `camera2DTypographyState`, `narrativeClusterWord`, `goldenTypeScale`. Must stay byte-identical across all 6 `studio_kit/motifs/*/motion_primitives.js`. |
| `studio_kit/keyframe_rig.js` | v2 4-axis spatial camera & curve engine (`evalTrack`, `aeWhipOut` ~17% influence, `resolveCameraState` `35mm` DoF, `projectWorldToScreen`, `solveDollyZoomFov`, `buildSpiralWordLayout`, `popOvershootTrack`, `flashStrobeEval`, `toWeftCutLayerPlan`). |
| `studio_kit/optical_stage.js` | Offline GLSL optical passes & Three.js `r186` helpers (`studio_kit/vendor/three_optical.bundle.js`): `MotionTileWhipShader`, `OpticalRadialMatchShader`, `FlashCutoutStrobeShader`, `createCylinderRibbonTexture`, `glowSignaturePath`. |
| `studio_kit/occlusion_cutout.py` | Local `Smart Two-Tier Occlusion` subject isolation via `rembg` / Chrome for 3-layer foreground sandwich transitions & hooks. |
| `studio_kit/tactile_scene_kit.html` | Multi-aspect (`16:9` & `9:16`) Playwright overlay engine (`window.__setPlan`, `window.__seek`) supporting Speaker Captions, Cutting Mat, Prompt Cards, A/B Tags, NLE Stereo Waveform Pills & Music Dip Strip, Luda Letterbox, marksoy Collage Cards, Maciek 3-Tier Captions, Gaku Social Bubbles, plus v5 Engines (`narrative_cluster`, `camera_2d_canvas`, `explainer_visual_diagram`: `anatomy_ruler` / `flanking_word_field` / `chapter_slam`) and `--debug-safe-zone` HUD. |
| `studio_kit/narrative_composer.py` | Declarative dual-aspect composer (`--beat-sheet`, `--aspects 16x9,9x16`, `--debug-safe-zone`) tying `beat_sheet.py`, `sound_engine.py`, `safe_zones.audit_html_safe_zones(...)`, `color_grade.py`, FFmpeg assembly, `acoustic_audit.py`, and contact sheets together. |

---

## 2. Six Self-Contained Starter WeftCut Motifs (`studio_kit/motifs/`)

All 6 follow `motif.define({ async setup(props, ctx), frame(t, ctx) })` with bundled local `./fonts/`, transparent background, and zero external URLs:

1. `apple-follower-reveal`: Per-character left-to-right stagger with `6px -> 0px` blur resolve & per-glyph shadow.
2. `ghost-echo-kinetic`: `20%` trailing ghost expansion + `[0.38, 0, 0, 1]` kinetic phrase swap.
3. `rolling-cylinder-slot`: Clipped vertical reel columns with SVG directional Y blur at mid-velocity.
4. `kinetic-3d-spatial`: 3D spiral/planar word layout with `35mm` DoF rack-focus + Mixed-Voice contrast.
5. `cylinder-3d-orbit`: Offline Three.js `r186` beveled extruded typography + orbital cylinder ribbon + `SpotLight` shadows.
6. `signature-glow-trim`: Per-glyph vector Trim-Path stroke reveal + glowing bloom nib emitter.

---

## 3. Bundled Offline Fonts (`studio_kit/fonts/`)

Never fall back to `Segoe UI`. Load via `@font-face` + `await document.fonts.load(...)`:
- Display Sans: `InterTight-Latin.woff2`, `InterTight-Italic.woff2`, `Inter.ttf`, `Archivo.ttf`, `Geist.ttf`
- Editorial Serif: `InstrumentSerif.ttf`, `Fraunces.ttf`
- Condensed Impact: `Oswald-Latin.woff2`, `Montserrat-Latin.woff2`
- Technical Mono: `JetBrainsMono-Latin.woff2`, `GeistMono.ttf`

---

## 4. Studied Craft Guides (`references/`)

Update this table whenever Mode B absorbs a new batch of user references:

| Version | Study Guide Path | Core Mechanics Extracted |
|---|---|---|
| v1 | `references/transitions_study/TRANSITIONS_GUIDE.md` | 4 physical transitions (`foregroundOcclusionWipe`, `cutoutFrameHoldSlide`, `smoothMaskReveal`, `angledSplitZoom`). |
| v1 | `references/text_motion_study/TEXT_MOTION_GUIDE.md` | Per-glyph stagger, ghost echo, rolling slot columns, Mixed-Voice contrast, 180-360 deg shutter blur. |
| v2 | `references/transitions_study_v2/TRANSITIONS_V2_GUIDE.md` | Pop-Up overshoot (`0 -> 106 -> 100%`), Varo Flash Cutout strobe, Motion Tile Mirror Whip, Null-Rig radial optical match. |
| v2 | `references/depth_optical_study/DEPTH_OPTICS_ARCHITECTURE.md` | 3D Z separation, `35mm` DoF rack-focus, Dolly Zoom, `aeWhipOut` speed-graph (~17% influence), 3-layer occlusion sandwich. |
| v3 | `references/sound_cinematography_study/SOUND_CINEMA_ARCHITECTURE.md` | 5-stem separation, Room IR + Great Hall tails, 9-band voice carving, `visual_cause` causality, silence pockets, acoustic audit profiles. |
| v4 | `references/editorial_classup_study/EDITORIAL_CLASSUP_GUIDE.md` | Context routing (`Luda`, `marksoy`, `Gaku Lange`, `Herman Huang`, `Maciek Sulima`, `Jacob Nordin`), Flow-of-Motion, Transition Restraint, `HSV Ch-2` `.cube` LUTs + planar halation, 24 key-matched tonal WAVs, EQ sweeps. |
| v5 | `references/narrative_typography_study/NARRATIVE_TYPOGRAPHY_SAFEZONE_GUIDE.md` | Universal platform UI safe-zone contract (`safe_zones.py`), 3 narrative typography modes (`narrative_cluster`, `camera_2d_canvas` `-83ms` lead, `explainer_visual_diagram` `1.618x`/`8pt` + face-clearing `flanking_word_field`), context-aware highlight balance (`<=60%`). |
