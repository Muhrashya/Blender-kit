# blender-kit (v3.0)

Universal agent skills and bundled **Context-Free Native Creation, SubD, Node-Graph, Rigging & Multi-Agent Swarm MCP** for Blender 3D pipelines (`game_realtime`, `film_cinematic` Catmull-Clark SubD, and `dual_cage` high-to-low baking):
- Interactive `Q1..Qn` Matt Pocock-style decision interviews
- **18 Context-Free Native MCP Tools** (`mcp/blender_kit_mcp/`) executing directly on `bpy.data` / `bmesh` without mutating global viewport selection or generating fragile raw Python scripts
- **Universal Quad Control Cage & Dual-Target Compiler** (`mesh_subd_and_loops` + `mesh_compile_target`) supporting holding loops, edge creases, Catmull-Clark `SUBSURF`, and smart quads-to-triangles game compilation
- **Declarative Shader, Geometry Nodes & Compositor Graph Builder** (`node_graph_build`) with version-safe Blender 4.x/5.x socket aliases and macro presets
- **Declarative Armature, IK, Constraint & Analytical Weight Builder** (`rig_build_armature` + `anim_pro_motion`)
- **5-Role Multi-Agent Swarm Architecture** (`Orchestrator`, `Modeler`, `Material Maker`, `Rigger/Animator`, and read-only `Isolated Auditor`) with server-side Datablock Leases (`_DATABLOCK_LEASES`)
- **Zero-Footprint OS App-Data Session Vault** (`session_manage`) keyed to `.blend` scene UUID and mirrored into `bpy.data.texts[".blender_kit_session"]` so your working folder stays 100% clean

Contains **21 specialized skills** and **9 universal object archetypes** coordinated through a single router command: `/blender`.

- **Supported Target Modes:** `game_realtime` (FBX/GLB), `film_cinematic` (Catmull-Clark SubD, USD/Alembic/Blend/EXR), `dual_cage` (`_HP` SubD + `_LP` game mesh)
- **Supported Engines:** `generic-gltf`, `film-subd`, `roblox`, `unity`, `unreal`, `godot`, `web-three`
- **Supported Art Styles:** `voxel`, `lowpoly`, `stylized`, `realistic`
- **Supported Archetypes:** Props, Hard-Surface/Sci-Fi, Weapons & Armor, Vehicles & Mechs, Architecture & Interiors, Modular Environment Kits, Nature/Foliage/Rocks/Crystals, Characters & Hands, Creatures & Pets

---

## Key Capabilities (v3.0)

1. **18 Context-Free Native MCP Tools (`mcp/blender_kit_mcp/`)**:
   Executes primitive creation, BMesh modeling (`bevel`, `extrude`, `inset`, `subdivide_edges`, `bisect`, `taper_twist`, `spin_lathe`, `symmetrize`), SubD holding loops and creases (`mesh_subd_and_loops`), dual-target compilation (`mesh_compile_target`), isolated single-modifier evaluation (`mesh_modifier`), declarative Shader/Geometry/Compositor graphs (`node_graph_build`), batch Armature/IK/KDTree-weight rigging (`rig_build_armature`), and read-only isolated audits (`audit_run_isolated`) via native JSON-RPC handlers.
2. **5-Role Multi-Agent Swarm on the Same Asset (`swarm-protocol.md`)**:
   - **Phase 1 (Lease-Isolated Parallel Datablock Authoring):** `Modeler(s)` author `SM_<Asset>_<Part_k>`, `Material Maker` authors standalone `MAT_<Asset>_*` node graphs, and `Rigger/Animator` authors `ARM_<Asset>` bones/IK and `AN_<Asset>_*` clips concurrently under `_DATABLOCK_LEASES`.
   - **Phase 2 (Assembly Barrier & Isolated Audit):** `Orchestrator` binds materials, UVs, and skin weights, and dispatches the read-only `Isolated Auditor` (`audit_run_isolated` + `look`).
3. **Zero-Footprint OS App-Data Session Vault**:
   Running `/blender` in any directory without `./docs/blender/` automatically stores `config.md`, `state.md`, `brief.md`, `audit/*.json`, `screens/*.png`, and rolling `.blend` checkpoints (`keep_last = 5`) inside `%LOCALAPPDATA%/blender-kit/sessions/<stem>_<scene_uuid>/` and mirrors session metadata into `bpy.data.texts[".blender_kit_session"]`.
4. **Universal Quad Control Cage (`game_realtime` & `film_cinematic`)**:
   Author clean quad cages with 2-segment profile-1.0 holding loops and `crease_edge` weights; compile non-destructively to `film_cinematic` (live Catmull-Clark `SUBSURF`, `curved_surface_tris == 0`, `pole_balance % 8 == 0`) or `game_realtime` (double-shell stripping, 3-ring joint quads preserved, static quads beauty-triangulated, `.kit_cage_<obj>` backed up).

---

## Installation

### 1. Prerequisites

- **Blender 4.x or 5.x** installed and accessible.
- **Node.js (v18+)** for running `npx` and skill validation.
- **Python 3.10+** and tool runner `uv`.

### 2. Install Skills

| Environment | Command |
|---|---|
| Project directory (default) | `npx skills@latest add Muhrashya/blender-kit` |
| Global install | `npx skills@latest add Muhrashya/blender-kit -g` |
| Specific agent only | `npx skills@latest add Muhrashya/blender-kit -a claude-code` (or `cursor`, `codex`, `antigravity`) |
| Local repository copy | `npx skills add ./blender-kit` |
| Claude Code plugin | `/plugin marketplace add Muhrashya/blender-kit` |
| ChatGPT / Web LLM | Run `npm run bundle:chatgpt`, then use `dist/chatgpt-instructions.md` and `dist/chatgpt-knowledge.md` |

### 3. Register MCP Servers in Your Agent

- **Claude Code**:
  ```bash
  claude mcp add blender -- uvx blender-mcp
  claude mcp add blender-kit -- uv run --directory ./mcp/blender_kit_mcp blender-kit-mcp
  ```

- **Cursor** (`.cursor/mcp.json`) / **Claude Desktop** (`claude_desktop_config.json`):
  ```json
  {
    "mcpServers": {
      "blender": {
        "command": "uvx",
        "args": ["blender-mcp"]
      },
      "blender-kit": {
        "command": "uv",
        "args": ["run", "--directory", "./mcp/blender_kit_mcp", "blender-kit-mcp"]
      }
    }
  }
  ```

---

## Complete v3.0 Native MCP Tool Matrix (`mcp/blender_kit_mcp/`)

| # | FastMCP Tool Name | Blender RPC Handler | Legacy Alias (`blender_kit_ops.py`) | Capability |
|---|---|---|---|---|
| 1 | `session_manage` | `kit_session_manage` | `kit_session_manage` | Initializes OS App-Data Session Vault, manages `_DATABLOCK_LEASES` (`init`, `acquire_lease`, `release_lease`, `reset_leases`, `prune_checkpoints`, `get_state`). |
| 2 | `workflow_checkpoint` | `kit_checkpoint` | `ensure_checkpoint` | Saves rolling `.blend` checkpoints (`keep_last = 5`) to the Session Vault and mirrors state into `bpy.data.texts[".blender_kit_session"]`. |
| 3 | `mesh_create_primitive` | `kit_create_primitive` | `mesh_create_part` | Creates 14+ parametric shapes (`box`, `cylinder`, `cone`, `pyramid`, `sphere`, `icosphere`, `capsule`, `torus`, `blade_foil`, `arch`, `crystal_shard`, `starburst_glint`, `fang`, `spike`) with explicit collection linking and `target_mode` shading. |
| 4 | `mesh_bmesh_edit` | `kit_bmesh_edit` | `kit_bmesh_edit` | Context-free BMesh operations: `bevel`, `extrude`, `inset`, `subdivide_edges`, `bisect`, `taper_twist`, `spin_lathe`, `symmetrize`. |
| 5 | `mesh_subd_and_loops` | `kit_subd_and_loops` | `kit_subd_and_loops` | Pure-BMesh SubD cage tools: `add_holding_loops` (`segments=2, profile=1.0`), `set_crease`, `set_bevel_weight`, `bridge_loops`, `grid_fill`, `setup_subsurf`. |
| 6 | `mesh_compile_target` | `kit_compile_target` | `kit_compile_target` | Compiles a Universal Quad Control Cage for `game_realtime`, `film_cinematic` (SubD), or `dual_cage` (`_HP` + `_LP`) while backing up `.kit_cage_<obj>`. |
| 7 | `mesh_transform_and_assemble` | `kit_transform_and_assemble` | `kit_transform_and_assemble` | Applies location/rotation/scale in pure BMesh, sets origins (`BOTTOM_CENTER`, `GEOMETRY_CENTER`, `WORLD_ORIGIN`), joins meshes, and assigns material slots. |
| 8 | `mesh_modifier` | `kit_modifier` | `kit_modifier` | Adds, applies (via isolated single-modifier dependency-graph evaluation), or removes modifiers (`BEVEL`, `SUBSURF`, `MIRROR`, `SOLIDIFY`, `ARRAY`, `BOOLEAN`, etc.). |
| 9 | `curve_create_tube` | `kit_curve_tube` | `kit_curve_tube` | Builds 3D spline tubes, cables, pipes, hilts, horns, branches, or hair strips with radius taper. |
| 10 | `node_graph_build` | `kit_node_graph_build` | `kit_node_graph_build` | Builds declarative `SHADER`, `GEOMETRY`, and `COMPOSITOR` node graphs with version-safe socket aliases and 6 built-in macros (`triplanar_pbr`, `edge_cavity_wear`, `subd_micro_displacement`, `gn_surface_scatter`, `gn_curve_profile_sweep`, `comp_cinematic_glare_grade`). |
| 11 | `uv_unwrap_and_pack` | `kit_uv_unwrap` | `kit_uv_unwrap` | Context-guarded auto-seam marking, `ANGLE_BASED` / `smart_project` / `cube_project` unwrapping, and island packing. |
| 12 | `material_apply_preset` | `kit_material_preset` | `kit_material_preset` | Creates standalone or object-bound Principled BSDF presets (`metal_steel`, `gold_trim`, `wood_warm`, `stone_slate`, `crystal_glow`, `foliage_leaf`, `stylized_pbr`). |
| 13 | `surface_add_gleam_effect` | `kit_add_gleam_effect` | `surface_add_gleam_effect` | Authors animated diagonal emission sweeps (`shader_sweep`) or 3D diamond starburst glints (`starburst_mesh`). |
| 14 | `rig_build_armature` | `kit_rig_build_armature` | `kit_rig_build_armature` | Context-guarded batch `EditBone` creation, `PoseBone` constraints (`IK`, `COPY_ROTATION`, `DAMPED_TRACK`, etc.), and analytical `ENVELOPE_KDTREE` / `RIGID_BONE` / `AUTO_HEAT` weight binding. |
| 15 | `anim_pro_motion` | `kit_pro_motion` | `anim_pro_motion` | Generates phase-offset `overlapping_wave`, `floating_idle`, and 5-phase `attack_anticipation` clips with `AUTO_CLAMPED` Bezier handles. |
| 16 | `mesh_clean_and_strip_shells` | `kit_clean_and_strip_shells` | `mesh_clean_and_strip_shells` | Welds seams (`0.5mm`), BVH-raycasts to strip hidden inner duplicate AI shells, and clears custom split normals. |
| 17 | `topo_optimize_quads_to_tris` | `kit_optimize_quads_to_tris` | `topo_optimize_quads_to_tris` | Preserves 3-ring quad loops around joints, dissolves coplanar loops, and beauty-triangulates static facets. |
| 18 | `audit_run_isolated` | `kit_audit_run_isolated` | `kit_audit_run_isolated` | Runs read-only context-free `mesh`, `topology`, `visual_match`, and `rig` audits on explicit object lists and writes JSON reports to the Session Vault. |

---

## Development, Sync & Verification

```bash
npm run sync             # Bundle mcp/blender_kit_mcp/handlers/*.py -> blender_kit_ops.py
npm run validate         # Lint all 21 skill definition files and cross-references (0 warnings, 0 errors)
npm run test             # Run Python unit & 5-role swarm lease tests (tests/test_v3_handlers.py)
npm run check            # Run sync + validate + python compileall + unit tests
npm run bundle:chatgpt   # Build bundled documentation files for ChatGPT
```

## License

MIT
