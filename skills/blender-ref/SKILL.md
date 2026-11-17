---
name: blender-ref
description: Use when the user gives a reference image, concept art or screenshot to turn into a 3D asset, or says "like this picture", "match this", "dari gambar", "sesuai referensi". Produces a measured ref-analysis.md and Q1..Qn creation decision list BEFORE any modeling.
---
# Reference analysis

## Requires
config.md, brief.md started (asset name, role). Image path readable by Blender (or visible in chat).

## Inputs
Image file(s). Optional: real size, style, which side is front, creation pipeline preference.

## Steps
1. List every image: view (front / side / back / top / 3-4), projection (ortho / perspective / unknown). Several views: use all of them.
2. MEASURE: run `docs/blender/scripts/measure_ref.py` (set PATH). Copy bbox, aspect ratio, padding and exact RGB/hex palette quantiles into the analysis as [MEASURED]. No Blender access: estimate and label [ESTIMATED].
3. Copy `docs/blender/templates/ref-analysis.md` to `blender-out/<asset>/ref-analysis.md` and fill it using `references/analysis-guide.md`.
4. Section 7 (hidden or unclear): list EVERY side or part you cannot see, choose the simplest plausible shape, label it [ASSUMED]. Mark it critical only if a wrong guess changes silhouette or function.
5. Classify the object (prop / hard-surface / character / creature / environment / vehicle / effect) and set the next stage: character with hands -> blender-hands runs inside the char chain; effect -> blender-vfx.
6. DECISION LIST (`Q1..Q3`): present the stage decision list before `blender-model`:
   - `Q1: Creation Method` — `(Recommended) Hybrid Procedural BMesh + Zero-Bleed Facet Atlas` vs `AI Image-to-3D (generate_3d) + Surgical Shell/Topology Cleanup` vs `Pure Blockout Primitives`.
   - `Q2: Target Real-World Size` — recommended height/length in meters.
   - `Q3: Critical Hidden Parts / Gleam or Animation Needs` — confirm any critical assumption from Section 7.

## Hard rules
| Rule | Detail |
|---|---|
| Observed vs assumed | Never describe a hidden side as if it were seen |
| Numbers | Proportions are ratios to total height = 1.0; pixel measures come from measure_ref.py or are labeled [ESTIMATED] |
| Colors | Hex/RGB quantiles from measure_ref.py are [MEASURED]; other colors are [ESTIMATED] |
| No style drift | If the image breaks the active style file, say so in section 8; do not silently switch style |
| Decision list | Ask `Q1..Q3` with `(Recommended)` defaults before starting `blender-model` |

## Done when
ref-analysis.md has no empty section; section 9 verdict = yes; every hidden item has a label; `Q1..Q3` creation decisions recorded in `state.md`.

## On fail
| Failure | Action |
|---|---|
| Image unreadable by Blender | describe from chat view, label every number [ESTIMATED] |
| Low-quality or one view only | proceed with [ASSUMED] hidden sides, flag critical ones in `Q3` |
| Image is a photo with perspective | do not read exact ratios from edges near the frame; label [ESTIMATED] |

## Next
blender-model (props, environments, characters) or blender-vfx (effects).
