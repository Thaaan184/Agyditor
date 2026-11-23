---
name: editing-gaming-clips
description: >-
  Executes audio-first gaming and narrative video editing (Faide montage, Windah comedic timing, MILYHYA cut-and-play)
  directly on a live WeftCut NLE timeline via MCP, paired with local faster-whisper transcription, librosa beat analysis,
  role-based SFX/BGM ducking, and programmable WeftCut Motifs.
---

# Editing Gaming Clips & Narrative Videos (WeftCut MCP + Local Audio)

## When to use this skill
- When editing raw gameplay, stream VODs, or narrative talking-head footage with tight cut-and-play pacing.
- When syncing montage cuts to music beats (Faide style) or placing comedic SFX and music cut-outs (Windah / MILYHYA style) in WeftCut.

## Workflow Checklist
- [ ] **Step 1: Connect & Inspect WeftCut Timeline** - Verify WeftCut MCP via `weftcut_status` (or launch via `launch_weftcut`) and inspect active media/layers with `read_project`.
- [ ] **Step 2: Audio & Transcript Recon** - Extract clip audio (`extract_clip_audio` or `bin/ffmpeg.exe`), run `faster-whisper` (`int8` / `float16` on GTX 1650) for word-level timestamps, run `detect_pauses` for dead air, and use `librosa` to map music beat/onset timestamps for montages.
- [ ] **Step 3: Interactive Cut-Sheet & Tacks Review** - Present candidate highlight cuts, dead-air cuts, and punchline SFX moments using WeftCut `create_tacks` (or a chat cut-sheet) before executing destructive edits.
- [ ] **Step 4: Cut-and-Play & Role Audio Mixing** - Execute `remove_pauses`, `split_layer`, `trim_layer`, and `shift_layers`. Enforce BGM hard-cuts (`set_keyframe` on volume or split/mute music role) `0.15s` to `0.5s` before comedic punchlines, and place dry SFX hits on the SFX role track.
- [ ] **Step 5: Visual Cleanliness & Dynamic Motifs** - Apply `115%` to `130%` snap-zooms via `set_keyframe` on reaction beats, add animated word-level captions (`apply_subtitles`) or custom HTML/CSS/SVG Motifs (`motif.define`) with zero web-page chrome.
- [ ] **Step 6: Verify & Export** - Audit the timeline diff in WeftCut Agent View (`Changes` / `Tacks`), preview frames with `compare_frames`, and export H.264/HEVC MP4 when approved.
