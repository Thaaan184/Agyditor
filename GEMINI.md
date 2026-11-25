# AGY Video Editor: Option A Open-Source Studio Rules & Anti-Slop Guardrails

## 1. 100% Open-Source & Local-First Stack (Option A)
- NEVER invoke, suggest, or route tasks to the `invideo` plugin skills or paid cloud video web apps.
- NEVER use paid per-second video generation APIs or paid voiceover APIs (such as ElevenLabs) unless explicitly requested by the user.
- NEVER use DaVinci Resolve `.fcpxml` or `.setting` workarounds. Use the native open-source Option A stack installed on drive `D:`:
  1. **Desktop NLE, Audio/SFX Mixing & Live Overlays:** **WeftCut** (`tools/WeftCut/WeftCut.exe` + `bin/weftcut.exe mcp` localhost MCP server) with programmable **Motifs** (`motif.define({ setup, frame })`).
  2. **Continuous-Take Motion Films & Measured Camera/Foley:** **OneTake Official** (`.agents/skills/onetake/`, using `lib/motion.js`, `lib/ui_kit.js`, `scripts/sfx_palette.py`, `scripts/render.py`, `scripts/probe.py`, `scripts/verify_promo.py`).
  3. **GSAP/HTML Multi-Scene Video Compositions & Style Capture:** **HyperFrames Official** (`npx hyperframes` + `.agents/skills/hyperframes*`).
  4. **Local FFmpeg, Clipping & Media Backends:** `bin/ffmpeg.exe`, `bin/ffprobe.exe`, `bin/yt-dlp.exe`, `ffmpeg-skill` (42 FFmpeg JSON/MCP operations), `claude-shorts` (longform VOD scoring & audio boundary snapping), and Python 3.11 (`faster-whisper`, `librosa`, `opencv-python`, `playwright`).
  5. **Specialized Motion, Audio, 3D & Style Skills:**
     - **Barty-Bart Motion Graphics Pack:** `sound-effects` (beat-locked CC0 SFX & `-16 LUFS` mixing), `object-separation` (local subject isolation/rotoscoping), `motion-broll`, `explainer-high-energy`, `explainer-default`, `explainer-engaging`.
     - **Three.js r186 Skill Pack (`threejs-*`):** Use for any 3D WebGL/WebGPU/TSL scenes inside HyperFrames or WeftCut Motifs so code targets modern `three@0.186`.
     - **Adapted Blueprints (Windows & Free Audio Overrides):** `ghost-editor` (19 reel visual styles adapted to Windows local tools) and `motion-video-director` (adapted for 100% free local audio/VO without ElevenLabs).

## 2. Hardware & Storage Guardrails (Ryzen 5 5500 / 16GB RAM / GTX 1650)
- Keep all project workspaces, tool installations, intermediate renders, Chromium caches, and audio analyses on drive `D:` (`d:/Files/Project Iseng/AGY Video Editor`). Do not dump heavy temporary files on `C:`.
- Default draft renders to `1920x1080` (or `1080x1920` vertical) at `30fps` (or `60fps` for gaming/montage finals). Do not default to 4K60 multi-sample shutter blur unless the user explicitly asks for an overnight heavy final render.
- Run `faster-whisper` with `int8` or `float16` quantization on CUDA (GTX 1650 4GB VRAM) or CPU fallback to prevent VRAM out-of-memory errors.
- Ensure `d:\Files\Project Iseng\AGY Video Editor\bin` is prepended to `PATH` AND `HYPERFRAMES_FFMPEG_PATH` / `HYPERFRAMES_FFPROBE_PATH` point to `d:\Files\Project Iseng\AGY Video Editor\bin\ffmpeg.exe` and `ffprobe.exe` before invoking `npx hyperframes` or `onetake` scripts so FFmpeg resolves cleanly (HyperFrames ignores project-internal `PATH` entries by design).

## 3. Strict Separation of Video Canvas vs. Web App UI (`antislop` Video Guardrail)
- NEVER render web navigation bars (`<header>`, `<nav>`, clickable tab buttons, "Pause/Play" buttons, or footer chrome) inside a video composition or WeftCut Motif frame. A video frame is a camera viewport, not a web page shell.
- Every visual cut, zoom, transition, motion graphic, and SFX placement MUST pass a purpose test (R-19, R-31): state in one line what narrative, rhythmic, or comedic beat it serves.
- FORBIDDEN copywriting and punctuation patterns: zero em dashes (`\u2014`) and zero en dashes (`\u2013`) in any prose, subtitle, or title card (R-02); zero generic AI buzzwords (`revolutionary`, `seamless`, `cutting-edge`, `next-level`, `AI-powered`, `game-changer`) (R-16); zero fabricated numbers, metrics, or testimonials (R-17, R-18, R-36, R-38).
- FORBIDDEN visual slop patterns: uniform slide-show cadence ("PPT style"), gratuitous blue-to-purple gradients without brand proof (R-01), continuous background music with no dynamic ducking or cut-outs, and unmotivated camera shakes.
- Before generating motion graphics or subtitle styles, read `.agents/skills/managing-video-brand/SKILL.md` and `DESIGN.md` to lock the active `ENERGY`, `RHYTHM`, and `MOTION` dials.

## 4. Calibrated Transition, Typography & Motion Baseline (`studio_kit/`)
- **Self-Hosted Fonts Mandatory:** NEVER rely on Windows fallback fonts (`Segoe UI` / bare system display stacks). Load local `.woff2` / `.ttf` assets from `studio_kit/fonts/` via `@font-face` and await `document.fonts.load(...)` for every rendered weight/style before capture. Use Mixed-Voice contrast (`Inter Tight` tight bold + italic `Instrument Serif` / `Fraunces` + `JetBrains Mono` telemetry).
- **Shared Motion & Motif Baseline:** Route reusable transitions and kinetic text through `studio_kit/motion_primitives.js` (`appleFollowerChar`, `ghostEchoPair`, `rollingSlotColumn`, `spatial3DCameraWord`, `foregroundOcclusionWipe`, `cutoutFrameHoldSlide`, `smoothMaskReveal`, `angledSplitZoom`) and starter WeftCut Motifs in `studio_kit/motifs/` (`apple-follower-reveal`, `ghost-echo-kinetic`, `rolling-cylinder-slot`, `kinetic-3d-spatial`).
- **Studied Craft References:** Enforce mechanics documented in `references/transitions_study/TRANSITIONS_GUIDE.md` and `references/text_motion_study/TEXT_MOTION_GUIDE.md`: per-character/per-word isolation instead of monolithic CSS text boxes, `180-360` degree shutter or directional motion blur on fast travel, lit ambient compositing ground (bokeh/vignette/cast shadow), and mandatory peak-velocity contact-sheet frame inspection via `read_file`.
- **Chrome GPU Playwright Flag on Windows:** When invoking Playwright Python scripts on this workstation (`GTX 1650`), launch headless Chrome with `channel="chrome"` and `["--use-gl=angle", "--use-angle=d3d11", "--enable-webgl", "--ignore-gpu-blocklist"]` instead of macOS Metal flags or unbundled Playwright shells.
