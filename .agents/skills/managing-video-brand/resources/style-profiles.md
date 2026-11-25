# Video Style Profiles & Anti-Slop Dials

## 1. `mograph-pro` (Continuous Kinetic Editorial)
- **Dials:** `ENERGY 2 / RHYTHM 3 / MOTION 3`
- **Visual Rules:** Exactly one focal point per beat. At every beat boundary, at least one anchor element (a coordinate line, a card frame, a data pillar, or a kinetic word) survives on screen and physically morphs into the next beat (`carry_score >= 0.75`).
- **Audio Rules:** Synthesized room-matched transients (soft low sub-thud on expansion, crisp click on data lock, filtered air whoosh on camera whip).

## 2. `gaming-montage` (Faide Movement & Clutch Reference)
- **Dials:** `ENERGY 3 / RHYTHM 3 / MOTION 3`
- **Visual Rules:** Clean gameplay frame without sticker clutter. Velocity speed-ramps (`1.5x` into `0.4x` hit-stop into `1.2x` recovery) aligned within 1 frame of audio beat transients.
- **Audio Rules:** Weapon/movement transient boosted `+2.5 dB` over BGM; low-pass filter sweep during slow-motion pre-drop.

## 3. `gaming-comedic` (Windah Basudara & MILYHYA Reference)
- **Dials:** `ENERGY 3 / RHYTHM 3 / MOTION 2`
- **Visual Rules:** Hard cuts on speech completion. 115% to 130% instant snap-zoom on facecam or subject reaction. Word-level subtitles positioned in lower safe zone with color shifts strictly tied to vocal pitch/volume peaks.
- **Audio Rules:** Mandatory BGM hard-cut (`0.0` amplitude) `0.15s` to `0.5s` before comedic punchline or awkward silence, followed by a single dry stinger SFX.

## 4. Calibrated Text, Subtitle & Transition Baseline
- **Never Ship Unstyled System Fonts:** All profiles MUST load bundled `.woff2` or `.ttf` faces from `studio_kit/fonts/` via explicit `@font-face` rules and call `await document.fonts.load(...)`. Unbundled `Segoe UI` fallbacks are rejected.
- **Profile-to-Primitive Routing (`studio_kit/motion_primitives.js` & `studio_kit/motifs/`):**
  - `mograph-pro`: Combine `kinetic-3d-spatial` (Mixed-Voice `Inter Tight` + italic `Instrument Serif` + DoF blur) with `rolling-cylinder-slot`, `smoothMaskReveal`, and `180-360` deg shutter motion blur.
  - `talking-head-reel`: Prefer `apple-follower-reveal` (`2-frame` per-glyph stagger + blur resolve) and `ghost-echo-kinetic` (`0.20` residual echo trail) over uniform block fades; use `object-separation` only for `1s-3s` hook behind-subject cutouts on CPU.
  - `gaming-comedic` & `gaming-montage`: Keep frame clean with ultra-brief 1-2 punch words tied to `faster-whisper` / `librosa` spikes (`ghost-echo-kinetic`, `rolling-cylinder-slot`, or `cutoutFrameHoldSlide` 5-8 frame overlap) instead of flat CSS caption cards.
