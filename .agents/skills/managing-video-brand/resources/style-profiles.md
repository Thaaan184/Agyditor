# Video Style Profiles & Anti-Slop Dials

## 1. `mograph-pro` (Continuous Kinetic Editorial)
- **Dials:** `ENERGY 2 / RHYTHM 3 / MOTION 3`
- **Visual Rules:** Exactly one focal point per beat. At every beat boundary, at least one anchor element (a coordinate line, a card frame, a data pillar, or a kinetic word) survives on screen and physically morphs into the next beat (`carry_score >= 0.75`).
- **Audio Rules:** Synthesized room-matched transients (soft low sub-thud on expansion, crisp click on data lock, filtered air whoosh on camera whip).

## 2. `gaming-montage` (Faide Movement & Clutch Reference)
- **Dials:** `ENERGY 3 / RHYTHM 3 / MOTION 3`
- **Visual Rules:** Clean gameplay frame without sticker clutter. Velocity speed-ramps (`1.5x` into `0.4x` hit-stop into `1.2x` recovery) aligned within 1 frame of audio beat transients.
- **Audio Rules:** Weapon/movement transient boosted `+2.5 dB` over BGM; low-pass filter sweep during slow-motion pre-drop.

## 3. `gaming-comedic` (Windah Basudara & MILYHYA Reference)
- **Dials:** `ENERGY 3 / RHYTHM 3 / MOTION 2`
- **Visual Rules:** Hard cuts on speech completion. 115% to 130% instant snap-zoom on facecam or subject reaction. Word-level subtitles positioned in lower safe zone with color shifts strictly tied to vocal pitch/volume peaks.
- **Audio Rules:** Mandatory BGM hard-cut (`0.0` amplitude) `0.15s` to `0.5s` before comedic punchline or awkward silence, followed by a single dry stinger SFX.

## 4. `narrative-film` & Class-Up v4 Context Profiles (`studio_kit/context_router.py`)
- **`cinematic-essay` (`Luda` & `Jacob Nordin` - `ENERGY 1 / RHYTHM 3 / MOTION 2`):** `2.39:1` anamorphic or vertical `#000000` rounded letterbox with bare crimson micro captions, `luda_filmic_warm` + halation clean-plate grade, wide dynamics (`-19.5 LUFS`, `LRA 6-12 LU`), and key-matched tonal drones/hits.
- **`podcast-collage-short` (`marksoy` - `ENERGY 3 / RHYTHM 3 / MOTION 3`):** High-punch `-11 LUFS` vertical cuts alternating clean talking head with full-bleed mixed-media collage cards (`#ECEAD8` cream sans+italic, `#0B1A8A` cobalt grid, newspaper red-oval circle, dark red highlighter).
- **`creator-editorial` (`Gaku Lange`, `Herman Huang`, `Andrew` - `ENERGY 2 / RHYTHM 3 / MOTION 3`):** Show-First `-15.5 LUFS` breakdowns, Flow-of-Motion directional cuts (`static_reset` palate cleansers between opposing vectors), Transition Restraint (`<= 55%` stylized cuts), `gaku_filmic_teal` grade, cutting mat, live NLE waveforms, and organic social bubbles.
- **`kinetic-reel-typography` (`Maciek Sulima` - `ENERGY 3 / RHYTHM 3 / MOTION 3`):** `splitSCurveHandoff` across single motion axis + 3-tier asymmetric captions (`lead` / `HERO` / `tail`).
- **`narrative-film` (`Andrew` & `Herman Huang` - `ENERGY 2 / RHYTHM 3 / MOTION 2`):** Natural footage, tactile craft paper (`#F4EFE6`) on green cutting mat (`#1B3B2B`), authentic NLE stereo waveforms, literal sound causality, and warm close-mic voice priority.

## 5. Calibrated Text, Subtitle & Transition Baseline
- **Never Ship Unstyled System Fonts:** All profiles MUST load bundled `.woff2` or `.ttf` faces from `studio_kit/fonts/` via explicit `@font-face` rules and call `await document.fonts.load(...)`. Unbundled `Segoe UI` fallbacks are rejected.
- **Profile-to-Primitive Routing (`studio_kit/motion_primitives.js` & `studio_kit/motifs/`):**
  - `mograph-pro`: Combine `kinetic-3d-spatial` (3D spiral Mixed-Voice + `35mm` keyframed DoF), `cylinder-3d-orbit` (Three.js `r186` extrusion/ribbon + `SpotLight`), `signature-glow-trim` (Trim-Path bloom nib), `rolling-cylinder-slot`, `MotionTileWhipShader`, and `OpticalRadialMatchShader` with `180-360` deg shutter blur only when the subject serves a concrete narrative beat.
  - `narrative-film`: Drive composition through `studio_kit/narrative_composer.py` and `studio_kit/tactile_scene_kit.html` (`16:9` and `9:16` modular overlays) with clean human-voice priority.
  - `talking-head-reel`: Prefer `apple-follower-reveal`, `ghost-echo-kinetic`, and `kinetic-3d-spatial` (`talking_head_depth` adapter with Z-pushed background parallax); use `studio_kit/occlusion_cutout.py` (`Smart Two-Tier Occlusion`) for instant Pop-Up/Flash bursts or 1-3s hooks.
  - `gaming-comedic` & `gaming-montage`: Keep frame clean with ultra-brief 1-2 punch words tied to `faster-whisper` / `librosa` spikes (`ghost-echo-kinetic`, `rolling-cylinder-slot`, `FlashCutoutStrobeShader`, or `cutoutFrameHoldSlide`) instead of flat CSS caption cards.

## 6. Platform Safe-Zone Guard & 3 Narrative Typography Engines (v5)
- **Strict Platform UI Safe-Zone Contract (`studio_kit/safe_zones.py`):** Every Playwright overlay render runs `audit_html_safe_zones(...)` before exporting frames. Keep vertical Shorts/TikTok/Reels overlays strictly inside `universal_vertical` (`top >= 13.5%`, `bottom <= 70.2%`, `left >= 5.5%`, `right <= 83.0%`) and landscape overlays inside `youtube_16x9` (`top >= 8.0%`, `bottom <= 88.5%`, `left >= 6.0%`, `right <= 94.0%`).
- **Context-Matched Narrative Typography Routing (`studio_kit/motion_primitives.js` & `studio_kit/tactile_scene_kit.html`):**
  - `narrative_cluster` (`RhVB8WPLJAI` / Editor Keling): Staggered 2-line Mixed-Voice word accumulation inside the chest-safe zone (`y = 49%..65%`) with stroke/shadow contrast over bright shirts and restrained `cobalt` / `brush_red` / `oval_red` anchor highlights (`AGYMotion.narrativeClusterWord`).
  - `camera_2d_canvas` (`G-DHQAzulyU` / PeeJ ENT): Spatial 2D word storyboard driven by virtual camera pan/zoom/rotate + dashed SVG connector path with `-83ms` (`2-3` frame) pre-beat arrival lead (`AGYMotion.camera2DTypographyState`).
  - `explainer_visual_diagram` (`BWRdNeNkph4` / aayusucks): `1.618x` Golden Ratio scale on `8pt` grid (`AGYMotion.goldenTypeScale`) across 3 long-form visual explanation templates: `anatomy_ruler`, face-clearing `flanking_word_field` (`86% x 74%`), and `chapter_slam`.
- **Context-Aware Highlight Restraint (`studio_kit/beat_sheet.py`):** Never force loud highlight badges on quiet `cinematic-essay` scenes. Warn on `3+` consecutive flat text beats in explanatory/short profiles (`creator-editorial`, `podcast-collage-short`, `kinetic-reel-typography`) and warn on highlight overuse (`>60%` of words emphasized in a single beat) across all profiles.

## 7. Sound Palettes, 5-Stem Routing & Zero-Waste Storytelling
- **No Unlayered Sine Beeps or Dead Vacuums:** Route all renders through `studio_kit/sound_engine.py` (`voice`, `ambience` room tone, tactile `foley`, 3-layer `transitions`, `music` with 9-band voice carving + `Great Hall` tail exits, plus explicit `silence_pockets`).
- **Coherent Palette Mapping (`studio_kit/sound_palette_index.json`):** Lock every project to `editorial-clean` (`mograph-pro`, `talking-head-reel`), `kinetic-street` (`promo-editorial`), `organic-cinema` (`narrative-film` / `cinematic-doc` / `Emotional Realism`), `comedic-dry` (`gaming-comedic`), or `gaming-montage`.
- **Mandatory Gates:** Validate `studio_kit/beat_sheet.py` (`visual_subject` free of abstract slop terms, explicit `visual_cause` or `contrast_rule` per sound cue, `narrative_purpose`, `broll_justification`, `shot_cv >= 0.20`, rest pockets) pre-render, and enforce `studio_kit/acoustic_audit.py` post-render under `narrative_voice_film` (`mud <= 48%`, `voice >= 18%`, `detail+air >= 2.5%`) or `mograph_sfx` (`mud < 35%`, `detail+air >= 4.0%`).
