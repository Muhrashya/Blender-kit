---
name: blender-qa
description: Use when verifying an asset before export or when asked "is it ready/ship?", audit, review, QA - runs context-free isolated audits (audit_run_isolated) across geometry, dual-target topology (game_realtime vs film_cinematic SubD), UV bleed, visual reference match, rig, and animation, and records a SHIP or NO-SHIP verdict.
---
# QA (context-free isolated audits + AI vision reference match + verdict)

## Requires
`state.md` for the asset; all earlier stages PASS (no STALE). Screenshot tool (`look`) via MCP (or user-provided images in script mode).

## Inputs
Asset name | asset type (`prop` / `env` / `char` / `hands` / `fx-mesh` / `fx-flipbook` / `fx-chunks` / `anim` / `camera`) | `target_mode` (`game_realtime` | `film_cinematic` | `dual_cage`).

## Steps
1. GATES: read `references/gates.md` for the asset type and active `target_mode`; list the required audits.
2. RUN CONTEXT-FREE ISOLATED AUDITS (`audit_run_isolated` / `kit_audit_run_isolated` in `docs/blender/scripts/blender_kit_ops.py`):
   - Pass explicit `target_objects=[...]` and `target_mode` (never relying on `bpy.context.selected_objects`).
   - Also run stage scripts as needed: `docs/blender/scripts/audit_mesh.py`, `docs/blender/scripts/audit_topology.py`, `docs/blender/scripts/audit_visual_match.py`, `docs/blender/scripts/audit_uv.py`, `docs/blender/scripts/audit_naming.py`, `docs/blender/scripts/audit_rig.py`, `docs/blender/scripts/audit_anim.py`, `docs/blender/scripts/audit_flipbook.py`, `docs/blender/scripts/audit_fx_style.py`, `docs/blender/scripts/audit_camera.py`.
3. SCREENS per `references/screenshot-angles.md`: capture `look(mode="angles", views=["front", "right", "back", "three_quarter"], shading="material")` and `shading="wireframe"` (plus `shading="rendered"` for `film_cinematic` and `look(mode="frames")` if animated); save to `<session_dir>/assets/<asset>/screens/qa_*.png`.
4. AI VISION COMPARE AGAINST REFERENCE:
   - Compare the captured `look` views side-by-side against the reference image and `ref-analysis.md`:
     1. Silhouette & aspect ratio (`audit_visual_match.py` `pass = true`).
     2. Dual-target topology integrity (`film_cinematic`: `ngons == 0`, `curved_surface_tris == 0`, `pole_balance % 8 == 0`, `SUBSURF` live; `game_realtime`: `ngons == 0`, `tris <= budget`, `poles_near_joints == 0`).
     3. Texture & surface quality (`bleed_faces == 0`, zero missing-texture white occlusion patches, zero inverted black facets).
5. DEFECTS: classify per `references/verdict-template.md` section 2 (blocker, major, minor).
6. VERDICT: SHIP only with zero blockers and zero majors; minors listed. Else NO-SHIP with the route for each defect (and in Swarm Mode, route strictly to the owning specialist `agent_role`).
7. RECORD: write the verdict block (`references/verdict-template.md` section 1) to `<session_dir>/assets/<asset>/qa.md`; update `assets.md` row and `state.md`.

## Hard rules
| Rule | Detail |
|---|---|
| Context-free & read-only | QA audits run with `agent_role="auditor"` (`READ_ONLY`) on explicit `target_objects` lists and never mutate viewport selection |
| Fresh audits | every required audit runs in this QA pass |
| Numbers | every pass/fail cites a JSON value |
| Vision match mandatory | QA must inspect `look` multi-angle renders against the reference image |
| Blockers | any audit fail, `bleed_ratio > 0.05`, budget overrun, `curved_surface_tris > 0` in `film_cinematic`, STALE stage, missing file |
| No self-approval | do not edit thresholds to make an asset pass |
| Waivers | `state.md` waivers are listed in the verdict as accepted risk; a WAIVED gate is never reported as PASS |

## Done when
`qa.md` written with verdict; `assets.md` and `state.md` updated; each defect has a routed fix.

## On fail
| Failure | Action |
|---|---|
| Audit or `audit_visual_match.py` fails | route per `routes.md` section 4 to the owning specialist role or run surgical repair in `blender_kit_ops.py` |
| Screenshot unavailable | script mode: ask the user for images; verdict stays NO-SHIP until received |
| Stage STALE | re-run that stage's audit first |

## Next
SHIP -> blender-export. NO-SHIP -> the first routed fix skill.
