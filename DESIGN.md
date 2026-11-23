# AGY Video Studio: Default Design & Brand Direction (Option A)

Reading this as: Multi-profile local open-source video studio combining WeftCut MCP timeline editing, OneTake continuous-take motion films, HyperFrames GSAP/Three.js compositions, and audio-first clipping/SFX skills, dial `ENERGY 2 / RHYTHM 3 / MOTION 3`.

## 1. Anti-Slop Dials (Default Studio Baseline)
- **ENERGY: 2 (Balanced-to-Bold):** Clean visual hierarchy and purposeful typography without neon or rainbow clutter.
- **RHYTHM: 3 (Varied & Asymmetric):** Every beat varies in duration, framing, and density. Uniform slide-show cadence is rejected by OneTake's `probe.py` / `verify_promo.py`.
- **MOTION: 3 (Choreographed & Continuous):** Elements carry across beat boundaries using measured OneTake springs (`lib/motion.js`), GSAP timelines (`hyperframes`), Three.js `r186` scenes, or WeftCut bezier keyframes and Motifs rather than generic fade-up template loops.

## 2. Core Palette & Typography Rules (One-Line Reasons per R-31)
- **Base Surface (`#0B0F17` Deep Carbon / `#F8FAFC` Editorial Paper):** Provides high-contrast ground (>12:1 WCAG AAA against primary text) so kinetic typography and captured UI read effortlessly at 30/60fps.
- **Primary Text (`#F8FAFC` on Dark / `#0F172A` on Light):** Ensures instant legibility during fast camera moves.
- **Muted Technical Metadata (`#94A3B8`):** Separates secondary captions and labels from primary headlines while keeping contrast >= 4.6:1.
- **Single Deliberate Accent (Project-Scoped):** Reserved strictly for the active focal point of each beat (R-29).
- **Typography:** Geometric sans for kinetic headlines (`Plus Jakarta Sans` / `Inter` / `Segoe UI` Bold) paired with tabular monospace (`JetBrains Mono` / `Consolas`) strictly for real numeric data and telemetry (R-06).

## 3. Style Profiles & Skill Routing
1. **`mograph-pro` (OneTake / HyperFrames / Three.js r186 / Barty-Bart Explainers - ENERGY 2 / RHYTHM 3 / MOTION 3):** Continuous camera carry, captured/rebuilt real UI (`record_footage.py` / `npx hyperframes capture`), 180-degree shutter motion blur, Three.js `r186` 3D accents, and beat-measured SFX (`sound-effects` / `scripts/sfx_palette.py`).
2. **`gaming-montage` (Faide Reference via WeftCut MCP + `ffmpeg-skill` + `librosa` - ENERGY 3 / RHYTHM 3 / MOTION 3):** Beat-synced cuts (`librosa` onsets), velocity speed-ramps, zero sticker clutter, crisp transient audio hits on WeftCut's SFX role track.
3. **`gaming-comedic` (Windah / MILYHYA Reference via WeftCut MCP + `claude-shorts` + `object-separation` - ENERGY 3 / RHYTHM 3 / MOTION 2):** Audio-first cut-and-play (`detect_pauses` / `remove_pauses` / `claude-shorts` boundary snapping), sudden music cut-outs (`set_role_gain` / keyframed music mute) before punchlines, expressive snap-zooms, optional subject cutout for text-behind-subject, and animated Motif word-level subtitles.
4. **`talking-head-reel` (`ghost-editor` 19 Visual Styles + `motion-video-director` Free Audio Override - ENERGY 2 / RHYTHM 3 / MOTION 2):** Clean OS, Kinetic doc, Swiss Grid, Halftone Dossier, or Telestrator blueprints rendered locally on Windows with original speaker audio or free local audio.
