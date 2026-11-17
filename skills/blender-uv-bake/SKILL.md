---
name: blender-uv-bake
description: "Use for UV unwrapping, auto-seams, texel density, island packing, zero-bleed per-facet palette atlases, and baking normal, AO, curvature, or procedural PBR maps from high-poly or shader nodes to exportable textures. Triggers: UV, unwrap, seam, texel density, bake, normal map, AO, texture stretched."
---
# UV and bake (universal auto-seams, texel density, facet atlas & map baking)

## Requires
Low-poly mesh that passed blender-topology (audit_mesh pass). HP object for realistic/stylized bakes. config.md texel density + texture sizes. engine.md Materials row (normal map convention, color spaces).

## Inputs
Role | texture size (config.md) | UV mode (`auto_seams` | `smart_project` | `cube_project` | `zero_bleed_facet_atlas`) | HP name if baking.

## Steps
1. DECISION CHECK: if `state.md` has not locked the UV/texture strategy (`Q1: UV Mode — Zero-Bleed Per-Facet Palette Atlas vs Auto-Seam Angle/Conformal Unwrap vs Box/Trim Projection`, `Q2: Texture Resolution & Map Slots`), present `Q1..Q2` with `(Recommended)` first.
2. PATH by style (`style.md`): palette / low-poly (`voxel`, `lowpoly`) -> section A of `references/uv-rules.md` or zero-bleed per-facet cell atlas; baked / PBR (`stylized`, `realistic`) -> section B of `references/uv-rules.md`.
3. NATIVE SEAMS, UNWRAP & PACK:
   - Run `uv_unwrap_and_pack` (`kit_uv_unwrap` in `docs/blender/scripts/blender_kit_ops.py`) with `method="auto_seams"` (marks seams at boundary edges + hard edges `>= seam_angle_deg`, unwraps with `ANGLE_BASED`, and packs islands with `island_margin`).
   - For architectural/boxy assets use `method="cube_project"`; for mechanical parts without organic seams use `method="smart_project"`.
4. TEXEL DENSITY: set `TEXTURE_PX` and `TARGET_DENSITY` in `docs/blender/scripts/audit_uv.py` and run it. Keep all islands within `+-20%` tolerance.
5. BAKE (baked styles or procedural-to-texture): follow `references/bake.md` (cage, ray distance, margin, naming `T_<Asset>_Normal`, `T_<Asset>_BaseColor`, `T_<Asset>_Roughness`, `T_<Asset>_AO`). Verify by `look` screenshot: LP with baked map vs HP/reference.
6. SAVE textures to `blender-out/<asset>/textures/`; pack images (`img.pack()`); names per config.md.
7. AUDIT: run `docs/blender/scripts/audit_uv.py` and `docs/blender/scripts/audit_visual_match.py` (`bleed_ratio <= 0.05`).

## Hard rules
| Rule | Detail |
|---|---|
| One UV set for the game texture | extra sets only if engine.md lists lightmap/second UV use |
| 0-1 space | all islands inside 0-1 unless the role is tiling/trim (then state it in state.md) |
| Zero bleed on low-poly atlases | per-facet cells must include `>= 6px` inner padding so `bleed_faces == 0` |
| Texel density | one project value; assets within +-20 percent |
| Color spaces | base color sRGB; normal/roughness/metallic/AO Non-Color |
| Bake inputs | HP and LP aligned, scale applied, normals consistent |

## Done when
has_uv; `audit_uv.py` and `audit_visual_match.py` pass; baked or atlas maps exist and `look` verification screenshot shows zero stretching, seams, or white occlusion blotches; textures saved and named.

## On fail
| Failure | Action |
|---|---|
| Density out of tolerance | rescale islands; re-pack; rerun audit_uv |
| Bake artifacts or white occlusion patches | repack into padded per-facet UV cells or adjust cage/ray distance (`blender-diagnose` row B) |
| Seams visible | raise `island_margin`; move seams to hard/hidden edges |
| Stretched UVs | lower `seam_angle_deg` in `kit_uv_unwrap` or switch between `auto_seams` and `smart_project` |

## Next
blender-material -> blender-rig (deforming) or blender-qa.
