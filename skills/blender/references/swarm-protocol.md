# Multi-Agent Swarm Protocol & Zero-Footprint Session Vault

Contents: 1 roles and leases | 2 two-phase execution | 3 PartSpec and Landmark Graph | 4 zero-footprint session vault

## 1. Roles and datablock leases (`_DATABLOCK_LEASES`)
When `swarm_mode` is `swarm` (or `auto` on multi-part assets), `/blender` coordinates 5 specialist roles over the native MCP server (`session_manage(action="acquire_lease", ...)`):

| Role Display Name | `agent_role` Token | Leased Datablock Prefixes | Allowed Native MCP Tools |
|---|---|---|---|
| Orchestrator | `"orchestrator"` | All datablocks (Phase 2 assembly & barriers) | `session_manage`, `workflow_checkpoint`, `mesh_transform_and_assemble`, `mesh_compile_target`, `uv_unwrap_and_pack` |
| Modeler / Artist (`1..N`) | `"modeler"` | `SM_<Asset>_<Part_k>*`, `GN_<Asset>_<Part_k>*` | `mesh_create_primitive`, `mesh_bmesh_edit`, `mesh_subd_and_loops`, `mesh_modifier`, `curve_create_tube` |
| Material / Texture Maker | `"material_maker"` | `MAT_<Asset>_*`, `T_<Asset>_*` | `node_graph_build`, `material_apply_preset`, `surface_add_gleam_effect` |
| Rigger / Animator | `"rigger_animator"` | `ARM_<Asset>*`, `AN_<Asset>_*` | `rig_build_armature` (`bind_meshes=[]` in Phase 1), `anim_pro_motion` (`set_scene_range=False`) |
| Isolated Auditor | `"auditor"` | `READ_ONLY` (all datablocks) | `audit_run_isolated`, `look` |

## 2. Two-phase execution on the same asset
1. **Phase 1 — Lease-Isolated Parallel Datablock Authoring:**
   - The Orchestrator runs the `Q1..Qn` interview, calls `session_manage(action="init")`, writes the `PartSpec` and `Landmark Graph` into `state.md`, and registers leases via `session_manage(action="acquire_lease")` (`TTL = 300s`).
   - **Modeler(s)** build each mesh component (`SM_<Asset>_<Part_k>`) as a clean quad control cage.
   - **Material Maker** authors standalone `MAT_<Asset>_*` node trees (`obj_name=None, material_name="MAT_..."`).
   - **Rigger/Animator** authors `ARM_<Asset>` bones/constraints (`bind_meshes=[]`) and `AN_<Asset>_*` actions from the `Landmark Graph` coordinates.
2. **Phase 2 — Assembly Barrier & Isolated Audit:**
   - The Orchestrator calls `session_manage(action="reset_leases")`, joins or parents parts (`mesh_transform_and_assemble(assign_materials=[...])`), unwraps UVs (`uv_unwrap_and_pack`), compiles the target (`mesh_compile_target`), and binds skin weights (`rig_build_armature(bones=[], bind_meshes=[...])`).
   - **Isolated Auditor** runs `audit_run_isolated` + multi-angle `look` captures. Any failed check re-dispatches only the owning specialist role.

## 3. `PartSpec` and `Landmark Graph`
Recorded in `<session_dir>/assets/<Asset>/state.md` before Phase 1 starts:
- **`PartSpec`**: table of sub-parts (`part_name`, `shape_archetype`, `bbox_min`, `bbox_max`, `material_slot`, `parent_bone`).
- **`Landmark Graph`**: exact 3D joint head/tail coordinates (`[x, y, z]`) shared between Modeler(s) and Rigger so armature bones align with mesh joint loops before binding.

## 4. Zero-footprint OS App-Data Session Vault
When `./docs/blender/config.md` is absent in the working directory, `session_manage(action="init")` stores all session files in `%LOCALAPPDATA%/blender-kit/sessions/<stem>_<scene_uuid>/` (seeded from `docs/blender/` templates) and mirrors state to `bpy.data.texts[".blender_kit_session"]`, leaving the user's project directory untouched.
