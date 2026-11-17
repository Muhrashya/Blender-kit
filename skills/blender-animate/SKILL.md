---
name: blender-animate
description: "Use when creating pro game animation clips in Blender - overlapping wave motion, floating crystal idles, walk, run, attack with anticipation/overshoot, gleam pulses, prop animations; loops, root motion, frame ranges, NLA, and frame-strip visual verification."
---
# Animate (pro game clips with overlapping motion & easing)

## Requires
Rigged asset with state.md rig = PASS. engine.md Animation rows (fps, clip source, loop flag, root motion, clip naming). Clip list from the brief.

## Inputs
Clips: name, type (loop / one-shot), motion recipe (`overlapping_wave` | `floating_idle` | `attack_anticipation` | `locomotion`), duration or frame count, root motion yes/no.

## Steps
1. DECISION CHECK: present `Q1..Q3` with `(Recommended)` defaults (`Q1: Motion Recipe — Pro Overlapping Wave / Floating Idle / Attack Anticipation`, `Q2: Frame Count & FPS`, `Q3: Combine with Gleam Sweep Pulse?`).
2. FPS: set scene fps from engine.md (UNVERIFIED -> ask in `Q2`; label [USER]). Never key at one fps and export at another.
3. CLIP LIST: write the table into state.md Decisions (name, frames, loop, root motion, recipe).
4. PRO MOTION GENERATION: read `references/pro-motion-recipes.md`, `references/cycles.md`, `references/combat.md`, `references/props.md`:
   - For serpentine, multi-segment, tail, cape, or floating crystal rigs: run `anim_pro_motion` from `docs/blender/scripts/blender_kit_ops.py` (`motion_type="overlapping_wave"` or `"floating_idle"`) so child bones follow parent bones with smooth phase-offset sine waves ($\Delta\phi = 0.45\text{–}0.75\text{ rad}$) and root-to-tip amplitude progression.
   - For attacks and interactions: key 3-phase poses (anticipation wind-up -> strike with `+8%` overshoot -> damped settle) using `BEZIER` `AUTO_CLAMPED` F-curves.
5. LOOPS: first and last pose identical (`loop_closed = True`); loop clip names end with `_loop` (config.md).
6. ROOT MOTION & NAMING: keep root fixed for in-place clips; name actions `AN_<Asset>_<Clip>` (+ `_loop`); set `use_fake_user = True`.
7. VISUAL FRAME-STRIP CHECK: call `look(mode="frames", target=[armature], frame_count=6, shading="material")` to visually verify smooth arcs, overlapping follow-through, and zero mesh tearing across the timeline.
8. AUDIT: run `docs/blender/scripts/audit_anim.py` (ROOT_BONE set when root motion matters); save key pose screenshots.

## Hard rules
| Rule | Detail |
|---|---|
| No robotic linear keys | Multi-bone chains must use phase-offset overlapping motion (`pro-motion-recipes.md`), never simultaneous flat keys |
| Fps | from engine.md before keying |
| Loops | closed channels (`audit_anim.py` `loop_closed = true`) |
| Frame-strip look | Every clip must be visually verified with `look(mode="frames")` before passing |
| Keys | no keys on non-deform helper bones unless baked for export |
| Evidence | durations in seconds are computed from frames and fps in the audit |

## Done when
audit_anim pass; every loop clip closed; `look(mode="frames")` confirms fluid overlapping motion with zero mesh tearing; key pose screenshots saved.

## On fail
| Failure | Action |
|---|---|
| Stiff / robotic motion | apply phase-offset wave (`anim_pro_motion`) and `AUTO_CLAMPED` Bezier handles per `references/pro-motion-recipes.md` |
| Loop pops | copy first key to last frame for all open channels |
| Mesh breaks in pose | blender-rig test poses / blender-diagnose |
| Clip not exported | blender-export animation option introspection |

## Next
blender-qa -> blender-export.
