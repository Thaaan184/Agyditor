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

## Core Reference Docs
- See [references/bundled-skill/SKILL.md](references/bundled-skill/SKILL.md) for the official skill shipped inside WeftCut v0.8.1 (including `craft/rules.md`, `craft/editing.md`, and `recipes/teaching-explainer.md`).
- See [references/mcp.md](references/mcp.md) for MCP transport, tool lifecycle, Tacks, and Timeline Diff conventions.
- See [references/motif-authoring.md](references/motif-authoring.md) for the exact `motif.define({ setup, frame })` authoring contract (one purpose per Motif layer, pure function of time `t`, cue props `cue_<name>_s`, zero web app navigation bars).
