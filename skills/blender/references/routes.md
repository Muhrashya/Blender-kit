# Routes (universal mode -> stage chain) and invalidation

Contents: 1 chains | 2 stage gates | 3 invalidation | 4 failure routing | 5 skip rules

## 1. Chains
| Mode / Archetype | Chain (in order) |
|---|---|
| prop (furniture, items, food, tools, loot) | ref? -> model(prop) -> topology -> uv-bake -> material -> qa -> export |
| weapon / armor (swords, guns, shields, helmets) | ref? -> model(weapons-armor) -> topology -> uv-bake -> material -> rig? -> vfx?(gleam) -> qa -> export |
| vehicle / mech (cars, aircraft, boats, spaceships) | ref? -> model(vehicles) -> topology -> uv-bake -> material -> rig?(wheels/turrets) -> animate? -> qa -> export |
| arch / interior (buildings, rooms, stairs, arches) | ref? -> model(architecture-interior) -> topology -> uv-bake -> material -> qa -> export |
| env (modular grid kits, walls, floors, trims) | ref? -> model(env-kit) -> topology -> uv-bake -> material -> qa -> export |
| nature (trees, foliage, rocks, cliffs, crystals) | ref? -> model(nature-foliage) -> topology -> uv-bake -> material -> vfx?(gleam/wind) -> qa -> export |
| char (humanoids, avatars, NPCs) | ref? -> model(character) -> hands -> retopo? -> topology -> uv-bake -> material -> rig -> animate? -> qa -> export |
| creature (animals, monsters, serpents, pets) | ref? -> model(creature) -> retopo? -> topology -> uv-bake -> material -> rig -> animate? -> qa -> export |
| hands | ref? -> hands -> topology -> qa |
| match | ref -> (chain of the object class found in ref-analysis.md) |
| retopo | retopo -> topology -> uv-bake -> qa |
| fix | topology-fix -> topology -> qa |
| rig | topology (rig-ready check) -> rig -> qa |
| anim | animate -> qa -> export |
| fx | vfx -> (vfx-texture / vfx-mesh / vfx-sim -> vfx-flipbook) -> qa -> export (optional showcase shot: camera) |
| cam | camera -> qa -> export (only if engine.md Camera rows allow; else deliver renders) |
| optimize | topology-fix -> topology -> qa |
| export | qa -> export |
| audit | topology -> qa |
`?` = only when the brief or `Q1..Qn` decision list asks for it. `retopo?` = only when the source is a sculpt or an AI-generated mesh.

## 2. Stage gates (a stage PASSES only when)
| Stage | Gate (all required) |
|---|---|
| ref | ref-analysis.md complete; `Q1..Q3` creation decisions locked; no critical unknown left |
| model | `look` silhouette matches ref (`audit_visual_match.py` pass); objects named; transforms applied; tris <= 1.5 x budget |
| topology | `audit_mesh.py` pass; `optimize_quads_to_tris.py` pass (ngons 0, double shells stripped, poles not near joints, tris <= budget) |
| topology-fix | `audit_topology.py` counts at or below thresholds in blender-topology-fix; before/after numbers reported |
| retopo | audit pass; silhouette HP vs LP match; HP kept |
| hands | per-hand tris within the hand budget; ring continuity true; joint loops present |
| uv-bake | `has_uv`; texel density within tolerance; `audit_visual_match.py` `bleed_ratio <= 0.05`; bake verified by `look` |
| material | only exportable Principled PBR + clean textures; zero white occlusion blotches; names `MAT_`/`T_` |
| rig | `audit_rig.py` pass; 3 test poses per joint without artifacts (`look` screenshots) |
| animate | `audit_anim.py` pass; loop clips closed; `look(mode="frames")` confirms fluid overlapping motion |
| vfx-* | their own audit pass; flipbooks also `audit_fx_style.py`; FX spec complete |
| camera | `audit_camera.py` pass for every shot; shot list complete; screenshots saved |
| qa | verdict SHIP (`audit_visual_match.py` pass + zero blockers/majors) |
| export | file exists and non-empty; export report written |

## 3. Invalidation (a change at stage S marks these STALE)
| Changed | Stages that become STALE |
|---|---|
| model, retopo, topology-fix, topology (mesh edited) | uv-bake, material, hands, rig, animate, qa, export |
| uv-bake (UV edited) | material, qa, export |
| material | qa, export |
| rig (bones, weights) | animate, qa, export |
| animate | qa, export |
| vfx-* | qa, export |
| camera (shots or subject moved) | qa, export |
STALE stage = run its audit again before continuing. Do not redo the whole stage unless the audit fails.

## 4. Failure routing
| Failing check | Go to |
|---|---|
| ngons, thin or non-planar quads, poles near joints, missing joint loops, double shells | blender-topology-fix / `optimize_quads_to_tris.py` |
| topology-fix defect rate above its escalation threshold | blender-retopo |
| rig deformation artifacts | blender-diagnose -> topology-fix -> rig |
| bake artifacts, stretched textures, white occlusion patches, UV bleed | blender-uv-bake -> blender-material |
| wrong scale/axis in engine | blender-export (import test), then blender-diagnose |
| camera audit fails (framing, horizon, clip planes) | blender-camera |
| flipbook style audit fails | blender-vfx (style fixes), then the sub-skill |
| unknown symptom | blender-diagnose |

## 5. Skip rules (adaptive chain; every skip is a Decision labeled [ASSUMED], reversible by the user)
| Condition | Skip or shorten |
|---|---|
| no reference image | skip ref |
| static asset (no deforming, no animation) | skip rig and animate; topology uses static rules (`optimize_quads_to_tris.py`) |
| source is not a sculpt, scan or AI mesh | skip retopo |
| style voxel or lowpoly with palette | uv-bake takes the zero-bleed per-facet cell atlas or palette path |
| character with blocky hands (voxel) | blender-hands blocky variant |
| FX type gleam sweep or mesh only | skip flipbook and sim |
| camera-only request | skip every asset stage |
| quick path: role prop-small AND style voxel or lowpoly AND balanced or flex rigor | model -> topology -> uv-bake (palette) + material in one turn -> qa -> export |
