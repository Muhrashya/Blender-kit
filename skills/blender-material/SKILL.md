---
name: blender-material
description: "Use when creating, baking, or fixing materials and textures that must export to a game engine - Principled PBR, zero-bleed per-facet palette atlases, animated gleam sweeps, emissive glow, transparency modes, texture slots, and missing-texture repair."
---
# Material (exportable PBR, zero-bleed facet atlas & gleam)

## Requires
UVs done (blender-uv-bake). engine.md Materials rows (workflow, channel packing, normal map convention, color spaces, transparency).

## Inputs
Style (palette or PBR) | list of materials from ref-analysis section 6 | gleam/glow/transparency needs.

## Steps
1. DECISION CHECK: if `state.md` has not locked surface choices (`Q1: Zero-bleed per-facet palette atlas vs PBR texture maps`, `Q2: Add animated gleam/shimmer sweep or emissive rim`), ask `Q1..Q2` with `(Recommended)` first.
2. LIST materials: one per surface type; merge identical ones (fewer materials = fewer draw calls).
3. BUILD with `references/pbr-minimum.md`: Principled BSDF + Image Texture nodes for export; disconnect corrupted normal maps on flat-shaded low-poly meshes so facets never invert.
4. ZERO-BLEED FACET ATLAS (for low-poly / stylized / repaired AI meshes):
   - Pack each triangle into its own padded cell on the atlas texture (`2048x2048` with `>= 6px` inner padding) using the anatomical palette from `ref-analysis.md` so `bleed_faces == 0` and unbaked white occlusion patches are 100% eliminated.
5. GLEAM & EMISSIVE:
   - If the brief or user requests a gleam/shimmer effect, run `surface_add_gleam_effect` from `docs/blender/scripts/blender_kit_ops.py` (`mode="shader_sweep"` or `mode="starburst_mesh"`).
6. TRANSPARENCY & NAMES: pick the mode that engine.md lists (`opaque` / `cutout` / `blend`, default `opaque`). Name materials `MAT_<Asset>_<Part>` and textures `T_<Asset>_<Slot>`. Pack modified images (`img.pack()`).
7. VISUAL & BLEED AUDIT: run `docs/blender/scripts/audit_naming.py` and `docs/blender/scripts/audit_visual_match.py` (`bleed_faces == 0`); capture `look(mode="angles", shading="material")` to verify zero missing-texture patches.

## Hard rules
| Rule | Detail |
|---|---|
| Zero UV bleed | `audit_visual_match.py` must report `bleed_ratio <= 0.05` (`0` intra-triangle color bleed for facet atlases) |
| Principled export | exporters read Principled BSDF + image nodes; bake procedural or gleam sweeps before final engine export |
| Socket names | read them from the node (`[i.name for i in bsdf.inputs]`), they differ between Blender versions |
| Color spaces | base color sRGB; all data maps Non-Color |
| No noisy normal maps on low-poly | disconnect normal/metallic maps that cause inverted black facet shading on flat-shaded meshes |

## Done when
Every material uses clean Principled BSDF nodes; `audit_visual_match.py` passes with zero missing-texture blotches; names pass `audit_naming.py`; `look` multi-angle screenshots saved.

## On fail
| Failure | Action |
|---|---|
| Intra-triangle color bleed or white occlusion patches | repack into per-facet padded UV cells and fill from `ref-analysis.md` palette |
| Dark/inverted facet shading | clear `custom_normal` attribute, set `use_smooth = False`, disconnect corrupt normal map |
| Missing textures after export | run `img.pack()` and save images to `blender-out/<asset>/textures/` |

## Next
blender-rig (deforming) or blender-qa.
