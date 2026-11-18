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
- **Q1: Target Pipeline Mode (`target_mode`)**
  - `(Recommended) game_realtime` — optimized low/mid-poly triangles, quad rings at joints, baked/atlas textures.
  - `film_cinematic` — 100% quad Catmull-Clark SubD control cage, holding loops, edge creases, procedural node graphs.
  - `dual_cage` — author `_HP` SubD control cage and compile `_LP` game mesh.

## 3. Stage decision tables
| Stage | Unresolved Decision Branches to Check (`Q1..Qn`) |
|---|---|
| `blender` (New Asset) | **Q1:** Target mode (`game_realtime` vs `film_cinematic` vs `dual_cage`)? **Q2:** Execution mode (`single` agent vs 5-role `swarm`)? |
| `blender-ref` / `blender-model` | **Q1:** Native Procedural BMesh/SubD vs AI Image-to-3D (`generate_3d`) + surgical retopo? **Q2:** Real-world target height/length in meters? **Q3:** Multi-part `PartSpec` split? |
| `blender-topology` | **Q1:** `film_cinematic` all-quad SubD cage (`mesh_subd_and_loops`) vs `game_realtime` quad-at-joints + triangulated static facets (`mesh_compile_target`)? **Q2:** Budget ceiling? |
| `blender-material` / `blender-uv-bake` | **Q1:** Declarative shader node graph (`node_graph_build`) vs zero-bleed per-facet cell atlas vs baked PBR maps? **Q2:** Add animated gleam sweep (`surface_add_gleam_effect`)? |
| `blender-rig` / `blender-animate` | **Q1:** Declarative armature (`rig_build_armature` with `ENVELOPE_KDTREE` vs `RIGID_BONE` vs `AUTO_HEAT`)? **Q2:** Motion recipe (`overlapping_wave`, `floating_idle`, `attack_anticipation`)? |
| `blender-vfx` | **Q1:** Effect delivery (`shader_sweep` + `starburst_mesh` vs `flipbook` vs `scrolling_mesh`)? **Q2:** Enable viewport compositor glare (`comp_cinematic_glare_grade`)? |

## 4. Recording decisions
Lock every user answer into `<session_dir>/assets/<asset>/state.md` under `Decisions` with the `[USER]` label so later stages never re-ask or override it.
