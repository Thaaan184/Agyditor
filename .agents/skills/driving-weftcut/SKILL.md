---
name: driving-weftcut
description: >-
  Connects to and drives the local WeftCut desktop NLE via its stdio MCP binary (bin/weftcut.exe mcp)
  and authors programmable HTML/CSS/SVG/WebGL Motifs (motif.define). Use for interactive timeline editing,
  pause removal, role-based audio/SFX mixing, keyframing, and live overlay Motifs in WeftCut.
---

# Driving WeftCut Desktop NLE via MCP & Authoring Motifs

## When to use this skill
- Whenever editing footage, cutting pauses/dead air, placing SFX/music, or adding keyframes and animated overlays on a live WeftCut timeline.
- Whenever authoring a WeftCut Motif (a pure function of time rendered via `motif.define({ setup, frame })`).

## Connection & MCP Setup
- The stdio MCP server binary lives at `bin/weftcut.exe` (usage: `bin/weftcut.exe mcp`).
- Check Antigravity's global MCP config (`~/.gemini/config/mcp_config.json`) or run `.\bin\weftcut.exe print-config` to verify the `weftcut` MCP entry points to `D:\Files\Project Iseng\AGY Video Editor\bin\weftcut.exe` with args `["mcp"]`.
- Note: Also check `.\tools\WeftCut\WeftCut.exe` is launched (or call `launch_weftcut` once MCP is registered) before editing a live timeline.
- When starting an editing session:
  1. Call `weftcut_status` to check whether the WeftCut desktop GUI is running.
  2. If not running, call `launch_weftcut` to start `tools/WeftCut/WeftCut.exe`.
  3. Use `begin_agent_session` for multi-step edits so the user can review changes visually via `Tacks` and `Changes` (Timeline Diff).

## Core Reference Docs & Studio Starter Motifs
- See [references/bundled-skill/SKILL.md](references/bundled-skill/SKILL.md) for the official skill shipped inside WeftCut v0.8.1 (including `craft/rules.md`, `craft/editing.md`, and `recipes/teaching-explainer.md`).
- See [references/mcp.md](references/mcp.md) for MCP transport, tool lifecycle, Tacks, and Timeline Diff conventions.
- See [references/motif-authoring.md](references/motif-authoring.md) for the exact `motif.define({ async setup(props, ctx), frame(t, ctx) })` authoring contract (one purpose per Motif layer, pure function of time `t`, cue props `cue_<name>_s`, bundled relative `./fonts/` loaded via `document.fonts.load(...)`, zero web app navigation bars).
- Ready-to-use self-contained Starter Motifs live under `studio_kit/motifs/` (sharing `studio_kit/motion_primitives.js`, `keyframe_rig.js`, and `optical_stage.js`):
  - `studio_kit/motifs/apple-follower-reveal` (2-frame per-character stagger with blur resolve and tight per-glyph shadow).
  - `studio_kit/motifs/ghost-echo-kinetic` (20% trailing ghost expansion + `[0.38, 0, 0, 1]` kinetic swap).
  - `studio_kit/motifs/rolling-cylinder-slot` (clipped vertical reel columns with SVG directional Y blur at mid-velocity + split color accent).
  - `studio_kit/motifs/kinetic-3d-spatial` (true 3D spiral/planar layout with `35mm` camera Z pull/push + keyframed DoF blur + Mixed-Voice contrast).
  - `studio_kit/motifs/cylinder-3d-orbit` (Three.js `r186.1` extruded beveled typography + curved `CylinderGeometry` orbital ribbon + `SpotLight` + `Cast Shadow` ready for WeftCut subject sandwiching).
  - `studio_kit/motifs/signature-glow-trim` (per-glyph vector Trim-Path stroke reveal + glowing bloom nib emitter).

## 5-Stem Role Mixing & Zero-Waste Sound Hygiene
- Export or import pre-rendered audio via `studio_kit/sound_engine.py` (`stems/stem_voice.wav`, `stem_ambience.wav`, `stem_foley.wav`, `stem_transitions.wav`, `stem_music.wav` + `weftcut_stem_plan.json`) mapped cleanly to WeftCut `dialogue`, `ambience`, `sfx`, and `bgm` tracks.
- Enforce continuous room-tone ambience across visual cuts (`J/L-cut`), `50-240 ms` pre-lap on hero transitions, BGM micro-silence drop-outs before reveals/punchlines, and final validation through `studio_kit/acoustic_audit.py`.
