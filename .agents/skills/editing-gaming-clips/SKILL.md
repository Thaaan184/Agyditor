---
name: editing-gaming-clips
description: >-
  Executes audio-first gaming and narrative video editing (Faide montage, Windah comedic timing, MILYHYA cut-and-play)
  directly on a live WeftCut NLE timeline via MCP, paired with local faster-whisper transcription, librosa beat analysis,
  role-based SFX/BGM ducking, and programmable WeftCut Motifs.
---

# Editing Gaming Clips & Narrative Videos (WeftCut MCP + Local Audio)

## When to use this skill
- When brainstorming (`/grill-me`) or editing raw gameplay, stream VODs, or narrative talking-head footage with tight cut-and-play pacing.
- When syncing montage cuts to music beats (Faide style) or placing comedic SFX, freeze whip-zooms, and music cut-outs (Windah / MILYHYA / Shorts montage style) via WeftCut MCP or the local FFmpeg + Playwright transparent overlay pipeline.

## Brainstorm & `/grill-me` Alignment (Step 0)
Before cutting or building overlays for a gaming clip, align on these 5 points (skip any point already answered by the user):
1. **Story / Arc:** Comedic or lucky moment, beat-synced montage, or clutch/ace showcase? Route editorial pacing/loudness via `studio_kit/context_router.py`.
2. **Vertical Framing:** Wide-FOV over live blurred top/bottom fill with dynamic beat scaling (default), or tight vertical crop?
3. **Overlay & Subtitle Policy:** Zero HTML cards; box-less subtitles strictly inside the `universal_vertical` safe zone (`studio_kit/safe_zones.py`: `top >= 13.5%`, `bottom <= 70.2%`, `left >= 5.5%`, `right <= 83.0%`), language matching comms, plus optional raw in-game HUD crops (e.g. killfeed).
4. **Reference Study:** Download user-provided Shorts/Reels with `bin/yt-dlp.exe` and inspect frames/audio to extract concrete camera/transition mechanics (horizontal smear-blur, freeze whip-zoom, brush-slash finisher).
5. **Output & Versioning:** Confirm exact output folder (e.g. `D:\Clip\Edit\<Game>\`) and versioned filenames (`draft_edit_1`, `v2`).

## Workflow Checklist
- [ ] **Step 1: Connect & Inspect Timeline / Source** - For WeftCut NLE editing, verify WeftCut MCP via `weftcut_status` (or launch via `launch_weftcut`) and inspect active media/layers with `read_project`. For scripted vertical edits, probe source specs (`bin/ffprobe.exe`) and extract recon contact sheets (`bin/ffmpeg.exe`) to verify HUD/target coordinates.
- [ ] **Step 2: Audio, Censor & Transcript Recon** - Extract clip audio (`extract_clip_audio` or `bin/ffmpeg.exe`), run `faster-whisper` (`int8` / `float16` on GTX 1650) for word-level timestamps, run `detect_pauses` for dead air, and use `librosa` to map music beat/onset timestamps. For profanity censor bleeps or tight comedic SFX, measure the voice-band envelope (50ms windows) and listen directly to the rendered audio via `read_file` to verify the exact span before final mux.
- [ ] **Step 3: Interactive Cut-Sheet & Tacks Review** - Present candidate highlight cuts, dead-air cuts, and punchline SFX moments using WeftCut `create_tacks` (or a chat cut-sheet) before executing destructive edits.
- [ ] **Step 4: Cut-and-Play & Role Audio Mixing** - Execute `remove_pauses`, `split_layer`, `trim_layer`, and `shift_layers`. Route the audio timeline into `studio_kit/sound_engine.py` 5-stem role exports (`stems/*.wav` + `weftcut_stem_plan.json`) or matching WeftCut role tracks (`dialogue`, `ambience` room-tone bedrock across cuts for J/L-cut continuity, `sfx`, `bgm`): NEVER synthesize fake BGM from raw `np.sin`/noise loops and NEVER overuse sustained tonal drones until the mix buzzes. Use real BGM or let native game audio breathe, apply LPF muffle sweeps (`add_filter_sweep`) or BGM hard cut-outs `0.15s` to `0.5s` before comedic punchlines, and pick restrained, context-matched comedic accents from `studio_kit/sfx/meme_pack/` (`meme/*` in `sound_palette_index.json`).
- [ ] **Step 5: Clean-Plate Grade, Wide-FOV Blur Fill & Spatial Safe-Zone Overlays** - Validate zero-waste B-roll justifications via `studio_kit/beat_sheet.py`. Apply clean-plate grading via `studio_kit/color_grade.py` BEFORE compositing crisp overlays when color polish helps. On vertical gaming edits, use sharp `aeWhipOut` camera snaps instead of sluggish smoothstep drifts, cut filler cleanly instead of long flat speed-ups, vary subtitle spatial topology inside `studio_kit/safe_zones.py` (`universal_vertical`: `top >= 13.5%`, `bottom <= 70.2%`, `right <= 83.0%`) instead of parking every line at one bottom Y coordinate, highlight real gameplay comedy via raw cropped in-game HUD elements (no HTML cards or pasted SVG arcs), and load bundled local fonts (`studio_kit/fonts/`) with zero web-page chrome.
- [ ] **Step 6: Verify & Export** - Audit the timeline diff in WeftCut Agent View (`Changes` / `Tacks`), inspect mid-motion preview frames and contact sheets with `compare_frames` / `read_file`, pass `studio_kit/acoustic_audit.py` under the matching loudness/spectral profile, and export H.264/HEVC MP4 to the confirmed destination folder.
