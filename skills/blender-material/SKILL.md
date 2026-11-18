---
name: blender-material
description: "Use when creating, baking, or fixing materials, declarative shader/geometry/compositor node graphs, zero-bleed per-facet palette atlases, animated gleam sweeps, emissive glow, transparency modes, and PBR texture slots."
---
# Material (declarative node graphs, exportable PBR, zero-bleed facet atlas & gleam)

## Requires
UVs done (blender-uv-bake) or standalone Phase 1 swarm material lease (`MAT_<Asset>_*`). `docs/blender/engine.md` Materials rows (workflow, channel packing, normal map convention, color spaces, transparency).

## Inputs
`target_mode` (`game_realtime` | `film_cinematic` | `dual_cage`) | Style (palette, procedural node graph, or PBR) | list of materials from `ref-analysis.md` section 6 | gleam/glow/transparency needs.

## Steps
1. DECISION CHECK: if `state.md` has not locked surface choices (`Q1: Surface workflow — Declarative Node Graph (node_graph_build) vs Zero-Bleed Per-Facet Palette Atlas vs Baked PBR Maps`, `Q2: Add animated gleam/shimmer sweep or compositor glare?`), ask `Q1..Q2` with `(Recommended)` first.
2. LIST materials: one per surface type (`MAT_<Asset>_<Part>`); merge identical ones to minimize draw calls. In Swarm Phase 1, author standalone `MAT_<Asset>_*` datablocks (`obj_name=None, material_name="MAT_..."`) before binding at the Phase 2 Assembly Barrier.
3. BUILD MATERIALS NATIVELY (`blender-kit-mcp` / `docs/blender/scripts/blender_kit_ops.py`):
   - **Preset PBR (`material_apply_preset` / `kit_material_preset`):** build `metal_steel`, `gold_trim`, `wood_warm`, `stone_slate`, `crystal_glow`, `foliage_leaf`, or `stylized_pbr` using version-safe Principled BSDF sockets.
   - **Declarative Shader, Geometry Nodes & Compositor DAGs (`node_graph_build` / `kit_node_graph_build`):** construct multi-node graphs using semantic socket aliases (`base_color`, `roughness`, `metallic`, `specular`, `emission`, `transmission`, `coat`, `normal`) or built-in macros (`"triplanar_pbr"`, `"edge_cavity_wear"`, `"subd_micro_displacement"`, `"gn_surface_scatter"`, `"gn_curve_profile_sweep"`, `"comp_cinematic_glare_grade"`).
   - **Zero-Bleed Facet Atlas (for low-poly / repaired AI meshes):** pack each triangle into its own padded cell (`2048x2048` with `>= 6px` inner padding) using the palette from `ref-analysis.md` so `bleed_faces == 0`.
4. GLEAM & EMISSIVE:
   - If requested, call `surface_add_gleam_effect` (`kit_add_gleam_effect` in `docs/blender/scripts/blender_kit_ops.py`) with `mode="shader_sweep"` or `mode="starburst_mesh"`.
5. TRANSPARENCY & NAMES: pick the mode `engine.md` lists (`opaque` / `cutout` / `blend`, default `opaque`). Name materials `MAT_<Asset>_<Part>` and textures `T_<Asset>_<Slot>`. Pack modified images (`img.pack()`).
6. VISUAL & BLEED AUDIT: run `docs/blender/scripts/audit_naming.py` and `audit_run_isolated(audit_type="visual_match")` (`docs/blender/scripts/audit_visual_match.py`); capture `look(mode="angles", shading="material")` (and `shading="rendered"` for `film_cinematic`).

## Hard rules
| Rule | Detail |
|---|---|
| Zero UV bleed | `audit_visual_match.py` must report `bleed_ratio <= 0.05` (`0` intra-triangle bleed for facet atlases) |
| Target-aware export | `game_realtime` exports Principled BSDF + baked image nodes (`references/pbr-minimum.md`); `film_cinematic` supports live procedural `node_graph_build` trees |
| Version-safe sockets | Always resolve sockets via `node_graph_build` aliases or `[i.name for i in bsdf.inputs]`; never hardcode Blender 3.x socket names |
| Color spaces | base color sRGB; all data maps Non-Color |
| No noisy normal maps on flat low-poly | disconnect corrupt normal/metallic maps on flat-shaded low-poly meshes |

## Done when
Every material is valid for `target_mode`; `audit_visual_match.py` passes with zero missing-texture blotches; names pass `audit_naming.py`; `look` multi-angle screenshots saved.

## On fail
| Failure | Action |
|---|---|
| Unknown socket error from `node_graph_build` | read the returned `Valid inputs/outputs` list and re-call `node_graph_build` |
| Intra-triangle color bleed or white occlusion patches | repack into per-facet padded UV cells and fill from `ref-analysis.md` palette |
| Dark/inverted facet shading | clear `custom_normal` attribute, set `use_smooth = False` (low-poly) or `True` (SubD), disconnect corrupt normal map |
| Missing textures after export | run `img.pack()` and save images to `<session_dir>/assets/<asset>/textures/` |

## Next
blender-rig (deforming) or blender-qa.
