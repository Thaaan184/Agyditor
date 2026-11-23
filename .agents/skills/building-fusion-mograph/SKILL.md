---
name: building-fusion-mograph
description: >-
  Generates native DaVinci Resolve Fusion motion graphics (.setting macros, .comp files, .drfx bundles,
  and copy-pasteable Lua node graphs) that work 100% in DaVinci Resolve Free. Includes KeyFrameStretcher
  for responsive duration scaling and UserControls for Edit Page Inspector tweaking.
---

# Building Native DaVinci Resolve Fusion Mograph

## When to use this skill
- When creating non-destructive titles, lower thirds, callouts, HUD elements, or transitions for DaVinci Resolve Free.
- When packaging reusable `.setting` macros into `.drfx` bundles for one-click installation into Resolve's Effects Library.

## Workflow Checklist
- [ ] **Step 1: Read Brand Tokens** - Load `.agents/skills/managing-video-brand/resources/video-design-tokens.json` to get verified RGB values and typography.
- [ ] **Step 2: Generate Lua Macro** - Use `studio_core.fusion_lua.generate_kinetic_callout_setting()` or author a custom ordered Lua table with `MacroOperator`.
- [ ] **Step 3: Validate Node Graph** - Run `studio_core.fusion_lua.validate_fusion_setting()` to enforce brace balance, `KeyFrameStretcher`, `InstanceInput` Inspector controls, and `MediaOut1` termination.
- [ ] **Step 4: Package `.drfx`** - Bundle validated `.setting` files into a `.drfx` archive under `Fusion/Templates/Edit/Titles/` (or `Effects/` / `Transitions/`) using `studio_core.fusion_lua.package_drfx()`.

## Core Rules
1. Never flatten simple callouts or titles into baked MP4s when a native `.setting` macro lets the user edit text, size, color, and duration live on the DaVinci Resolve Free Edit Page.
2. Always include `MotionBlur = Input { Value = 1 }` and `ShutterAngle = Input { Value = 180 }` on primary `Transform` nodes so fast kinetic entrances smear naturally instead of strobing.
