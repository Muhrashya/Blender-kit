---
name: blender-model
description: Use when building or editing ANY 3D asset from a brief or reference image - props, weapons, armor, vehicles, buildings/architecture, nature/foliage/rocks/crystals, modular kits, characters, creatures. Uses native MCP BMesh/modifier/curve tools and verifies visually with look.
---
# Model (universal native modeling & image-to-3D -> verified base mesh)

## Requires
`blender-out/<asset>/brief.md` (budget, style, engine). ref-analysis.md when a reference exists. state.md.

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
1. DECISION CHECK: if `state.md` lacks modeling decisions (`Q1: Creation method — Native Procedural BMesh/Modifiers vs Hybrid AI Image-to-3D + Surgical Cleanup`, `Q2: Real-world dimensions`, `Q3: Moving/articulated sub-parts`), present `Q1..Q3` with `(Recommended)` first.
2. SCENE & CHECKPOINT: verify metric units (`unit_scale 1.0`) via `docs/blender/scripts/scene_info.py`. Call `workflow_checkpoint` (`ensure_checkpoint` in `docs/blender/scripts/blender_kit_ops.py`). Create collection `COL_<Asset>`.
3. REFERENCE: if a reference exists, set it up with `references/reference-setup.md` (ortho cameras + image empties).
4. NATIVE CREATION & SURGICAL EDITING (`blender-kit-mcp` / `docs/blender/scripts/blender_kit_ops.py`):
   - **Parametric Parts (`mesh_create_primitive`):** create `box`, `cylinder`, `cone`, `pyramid`, `sphere`, `icosphere`, `capsule`, `torus`, `blade_foil`, `arch`, `crystal_shard`, `starburst_glint`, `fang`, `spike` with native bevels and bottom-center origins.
   - **Pro BMesh Operations (`mesh_bmesh_edit` / `kit_bmesh_edit`):** shape parts natively with `bevel` (sharp/top/bottom/vertical edges), `extrude` (along normal/vector + scale), `inset`, `subdivide_edges` (loop cuts), `bisect` (planar cuts), `taper_twist` (blades, horns, roofs), `spin_lathe` (bottles, vases, wheels, pillars, barrels), and `symmetrize`.
   - **3D Curves & Tubes (`curve_create_tube` / `kit_curve_tube`):** build cables, pipes, handles, tree trunks/vines, horns, or stylized hair strips with start-to-end taper.
   - **Non-Destructive Modifiers (`mesh_modifier` / `kit_modifier`):** add/apply `MIRROR`, `BEVEL`, `SOLIDIFY`, `ARRAY`, `BOOLEAN`, `SIMPLE_DEFORM`, `WEIGHTED_NORMAL`.
   - **AI Image-to-3D Path (`generate_3d`):** if using AI generation, immediately run `mesh_clean_and_strip_shells` to strip inner duplicate shells and replace broken appendages.
5. AI VISION COMPARE LOOP (`look` + `audit_visual_match.py`):
   - Capture `look(mode="angles", views=["front", "right", "back", "three_quarter"], shading="material")` and `shading="wireframe"`.
   - Run `docs/blender/scripts/audit_visual_match.py`. Compare every sub-part against the reference image and fix any silhouette or detail mismatch before continuing.
6. CLEAN & AUDIT: apply scale/rotation (`recipe R1` in `docs/blender/reference/bpy-recipes.md`), delete hidden interior/bottom faces, and run `docs/blender/scripts/audit_mesh.py` (`BUDGET = 1.5 * budget`).
7. SCREENS: save front, side, 3/4 shaded and wireframe views in `blender-out/<asset>/screens/`.

## Hard rules
| Rule | Detail |
|---|---|
| Universal coverage | Always load the matching archetype file from `variants/` before modeling |
| Native operations first | Use native MCP handlers (`mesh_create_primitive`, `mesh_bmesh_edit`, `mesh_modifier`, `curve_create_tube`) instead of fragile raw scripts |
| Real size | Dimensions come from [USER] or [MEASURED] reference ratios |
| Strip AI double shells | Every AI-generated mesh MUST run `mesh_clean_and_strip_shells` |
| Vision verification | Never pass `blender-model` without inspecting `look` multi-angle screenshots against the reference |
| Separate what moves | Wheels, doors, triggers, turrets, limbs, and floating shards get separate objects or bone groups |

## Done when
audit_mesh: no ngons, no doubles, transforms applied, tris <= 1.5 x budget; `audit_visual_match.py` pass; AI vision check confirms silhouette matches reference; screenshots saved.

## On fail
| Failure | Action |
|---|---|
| tris > 1.5 x budget at blockout | run `docs/blender/scripts/optimize_quads_to_tris.py` or reduce bevel/curve segments |
| silhouette mismatch in `look` | refine with `kit_bmesh_edit` (`bevel`, `extrude`, `taper_twist`, `spin_lathe`) and re-screenshot |
| hands needed for a character | run blender-hands before topology |
| dense sculpt source | blender-retopo |

## Next
blender-topology (then uv-bake). Characters: blender-hands first.
