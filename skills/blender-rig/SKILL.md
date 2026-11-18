---
name: blender-rig
description: "Use when rigging a mesh for game_realtime or film_cinematic - declarative armature creation (rig_build_armature), bone hierarchies, IK/FK and bone constraints, analytical ENVELOPE_KDTREE or AUTO_HEAT skin weights, influence limits, and test poses."
---
# Rig (declarative armature, IK/constraints & deterministic skin weights)

## Requires
Mesh with `state.md` topology = PASS (or `Landmark Graph` coordinates in Swarm Phase 1). Hands done (characters). `docs/blender/engine.md` Rig rows (skeleton type, bone naming, influences, max bones). Transforms applied.

## Inputs
Rig type (humanoid / quadruped / mech-prop) -> read ONE file from `variants/`. `target_mode` (`game_realtime` max 4 influences vs `film_cinematic` max 8 influences + bendy bones).

## Steps
1. DECISION CHECK: if `state.md` has not locked rigging choices (`Q1: Weight binding mode — Analytical ENVELOPE_KDTREE vs AUTO_HEAT vs RIGID_BONE`, `Q2: IK & Constraint setup`), present `Q1..Q2` with `(Recommended)` first.
2. PRE-CHECK: in single-agent or Phase 2 mode, run `audit_run_isolated(audit_type="topology")` (`docs/blender/scripts/audit_topology.py`). Joint-zone pole/tri counts must be 0.
3. BUILD ARMATURE & CONSTRAINTS NATIVELY (`rig_build_armature` / `kit_rig_build_armature` in `docs/blender/scripts/blender_kit_ops.py`):
   - Pass `armature_name="ARM_<Asset>"`, `bones=[{name, head, tail, roll_deg, parent, use_connect, use_deform, bbone_segments}]` placed at exact `Landmark Graph` / measured joint centers with symmetric `.L` / `.R` names and single root bone.
   - Pass `constraints=[{bone, type: "IK"|"COPY_ROTATION"|"DAMPED_TRACK"|"LIMIT_ROTATION"|"STRETCH_TO", target_obj, subtarget, chain_count, pole_target, pole_subtarget, pole_angle_deg, influence}]`.
   - In Swarm Phase 1, pass `bind_meshes=[]` so `ARM_<Asset>` is authored without touching `SM_*` meshes.
4. SKIN & BIND WEIGHTS (Phase 2 Assembly or Single-Call):
   - Call `rig_build_armature` with `bind_meshes=[{mesh_name, bind_mode: "ENVELOPE_KDTREE"|"AUTO_HEAT"|"RIGID_BONE", max_influences: 4 (game) or 8 (film)}]`.
   - `ENVELOPE_KDTREE` computes analytical bone-segment distances, normalizes weights to `1.0`, and caps influences automatically even on multi-part non-manifold meshes where `AUTO_HEAT` fails.
5. HANDS: apply the weight ramps from `docs/blender/reference/hand-topology.md` section 8.
6. TEST POSES & VISUAL CHECK: test 3 poses per joint (`references/weights.md` section 4) and capture `look(mode="angles", shading="material")` + `shading="xray"`.
7. AUDIT: run `audit_run_isolated(audit_type="rig", armature_name="ARM_<Asset>", target_mode=target_mode)` (`docs/blender/scripts/audit_rig.py`) and `docs/blender/scripts/audit_naming.py`.

## Hard rules
| Rule | Detail |
|---|---|
| One root bone | and a single armature object `ARM_<Asset>` |
| Native context-free build | Use `rig_build_armature` (`kit_rig_build_armature`) so `EditBone` creation and weight binding are guarded by `atomic_context_guard` |
| Naming | `engine.md` rules first; else variant file names with `.L` / `.R` |
| Rest pose | the pose the mesh was modeled in; never skin in a different pose |
| Influences | `<= 4` for `game_realtime` (or `engine.md` limit); `<= 8` for `film_cinematic` |
| Weights | normalized (`sum == 1.0`), `unweighted_verts == 0` |
| Scale | armature scale 1, rotation applied |

## Done when
`audit_rig.py` / `audit_run_isolated(audit_type="rig")` pass; test pose `look` screenshots show no tears or collapse; weights normalized; `state.md` updated.

## On fail
| Failure | Action |
|---|---|
| `AUTO_HEAT` solver fails on disconnected parts | switch `bind_mode` to `"ENVELOPE_KDTREE"` or `"RIGID_BONE"` in `rig_build_armature` |
| Collapse or pinch at a joint | blender-diagnose row D -> blender-topology-fix (joint loops) |
| Too many influences | re-run `rig_build_armature` with `max_influences=4` |
| Candy-wrapper forearm | twist bones (`variants/humanoid.md` section 3) |

## Next
blender-animate (clips) or blender-qa -> blender-export.
