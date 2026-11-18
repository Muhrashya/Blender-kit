---
name: blender-topology
description: Use for clean quad topology, dual-target compilation (game_realtime quads-to-triangles vs film_cinematic 100% quad Catmull-Clark SubD control cages), double-shell stripping, holding loops, poles, joint loops, and rig-ready meshes.
---
# Topology: Universal Quad Control Cage -> Film SubD or Game Triangles

## Requires
`brief.md` (budget, `target_mode`, deforming yes/no, style, camera distance). A mesh from blender-model, blender-hands or blender-retopo. `docs/blender/engine.md` Rig section for influence/bone limits.

## Inputs
Budget (`config.md` row) | `target_mode` (`game_realtime` | `film_cinematic` | `dual_cage`) | deforming? | camera distance | armature or `Landmark Graph` if it exists.

## Steps
1. DECISION CHECK: if `state.md` has not locked the topology strategy (`Q1: Target compilation — game_realtime (quad rings at joints + beauty-triangulated static facets) vs film_cinematic (100% quad Catmull-Clark SubD cage) vs dual_cage (_HP + _LP)`, `Q2: Budget ceiling`), present the `Q1..Q2` decision list with `(Recommended)` first.
2. LOOK at `docs/blender/reference/figures/` (joint-loops, rig-ready-zones, transition-patterns). READ `references/rules.md` (always), `docs/blender/reference/deformation-zones.md` (deforming assets), `docs/blender/reference/transition-patterns.md` (density changes).
3. COMPILE TARGET TOPOLOGY (`mesh_compile_target` in `docs/blender/scripts/blender_kit_ops.py` or `docs/blender/scripts/optimize_quads_to_tris.py`):
   - **If `target_mode == "film_cinematic"`:**
     1. Restores/validates the un-triangulated quad control cage (`.kit_cage_<obj>`).
     2. Uses `mesh_subd_and_loops` (`kit_subd_and_loops`) to ensure holding loops (`segments=2, profile=1.0`) and `crease_edge` weights support sharp features without triangles or ngons.
     3. Attaches weight-driven `BEVEL` + Catmull-Clark `SUBSURF` (`uv_smooth='PRESERVE_BOUNDARIES'`).
   - **If `target_mode == "game_realtime"`:**
     1. Snapshots the source quad control cage into `.kit_cage_<obj>` so it can always be restored non-destructively.
     2. Welds coincident seams (`0.5mm`) and raycasts to strip hidden inner duplicate shells (`mesh_clean_and_strip_shells`).
     3. Preserves 3-ring quad loops within `joint_radius` of armature bones or `Landmark Graph` joints, dissolves flat coplanar interior edges (`planar_angle_deg = 2.5`), and beauty-triangulates non-planar static quads (`topo_optimize_quads_to_tris`).
   - **If `target_mode == "dual_cage"`:** generates both `SM_<Asset>_HP` (`film_cinematic`) and `SM_<Asset>_LP` (`game_realtime`).
4. AUDIT TOPOLOGY (`audit_run_isolated` / `docs/blender/scripts/audit_mesh.py` & `docs/blender/scripts/audit_topology.py`):
   - Run `audit_run_isolated(audit_type="all", target_mode=target_mode, budget=budget)` with `SELECT_DEFECTS = False`.
5. SYMMETRY & DEFECT REPAIR: run `docs/blender/scripts/audit_topology.py` with `SYMMETRIC=True` when symmetric. If ngons, joint poles, or `curved_surface_tris` (in `film_cinematic`) remain, run `blender-topology-fix`.
6. VISUAL & WIREFRAME VERIFICATION: call `look(mode="angles", views=["front", "right", "three_quarter"], shading="wireframe")` and `shading="solid"`; save to `screens/topo_*.png`.

## Rig-ready & dual-target checklist
| Check | Pass when (`game_realtime`) | Pass when (`film_cinematic`) | Source |
|---|---|---|---|
| Ngons | 0 | 0 | audit_topology |
| Curved-surface triangles | allowed on static facets | `curved_surface_tris == 0` | audit_topology |
| Closed quad pole balance | n/a when triangulated | `pole_balance % 8 == 0` ($\sum (4 - \text{valence})$) | audit_topology |
| Joint loops & poles | 0 poles/tris within 1 ring of joints | 0 poles/tris within 1 ring of joints | audit_topology joints |
| Double shells stripped | `stripped_inner_shells == 0` remaining | `stripped_inner_shells == 0` remaining | mesh_compile_target |
| Transforms | scale=1, rotation=0 applied | scale=1, rotation=0 applied | audit_mesh |
| Budget | evaluated `tris <= budget` | base cage quads within role row | audit_mesh |

## Hard rules
| Rule | Detail |
|---|---|
| n-gons | 0 in every final mesh across all target modes |
| Deforming zones | quads only within joint radius; no triangles or poles within 1 ring of a joint |
| Dual-target polarity | `film_cinematic` keeps 100% quad cages (`curved_surface_tris == 0`) with live `SUBSURF`; `game_realtime` beauty-triangulates static quads and strips `SUBSURF` |
| Preserve source cage | Always snapshot `.kit_cage_<obj>` before `game_realtime` triangulation so edits stay reversible |
| Context-free audits | Never rely on `bpy.context.selected_objects` (`SELECT_DEFECTS = False` by default) |

## Done when
`audit_run_isolated` (`audit_mesh.py` + `audit_topology.py`) passes for the active `target_mode`; rig-ready checklist all pass; wireframe `look` screenshots saved.

## On fail
| Failure | Action |
|---|---|
| ngons, thin/non-planar quads, poles near joints, or `curved_surface_tris > 0` in `film_cinematic` | blender-topology-fix (or restore `.kit_cage_<obj>` and re-run `mesh_subd_and_loops`) |
| Defect rate above fix thresholds | blender-retopo |
| Over budget in `game_realtime` | `references/rules.md` section 6 cut order + `mesh_compile_target`; then ask approval |
| Hands wrong | blender-hands |

## Next
blender-uv-bake (static) or after hands/topology: blender-uv-bake -> blender-material -> blender-rig (deforming).
