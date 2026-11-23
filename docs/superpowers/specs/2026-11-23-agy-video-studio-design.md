# AGY Video Studio & NCT AI Motion Graphic Design Specification

## 1. Intent and Why
Build a 100% local, free, anti-slop video editing and motion graphics studio inside `d:/Files/Project Iseng/AGY Video Editor` tailored for AMD Ryzen 5 5500, 16 GB RAM, and NVIDIA GTX 1650. The system must first reach a verified, test-passing stable state (**Goal 1: Sistem Stable**), then prove itself by researching **PT Nalar Cerdas Teknologi (NCT AI)** from its official sources and producing a complete, non-slop motion graphic film plus native DaVinci Resolve Free deliverables (**Goal 2: NCT AI Mograph**).

## 2. Goals, Non-Goals, and Anti-Goals
- **Goals:**
  1. Establish workspace guardrails (`GEMINI.md`) and the modular 4-skill suite (`.agents/skills/managing-video-brand`, `building-fusion-mograph`, `editing-gaming-clips`, `rendering-code-mograph`).
  2. Install and verify local media runtimes (FFmpeg/FFprobe, Python audio/video/testing tools, Playwright Chromium headless renderer).
  3. Build and test (via `pytest` TDD) four deterministic local pipeline tools:
     - `validate_fusion_lua.py` and `generate_fusion_macro.py`: builds and validates native DaVinci Resolve Fusion `.setting` macros and `.drfx` bundles with `KeyFrameStretcher` and `UserControls`.
     - `fcpxml_builder.py`: generates DaVinci Resolve Free compatible FCPXML v1.9 timelines (`V1` base/gameplay, `V2` punch-in zoom, `V3` mograph overlay, `A1` voice, `A2` SFX, `A3` ducked BGM) and `.srt` subtitles.
     - `audio_cutter.py`: synthesizes room-matched foley/SFX WAVs, detects audio peaks/silences, applies BGM ducking/hard-cuts, and mixes master audio via FFmpeg.
     - `render_html_video.py` and `probe_continuity.py`: renders deterministic `window.__seek(t)` HTML/Canvas/SVG motion compositions at 1080p via headless Chromium + FFmpeg, and audits frame-to-frame continuity and anti-slop rhythm.
  4. Research PT Nalar Cerdas Teknologi (`https://pt-nct.ai/`, Instagram `@nalarcerdasteknologi`, LinkedIn `nct-ai`) and record only verified facts.
  5. Produce the NCT AI motion graphic (`projects/nct-ai-mograph/`) including `DESIGN.md`, deterministic `composition.html`, synthesized master audio, rendered `nct_ai_mograph_1080p.mp4`, continuity audit report, contact sheet QA, and native DaVinci Resolve Free `.fcpxml` + Fusion `.setting`/`.drfx` package.
- **Non-Goals:**
  - Cloud rendering or paid external API video generation.
  - External live scripting of DaVinci Resolve (blocked in DaVinci Resolve Free).
- **Anti-Goals (Failures even if code runs):**
  - Any em dash or en dash in copy, code comments, or documentation (`antislop` R-02).
  - Any fabricated statistics, fake testimonials, or unverified claims about NCT AI (`antislop` R-17, R-18, R-36, R-38).
  - Generic AI visual slop: default blue-to-purple gradient without brand proof, sparkle/robot icons, uniform slideshow transitions with zero visual carry between beats.

## 3. Selected Approach
**Approach 1 (Modular 4-Skill Suite + Core Python/Node CLI Bridge)**. Chosen for progressive disclosure efficiency and strict separation of concerns between brand tokens, native Resolve Fusion Lua generation, audio-first editorial cutting, and code-driven HTML/JS rendering.
