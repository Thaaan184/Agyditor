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
2. Select the target preset profile from [resources/style-profiles.md](resources/style-profiles.md):
   - `mograph-pro`: Continuous kinetic editorial (`ENERGY 2`, `RHYTHM 3`, `MOTION 3`) via OneTake, HyperFrames, Three.js (`threejs-*`), `studio_kit/motifs/kinetic-3d-spatial`, and `sound-effects` / `explainer-*`.
   - `gaming-montage` (Faide reference): High-velocity beat-sync, minimal visual clutter, sharp audio transients (`ENERGY 3`, `RHYTHM 3`, `MOTION 3`) via WeftCut MCP, `ffmpeg-skill`, `librosa`, and `rolling-cylinder-slot` / `cutoutFrameHoldSlide`.
   - `gaming-comedic` (Windah / MILYHYA reference): Tight cut-and-play, sudden BGM cut-outs, expressive snap-zooms, color-coded word/letter kinetic subtitles (`ENERGY 3`, `RHYTHM 3`, `MOTION 2`) via WeftCut MCP + starter Motifs (`ghost-echo-kinetic`, `apple-follower-reveal`) + `claude-shorts` / `object-separation`.
   - `talking-head-reel`: Vertical talking-head / reel layouts (`ENERGY 2`, `RHYTHM 3`, `MOTION 2`) using `ghost-editor` (19 style recipes adapted for Windows), `apple-follower-reveal`, and `motion-video-director` (100% free local audio override).
   - `promo-editorial`: Product/commercial polish with purposeful hierarchy (`ENERGY 2`, `RHYTHM 2`, `MOTION 2`) via HyperFrames, OneTake, or WeftCut.
3. Verify every visual and audio choice against the active profile (`references/transitions_study/TRANSITIONS_GUIDE.md` and `references/text_motion_study/TEXT_MOTION_GUIDE.md`) and document a one-line reason per `antislop` R-31. Ensure zero fallback to Windows system fonts (`Segoe UI`), enable `180-360` deg shutter/directional blur on rapid text moves, inspect peak-motion contact sheets, never place web app navigation bars or playback buttons inside a video frame, and never require paid voiceover APIs.
