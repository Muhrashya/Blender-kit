---
name: blender-topology
description: Use for clean topology, smart quads-to-triangles optimization, edge flow, polycount and triangle budgets, double-shell stripping, poles, joint loops, and rig-ready meshes - whenever a mesh must be light, crisp, and easy to rig, UV and export.
---
# Topology: clean quad flow + smart quads-to-triangles + rig-ready

## Requires
brief.md (budget, deforming yes/no, style, camera distance). A mesh from blender-model, blender-hands or blender-retopo. `docs/blender/engine.md` Rig section for influence/bone limits.

## Inputs
Budget (config.md row) | deforming? | camera distance | armature if it already exists | quad-to-tri policy (`joint_quads_static_tris` | `strict_quads`).

## Steps
1. DECISION CHECK: if `state.md` has not locked the topology strategy (`Q1: Keep quad rings at joints + beauty-triangulate static facets vs strict all-quads`, `Q2: Triangle budget ceiling`), present the `Q1..Q2` decision list with `(Recommended)` first.
2. LOOK at `docs/blender/reference/figures/` (joint-loops, rig-ready-zones, transition-patterns). READ `references/rules.md` (always), `docs/blender/reference/deformation-zones.md` (deforming assets), `docs/blender/reference/transition-patterns.md` (density changes).
3. STRIP DOUBLE SHELLS & OPTIMIZE QUADS-TO-TRIANGLES:
   - Run `docs/blender/scripts/optimize_quads_to_tris.py` (or `topo_optimize_quads_to_tris` in `docs/blender/scripts/blender_kit_ops.py`):
     1. Welds coincident seams (`0.5mm`) and raycasts to strip hidden inner duplicate shells (`STRIP_INNER_SHELLS = True`).
     2. Preserves 3-ring quad loops within `JOINT_RADIUS` of deforming armature joints.
     3. Dissolves flat coplanar interior edges (`PLANAR_ANGLE_DEG = 2.5`) that do not change the silhouette.
     4. Applies curvature-aware `BEAUTY` triangulation (`quad_method='BEAUTY'`) to non-planar static quads so low-poly facets shade crisply without folding.
4. BUDGET -> SILHOUETTE -> REMOVE -> BAKE -> MEASURE (`references/rules.md` section 6):
   - Delete hidden interior/bottom faces; run `docs/blender/scripts/audit_mesh.py` (`BUDGET` set) and `docs/blender/scripts/audit_topology.py` (`ARMATURE` set when it exists).
5. DEFORMING & SYMMETRY: place joint loops per `docs/blender/reference/deformation-zones.md`; run `docs/blender/scripts/audit_topology.py` with `SYMMETRIC=True` when symmetric.
6. FIX DEFECTS: if ngons, joint poles, or flipped normals remain, run `blender-topology-fix` with the defect map.
7. VISUAL & WIREFRAME VERIFICATION: call `look(mode="angles", views=["front", "right", "three_quarter"], shading="wireframe")` and `shading="solid"` to confirm clean facet flow and zero shading inversions; save to `screens/topo_*.png`.

## Rig-ready checklist (deforming assets)
| Check | Pass when | Source |
|---|---|---|
| Rest pose | A-pose (or engine pose), slight bend at elbows/knees | model variant |
| Symmetry | mirror_unmatched = 0, off-plane = 0 | audit_topology |
| Joint loops | per deformation-zones.md tier | visual + loop count |
| Poles near joints | 0 | audit_topology joints |
| Ngons / tris in joint zones | 0 / 0 | audit_topology joints |
| Double shells stripped | stripped_inner_shells = 0 remaining | optimize_quads_to_tris |
| Custom split normals | has_custom_normals = False | audit_visual_match |
| Transforms | scale/rotation applied | audit_mesh |
| Hands | ring continuity forearm -> wrist -> palm | blender-hands |
| Budget | tris <= budget | audit_mesh |

## Hard rules
| Rule | Detail |
|---|---|
| n-gons | 0 in every final mesh |
| Deforming zones | quads only within joint radius; no triangles or poles within 1 ring of a joint |
| Static / low-poly facets | beauty-triangulate non-planar quads and dissolve coplanar interior loops via `optimize_quads_to_tris.py` |
| Subdivision | never used to get roundness; no subdivision modifier on exports |
| Numbers | every count quoted comes from the audit JSON of this session |
| Budget overrun | needs user approval; otherwise cut in the rules.md section 6 order |

## Done when
audit_mesh.pass = true AND audit_topology: ngons = 0, poles_near_joints = [] (deforming), double shells stripped, custom normals cleared, rig-ready table all yes, and wireframe `look` screenshots verified.

## On fail
| Failure | Action |
|---|---|
| ngons, thin or non-planar quads, poles near joints, missing joint loops | blender-topology-fix |
| Defect rate above fix thresholds | blender-retopo |
| Over budget | rules.md section 6 cut order + `optimize_quads_to_tris.py`; then ask approval |
| Silhouette lost after cuts | restore checkpoint; cut elsewhere |
| Hands wrong | blender-hands |

## Next
blender-uv-bake (static) or after hands/topology: blender-uv-bake -> blender-material -> blender-rig (deforming).
