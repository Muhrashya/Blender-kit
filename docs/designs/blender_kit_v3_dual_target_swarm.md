# Blender-Kit v3.0: Dual-Target (Game & Film/SubD), Context-Free Native MCP & Multi-Agent Swarm Architecture

*   **Author:** Raz
*   **Status:** Approved
*   **Date:** 2026-11-18

--------------------------------------------------------------------------------

## Overview

`blender-kit` v3.0 upgrades the toolkit from a single-agent, game-only asset pipeline into a multi-agent 3D creation system supporting both real-time game engines (`game_realtime`) and subdivision-surface film/cinematic production (`film_cinematic`). It replaces fragile Python script generation with context-free native MCP tools inside Blender, coordinates a 5-role specialist agent swarm (Orchestrator, Modeler/Artist, Material/Texture Maker, Rigger/Animator, and Isolated Auditor) working concurrently on the same asset without viewport state collisions, and relocates all intermediate session files into an OS App-Data directory keyed to the `.blend` file so user workspaces remain untouched.

## The Problem

Creating production-ready 3D assets with AI agents in Blender currently hits four operational walls:

1.  **Game-Only Topological Bias Breaks Film & Subdivision Work:**
    Current v2.0 tools force flat polygon shading (`use_smooth = False`) and triangulate static quads to meet low-poly game budgets. Artists and technical directors building film, broadcast, or high-poly bake sources require 100% quad Catmull-Clark Subdivision Surface (`SUBSURF`) control cages, boundary holding loops, edge creases, UDIM or boundary-smoothed UVs, and live procedural node trees.
2.  **Routine Tasks Still Drop Back to Fragile Raw Python Scripts:**
    While v2.0 introduced 11 native MCP tools for basic primitives and simple BMesh edits, agents still have to generate multi-hundred-line Python scripts via `execute_blender_code` whenever an asset requires support loops, edge creasing, multi-node Shader/Geometry/Compositor graphs, or Armature skeletons with IK and bone constraints. Raw script generation fails frequently due to Blender 4.x/5.x API version differences, socket naming shifts, and BMesh pointer invalidation.
3.  **Global `bpy.context` Collisions Prevent Multi-Agent Collaboration on One Asset:**
    Blender's operator API (`bpy.ops`) and existing v2.0 UV, modifier, and audit scripts rely on global viewport state (`bpy.context.view_layer.objects.active`, `bpy.context.selected_objects`, and `OBJECT` vs. `EDIT` mode). When multiple agents work on the same asset concurrently (for example, one agent modeling armor sub-parts while another unwraps UVs or runs topology audits), they overwrite each other's active object and mode state, corrupting geometry or crashing with context poll errors.
4.  **Workspace Folder Pollution:**
    Running `/blender` currently requires `docs/blender/` and writes `blender-out/<asset>/` (containing `.blend` checkpoints, JSON audits, screenshots, and state files) directly into the user's current working directory. Running the skill inside an existing game repository or an arbitrary directory clutters version control with untracked files.

The proposed solution introduces a **Universal Quad Control Cage** compiled per target (`game_realtime` vs. `film_cinematic`), expands `blender-kit-mcp` with **context-free native builders** for SubD modeling, declarative node graphs, and armature/IK rigs, enforces a **Server-Side Datablock Lease Table** for 5-role swarm concurrency, and stores all intermediate state in an **OS App-Data Session Vault** mirrored inside the `.blend` file.

## Goals

*   **Dual-Target Asset Compliance (`game_realtime` & `film_cinematic`):** Allow any asset to target either real-time game budgets (quad rings at joints, triangulated static facets, zero-bleed single-tile textures, `<= 4` bone weights per vertex) or film/SubD standards (100% quad Catmull-Clark control cages, holding loops, edge creases, smooth normals, procedural Shader/Geometry/Compositor node graphs, and full IK/FK control rigs).
*   **Zero Raw Python Scripts for Standard Creation & Editing:** Handle 100% of standard modeling (primitives, bevels, holding loops, creases, booleans, lathes, curves), surfacing (declarative Shader, Geometry Nodes, and Compositor DAGs), rigging (armature bone trees, IK chains, bone constraints, weight binding), and auditing through native JSON-RPC MCP tools.
*   **Collision-Free 5-Role Swarm Execution on a Single Asset:** Enable an Orchestrator, 1..N Modeler/Artist agents, a Material/Texture Maker, a Rigger/Animator, and an Isolated Auditor to author independent datablocks (`bpy.data.meshes`, `bpy.data.materials`, `bpy.data.armatures`, `bpy.data.actions`) in parallel with zero `bpy.context` state corruption.
*   **Zero Project-Folder Footprint by Default:** Store all intermediate session files (`state.md`, `brief.md`, `ref-analysis.md`, `qa.md`, `audit/*.json`, `screens/*.png`, `checkpoints/*.blend`) in an OS App-Data directory keyed to the `.blend` session UUID, writing nothing to the user's working directory unless explicitly exporting a finished asset.
*   **Backward Compatibility with Skill Validation (`npm run check`):** Maintain 100% pass rates across all 21 skill definitions under `scripts/validate-skills.mjs` (`<= 140` lines per `SKILL.md`, valid section headers, and compiled Python modules).

## Non-Goals

*   **OS-Thread Parallel Mutation of `bpy.data` C Pointers:** Blender's internal C-RNA and dependency graph are not thread-safe across operating system threads. Parallelism occurs across concurrent agent planning and datablock isolation, while all `bpy.data` mutations serialize as fast (`< 15 ms`), atomic main-thread transactions.
*   **Removing `execute_blender_code` Completely:** Custom mathematical surface formulas or one-off user scripts remain supported via `execute_blender_code` as an explicit escape hatch.
*   **Multi-Machine Networked Blender Sync:** Coordinating multiple separate Blender GUI processes across different physical machines is out of scope.
*   **Replacing Dedicated Sculpting Applications for High-Frequency Pore Detail:** Multi-million-polygon digital clay sculpting (ZBrush-scale pore detailing) remains external; high-poly detail in `blender-kit` targets clean SubD control cages, holding loops, procedural displacement, and bevel/normal baking.

## Open Questions

*   *None at this stage; all brainstorm constraints (same-asset 5-role swarm, dual game/film target, native MCP preference with script fallback, and OS App-Data storage keyed to `.blend`) were resolved during ideation.*

## Critical User Journeys (CUJs)

### CUJ 1: Multi-Agent Creation of a Film-Ready SubD Hero Asset in a Non-Clean Directory

*   **Given**: A user opens an unsaved or arbitrary `.blend` file inside an existing project repository that has no `docs/blender/` folder, and requests `/blender prop "CyberKatana" target=film_cinematic`.
*   **When**: The `/blender` Orchestrator runs the `Q1..Q3` decision interview, initializes an OS App-Data session vault (`%LOCALAPPDATA%\blender-kit\sessions\unsaved_<uuid>\`), and spawns the Modeler (building the SubD quad blade, guard, and hilt with holding loops and edge creases), Material Maker (building a declarative anisotropic steel + gleam shader graph and compositor glare), and Rigger (building the weapon root, scabbard pivot, and gleam driver) in parallel.
*   **Then**: Each specialist agent writes only to its leased datablocks without mutating global viewport selection; the Isolated Auditor runs `audit_run_isolated(target_mode="film_cinematic")` confirming `ngons == 0`, `tris == 0` on curved SubD surfaces, and valid node links; and the user's project directory contains zero intermediate files.

### CUJ 2: Dual-Cage Compilation from High-Poly SubD to Real-Time Game Export

*   **Given**: A multi-part creature or weapon authored on a clean quad control cage (`_HP`) with SubD crease weights and procedural materials.
*   **When**: The user requests `/blender export engine=roblox style=lowpoly` (or switches `target_mode` to `game_realtime`).
*   **Then**: The native `mesh_compile_target` tool evaluates a game-ready `_LP` mesh that strips hidden inner shells, preserves 3-ring quad loops at deforming joints, dissolves coplanar loops, beauty-triangulates static facets within the role's triangle budget, bakes procedural shaders into a zero-bleed texture atlas, passes `blender-qa` (`SHIP`), and exports a verified `.fbx`/`.glb` file.

## Technical Plan (Architecture)

### 1. System Architecture & Data Flow

`blender-kit` v3.0 separates **concurrent multi-agent planning** (Orchestrator, Modeler, Material/Texture Maker, Rigger/Animator, and Isolated Auditor) from **atomic, context-free execution** inside Blender's single-threaded C-RNA runtime.

```text
+-----------------------------------------------------------------------------------+
|                        CODING AGENT HARNESS (HOST SESSION)                        |
|                                                                                   |
|                         +-------------------------------+                         |
|                         |     /blender ORCHESTRATOR     |                         |
|                         |  - Q1..Qn Decision Interview  |                         |
|                         |  - PartSpec & Landmark Graph  |                         |
|                         |  - Lease Token Assignment     |                         |
|                         +---------------+---------------+                         |
|                                         |                                         |
|            +----------------------------+----------------------------+            |
|            | (Phase 1: Parallel Datablock Authoring)                 |            |
|            v                            v                            v            |
|  +-------------------+        +-------------------+        +-------------------+  |
|  |  MODELER AGENT(S) |        |  MATERIAL MAKER   |        |  RIGGER/ANIMATOR  |  |
|  |  Lease: SM_<Part> |        |  Lease: MAT_*, T_*|        |  Lease: ARM_, AN_ |  |
|  +---------+---------+        +---------+---------+        +---------+---------+  |
|            |                            |                            |            |
|            +----------------------------+----------------------------+            |
|                                         | (Phase 2: Bind & Audit Barrier)         |
|                                         v                                         |
|                         +-------------------------------+                         |
|                         |       ISOLATED AUDITOR        |                         |
|                         |  Lease: READ_ONLY (bmesh copy)|                         |
|                         +---------------+---------------+                         |
+-----------------------------------------|-----------------------------------------+
                                          | JSON-RPC over TCP (127.0.0.1:9876)
                                          v
+-----------------------------------------------------------------------------------+
|                     BLENDER MAIN-THREAD ADDON (blender_kit_mcp)                   |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | 1. Datablock Lease Guard (_DATABLOCK_LEASES) & Atomic Context Lock          |  |
|  +-----------------------------------------------------------------------------+  |
|  | 2. Unified Native Handlers (mcp/blender_kit_mcp/handlers/)                  |  |
|  |    - session_store.py  : OS App-Data Vault + bpy.data.texts[".kit_session"] |  |
|  |    - modeling_subd.py  : Primitives, BMesh, Holding Loops, Edge Creases     |  |
|  |    - target_compile.py : Universal Quad Control Cage -> Film SubD or Game LP|  |
|  |    - node_graphs.py    : Declarative Shader, Geometry Nodes, Compositor DAG |  |
|  |    - rigging_anim.py   : Batch EditBone/PoseBone IK, Constraints, Pro Anim  |  |
|  |    - audits.py         : Context-Free Read-Only Mesh/Topo/SubD/UV/Rig Audits|  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|               OS APP-DATA SESSION VAULT (%LOCALAPPDATA%/blender-kit)              |
|  sessions/<stem>_<scene_uuid>/assets/<AssetName>/                                 |
|    ├── brief.md, ref-analysis.md, state.md, qa.md                                 |
|    ├── audit/ (mesh.json, topology.json, visual_match.json, rig.json, anim.json)  |
|    ├── screens/ (front.png, right.png, wireframe.png, frames_strip.png)           |
|    └── checkpoints/ (pre_model.blend, pre_topo.blend, pre_rig.blend)              |
+-----------------------------------------------------------------------------------+
```

### 2. Core Architectural Components

#### 2.1 Unified Handler Package & Single Source of Truth
To eliminate the 500-line code duplication between `mcp/blender_kit_mcp/native_handlers.py` and `skills/blender-setup/templates/scripts/blender_kit_ops.py`, all Blender-side execution logic is consolidated into `mcp/blender_kit_mcp/handlers/`:
*   `session_store.py`: Manages OS App-Data path resolution, `.blend` text-block state mirroring, checkpoint pruning, and the in-memory `_DATABLOCK_LEASES` table.
*   `modeling_subd.py`: Implements `kit_create_primitive`, `kit_bmesh_edit`, `kit_subd_and_loops`, `kit_curve_tube`, `kit_modifier`, and `kit_transform_and_assemble` using pure `bmesh` and `depsgraph` evaluation.
*   `target_compile.py`: Implements `kit_compile_target` to convert a Universal Quad Control Cage into either a `film_cinematic` Catmull-Clark SubD stack or a `game_realtime` optimized mesh.
*   `node_graphs.py`: Implements `kit_node_graph_build` for declarative Shader, Geometry Nodes, and Compositor DAG construction, plus `kit_uv_unwrap`, `kit_material_preset`, and `kit_add_gleam_effect`.
*   `rigging_anim.py`: Implements `kit_rig_build_armature` and `kit_pro_motion`.
*   `audits.py`: Implements `kit_audit_run_isolated` wrapping all geometry, SubD/game topology, UV bleed, rig, and animation checks without reading or mutating `bpy.context.selected_objects`.

During `npm run check`, a build/sync helper bundles `mcp/blender_kit_mcp/handlers/*.py` into `skills/blender-setup/templates/scripts/blender_kit_ops.py` so offline Script Mode and live MCP Mode execute identical code.

#### 2.2 Context-Free Execution & Atomic Context Guard
Every handler in `mcp/blender_kit_mcp/handlers/` obeys three context-isolation invariants:
1.  **Explicit Datablock Addressing:** Every tool requires explicit `obj_name`, `material_name`, `armature_name`, and `collection_name` parameters. Implicit references to `bpy.context.active_object`, `bpy.context.selected_objects`, or `bpy.context.collection` are removed.
2.  **Dependency-Graph Modifier Evaluation:** Applying modifiers in `kit_modifier` and `kit_compile_target` uses `obj.evaluated_get(bpy.context.evaluated_depsgraph_get())` and `bpy.data.meshes.new_from_object(eval_obj)` to swap `obj.data` in-place without calling `bpy.ops.object.modifier_apply` (which fails when objects are hidden or unselected).
3.  **Atomic Context Snapshot & Restore Guard (`_MAIN_THREAD_CONTEXT_LOCK`):** For the two Blender subsystems where C-level `EDIT` mode operators are mandatory (`bpy.ops.uv.unwrap` / `pack_islands` and `armature.edit_bones.new`), the handler enters a context manager `with atomic_context_guard(target_obj, mode='EDIT'):` that snapshots the current active object, selection list, and object mode, runs the batch operation in `< 15 ms`, and restores the exact prior state in a `finally:` block before returning control to the TCP event loop.

#### 2.3 Universal Quad Control Cage & Dual-Target Compiler (`target_mode`)
`config.md` gains `target_mode: game_realtime | film_cinematic | dual_cage`.
*   **Base Authoring (`kit_subd_and_loops`):** Models are constructed as clean quad cages using pure-BMesh float layers (`crease_edge` and `bevel_weight_edge`) and holding/support loops generated via `bmesh.ops.bevel(offset_type='OFFSET', segments=2, profile=1.0, affect='EDGES', clamp_overlap=True)`. Setting `profile=1.0` with `segments=2` inserts parallel quad support loops on either side of a sharp edge without chamfering the corner plane.
*   **`film_cinematic` Compilation (`kit_compile_target`):**
    *   Sets `poly.use_smooth = True` across all faces.
    *   Attaches a non-destructive `SUBSURF` modifier (`subdivision_type='CATMULL_CLARK'`, `levels=2`, `render_levels=3`, `use_creases=True`, `uv_smooth='PRESERVE_BOUNDARIES'`).
    *   Runs `kit_audit_run_isolated(target_mode="film_cinematic")`, enforcing `ngons == 0`, `tris == 0` in non-planar zones, and `pole_balance % 8 == 0` on closed quad manifolds.
*   **`game_realtime` Compilation (`kit_compile_target`):**
    *   Strips any hidden inner duplicate shells via BVH raycasting (`mesh_clean_and_strip_shells`).
    *   Preserves 3-ring quad loops within `joint_radius` of armature bones, dissolves coplanar interior edges (`planar_angle_deg <= 2.5`), and beauty-triangulates static quads (`quad_method='BEAUTY'`).
    *   Enforces the role's evaluated triangle ceiling from `config.md`.

#### 2.4 Declarative Node Graph Builder (`kit_node_graph_build`)
To eliminate raw Python scripts for complex shaders, Geometry Nodes setups, and viewport compositing, `node_graph_build` accepts a declarative JSON specification:
*   **Inputs:** `tree_type` (`"SHADER"` | `"GEOMETRY"` | `"COMPOSITOR"`), `target_name` (material, object, or scene name), `clear_existing` (`bool`), `interface_sockets` (`[{name, in_out, socket_type, default}]`), `nodes` (`[{id, type, location, properties, inputs}]`), `links` (`[{from_node, from_socket, to_node, to_socket}]`), and optional `macro` preset name.
*   **Version-Safe Socket Resolution:** A lookup table maps version-neutral socket aliases (`"emission"` -> `"Emission Color"` or `"Emission"`, `"specular"` -> `"Specular IOR Level"` or `"Specular"`, `"transmission"` -> `"Transmission Weight"` or `"Transmission"`, `"coat"` -> `"Coat Weight"` or `"Clearcoat"`) across Blender 4.x and 5.x. If an invalid socket or node type is passed, the handler aborts cleanly and returns the exact list of valid `inputs` and `outputs` on that node.

#### 2.5 Declarative Armature, IK & Constraint Builder (`kit_rig_build_armature`)
`rig_build_armature` authors complete game or film rigs in a single native call:
*   **Inputs:**
    *   `armature_name`: `"ARM_<Asset>"`
    *   `bones`: `[{name, head: [x,y,z], tail: [x,y,z], roll_deg, parent, use_connect, use_deform, bbone_segments}]`
    *   `constraints`: `[{bone, type: "IK" | "COPY_ROTATION" | "COPY_LOCATION" | "DAMPED_TRACK" | "STRETCH_TO" | "LIMIT_ROTATION", target_obj, subtarget, chain_count, pole_target, pole_subtarget, pole_angle_deg, influence, settings}]`
    *   `bind_meshes`: `[{mesh_name, bind_mode: "AUTO_HEAT" | "ENVELOPE_KDTREE" | "RIGID_BONE", max_influences: 4}]`
*   **Deterministic Weight Fallback:** When Blender's C heat-bone solver (`ARMATURE_AUTO`) fails on disconnected low-poly or hard-surface sub-parts, `ENVELOPE_KDTREE` computes analytical point-to-bone-segment distances in pure Python/NumPy, assigns smooth falloff weights to the nearest deform bones, prunes weights below `0.01`, caps per-vertex influences to `max_influences` (default `4` for game, `8` for film), and normalizes weight sums to `1.0`.

#### 2.6 Multi-Agent Swarm Coordination & Datablock Lease Table
When `/blender` spawns a multi-agent swarm on a complex asset:
1.  **Phase 1 — Lock-Free Parallel Datablock Authoring:**
    The Orchestrator decomposes the asset into a `PartSpec` table (bounding boxes, attachment coordinates, material names, bone landmarks) and registers leases in `_DATABLOCK_LEASES`:
    *   `modeler_<k>` receives write leases on `SM_<Asset>_<Part_k>` and `GN_<Asset>_*`.
    *   `material_maker` receives write leases on `MAT_<Asset>_*` and `T_<Asset>_*`.
    *   `rigger_animator` receives write leases on `ARM_<Asset>` and `AN_<Asset>_*`.
    *   `auditor` receives a `READ_ONLY` lease across all datablocks.
    Any write tool call whose `agent_role` violates the active lease table is rejected before mutating `bpy.data`.
2.  **Phase 2 — Assembly Barrier & Isolated Audit:**
    Once Phase 1 subagents complete, the Orchestrator binds materials (`MAT_*`) and armature weights (`ARM_*`) to the finished mesh parts (`SM_*`), and dispatches the Isolated Auditor (`audit_run_isolated` + offscreen `look` renders). Defects route strictly back to the owning specialist role.

#### 2.7 Zero-Footprint OS App-Data Session Vault
`session_manage` resolves the session directory without writing to the current working directory:
1.  Reads or creates `bpy.context.scene["kit_session_uuid"]` (12-hex-char UUID).
2.  Resolves the OS state root:
    *   Windows: `%LOCALAPPDATA%\blender-kit\sessions\<stem>_<uuid>\`
    *   macOS: `~/Library/Application Support/blender-kit/sessions/<stem>_<uuid>/`
    *   Linux: `${XDG_STATE_HOME:-~/.local/state}/blender-kit/sessions/<stem>_<uuid>/`
3.  Writes all stage reports, `brief.md`, `state.md`, `audit/*.json`, `screens/*.png`, and `checkpoints/*.blend` inside `<session_dir>/assets/<asset_name>/`.
4.  Mirrors a compact JSON summary of `state.md` and `config.md` into `bpy.data.texts[".blender_kit_session"]` (`use_fake_user = True`) so moving or renaming the `.blend` file automatically reconstructs the session state.

## Alternatives Considered

### Alternative A: Exposing 500+ 1-to-1 MCP Wrappers Around `bpy.ops.*` Operators

*   **Pros**: Minimal wrapper code per operator; mirrors Blender's UI menu structure directly.
*   **Cons**: Floods the agent's MCP tool schema with hundreds of fine-grained operator definitions, consuming tens of thousands of context tokens per turn and degrading tool-selection accuracy. Worse, `bpy.ops.*` operators depend on `bpy.context.active_object`, `bpy.context.selected_objects`, and `OBJECT`/`EDIT` mode, causing immediate state corruption when multiple swarm agents issue calls concurrently.
*   **Reason for Rejection**: Rejected by author: overflows the LLM tool schema context budget and fails during multi-agent execution because `bpy.ops` relies on shared global viewport context rather than explicit datablock references.

### Alternative B: Spawning Separate Headless Blender Processes per Subagent and Merging `.blend` Files on Disk

*   **Pros**: Provides OS-process isolation for each subagent without needing an in-memory Datablock Lease Table or atomic context guard.
*   **Cons**: Adds 3–8 seconds of process startup and `.blend` file serialization/append overhead on every stage, prevents the user from watching the asset take shape live in their open Blender viewport, and creates complex library-linking/name-collision bugs (`MAT_Asset.001`) when merging parallel `.blend` files back into the master scene.
*   **Reason for Rejection**: Rejected by author: high process startup and disk I/O latency, loss of live interactive viewport feedback, and brittle `.blend` library merge conflicts.

### Alternative C: Storing All Intermediate State in `./docs/blender/` and `./blender-out/` Inside the Working Directory

*   **Pros**: Simple relative path resolution (`./blender-out/<asset>/`) that requires no OS App-Data lookup or `.blend` UUID tracking.
*   **Cons**: Pollutes non-clean folders, existing Unity/Unreal/Roblox repositories, or quick `.blend` editing sessions with untracked markdown files, audit JSONs, viewport screenshots, and multi-hundred-megabyte `.blend` checkpoints.
*   **Reason for Rejection**: Rejected by author: violates the zero-footprint requirement when working inside arbitrary or existing project directories.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Performance & Main-Thread Latency:** Every native JSON-RPC handler (`kit_*`) must complete its main-thread execution in `< 50 ms` for standard modeling/node/rig operations (and hold `_MAIN_THREAD_CONTEXT_LOCK` for `< 15 ms` during batch UV unwrap or `EditBone` creation) so the user's Blender viewport remains responsive at 60 FPS.
*   **Storage Footprint & Auto-Pruning:** `.blend` checkpoints stored in `%LOCALAPPDATA%\blender-kit\sessions\` are capped at a rolling window of `keep_last = 5` checkpoints per asset by default, with `session_manage(action="prune_checkpoints")` available to reclaim disk space.
*   **Rollout & Backward Compatibility:** Existing projects that already contain a local `./docs/blender/config.md` continue to work without migration (`session_store.py` checks for an explicit workspace override before defaulting to the OS App-Data Session Vault). All 21 skill definitions must continue to pass `npm run validate` (`scripts/validate-skills.mjs`).

--------------------------------------------------------------------------------

### Additional Resources

*   Concept Brief: `./concepts_brief.md`
*   Skill Linter & Validator: `./scripts/validate-skills.mjs`
*   Existing MCP Server & Addon: `./mcp/blender_kit_mcp/__init__.py`, `./mcp/blender_kit_mcp/addon.py`, `./mcp/blender_kit_mcp/native_handlers.py`

### Future Improvements

*   **Offscreen Dedicated Audit ViewLayer (`ViewLayer_Audit`):** Render Isolated Auditor screenshots from a dedicated background ViewLayer so viewport captures never show in-progress wireframes or hidden helper rigs even if the user rotates the active 3D viewport camera mid-build.
*   **UDIM Multi-Tile Texture Baking:** Extend `kit_uv_unwrap` and `node_graph_build` to bake multi-tile `1001..100N` EXR displacement and PBR maps for hero film characters.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

### Target Files to Create/Modify

#### 1. `./mcp/blender_kit_mcp/handlers/__init__.py` (Create)

*   **Type / Scope**: Python Package Initializer
*   **Proposed Changes**: Export the unified `NATIVE_HANDLER_MAP` dictionary mapping all 18 `kit_*` RPC command strings (`kit_session_manage`, `kit_checkpoint`, `kit_create_primitive`, `kit_bmesh_edit`, `kit_subd_and_loops`, `kit_compile_target`, `kit_transform_and_assemble`, `kit_modifier`, `kit_curve_tube`, `kit_node_graph_build`, `kit_uv_unwrap`, `kit_material_preset`, `kit_add_gleam_effect`, `kit_rig_build_armature`, `kit_pro_motion`, `kit_clean_and_strip_shells`, `kit_optimize_quads_to_tris`, `kit_audit_run_isolated`) to their domain handler functions. Rationale: provides a single registry consumed by both `./mcp/blender_kit_mcp/addon.py` and the offline script bundler.

#### 2. `./mcp/blender_kit_mcp/handlers/session_store.py` (Create)

*   **Type / Scope**: Python Module (Session Vault, Leases & Atomic Context Lock)
*   **Proposed Changes**:
    *   Implement `resolve_session_dir(asset_name: Optional[str]) -> str` to compute the OS App-Data path (`%LOCALAPPDATA%/blender-kit/sessions/<stem>_<scene_uuid>/` on Windows, `~/Library/Application Support/blender-kit/sessions/...` on macOS, `${XDG_STATE_HOME:-~/.local/state}/blender-kit/sessions/...` on Linux), falling back to local `./blender-out/` only if explicitly configured in `./docs/blender/config.md`.
    *   Implement `mirror_state_to_blend(state_dict: dict)` and `restore_state_from_blend() -> dict` using `bpy.data.texts[".blender_kit_session"]` (`use_fake_user = True`).
    *   Implement `_DATABLOCK_LEASES` (`acquire_lease`, `verify_lease`, `release_lease`) to enforce single-writer datablock ownership across the 5 swarm roles (`orchestrator`, `modeler`, `material_maker`, `rigger_animator`, `auditor`).
    *   Implement the `atomic_context_guard(target_obj, mode='EDIT')` context manager that snapshots and restores `bpy.context.view_layer.objects.active`, `bpy.context.selected_objects`, and object mode within a single synchronous tick.
    *   Implement `kit_session_manage(action, asset_name, agent_role, lease_prefixes, keep_last)` and `kit_checkpoint(asset_name, tag)`.
    *   Rationale: keeps user project directories clean and prevents concurrent swarm agents from colliding on shared `bpy.context` or overwriting each other's datablocks.

#### 3. `./mcp/blender_kit_mcp/handlers/modeling_subd.py` (Create)

*   **Type / Scope**: Python Module (Context-Free BMesh, SubD, Holding Loops, Modifiers & Assembly)
*   **Proposed Changes**:
    *   Migrate and refactor `kit_create_primitive`, `kit_bmesh_edit`, `kit_modifier`, and `kit_curve_tube` from `./mcp/blender_kit_mcp/native_handlers.py`:
        *   Add `smooth_shading: Optional[bool] = None` (auto-selecting `True` when `target_mode == "film_cinematic"` and `False` when `target_mode == "game_realtime"` with `style == "lowpoly"`).
        *   Replace `bpy.context.collection.objects.link(obj)` with explicit collection lookup/creation (`COL_<Asset>`).
        *   Replace `bpy.ops.object.modifier_apply` with dependency-graph mesh evaluation (`obj.evaluated_get(depsgraph)` -> `bpy.data.meshes.new_from_object`).
    *   Implement `kit_subd_and_loops(obj_name, action, selector, edge_indices, offset, crease_value, bevel_weight, subd_levels, render_levels)`:
        *   Supports `action="add_holding_loops"` (`bmesh.ops.bevel` with `segments=2, profile=1.0, clamp_overlap=True`), `action="set_crease"` (writing `bm.edges.layers.float["crease_edge"]`), `action="set_bevel_weight"` (writing `bm.edges.layers.float["bevel_weight_edge"]`), `action="bridge_loops"`, `action="grid_fill"`, and `action="setup_subsurf"`.
    *   Implement `kit_transform_and_assemble(obj_name, apply_location, apply_rotation, apply_scale, set_origin, join_objects, target_collection)` using pure `bmesh.ops.transform` and matrix math.
    *   Rationale: enables full Subdivision Surface and hard-surface modeling without entering `EDIT` mode or generating raw Python scripts.

#### 4. `./mcp/blender_kit_mcp/handlers/target_compile.py` (Create)

*   **Type / Scope**: Python Module (Dual-Target Mesh Compiler)
*   **Proposed Changes**:
    *   Migrate `mesh_clean_and_strip_shells` and `topo_optimize_quads_to_tris` from `./skills/blender-setup/templates/scripts/blender_kit_ops.py`.
    *   Implement `kit_compile_target(obj_name, target_mode="game_realtime" | "film_cinematic" | "dual_cage", tri_budget=2500, subd_levels=2, preserve_joint_quads=True, joint_radius=0.18)`:
        *   For `film_cinematic`: validates quad cage, enables smooth shading, configures weight-driven support `BEVEL` + Catmull-Clark `SUBSURF` (`uv_smooth='PRESERVE_BOUNDARIES'`).
        *   For `game_realtime`: strips inner shells, preserves 3-ring joint quads, dissolves planar loops, beauty-triangulates static facets, and checks `total_triangles <= tri_budget`.
        *   For `dual_cage`: duplicates the mesh into `SM_<Asset>_HP` (compiled as `film_cinematic`) and `SM_<Asset>_LP` (compiled as `game_realtime`).
    *   Rationale: resolves the topological contradiction between game and film pipelines from a single authored control cage.

#### 5. `./mcp/blender_kit_mcp/handlers/node_graphs.py` (Create)

*   **Type / Scope**: Python Module (Declarative Shader, Geometry Nodes, Compositor & UV Handler)
*   **Proposed Changes**:
    *   Migrate `kit_uv_unwrap` (wrapped in `atomic_context_guard` so selection and mode are restored immediately), `kit_material_preset`, and `surface_add_gleam_effect`.
    *   Implement `kit_node_graph_build(tree_type, target_name, nodes, links, interface_sockets, macro, clear_existing)` with a version-neutral socket alias map covering Blender 4.x and 5.x (`Principled BSDF`, `GeometryNodeTree`, and `CompositorNodeTree`) and built-in macros (`"triplanar_pbr"`, `"edge_cavity_wear"`, `"subd_micro_displacement"`, `"gn_surface_scatter"`, `"gn_curve_profile_sweep"`, `"comp_cinematic_glare_grade"`).
    *   Rationale: allows Material/Texture Maker and VFX agents to build complex procedural shaders, Geometry Nodes modifiers, and viewport compositing setups declaratively without raw Python scripts.

#### 6. `./mcp/blender_kit_mcp/handlers/rigging_anim.py` (Create)

*   **Type / Scope**: Python Module (Declarative Armature, IK, Constraints & Pro Animation)
*   **Proposed Changes**:
    *   Implement `kit_rig_build_armature(armature_name, collection_name, bones, constraints, bind_meshes)`:
        *   Uses `atomic_context_guard(arm_obj, mode='EDIT')` to batch-create `EditBone` hierarchies (`head`, `tail`, `roll_deg`, `parent`, `use_connect`, `use_deform`, `bbone_segments`).
        *   Populates `pose.bones` constraints (`IK`, `COPY_ROTATION`, `COPY_LOCATION`, `DAMPED_TRACK`, `STRETCH_TO`, `LIMIT_ROTATION`).
        *   Binds meshes using `AUTO_HEAT`, `RIGID_BONE`, or the pure-Python `ENVELOPE_KDTREE` segment-distance solver, capping influences at `max_influences` and normalizing weights.
    *   Migrate and extend `anim_pro_motion` (`kit_pro_motion`) to support `overlapping_wave`, `floating_idle`, and `attack_anticipation` (3-phase anticipation, strike overshoot, and damped settle with `AUTO_CLAMPED` Bezier handles).
    *   Rationale: fills the missing native rigging/IK gap so Rigger/Animator agents never need raw scripts to rig or skin an asset.

#### 7. `./mcp/blender_kit_mcp/handlers/audits.py` (Create)

*   **Type / Scope**: Python Module (Context-Free Isolated Audits)
*   **Proposed Changes**:
    *   Implement `kit_audit_run_isolated(audit_type, target_objects, target_mode="game_realtime", budget=0, armature_name=None, ref_aspect_xz=0.0)`:
        *   Operates strictly on explicit `target_objects` lists using read-only `bmesh` copies and evaluated dependency graphs (`select_defects=False`), never reading or mutating `bpy.context.selected_objects` or `active_object`.
        *   In `film_cinematic` mode, checks `ngons == 0`, `curved_surface_tris == 0`, `pole_balance % 8 == 0`, and SubD modifier presence.
        *   In `game_realtime` mode, checks `ngons == 0`, `tris <= budget`, `poles_near_joints == 0`, `bleed_ratio <= 0.05`, and `max_influences <= 4`.
        *   Writes audit JSON outputs to the resolved OS App-Data session vault (`<session_dir>/assets/<asset>/audit/`).
    *   Rationale: enables the Isolated Auditor subagent to verify assets safely in parallel without interfering with active modeling or rigging state.

#### 8. `./mcp/blender_kit_mcp/native_handlers.py` (Modify)

*   **Type / Scope**: Python Compatibility Shim
*   **Proposed Changes**: Replace the 606-line monolithic implementation with a thin re-export (`from .handlers import *`) so existing imports remain backward-compatible. Rationale: eliminates duplicate maintenance between `native_handlers.py` and `handlers/`.

#### 9. `./mcp/blender_kit_mcp/addon.py` (Modify)

*   **Type / Scope**: Blender Addon Entrypoint
*   **Proposed Changes**: Import `NATIVE_HANDLER_MAP` from `./mcp/blender_kit_mcp/handlers` and wrap `_patched_execute` in `session_store.verify_lease(command)` so every incoming `kit_*` JSON-RPC command enforces datablock leases and routes to the unified handler registry. Rationale: wires the 18 native tools and swarm lease protection into Blender's main-thread server.

#### 10. `./mcp/blender_kit_mcp/__init__.py` (Modify)

*   **Type / Scope**: FastMCP Server Definition
*   **Proposed Changes**: Register the 7 new MCP tools (`session_manage`, `mesh_subd_and_loops`, `mesh_compile_target`, `mesh_transform_and_assemble`, `node_graph_build`, `rig_build_armature`, `audit_run_isolated`) alongside the existing 11 tools, adding optional `agent_role: str = "orchestrator"` and `target_mode: str = "game_realtime"` parameters. Rationale: exposes the complete v3.0 native capability set to coding agents.

#### 11. `./scripts/sync-ops.mjs` (Create) & `./package.json` (Modify)

*   **Type / Scope**: Node.js Build/Sync Utility & Package Config
*   **Proposed Changes**:
    *   Create `./scripts/sync-ops.mjs` to bundle `./mcp/blender_kit_mcp/handlers/*.py` into `./skills/blender-setup/templates/scripts/blender_kit_ops.py` automatically.
    *   Update `./package.json` `"check"` script to run `node scripts/sync-ops.mjs && node scripts/validate-skills.mjs && python3 -m compileall -q skills/blender-setup/templates/scripts mcp/blender_kit_mcp`.
    *   Rationale: guarantees zero drift between live MCP handlers and offline Script Mode templates.

#### 12. `./skills/blender-setup/templates/scripts/blender_kit_ops.py` (Modify)

*   **Type / Scope**: Auto-Bundled Template Script
*   **Proposed Changes**: Generated by `./scripts/sync-ops.mjs` containing all 18 unified handler functions. Rationale: keeps offline Script Mode and `validate-skills.mjs` template path checks in sync with `mcp/blender_kit_mcp/handlers/`.

#### 13. `./skills/blender-setup/templates/scripts/audit_mesh.py`, `./skills/blender-setup/templates/scripts/audit_topology.py`, and `./skills/blender-setup/templates/scripts/audit_rig.py` (Modify)

*   **Type / Scope**: Python Audit Scripts
*   **Proposed Changes**: Update default target resolution so explicit `TARGETS = ["ObjName"]` is preferred over `"SELECTED"`, set `SELECT_DEFECTS = False` by default in `audit_topology.py`, and add `TARGET_MODE = "game_realtime" | "film_cinematic"` support. Rationale: prevents standalone audit script runs from mutating viewport selection or failing on SubD control cages.

#### 14. `./skills/blender-setup/templates/config.md` & `./skills/blender-setup/templates/engines/film-subd.md` (Modify / Create)

*   **Type / Scope**: Configuration & Target Profile Templates
*   **Proposed Changes**:
    *   In `./skills/blender-setup/templates/config.md`: add `target_mode: game_realtime` (`game_realtime | film_cinematic | dual_cage`), `session_storage: appdata` (`appdata | workspace`), and `swarm_mode: auto` (`auto | single | swarm`), plus a `## Control-cage quad budgets (film_cinematic) [START]` table.
    *   Create `./skills/blender-setup/templates/engines/film-subd.md` containing all 12 required engine profile headers enforced by `./scripts/validate-skills.mjs` (`## Import`, `## Coordinates and scale`, `## Limits`, `## Mesh rules`, `## Naming`, `## Rig`, `## Animation`, `## Materials`, `## VFX`, `## Camera`, `## Export call`, `## Import test`) tailored for USD/Alembic/Blend Catmull-Clark SubD delivery.
    *   Rationale: gives `film_cinematic` assets a first-class profile that passes `validate-skills.mjs`.

#### 15. `./skills/blender/SKILL.md`, `./skills/blender/references/swarm-protocol.md` (Create), `./skills/blender/references/routes.md`, and `./skills/blender/references/decision-interview.md` (Modify)

*   **Type / Scope**: Master Router Skill & Reference Specifications
*   **Proposed Changes**:
    *   Create `./skills/blender/references/swarm-protocol.md` defining the 5 swarm roles (`Orchestrator`, `Modeler`, `Material Maker`, `Rigger/Animator`, `Isolated Auditor`), the Phase 1 (`PartSpec` + `_DATABLOCK_LEASES`) and Phase 2 (Assembly + Isolated Audit) execution protocol, and the OS App-Data Session Vault layout.
    *   Update `./skills/blender/SKILL.md` (`<= 140` lines) to resolve the session vault via `session_manage` (no mandatory `./docs/blender/` pollution in dirty folders), ask `target_mode` (`game_realtime` vs. `film_cinematic`) in the `Q1..Qn` interview, and dispatch the 5-role swarm when `swarm_mode` is active.
    *   Update `./skills/blender/references/routes.md` and `./skills/blender/references/decision-interview.md` with `film_cinematic` and `dual_cage` chains and gates.
    *   Rationale: enables zero-footprint operation in arbitrary folders and orchestrates multi-agent swarm workflows.

#### 16. `./skills/blender-model/SKILL.md`, `./skills/blender-topology/SKILL.md`, `./skills/blender-material/SKILL.md`, `./skills/blender-rig/SKILL.md`, and `./skills/blender-qa/SKILL.md` (Modify)

*   **Type / Scope**: Stage Skill Definitions (`<= 140` lines each)
*   **Proposed Changes**:
    *   `./skills/blender-model/SKILL.md`: reference `mesh_subd_and_loops` (holding loops, edge creases) and `mesh_transform_and_assemble`.
    *   `./skills/blender-topology/SKILL.md`: branch rules by `target_mode` (`film_cinematic` 100% quad cage + SubD vs. `game_realtime` `optimize_quads_to_tris` via `mesh_compile_target`).
    *   `./skills/blender-material/SKILL.md`: reference `node_graph_build` for declarative Shader/Geometry/Compositor graphs.
    *   `./skills/blender-rig/SKILL.md`: reference `rig_build_armature` for native bone hierarchy, IK/constraints, and `ENVELOPE_KDTREE` weight binding.
    *   `./skills/blender-qa/SKILL.md`: reference `audit_run_isolated` with `target_mode` compliance gates.
    *   Rationale: aligns all stage skills with the new native MCP tools and dual-target rules while staying strictly under the 140-line linter ceiling.

#### 17. `./evals/cases.md` & `./README.md` (Modify)

*   **Type / Scope**: Evaluation Suite & Documentation
*   **Proposed Changes**: Add test cases in `./evals/cases.md` covering `film_cinematic` SubD quad-cage validation, `node_graph_build` socket alias resolution, `rig_build_armature` IK + weight binding, 5-role swarm datablock lease enforcement, and OS App-Data session vault creation in a directory without `./docs/blender/`. Update `./README.md` with the v3.0 tool table and swarm/dual-target documentation. Rationale: documents and verifies all v3.0 capabilities.

### Verification Plan

*   **Compilation/Build**: `npm run check` (runs `node scripts/sync-ops.mjs`, `node scripts/validate-skills.mjs`, and `python -m compileall -q skills/blender-setup/templates/scripts mcp/blender_kit_mcp`).
*   **Unit Tests**: Run Python unit tests verifying:
    1. `session_store.py` OS App-Data path resolution, `.blend` text-block state mirroring, and `_DATABLOCK_LEASES` rejection of unauthorized role writes.
    2. `modeling_subd.py` & `target_compile.py` pure-BMesh holding-loop generation (`segments=2, profile=1.0`), `crease_edge` assignment, `film_cinematic` all-quad validation, and `game_realtime` triangulation.
    3. `node_graph_build` version-safe socket alias resolution and introspection error reporting across Shader, Geometry Nodes, and Compositor trees.
    4. `rig_build_armature` batch `EditBone` creation, IK constraint attachment, `ENVELOPE_KDTREE` weight normalization (`max_influences <= 4`), and `atomic_context_guard` restoration of active object and mode.
*   **Static Analysis & Linting**: `npm run validate` (`scripts/validate-skills.mjs`) must report `skills: 21`, `0 warnings`, `0 errors` (`OK`), confirming every `SKILL.md` is `<= 140` lines and all referenced template/reference files exist.
*   **Test Coverage Requirement**: 100% of the 18 native MCP handlers registered in `NATIVE_HANDLER_MAP` and all 3 target modes (`game_realtime`, `film_cinematic`, `dual_cage`) covered by automated verification calls.
*   **E2E/Integration**: Execute an end-to-end 5-role swarm simulation creating a multi-part SubD asset (`target_mode="film_cinematic"`) and compiling it to `game_realtime` inside a clean temporary directory without `./docs/blender/`, verifying that zero files are written to the working directory and `audit_run_isolated` returns `pass: true`.

--------------------------------------------------------------------------------

<!-- Provenance: Indicates initial structural drafting via EGM. -->

*Drafted with EGM*
