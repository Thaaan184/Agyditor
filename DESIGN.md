# AGY Video Studio: Default Design & Brand Direction

Reading this as: Multi-profile local video and motion graphics studio for technical promo, kinetic editorial, and high-impact gaming edits, dial `ENERGY 2 / RHYTHM 3 / MOTION 3`.

## 1. Anti-Slop Dials (Default Studio Baseline)
- **ENERGY: 2 (Balanced-to-Bold):** Clean structural contrast and purposeful typography without neon or rainbow clutter.
- **RHYTHM: 3 (Varied & Asymmetric):** Every beat varies in duration, framing, and density. Uniform slide-show cadence is rejected by `studio_core.continuity_probe`.
- **MOTION: 3 (Choreographed & Continuous):** Elements carry across beat boundaries (`window.__seek(t)`) using measured spring and cubic-bezier curves rather than simultaneous fade-up template loops.

## 2. Core Palette & Typography Rules (One-Line Reasons per R-31)
- **Base Surface (`#0B0F17` Deep Carbon / `#F8FAFC` Editorial Paper):** Provides high-contrast ground (>12:1 WCAG AAA against primary text) so kinetic typography and UI callouts read effortlessly at 30/60fps.
- **Primary Text (`#F8FAFC` on Dark / `#0F172A` on Light):** Ensures instant legibility during fast camera moves.
- **Muted Technical Metadata (`#94A3B8`):** Separates secondary timestamps, coordinate labels, and subtitles from primary headlines while keeping contrast >= 4.6:1.
- **Single Deliberate Accent (Project-Scoped, e.g., `#0EA5E9` or Brand-Verified Hex):** Reserved strictly for the active focal point of each beat (R-29).
- **Typography:** Geometric sans for kinetic headlines (`Plus Jakarta Sans` / `Inter` / `Segoe UI` Bold) paired with tabular monospace (`JetBrains Mono` / `Consolas`) strictly for frame counters, code data, and numeric callouts (R-06).

## 3. Style Profiles
1. **`mograph-pro` (ENERGY 2 / RHYTHM 3 / MOTION 3):** Continuous camera carry, 1-focal-point composition per beat, room-matched synthesized foley transients.
2. **`gaming-montage` (Faide Reference - ENERGY 3 / RHYTHM 3 / MOTION 3):** Beat-synced cuts, velocity speed-ramps, zero HUD clutter, crisp transient audio hits.
3. **`gaming-comedic` (Windah / MILYHYA Reference - ENERGY 3 / RHYTHM 3 / MOTION 2):** Audio-first cut-and-play, BGM hard-cut silence before punchlines, 120% snap-zoom on expressive beats, color-coded word-level subtitles.
