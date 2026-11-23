# AGY Video Editor: Option A Open-Source Studio Rules & Anti-Slop Guardrails

## 1. 100% Open-Source & Local-First Stack (Option A)
- NEVER invoke, suggest, or route tasks to the `invideo` plugin skills or paid cloud video web apps.
- NEVER use paid per-second video generation APIs unless explicitly requested by the user.
- NEVER use DaVinci Resolve `.fcpxml` or `.setting` workarounds. Use the native open-source Option A stack installed on drive `D:`:
  1. **Desktop NLE, Audio/SFX Mixing & Live Overlays:** **WeftCut** (`tools/WeftCut/WeftCut.exe` + `bin/weftcut.exe mcp` localhost MCP server) with programmable **Motifs** (`motif.define({ setup, frame })`).
  2. **Continuous-Take Motion Films & Measured Camera/Foley:** **OneTake Official** (`.agents/skills/onetake/`, using `lib/motion.js`, `lib/ui_kit.js`, `scripts/sfx_palette.py`, `scripts/render.py`, `scripts/probe.py`, `scripts/verify_promo.py`).
  3. **GSAP/HTML Multi-Scene Video Compositions & Style Capture:** **HyperFrames Official** (`npx hyperframes` + `.agents/skills/hyperframes*`).
  4. **Media & Speech Backends:** `bin/ffmpeg.exe`, `bin/ffprobe.exe`, Python 3.11 (`faster-whisper`, `librosa`, `opencv-python`, `playwright`).

## 2. Hardware & Storage Guardrails (Ryzen 5 5500 / 16GB RAM / GTX 1650)
- Keep all project workspaces, tool installations, intermediate renders, Chromium caches, and audio analyses on drive `D:` (`d:/Files/Project Iseng/AGY Video Editor`). Do not dump heavy temporary files on `C:`.
- Default draft renders to `1920x1080` (or `1080x1920` vertical) at `30fps` (or `60fps` for gaming/montage finals). Do not default to 4K60 multi-sample shutter blur unless the user explicitly asks for an overnight heavy final render.
- Run `faster-whisper` with `int8` or `float16` quantization on CUDA (GTX 1650 4GB VRAM) or CPU fallback to prevent VRAM out-of-memory errors.
- Ensure `d:\Files\Project Iseng\AGY Video Editor\bin` is prepended to `PATH` before invoking `npx hyperframes` or `onetake` scripts so `ffmpeg.exe` and `ffprobe.exe` resolve reliably.

## 3. Strict Separation of Video Canvas vs. Web App UI (`antislop` Video Guardrail)
- NEVER render web navigation bars (`<header>`, `<nav>`, clickable tab buttons, "Pause/Play" buttons, or footer chrome) inside a video composition or WeftCut Motif frame. A video frame is a camera viewport, not a web page shell.
- Every visual cut, zoom, transition, motion graphic, and SFX placement MUST pass a purpose test (R-19, R-31): state in one line what narrative, rhythmic, or comedic beat it serves.
- FORBIDDEN copywriting and punctuation patterns: zero em dashes (`\u2014`) and zero en dashes (`\u2013`) in any prose, subtitle, or title card (R-02); zero generic AI buzzwords (`revolutionary`, `seamless`, `cutting-edge`, `next-level`, `AI-powered`, `game-changer`) (R-16); zero fabricated numbers, metrics, or testimonials (R-17, R-18, R-36, R-38).
- FORBIDDEN visual slop patterns: uniform slide-show cadence ("PPT style"), gratuitous blue-to-purple gradients without brand proof (R-01), continuous background music with no dynamic ducking or cut-outs, and unmotivated camera shakes.
- Before generating motion graphics or subtitle styles, read `.agents/skills/managing-video-brand/SKILL.md` and `DESIGN.md` to lock the active `ENERGY`, `RHYTHM`, and `MOTION` dials.
