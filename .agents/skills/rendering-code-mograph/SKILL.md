---
name: rendering-code-mograph
description: >-
  Builds and renders deterministic code-driven motion graphics locally using headless Chromium (Playwright),
  HyperFrames CLI patterns, and OneTake continuity principles. Enforces measured spring/camera curves,
  continuity checks (probe_video_continuity), and antislop audits before delivering 1080p MP4s.
---

# Rendering Code-Driven Motion Graphics

## When to use this skill
- When creating full-screen kinetic typography, multi-beat product launch films, technical architecture breakdowns, or interactive UI recreations.
- When rendering deterministic HTML/Canvas/SVG compositions (`window.__seek(t)`) to 1080p MP4 with room-matched audio.

## Workflow Checklist
- [ ] **Step 1: Declare Design Read & Dials** - Read project `DESIGN.md` and lock `ENERGY`, `RHYTHM`, and `MOTION` dials plus one-line purpose justifications per `antislop` R-31.
- [ ] **Step 2: Build Seekable HTML Composition** - Implement `window.__seek(t)` in `composition.html` as a pure function of time `t` (in seconds), ensuring every beat boundary carries at least one visual anchor across the cut.
- [ ] **Step 3: Audit Anti-Slop Gate** - Run `studio_core.antislop_gate.audit_antislop_deliverable()` on the HTML and copy strings to verify zero em/en dashes, zero banned buzzwords, and zero unsourced numbers.
- [ ] **Step 4: Render &Mux Master Audio** - Run `studio_core.html_renderer.render_seekable_html()` to capture deterministic frames at `1920x1080` and encode H.264 MP4 + AAC audio via `bin/ffmpeg.exe`.
- [ ] **Step 5: Verify Continuity & Contact Sheet** - Run `studio_core.continuity_probe.probe_video_continuity()` to verify carry score and extract a visual contact sheet for frame-by-frame inspection.
