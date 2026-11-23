---
name: editing-gaming-clips
description: >-
  Executes audio-first gaming and narrative video editing (Faide montage, Windah comedic timing, MILYHYA cut-and-play).
  Performs local audio peak/silence/beat detection, interactive Cut-Sheet approval, SFX/BGM ducking,
  and exports editable DaVinci Resolve Free timelines (.fcpxml + .srt) or direct MP4s.
---

# Editing Gaming Clips & Editorial Timelines

## When to use this skill
- When editing raw gameplay, stream VODs, or narrative talking-head footage with tight cut-and-play pacing.
- When building multi-track DaVinci Resolve Free timelines (`.fcpxml` + `.srt`) with separate Gameplay (`V1`), Punch-in Zoom (`V2`), Mograph (`V3`), Voice (`A1`), SFX (`A2`), and ducked BGM (`A3`).

## Workflow Checklist
- [ ] **Step 1: Synthesize or Verify Local SFX Catalog** - Use `studio_core.audio_engine.synthesize_sfx_catalog()` to ensure clean, room-matched WAV transients exist in `sfx/`.
- [ ] **Step 2: Audio & Transcript Recon** - Detect vocal peaks, dead-air intervals, and BGM beat timestamps.
- [ ] **Step 3: Audio Mixing & Punchline Silence** - Use `studio_core.audio_engine.mix_editorial_audio()` to enforce hard BGM silence (`0.0` amplitude) during `punchline_windows` and `-18 dB` ducking under active dialogue.
- [ ] **Step 4: Build Resolve Editorial Timeline** - Call `studio_core.fcpxml_builder.build_fcpxml_timeline()` and `export_srt()` to produce non-destructive `.fcpxml` and `.srt` files ready for `File -> Import -> Timeline` in DaVinci Resolve Free.
