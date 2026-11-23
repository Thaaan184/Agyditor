---
name: managing-video-brand
description: >-
  Provides the single source of truth for video brand identity, motion dials (ENERGY, RHYTHM, MOTION),
  typography, color tokens, and SFX routing across WeftCut Motifs, HyperFrames compositions, and OneTake films.
  Use whenever planning a video, styling subtitles, authoring Motifs, or composing scenes.
---

# Managing Video Brand & Anti-Slop Dials

## When to use this skill
- Before designing any motion graphic, WeftCut Motif overlay, HyperFrames composition, OneTake film, or dynamic subtitle style.
- When configuring `antislop` dials (`ENERGY`, `RHYTHM`, `MOTION`) for a new video project or preset.

## Workflow
1. Read [resources/video-design-tokens.json](resources/video-design-tokens.json) for active color palettes, safe margins, font families, and easing curves.
2. Select the target preset profile from [resources/style-profiles.md](resources/style-profiles.md):
   - `mograph-pro`: Continuous kinetic editorial (`ENERGY 2`, `RHYTHM 3`, `MOTION 3`) via OneTake / HyperFrames.
   - `gaming-montage` (Faide reference): High-velocity beat-sync, minimal visual clutter, sharp audio transients (`ENERGY 3`, `RHYTHM 3`, `MOTION 3`) via WeftCut MCP.
   - `gaming-comedic` (Windah / MILYHYA reference): Tight cut-and-play, sudden BGM cut-outs, expressive snap-zooms, color-coded word subtitles (`ENERGY 3`, `RHYTHM 3`, `MOTION 2`) via WeftCut MCP + Motifs.
   - `promo-editorial`: Product/commercial polish with purposeful hierarchy (`ENERGY 2`, `RHYTHM 2`, `MOTION 2`) via HyperFrames / OneTake / WeftCut.
3. Verify every visual and audio choice against the active profile and document a one-line reason per `antislop` R-31. Never place web app navigation bars, clickable tab menus, or UI playback buttons inside a video frame.
