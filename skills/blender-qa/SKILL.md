---
name: blender-qa
description: Use when verifying an asset before export or when asked "is it ready/ship?", audit, review, QA - runs all geometry, topology, UV bleed, visual reference match, rig, animation, and VFX audits, compares multi-angle look screenshots to the reference, and gives a SHIP or NO-SHIP verdict.
---
# QA (measured audits + AI vision reference match + verdict)

## Requires
state.md for the asset; all earlier stages PASS (no STALE). Screenshot tool (`look`) via MCP (or user-provided images in script mode).

## Inputs
Asset name | asset type (prop / env / char / hands / fx-mesh / fx-flipbook / fx-chunks / anim / camera).

## Steps
1. GATES: read `references/gates.md` for the asset type; list the required audits.
2. RUN every required audit now (do not reuse old JSON for STALE stages): `docs/blender/scripts/audit_mesh.py`, `docs/blender/scripts/audit_topology.py`, `docs/blender/scripts/audit_visual_match.py`, `docs/blender/scripts/audit_uv.py`, `docs/blender/scripts/audit_naming.py`, `docs/blender/scripts/audit_rig.py`, `docs/blender/scripts/audit_anim.py`, `docs/blender/scripts/audit_flipbook.py`, `docs/blender/scripts/audit_fx_style.py`, `docs/blender/scripts/audit_camera.py` as listed.
3. SCREENS per `references/screenshot-angles.md`: capture `look(mode="angles", views=["front", "right", "back", "three_quarter"], shading="material")` and `shading="wireframe"` (plus `look(mode="frames")` if animated); save to `blender-out/<asset>/screens/qa_*.png`.
4. AI VISION COMPARE AGAINST REFERENCE:
   - Compare the captured `look` views side-by-side against the reference image and `ref-analysis.md`:
     1. Silhouette & aspect ratio (`audit_visual_match.py` `pass = true`).
     2. Appendages & details (teeth, spikes, claws, hands, crystal shards are sharp, single-shell, and oriented properly).
     3. Texture & surface quality (`bleed_faces == 0`, zero missing-texture white occlusion patches, zero inverted black facets).
5. DEFECTS: classify per `references/verdict-template.md` section 2 (blocker, major, minor).
6. VERDICT: SHIP only with zero blockers and zero majors; minors listed. Else NO-SHIP with the route for each defect.
7. RECORD: write the verdict block (`references/verdict-template.md` section 1) to `blender-out/<asset>/qa.md`; update assets.md row and state.md.

## Hard rules
| Rule | Detail |
|---|---|
| Fresh audits | every required audit (including `audit_visual_match.py`) runs in this QA pass |
| Numbers | every pass/fail cites a JSON value |
| Vision match mandatory | QA must inspect `look` multi-angle renders against the reference image and verify zero missing-texture patches or bad appendages |
| Open assumptions | listed in the verdict; [UNVERIFIED] engine limits never count as compliance |
| Blockers | any audit fail, `bleed_ratio > 0.05`, budget overrun, STALE stage, missing file |
| No self-approval | do not edit thresholds to make an asset pass |
| Waivers | state.md waivers are listed in the verdict as accepted risk; a WAIVED gate is never reported as PASS |

## Done when
qa.md written with verdict; assets.md and state.md updated; each defect has a routed fix.

## On fail
| Failure | Action |
|---|---|
| Audit or `audit_visual_match.py` fails | route per routes.md section 4 or run surgical repair in `blender_kit_ops.py` |
| Screenshot unavailable | script mode: ask the user for images; verdict stays NO-SHIP until received |
| Stage STALE | re-run that stage's audit first |

## Next
SHIP -> blender-export. NO-SHIP -> the first routed fix skill.
