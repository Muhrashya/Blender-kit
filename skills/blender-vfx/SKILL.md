---
name: blender-vfx
description: Use when the user wants a game visual effect or gleam/shimmer effect made in or exported from Blender, realistic or low-poly game-like - gleam sweep, starburst glint, hit, slash, explosion, smoke, fire, magic, aura, shockwave, beam, trail, shield, lightning, glow, dust, destruction.
---
# VFX router + FX spec + Gleam effects

## Requires
brief.md; `docs/blender/engine.md` section VFX; config.md (style, fx_style, platform).

## Inputs
Effect name | fx style (`fx=` or config.md `fx_style`) | trigger (loop / one-shot / on-hit) | duration | world size | palette | camera distance | platform.

## Steps
1. DECISION CHECK: present `Q1..Q3` with `(Recommended)` defaults (`Q1: Effect delivery — Gleam Sweep + 3D Starburst Glint vs Scrolling Mesh vs Flipbook`, `Q2: Palette & Emission Strength`, `Q3: Duration & Loop vs One-Shot`).
2. ENGINE: read engine.md VFX rows; mark each as [DOC], [RECALLED] or UNVERIFIED in the spec.
3. STYLE: fx_style = `fx=` argument, else config.md `fx_style`, else `style`. Read that column of `docs/blender/reference/vfx-styles.md` (shape language, alpha edges, colors, frames, triangles, motion).
4. RECIPE: find the effect in `references/cookbook.md` or `references/gleam-and-shimmer.md` (for gleam sweeps, crystal glints, starbursts, and fresnel rim glow); take its layers and the style variant.
5. CLASSIFY with `references/effect-types.md`: choose the CHEAPEST type that reads at the camera distance: gleam sweep / starburst mesh (`surface_add_gleam_effect` in `docs/blender/scripts/blender_kit_ops.py`), texture+mesh, flipbook, trail, chunks, baked.
6. TIMING: effect-types.md section 2 [START] and the life curve: build 10-20 percent, peak 20-30, fade 50-70.
7. SPEC: copy `docs/blender/templates/fx-spec.md` to `blender-out/<fx>/FX_<Name>.spec.md`; fill type, style, trigger, duration, fps, palette, blend, the LAYERS table, engine recipe draft, budgets.
8. ROUTE & EXECUTE:
   - gleam / glint -> run `surface_add_gleam_effect` (`mode="shader_sweep"` and/or `mode="starburst_mesh"`) from `docs/blender/scripts/blender_kit_ops.py` per `references/gleam-and-shimmer.md`;
   - mesh -> blender-vfx-texture then blender-vfx-mesh;
   - flipbook -> (blender-vfx-sim if volumetric and style is realistic) then blender-vfx-flipbook;
   - trail -> blender-vfx-texture; chunks -> blender-vfx-sim.
9. PREVIEW WITH `look`: capture `look(mode="frames", frame_count=6, shading="rendered")` (and `shading="material"`) across $t = 0, 0.1, 0.25, 0.5, 0.75, 1.0$ on dark and light backgrounds.
10. AUDIT: sub-skill audits; for every flipbook also `docs/blender/scripts/audit_fx_style.py` with STYLE set.

## Hard rules
| Rule | Detail |
|---|---|
| No Blender-only systems unbaked | particles, simulations, geometry nodes, and procedural gleam ramps are baked to meshes/textures/actions for engine export |
| Style obeyed | vfx-styles.md limits hold; low-poly and voxel use crisp geometry/alpha and a clean palette |
| Cheapest first | fewer, bigger, simpler shapes; overdraw is the main cost |
| Layers capped | pc 4-6, mobile 2-3 |
| Engine values | every engine value in the recipe is [DOC], [RECALLED] or UNVERIFIED |
| Readability | verified via `look(mode="frames")` on dark and light backgrounds at gameplay distance |

## Done when
Spec complete, gleam/mesh/flipbook assets pass their audits, `look(mode="frames")` readability screenshots saved.

## On fail
| Failure | Action |
|---|---|
| Engine cannot play the chosen type | next type in step 5 order |
| Looks muddy or inconsistent | vfx-styles.md section 4 fixes (cut colors, harden edges, match palette) |
| Peak too late or pops off | re-time the layers; audit_fx_style peak_position_ok / ends_clear |
| Over budget | simplify shapes, fewer frames, smaller textures |

## Next
blender-vfx-texture / -mesh / -flipbook / -sim, then blender-qa -> blender-export.
