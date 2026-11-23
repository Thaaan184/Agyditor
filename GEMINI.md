# AGY Video Editor: Workspace Rules & Anti-Slop Guardrails

## 1. Local-First & Free Tooling Constraint (Strict)
- NEVER invoke, suggest, or route tasks to the `invideo` plugin skills or paid cloud video web apps.
- NEVER use paid per-second video generation APIs unless explicitly requested by the user.
- All video, audio, transcript, and motion graphic pipelines MUST run locally using free tools: FFmpeg (`bin/ffmpeg.exe` or system PATH), FFprobe (`bin/ffprobe.exe` or system PATH), Python 3.11 (`faster-whisper`, `librosa`, `numpy`, `scipy`, `playwright`), Node.js 24 (`hyperframes` CLI, `onetake`), and DaVinci Resolve Free.

## 2. Hardware & Storage Guardrails (Ryzen 5 5500 / 16GB RAM / GTX 1650)
- Keep all project workspaces, intermediate renders, Chromium caches, and audio analyses on drive `D:` (`d:/Files/Project Iseng/AGY Video Editor`). Do not dump heavy temporary video files on `C:`.
- Default renders to `1920x1080` (or `1080x1920` vertical) at `30fps` (or `60fps` for gaming/montage finals). Do not default to 4K60 multi-sample shutter blur unless the user explicitly asks for an overnight final render.
- Run local speech/audio models with `int8` or `float16` quantization on CUDA (GTX 1650 4GB VRAM) or CPU fallback to prevent VRAM out-of-memory errors.

## 3. Anti-Slop Video & Motion Principle (`antislop` Integration)
- Every visual cut, zoom, transition, motion graphic, and SFX placement MUST pass a purpose test (R-19, R-31): state in one line what narrative, rhythmic, or comedic beat it serves.
- FORBIDDEN copywriting and punctuation patterns: zero em dashes and zero en dashes in any prose, subtitle, or title card (R-02); zero generic AI buzzwords (`revolutionary`, `seamless`, `cutting-edge`, `next-level`, `AI-powered`, `game-changer`) (R-16); zero fabricated numbers, metrics, or testimonials (R-17, R-18, R-36, R-38).
- FORBIDDEN visual slop patterns: uniform slide-show cadence ("PPT style"), gratuitous blue-to-purple gradients without brand proof (R-01), continuous background music with no dynamic ducking or cut-outs, and unmotivated camera shakes.
- Before generating motion graphics or subtitle styles, read `.agents/skills/managing-video-brand/SKILL.md` and `DESIGN.md` to lock the active `ENERGY`, `RHYTHM`, and `MOTION` dials.

## 4. DaVinci Resolve Free & Fusion Native Priority
- Do not assume DaVinci Resolve External Scripting API (`fuscript` / remote MCP) is available, because DaVinci Resolve Free blocks external process scripting.
- Always prioritize non-destructive, re-tweakable deliverables for DaVinci Resolve Free:
  1. **Editorial Timelines:** Export `.fcpxml` (Final Cut Pro XML v1.9 compatible with Resolve) + `.srt` with separate tracks for Base/Gameplay (`V1`), Facecam/Punch-in Zoom (`V2`), Mograph Overlays (`V3`), Dialogue (`A1`), SFX (`A2`), and BGM (`A3`).
  2. **Native Fusion Mograph:** Generate editable Fusion macros (`.setting` / `.drfx` / Lua node clipboard snippets) with `KeyFrameStretcher` and Inspector `UserControls` so parameters and duration can be tweaked directly inside DaVinci Resolve Free.
