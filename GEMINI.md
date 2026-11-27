# AGY Video Editor: Option A Open-Source Studio Rules & Anti-Slop Guardrails

## 1. 100% Open-Source & Local-First Stack (Option A)
- NEVER invoke, suggest, or route tasks to the `invideo` plugin skills, paid cloud video apps, paid per-second generation APIs, or paid voiceover APIs (e.g. ElevenLabs) unless explicitly requested by the user.
- NEVER use DaVinci Resolve `.fcpxml` or `.setting` workarounds. Use the native local Option A stack on drive `D:`:
  1. **WeftCut** (`tools/WeftCut/WeftCut.exe` + `bin/weftcut.exe mcp`) & programmable Motifs (`studio_kit/motifs/`).
  2. **OneTake Official** (`.agents/skills/onetake/`) & **HyperFrames Official** (`npx hyperframes` + `.agents/skills/hyperframes*` + **Three.js r186** `threejs-*`).
  3. **Local Media & Clipping:** `bin/ffmpeg.exe`, `bin/ffprobe.exe`, `bin/yt-dlp.exe`, `ffmpeg-skill`, `claude-shorts`, `sound-effects`, `object-separation`, `motion-broll`, `explainer-*`, plus adapted local-audio blueprints `ghost-editor` and `motion-video-director`.
  4. **Calibrated Studio Baseline (`studio_kit/`):** Always activate `.agents/skills/directing-agy-video/SKILL.md` (end-to-end production & reference-study ingestion) and `.agents/skills/managing-video-brand/SKILL.md` (`DESIGN.md`) before planning, editing, or absorbing new editing references.

## 2. Hardware & Storage Guardrails (Ryzen 5 5500 / 16GB RAM / GTX 1650)
- Keep all projects, renders, Chromium caches, and audio analyses on drive `D:` (`d:/Files/Project Iseng/AGY Video Editor`). Never dump heavy temp files on `C:`.
- Default draft renders to `1920x1080` or `1080x1920` at `30fps` (`60fps` for gaming/montage finals); avoid 4K60 multi-sample unless explicitly requested.
- Run `faster-whisper` with `int8` or `float16` quantization on CUDA/CPU to fit 4 GB VRAM.
- Prepend `d:\Files\Project Iseng\AGY Video Editor\bin` to `PATH` and set `HYPERFRAMES_FFMPEG_PATH` / `HYPERFRAMES_FFPROBE_PATH` before running `npx hyperframes` or `onetake`.
- Launch Playwright Chrome on Windows with `channel="chrome"` and `["--use-gl=angle", "--use-angle=d3d11", "--enable-webgl", "--ignore-gpu-blocklist"]`.

## 3. Strict Anti-Slop, Context-First & Visual Hygiene Guardrails
- NEVER render web chrome (`<header>`, `<nav>`, clickable buttons, footer bars) or generic HTML stat cards over video frames.
- FORBIDDEN copy & punctuation: zero em dashes (`\u2014`) and zero en dashes (`\u2013`) in prose, subtitles, or title cards; zero AI hype words (`revolutionary`, `seamless`, `cutting-edge`, `next-level`, `AI-powered`, `game-changer`); zero fabricated stats.
- FORBIDDEN visual slop: uniform slide-show cadence, unrequested dark-carbon neon grids, abstract 3D wireframe prisms/blobs standing in for story substance, unmotivated shakes, or flat continuous music without ducking/rest pockets. Default non-footage diagrams to tactile craft paper (`#F4EFE6`), green cutting mat (`#1B3B2B`), deep ink (`#18181B`), real footage, and real NLE waveforms.
- **Context Always Wins:** Route every brief via `studio_kit/context_router.py` first. Never force loud highlights onto quiet `cinematic-essay` scenes, and never leave explanatory/short-form narration as 3+ consecutive flat text walls or `>60%` over-highlighted words.
- **Self-Hosted Fonts Mandatory:** Never rely on `Segoe UI` or OS fallbacks. Load local fonts from `studio_kit/fonts/` via `@font-face` and await `document.fonts.load(...)`.
- **Platform Safe-Zone Gate Mandatory:** Keep all vertical overlays inside `universal_vertical` (`studio_kit/safe_zones.py`: `top >= 13.5%`, `bottom <= 70.2%`, `left >= 5.5%`, `right <= 83.0%`) and `16:9` inside `youtube_16x9` (`top >= 8.0%`, `bottom <= 88.5%`, `left >= 6.0%`, `right <= 94.0%`). Vertical gameplay defaults to wide-FOV over live blurred fill with beat-driven scaling.

## 4. Mandatory Quality Gates & Visual Proof
- **Pre-Render Gate (`studio_kit/beat_sheet.py`):** Every video plan must pass zero-waste checks (concrete `visual_subject`, `narrative_purpose`, `broll_justification`, `visual_cause` or `contrast_rule` per SFX, `shot_cv >= 0.20`, Flow-of-Motion & Transition Restraint discipline, rest pockets).
- **Clean-Plate Grade & 5-Stem Audio (`studio_kit/color_grade.py` & `studio_kit/sound_engine.py`):** Grade raw footage BEFORE compositing crisp text/UI overlays. Mix audio across 5 stems (`voice`, `ambience` room tone, `foley`, layered `transitions`, `music` with key-matched tonal SFX, voice-pocket carving, Great Hall tails, and silence pockets). Never lay bare sine oscillators or random dry whooshes into digital silence.
- **Post-Render Proof (`studio_kit/acoustic_audit.py` + `read_file`):** Pass profile-aware loudness/spectral checks (`cinematic_essay`, `podcast_collage_short`, `narrative_voice_film`, `mograph_sfx`), run live Playwright `audit_html_safe_zones(...)`, and visually inspect rendered contact sheets via `read_file` before final handoff.
