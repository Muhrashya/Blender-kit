# Blender MCP & Bundled Blender-Kit MCP Setup

Contents: 1 overview | 2 step-by-step setup | 3 agent registration | 4 structured tools in blender-kit-mcp

## 1. Overview
`blender-kit` works with two complementary MCP layers talking to the Blender addon bridge on port `9876`:
1. **Core Blender MCP (`blender-mcp`)**: provides `look` (multi-angle, wireframe, and animation frame-strip vision), `generate_3d` (Meshy/Tripo/Hyper3D/Hunyuan3D Image-to-3D), `get_scene_info`, and `execute_blender_code`.
2. **Bundled `blender-kit-mcp` (`mcp/blender_kit_mcp/`)**: provides structured creation & surgical editing tools inside Blender so the agent can create and edit models without writing fragile raw scripts from scratch.

## 2. Step-by-step setup
| Step | Action |
|---|---|
| 1 | Install `uv` (Python tool runner) |
| 2 | In Blender: Edit > Preferences > Add-ons > Install, choose the BlenderMCP `addon.py`, enable it |
| 3 | Blender 3D view: press `N`, open the MCP for Blender tab, click Start / Connect (port `9876`) |
| 4 | Register `blender` and/or `blender-kit-mcp` in your agent (table below) |
| 5 | Restart the agent. Test: run `scene_info.py` |

## 3. Agent registration
| Agent | Core Bridge (`blender`) | Bundled Structured Tools (`blender-kit-mcp`) |
|---|---|---|
| Claude Code | `claude mcp add blender -- uvx blender-mcp` | `claude mcp add blender-kit -- uv run --directory ./mcp/blender_kit_mcp blender-kit-mcp` |
| Cursor | `.cursor/mcp.json`: `{"mcpServers":{"blender":{"command":"uvx","args":["blender-mcp"]}}}` | Add `"blender-kit":{"command":"uv","args":["run","--directory","./mcp/blender_kit_mcp","blender-kit-mcp"]}` |
| Antigravity | MCP settings: `uvx blender-mcp` | Add `uv run --directory <path>/mcp/blender_kit_mcp blender-kit-mcp` (or call `docs/blender/scripts/blender_kit_ops.py` directly) |

## 4. Structured tools in `blender-kit-mcp` (`blender_kit_ops.py`)
- `workflow_checkpoint(asset_name, tag)` — saves non-destructive `.blend` checkpoints before edits.
- `mesh_create_part(name, shape, location, rotation_deg, size, segments, bevel_width, parent_name, bone_name)` — creates clean low-poly/stylized parts (`box`, `cylinder`, `cone`, `fang`, `spike`, `crystal_shard`, `starburst_glint`, `sphere`).
- `mesh_clean_and_strip_shells(obj_name, weld_dist, strip_inner_shells)` — welds open seams, raycasts to strip hidden inner AI duplicate shells, and clears corrupted custom split normals.
- `topo_optimize_quads_to_tris(obj_name, planar_angle_deg, preserve_joint_quads, joint_radius)` — keeps quad rings at joints, dissolves coplanar loops, and beauty-triangulates static facets.
- `surface_add_gleam_effect(obj_name, mode, gleam_color, strength, frame_start, frame_end)` — creates animated `shader_sweep` gleams or 3D `starburst_mesh` glints.
- `anim_pro_motion(armature_name, clip_name, motion_type, frame_start, frame_end, amplitude_deg, phase_step_rad)` — generates phase-offset `overlapping_wave` and `floating_idle` animations.
