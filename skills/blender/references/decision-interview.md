# Decision Interview Protocol (Matt Pocock Style: Q1, Q2, Q3...)

Contents: 1 when to ask | 2 question format | 3 stage decision tables | 4 recording decisions

## 1. When to ask
Before executing any Blender stage that has unresolved design branches (controlled by `ask_mode` in `docs/blender/config.md`, default `stage_decisions`), inspect the scene (`get_scene_info` / `look`) and any reference images first. Never ask what `config.md`, `state.md`, or the live scene already answers.

## 2. Question format (Q1, Q2, Q3...)
Present a concise numbered **Decision List** (using the native `ask_question` UI tool when available, or formatted markdown options):
- Prefix each question with `Q1:`, `Q2:`, `Q3:` (max 4 per stage).
- Put the best context-aware choice first, prefixed with `(Recommended)`.
- Explain the tradeoff in one short phrase.

Example:
- **Q1: Creation Pipeline for Reference Image**
  - `(Recommended) Hybrid Procedural BMesh + Per-Facet Palette Atlas` — crisp low-poly facets, zero UV bleed.
  - `AI Image-to-3D (generate_3d) + Surgical Shell/Topology Cleanup` — fast organic silhouette, auto-strips double shells.
  - `Pure Blockout Primitives` — manual control, lowest triangle count.

## 3. Stage decision tables
| Stage | Unresolved Decision Branches to Check (`Q1..Qn`) |
|---|---|
| `blender-ref` / `blender-model` | **Q1:** Procedural BMesh vs AI Image-to-3D (`generate_3d`) + surgical retopo? **Q2:** Real-world target height/length in meters? **Q3:** Rigid multi-part vs single unified mesh? |
| `blender-topology` | **Q1:** Keep quad rings at joints + beauty-triangulate static zones (`optimize_quads_to_tris.py`) vs strict all-quad? **Q2:** Target triangle ceiling within role budget? |
| `blender-material` / `blender-uv-bake` | **Q1:** Zero-bleed per-facet cell atlas (`surface_bake_facet_atlas`) vs standard UV island unwrap? **Q2:** Add animated gleam/shimmer sweep (`surface_add_gleam_effect`)? |
| `blender-animate` | **Q1:** Motion recipe (`overlapping_wave`, `floating_idle`, `attack_anticipation`)? **Q2:** Loop duration and frame count? |
| `blender-vfx` | **Q1:** Effect delivery (`shader_sweep` + `starburst_mesh` vs `flipbook` vs `scrolling_mesh`)? **Q2:** Enable viewport bloom/glare for showcase renders? |

## 4. Recording decisions
Lock every user answer into `blender-out/<asset>/state.md` under `Decisions` with the `[USER]` label so later stages never re-ask or override it.
