---
name: blender-model
description: Use when building or editing ANY 3D asset (game_realtime or film_cinematic SubD) from a brief or reference image - props, weapons, armor, vehicles, buildings, nature/foliage/crystals, modular kits, characters, creatures. Uses context-free native MCP BMesh, SubD holding-loop/crease, modifier, and curve tools, and verifies visually with look.
---
# Model (universal native BMesh, SubD control cage & image-to-3D -> verified base mesh)

## Requires
`brief.md` (budget, style, `target_mode`, engine). `ref-analysis.md` when a reference exists. `state.md`.

## Inputs
Universal asset archetype -> read ONE file from `variants/`:
- `variants/prop.md` (crates, furniture, tools, food, loot, everyday objects)
- `variants/hard-surface.md` (machines, robots, electronics, sci-fi panels, turrets)
- `variants/weapons-armor.md` (swords, axes, bows, firearms, shields, helmets, armor)
- `variants/vehicles.md` (cars, bikes, spaceships, boats, aircraft, tanks, mechs)
- `variants/architecture-interior.md` (buildings, rooms, arches, stairs, roofs, furniture)
- `variants/env-kit.md` (snap-to-grid modular walls, floors, trims, dungeons)
- `variants/nature-foliage.md` (trees, bushes, rocks, cliffs, crystals, terrain)
- `variants/character.md` (humanoids, stylized/bloxy avatars, NPCs)
- `variants/creature.md` (animals, monsters, birds, fish, serpents, bosses, pets)

## Steps
1. DECISION CHECK: if `state.md` lacks modeling decisions (`Q1: Creation method — Native Quad Cage/BMesh vs Hybrid AI Image-to-3D + Surgical Cleanup`, `Q2: Target mode (game_realtime vs film_cinematic SubD) & dimensions`, `Q3: Sub-part PartSpec split`), present `Q1..Q3` with `(Recommended)` first.
2. SCENE & CHECKPOINT: verify metric units (`unit_scale 1.0`) via `docs/blender/scripts/scene_info.py`. Call `workflow_checkpoint` (`ensure_checkpoint` in `docs/blender/scripts/blender_kit_ops.py`). Create collection `COL_<Asset>`.
3. REFERENCE: if a reference exists, set it up with `references/reference-setup.md` (ortho cameras + image empties).
4. NATIVE CONTEXT-FREE CREATION & SUBD AUTHORING (`blender-kit-mcp` / `docs/blender/scripts/blender_kit_ops.py`):
   - **Parametric Parts (`mesh_create_primitive` / `mesh_create_part`):** create `box`, `cylinder`, `cone`, `pyramid`, `sphere`, `icosphere`, `capsule`, `torus`, `blade_foil`, `arch`, `crystal_shard`, `starburst_glint`, `fang`, `spike` linked explicitly to `COL_<Asset>` with `target_mode`.
   - **Pro BMesh Operations (`mesh_bmesh_edit` / `kit_bmesh_edit`):** shape parts natively with `bevel`, `extrude`, `inset`, `subdivide_edges`, `bisect`, `taper_twist`, `spin_lathe`, and `symmetrize`.
   - **SubD Holding Loops & Creases (`mesh_subd_and_loops` / `kit_subd_and_loops`):** for `film_cinematic` or `dual_cage` assets, add 2-segment profile-1.0 quad holding loops (`action="add_holding_loops"`), set edge creases (`action="set_crease"`), set bevel weights (`action="set_bevel_weight"`), bridge/grid-fill loops, and attach Catmull-Clark `SUBSURF` (`action="setup_subsurf"`).
   - **3D Curves & Modifiers (`curve_create_tube`, `mesh_modifier`):** build tapered tubes/cables/branches and manage non-destructive modifiers (`MIRROR`, `BEVEL`, `SOLIDIFY`, `ARRAY`, `BOOLEAN`, `SIMPLE_DEFORM`, `WEIGHTED_NORMAL`).
   - **Transforms & Assembly (`mesh_transform_and_assemble`):** apply scale/rotation in pure BMesh (`apply_scale=True, apply_rotation=True, set_origin="BOTTOM_CENTER"`), join or organize parts, and bind materials.
   - **AI Image-to-3D Path (`generate_3d`):** if using AI generation, immediately run `mesh_clean_and_strip_shells` to strip inner duplicate shells and replace broken appendages.
5. AI VISION COMPARE LOOP (`look` + `audit_run_isolated`):
   - Capture `look(mode="angles", views=["front", "right", "back", "three_quarter"], shading="material")` and `shading="wireframe"`.
   - Run `audit_run_isolated(audit_type="visual_match")` (`docs/blender/scripts/audit_visual_match.py`). Fix any silhouette or appendage mismatch before continuing.
6. CLEAN & AUDIT: delete hidden interior faces; run `audit_run_isolated(audit_type="mesh")` (`docs/blender/scripts/audit_mesh.py` with `BUDGET = 1.5 * budget`).
7. SCREENS: save front, side, 3/4 shaded and wireframe views in `<session_dir>/assets/<asset>/screens/`.

## Hard rules
| Rule | Detail |
|---|---|
| Universal coverage | Always load the matching archetype file from `variants/` before modeling |
| Context-free native tools | Use `mesh_create_primitive`, `mesh_bmesh_edit`, `mesh_subd_and_loops`, `mesh_modifier`, and `mesh_transform_and_assemble` with explicit object names |
| Dual-target SubD rule | `film_cinematic` and `dual_cage` assets keep live Catmull-Clark `SUBSURF` + holding loops/creases; `game_realtime` exports never ship unapplied `SUBSURF` |
| Real size | Dimensions come from [USER] or [MEASURED] reference ratios |
| Strip AI double shells | Every AI-generated mesh MUST run `mesh_clean_and_strip_shells` |
| Vision verification | Never pass `blender-model` without inspecting `look` multi-angle screenshots against the reference |

## Done when
`audit_mesh.py` / `audit_run_isolated`: `ngons == 0`, `doubles == 0`, transforms applied, within stage budget; `audit_visual_match.py` pass; AI vision check confirms silhouette matches reference; screenshots saved.

## On fail
| Failure | Action |
|---|---|
| tris > 1.5 x budget in `game_realtime` | run `mesh_compile_target(target_mode="game_realtime")` or `docs/blender/scripts/optimize_quads_to_tris.py` |
| SubD pinching in `film_cinematic` | add holding loops or adjust crease weights via `mesh_subd_and_loops` |
| silhouette mismatch in `look` | refine with `mesh_bmesh_edit` / `mesh_transform_and_assemble` and re-screenshot |
| hands needed for a character | run blender-hands before topology |
| dense sculpt source | blender-retopo |

## Next
blender-topology (then uv-bake). Characters: blender-hands first.
