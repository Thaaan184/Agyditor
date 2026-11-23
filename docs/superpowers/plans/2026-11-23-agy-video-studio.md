# AGY Video Studio & NCT AI Motion Graphic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the local AGY Video Studio skill suite and CLI pipeline (Goal 1), then research PT Nalar Cerdas Teknologi (NCT AI) and produce a verified anti-slop motion graphic film and DaVinci Resolve Free project package (Goal 2).

**Architecture:** A modular 4-skill Antigravity workspace backed by a tested Python/Node/FFmpeg/Playwright library (`studio_core/`) that generates native DaVinci Resolve Fusion `.setting`/`.drfx` macros, FCPXML v1.9 multi-track timelines, synthesized/ducked audio mixes, and deterministic `window.__seek(t)` 1080p MP4 renders with continuity probing.

**Tech Stack:** Python 3.11 (`pytest`, `numpy`, `scipy`, `pillow`, `playwright`), Node.js 24, FFmpeg + FFprobe, DaVinci Resolve Free (`.fcpxml`, `.setting`, `.drfx`).

**Spec:** `docs/superpowers/specs/2026-11-23-agy-video-studio-design.md`

## Global Constraints

- Zero em dashes or en dashes in any text, UI copy, subtitles, or documentation (`antislop` R-02).
- Never use paid cloud video services (`invideo`, paid API generators); 100% local execution on drive `D:`.
- Default video render resolution is `1920x1080` at `30fps` (or `1080x1920` vertical) to match Ryzen 5 5500 + GTX 1650 thermal/VRAM envelope.
- Every factual claim in Goal 2 (NCT AI Mograph) must trace directly to verified research from `pt-nct.ai`, Instagram, or LinkedIn (`antislop` R-17, R-36, R-38).

## Review Focus

- Fusion `.setting` macro with unbalanced Lua braces or missing `KeyFrameStretcher` / `MediaOut1` fails validation cleanly before installation.
- FCPXML timeline with empty clip list or negative/inverted timestamps raises `ValueError` instead of emitting broken XML.
- Audio ducking and hard-cut silence before punchlines properly attenuates BGM to silence (`0.0` amplitude) in the specified punchline window.
- Continuity oracle (`probe_continuity.py`) rejects a static or uniform hard-cut slideshow and passes a continuous-carry motion composition.
- Anti-slop copy and UI gate scanner catches any em dash, banned buzzword (`revolutionary`, `seamless`, `cutting-edge`, `next-level`, `AI-powered`), or unsourced statistic in the NCT AI composition.

---

### Task 1: Local Media Runtimes & Workspace Rule (`GEMINI.md`)

**Files:**
- Create: `GEMINI.md`
- Create: `DESIGN.md`
- Create: `tests/test_env_and_rules.py`

**Interfaces:**
- Consumes: System Python 3.11, Node 24, FFmpeg binary.
- Produces: Verified `ffmpeg` and `ffprobe` on PATH, `GEMINI.md`, `DESIGN.md`.

- [ ] **Step 1: Write the failing test in `tests/test_env_and_rules.py`**
- [ ] **Step 2: Run `pytest tests/test_env_and_rules.py -v` to verify it fails**
- [ ] **Step 3: Install FFmpeg/FFprobe & Playwright Chromium, and write `GEMINI.md` and `DESIGN.md`**
- [ ] **Step 4: Run `pytest tests/test_env_and_rules.py -v` to verify it passes**
- [ ] **Step 5: Commit**

### Task 2: Native DaVinci Resolve Fusion Macro Engine & Skill (`building-fusion-mograph`)

**Files:**
- Create: `studio_core/__init__.py`
- Create: `studio_core/fusion_lua.py`
- Create: `.agents/skills/building-fusion-mograph/SKILL.md`
- Create: `tests/test_fusion_lua.py`

**Interfaces:**
- Consumes: None
- Produces: `generate_kinetic_callout_setting(name: str, default_text: str, accent_rgb: tuple[float, float, float], duration_frames: int) -> str`, `validate_fusion_setting(lua_text: str) -> dict`, `package_drfx(settings_map: dict[str, str], output_drfx_path: str) -> str`

- [ ] **Step 1: Write failing tests in `tests/test_fusion_lua.py` (including unbalanced brace rejection and missing `KeyFrameStretcher` rejection)**
- [ ] **Step 2: Run `pytest tests/test_fusion_lua.py -v` to verify failure**
- [ ] **Step 3: Implement `studio_core/fusion_lua.py` and `.agents/skills/building-fusion-mograph/SKILL.md`**
- [ ] **Step 4: Run `pytest tests/test_fusion_lua.py -v` to verify pass**
- [ ] **Step 5: Commit**

### Task 3: Audio-First Cutter, Foley Synthesizer, FCPXML Timeline Engine & Skills (`editing-gaming-clips` & `managing-video-brand`)

**Files:**
- Create: `studio_core/audio_engine.py`
- Create: `studio_core/fcpxml_builder.py`
- Create: `.agents/skills/managing-video-brand/SKILL.md`
- Create: `.agents/skills/managing-video-brand/resources/video-design-tokens.json`
- Create: `.agents/skills/managing-video-brand/resources/style-profiles.md`
- Create: `.agents/skills/editing-gaming-clips/SKILL.md`
- Create: `tests/test_audio_and_fcpxml.py`

**Interfaces:**
- Consumes: `ffmpeg` binary
- Produces: `synthesize_sfx_catalog(output_dir: str) -> dict[str, str]`, `mix_editorial_audio(duration_sec: float, events: list[dict], output_wav: str, punchline_windows: list[tuple[float, float]]) -> str`, `build_fcpxml_timeline(project_name: str, fps: int, width: int, height: int, video_clips: list[dict], audio_clips: list[dict], output_path: str) -> str`, `export_srt(captions: list[dict], output_path: str) -> str`

- [ ] **Step 1: Write failing tests in `tests/test_audio_and_fcpxml.py` (including punchline window silence test and invalid timestamp rejection)**
- [ ] **Step 2: Run `pytest tests/test_audio_and_fcpxml.py -v` to verify failure**
- [ ] **Step 3: Implement `studio_core/audio_engine.py`, `studio_core/fcpxml_builder.py`, and the 2 skills**
- [ ] **Step 4: Run `pytest tests/test_audio_and_fcpxml.py -v` to verify pass**
- [ ] **Step 5: Commit**

### Task 4: Deterministic HTML/Canvas Mograph Renderer, Continuity Probe & Skill (`rendering-code-mograph`)

**Files:**
- Create: `studio_core/html_renderer.py`
- Create: `studio_core/continuity_probe.py`
- Create: `studio_core/antislop_gate.py`
- Create: `.agents/skills/rendering-code-mograph/SKILL.md`
- Create: `tests/test_renderer_and_probe.py`

**Interfaces:**
- Consumes: Playwright Chromium, `ffmpeg`, `studio_core/audio_engine.py`
- Produces: `render_seekable_html(html_path: str, output_mp4: str, duration_sec: float, fps: int, width: int, height: int, audio_wav: str | None) -> dict`, `probe_video_continuity(mp4_path: str, beat_boundaries_sec: list[float]) -> dict`, `audit_antislop_deliverable(html_text: str, copy_strings: list[str]) -> dict`

- [ ] **Step 1: Write failing tests in `tests/test_renderer_and_probe.py` (testing real HTML render, continuity probe pass/fail, and antislop copy gate)**
- [ ] **Step 2: Run `pytest tests/test_renderer_and_probe.py -v` to verify failure**
- [ ] **Step 3: Implement `studio_core/html_renderer.py`, `studio_core/continuity_probe.py`, `studio_core/antislop_gate.py`, and `.agents/skills/rendering-code-mograph/SKILL.md`**
- [ ] **Step 4: Run `pytest tests/test_renderer_and_probe.py -v` to verify pass (completing Goal 1: Sistem Stable)**
- [ ] **Step 5: Commit**

### Task 5: Research PT Nalar Cerdas Teknologi (NCT AI) & Produce Verified Motion Graphic Film + Resolve Package (Goal 2)

**Files:**
- Create: `projects/nct-ai-mograph/RESEARCH_FACTS.md`
- Create: `projects/nct-ai-mograph/DESIGN.md`
- Create: `projects/nct-ai-mograph/composition.html`
- Create: `projects/nct-ai-mograph/build_nct_project.py`
- Create: `tests/test_nct_ai_deliverable.py`

**Interfaces:**
- Consumes: `studio_core.fusion_lua`, `studio_core.audio_engine`, `studio_core.fcpxml_builder`, `studio_core.html_renderer`, `studio_core.continuity_probe`, `studio_core.antislop_gate`
- Produces:
  - `projects/nct-ai-mograph/output/nct_ai_mograph_1080p.mp4`
  - `projects/nct-ai-mograph/output/contact_sheet.png`
  - `projects/nct-ai-mograph/resolve/nct_ai_editorial.fcpxml`
  - `projects/nct-ai-mograph/resolve/nct_ai_captions.srt`
  - `projects/nct-ai-mograph/resolve/NCT_AI_Kinetic_Callout.setting`
  - `projects/nct-ai-mograph/resolve/NCT_AI_Mograph_Pack.drfx`

- [ ] **Step 1: Research `https://pt-nct.ai/`, `https://www.instagram.com/nalarcerdasteknologi/`, and `https://www.linkedin.com/company/nct-ai`, and record verified facts in `projects/nct-ai-mograph/RESEARCH_FACTS.md` and `projects/nct-ai-mograph/DESIGN.md`**
- [ ] **Step 2: Write failing end-to-end verification tests in `tests/test_nct_ai_deliverable.py`**
- [ ] **Step 3: Run `pytest tests/test_nct_ai_deliverable.py -v` to verify failure**
- [ ] **Step 4: Build `projects/nct-ai-mograph/composition.html` and `projects/nct-ai-mograph/build_nct_project.py`, then execute the full render, audio mix, continuity probe, contact sheet extraction, and Resolve `.fcpxml`/`.setting`/`.drfx` packaging**
- [ ] **Step 5: Run full test suite `pytest -v` and inspect visual contact sheet frames to verify 100% pass**
- [ ] **Step 6: Commit**
