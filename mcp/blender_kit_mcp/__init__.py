"""
Blender-Kit v3.0 Native Creation, SubD, Node-Graph, Rigging & Multi-Agent Swarm MCP Server.
Exposes all 18 context-free native handlers over JSON-RPC to Blender's main-thread server:
1.  session_manage             -> kit_session_manage
2.  workflow_checkpoint        -> kit_checkpoint
3.  mesh_create_primitive      -> kit_create_primitive
4.  mesh_bmesh_edit            -> kit_bmesh_edit
5.  mesh_subd_and_loops        -> kit_subd_and_loops
6.  mesh_compile_target        -> kit_compile_target
7.  mesh_transform_and_assemble-> kit_transform_and_assemble
8.  mesh_modifier              -> kit_modifier
9.  curve_create_tube          -> kit_curve_tube
10. node_graph_build           -> kit_node_graph_build
11. uv_unwrap_and_pack         -> kit_uv_unwrap
12. material_apply_preset      -> kit_material_preset
13. surface_add_gleam_effect   -> kit_add_gleam_effect
14. rig_build_armature         -> kit_rig_build_armature
15. anim_pro_motion            -> kit_pro_motion
16. mesh_clean_and_strip_shells-> kit_clean_and_strip_shells
17. topo_optimize_quads_to_tris-> kit_optimize_quads_to_tris
18. audit_run_isolated         -> kit_audit_run_isolated
"""
import json
import os
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("blender-kit-mcp")

BLENDER_HOST = os.environ.get("BLENDER_HOST", "127.0.0.1")
BLENDER_PORT = int(os.environ.get("BLENDER_PORT", "9876"))
ADDON_PATH = Path(__file__).resolve().parent / "addon.py"


def _send_blender_command(cmd_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = json.dumps({"type": cmd_type, "params": params or {}}).encode("utf-8")
    with socket.create_connection((BLENDER_HOST, BLENDER_PORT), timeout=60.0) as sock:
        sock.sendall(payload)
        chunks: List[bytes] = []
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
            try:
                return json.loads(b"".join(chunks).decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
    return {"status": "error", "message": "Empty response from Blender"}


def _call_native(cmd_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Send a pure structured JSON command to Blender's native handler."""
    resp = _send_blender_command(cmd_type, params)
    if resp.get("status") == "error" and "Unknown command type" in str(resp.get("message", "")):
        boot_code = (
            f"import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('blender_kit_addon', {repr(str(ADDON_PATH))})\n"
            f"mod = importlib.util.module_from_spec(spec)\n"
            f"spec.loader.exec_module(mod)\n"
            f"mod.install_native_handlers_on_running_server()\n"
        )
        _send_blender_command("execute_code", {"code": boot_code})
        resp = _send_blender_command(cmd_type, params)
    return resp.get("result", resp)


@mcp.tool()
def session_manage(
    action: str = "init",
    asset_name: str = "Scene",
    target_mode: str = "game_realtime",
    agent_role: str = "orchestrator",
    lease_prefixes: Optional[List[str]] = None,
    keep_last: int = 5,
) -> Dict[str, Any]:
    """
    Manage the OS App-Data Session Vault and 5-role swarm datablock leases.
    Actions: 'init', 'acquire_lease', 'release_lease', 'reset_leases', 'prune_checkpoints', 'get_state'.
    """
    return _call_native(
        "kit_session_manage",
        {
            "action": action,
            "asset_name": asset_name,
            "target_mode": target_mode,
            "agent_role": agent_role,
            "lease_prefixes": lease_prefixes,
            "keep_last": keep_last,
        },
    )


@mcp.tool()
def workflow_checkpoint(
    asset_name: str = "Scene",
    tag: str = "pre_edit",
    keep_last: int = 5,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """Save a non-destructive .blend checkpoint into the OS App-Data Session Vault."""
    return _call_native(
        "kit_checkpoint",
        {"asset_name": asset_name, "tag": tag, "keep_last": keep_last, "agent_role": agent_role},
    )


@mcp.tool()
def mesh_create_primitive(
    name: str,
    shape: str = "box",
    location: List[float] = [0.0, 0.0, 0.0],
    rotation_deg: List[float] = [0.0, 0.0, 0.0],
    size: List[float] = [1.0, 1.0, 1.0],
    segments: int = 12,
    bevel_width: float = 0.0,
    bevel_segments: int = 1,
    origin_at_bottom: bool = True,
    collection_name: Optional[str] = None,
    parent_name: Optional[str] = None,
    bone_name: Optional[str] = None,
    target_mode: str = "game_realtime",
    smooth_shading: Optional[bool] = None,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Create a parametric 3D mesh natively inside Blender.
    Supported shapes: 'box', 'cylinder', 'cone', 'pyramid', 'sphere', 'icosphere',
    'capsule', 'torus', 'blade_foil', 'arch', 'crystal_shard', 'starburst_glint', 'fang', 'spike'.
    """
    return _call_native(
        "kit_create_primitive",
        {
            "name": name,
            "shape": shape,
            "location": location,
            "rotation_deg": rotation_deg,
            "size": size,
            "segments": segments,
            "bevel_width": bevel_width,
            "bevel_segments": bevel_segments,
            "origin_at_bottom": origin_at_bottom,
            "collection_name": collection_name,
            "parent_name": parent_name,
            "bone_name": bone_name,
            "target_mode": target_mode,
            "smooth_shading": smooth_shading,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def mesh_bmesh_edit(
    obj_name: str,
    operation: str = "bevel",
    selector: str = "sharp",
    indices: Optional[List[int]] = None,
    offset: float = 0.03,
    segments: int = 1,
    profile: float = 0.5,
    angle_deg: float = 30.0,
    translation: List[float] = [0.0, 0.0, 0.0],
    along_normal: float = 0.0,
    scale: List[float] = [1.0, 1.0, 1.0],
    thickness: float = 0.04,
    depth: float = 0.0,
    axis: str = "Z",
    taper_factor: float = 0.0,
    twist_deg: float = 0.0,
    plane_co: List[float] = [0.0, 0.0, 0.5],
    plane_no: List[float] = [0.0, 0.0, 1.0],
    clear_inner: bool = False,
    clear_outer: bool = False,
    lathe_profile_pts: Optional[List[List[float]]] = None,
    lathe_steps: int = 16,
    lathe_angle_deg: float = 360.0,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Run native context-free BMesh modeling operations on any mesh:
    'bevel', 'extrude', 'inset', 'subdivide_edges', 'bisect', 'taper_twist', 'spin_lathe', 'symmetrize'.
    """
    return _call_native(
        "kit_bmesh_edit",
        {
            "obj_name": obj_name,
            "operation": operation,
            "selector": selector,
            "indices": indices,
            "offset": offset,
            "segments": segments,
            "profile": profile,
            "angle_deg": angle_deg,
            "translation": translation,
            "along_normal": along_normal,
            "scale": scale,
            "thickness": thickness,
            "depth": depth,
            "axis": axis,
            "taper_factor": taper_factor,
            "twist_deg": twist_deg,
            "plane_co": plane_co,
            "plane_no": plane_no,
            "clear_inner": clear_inner,
            "clear_outer": clear_outer,
            "lathe_profile_pts": lathe_profile_pts,
            "lathe_steps": lathe_steps,
            "lathe_angle_deg": lathe_angle_deg,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def mesh_subd_and_loops(
    obj_name: str,
    action: str = "add_holding_loops",
    selector: str = "sharp",
    edge_indices: Optional[List[int]] = None,
    offset: float = 0.02,
    crease_value: float = 1.0,
    bevel_weight: float = 1.0,
    subd_levels: int = 2,
    render_levels: int = 3,
    angle_deg: float = 30.0,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Author Subdivision Surface control cages in pure BMesh:
    Actions: 'add_holding_loops' (2-seg profile-1.0 support loops), 'set_crease',
    'set_bevel_weight', 'bridge_loops', 'grid_fill', 'setup_subsurf'.
    """
    return _call_native(
        "kit_subd_and_loops",
        {
            "obj_name": obj_name,
            "action": action,
            "selector": selector,
            "edge_indices": edge_indices,
            "offset": offset,
            "crease_value": crease_value,
            "bevel_weight": bevel_weight,
            "subd_levels": subd_levels,
            "render_levels": render_levels,
            "angle_deg": angle_deg,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def mesh_compile_target(
    obj_name: str,
    target_mode: str = "game_realtime",
    tri_budget: int = 2500,
    subd_levels: int = 2,
    render_levels: int = 3,
    preserve_joint_quads: bool = True,
    joint_radius: float = 0.18,
    joint_landmarks: Optional[List[List[float]]] = None,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Compile a Universal Quad Control Cage for 'game_realtime', 'film_cinematic' (SubD), or 'dual_cage' (_HP + _LP).
    """
    return _call_native(
        "kit_compile_target",
        {
            "obj_name": obj_name,
            "target_mode": target_mode,
            "tri_budget": tri_budget,
            "subd_levels": subd_levels,
            "render_levels": render_levels,
            "preserve_joint_quads": preserve_joint_quads,
            "joint_radius": joint_radius,
            "joint_landmarks": joint_landmarks,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def mesh_transform_and_assemble(
    obj_name: str,
    apply_location: bool = False,
    apply_rotation: bool = True,
    apply_scale: bool = True,
    set_origin: Optional[str] = None,
    join_objects: Optional[List[str]] = None,
    assign_materials: Optional[List[str]] = None,
    target_collection: Optional[str] = None,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Apply transforms in pure BMesh, set origins ('BOTTOM_CENTER', 'GEOMETRY_CENTER', 'WORLD_ORIGIN'),
    join sub-meshes, bind material slots, and organize collections.
    """
    return _call_native(
        "kit_transform_and_assemble",
        {
            "obj_name": obj_name,
            "apply_location": apply_location,
            "apply_rotation": apply_rotation,
            "apply_scale": apply_scale,
            "set_origin": set_origin,
            "join_objects": join_objects,
            "assign_materials": assign_materials,
            "target_collection": target_collection,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def mesh_modifier(
    obj_name: str,
    action: str = "add",
    mod_type: str = "BEVEL",
    mod_name: Optional[str] = None,
    apply_now: bool = False,
    settings: Optional[Dict[str, Any]] = None,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Manage Blender modifiers natively (add, apply via isolated single-modifier depsgraph, remove).
    """
    return _call_native(
        "kit_modifier",
        {
            "obj_name": obj_name,
            "action": action,
            "mod_type": mod_type,
            "mod_name": mod_name,
            "apply_now": apply_now,
            "settings": settings or {},
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def curve_create_tube(
    name: str,
    points: List[List[float]],
    bevel_depth: float = 0.05,
    bevel_resolution: int = 2,
    resolution_u: int = 8,
    cyclic: bool = False,
    taper_start: float = 1.0,
    taper_end: float = 1.0,
    convert_to_mesh: bool = True,
    collection_name: Optional[str] = None,
    target_mode: str = "game_realtime",
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """Create 3D tubes, cables, pipes, handles, horns, vines, or hair strips from 3D control points."""
    return _call_native(
        "kit_curve_tube",
        {
            "name": name,
            "points": points,
            "bevel_depth": bevel_depth,
            "bevel_resolution": bevel_resolution,
            "resolution_u": resolution_u,
            "cyclic": cyclic,
            "taper_start": taper_start,
            "taper_end": taper_end,
            "convert_to_mesh": convert_to_mesh,
            "collection_name": collection_name,
            "target_mode": target_mode,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def node_graph_build(
    tree_type: str = "SHADER",
    target_name: str = "MAT_Default",
    nodes: Optional[List[Dict[str, Any]]] = None,
    links: Optional[List[Dict[str, Any]]] = None,
    interface_sockets: Optional[List[Dict[str, Any]]] = None,
    macro: Optional[str] = None,
    clear_existing: bool = True,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Declaratively build Shader, Geometry Nodes, or Compositor node graphs with version-safe socket aliases
    or built-in macros ('triplanar_pbr', 'edge_cavity_wear', 'subd_micro_displacement',
    'gn_surface_scatter', 'gn_curve_profile_sweep', 'comp_cinematic_glare_grade').
    """
    return _call_native(
        "kit_node_graph_build",
        {
            "tree_type": tree_type,
            "target_name": target_name,
            "nodes": nodes,
            "links": links,
            "interface_sockets": interface_sockets,
            "macro": macro,
            "clear_existing": clear_existing,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def uv_unwrap_and_pack(
    obj_name: str,
    method: str = "auto_seams",
    seam_angle_deg: float = 55.0,
    island_margin: float = 0.02,
    texture_size: int = 1024,
    target_density_px_per_m: float = 256.0,
    scale_to_target_density: bool = False,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Mark seams, unwrap and pack UV islands. Methods: 'auto_seams' (angle-based), 'conformal',
    'smart_project', 'cube_project', 'cylinder_project', 'sphere_project', 'zero_bleed_facet_atlas'
    (one padded cell per face, for palette/low-poly). Returns measured texel density and
    out_of_bounds_uvs; scale_to_target_density=True rescales UVs to target_density_px_per_m.
    """
    return _call_native(
        "kit_uv_unwrap",
        {
            "obj_name": obj_name,
            "method": method,
            "seam_angle_deg": seam_angle_deg,
            "island_margin": island_margin,
            "texture_size": texture_size,
            "target_density_px_per_m": target_density_px_per_m,
            "scale_to_target_density": scale_to_target_density,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def material_apply_preset(
    obj_name: Optional[str] = None,
    preset: str = "stylized_pbr",
    base_color: List[float] = [0.75, 0.25, 0.22],
    secondary_color: List[float] = [0.92, 0.78, 0.65],
    roughness: float = 0.65,
    metallic: float = 0.0,
    emission_strength: float = 0.0,
    material_name: Optional[str] = None,
    bake_to_texture: bool = False,
    texture_size: int = 1024,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """Create or apply an export-ready Principled BSDF material preset (standalone or bound to obj_name)."""
    return _call_native(
        "kit_material_preset",
        {
            "obj_name": obj_name,
            "preset": preset,
            "base_color": base_color,
            "secondary_color": secondary_color,
            "roughness": roughness,
            "metallic": metallic,
            "emission_strength": emission_strength,
            "material_name": material_name,
            "bake_to_texture": bake_to_texture,
            "texture_size": texture_size,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def surface_add_gleam_effect(
    obj_name: Optional[str] = None,
    mode: str = "shader_sweep",
    gleam_color: List[float] = [0.85, 0.98, 1.0],
    strength: float = 3.5,
    frame_start: int = 1,
    frame_end: int = 60,
    material_name: Optional[str] = None,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """Add an animated diagonal gleam sweep ('shader_sweep') or 3D diamond glint ('starburst_mesh')."""
    return _call_native(
        "kit_add_gleam_effect",
        {
            "obj_name": obj_name,
            "mode": mode,
            "gleam_color": gleam_color,
            "strength": strength,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "material_name": material_name,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def rig_build_armature(
    armature_name: str,
    collection_name: Optional[str] = None,
    bones: Optional[List[Dict[str, Any]]] = None,
    constraints: Optional[List[Dict[str, Any]]] = None,
    bind_meshes: Optional[List[Dict[str, Any]]] = None,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """
    Create or update an Armature with batch EditBones, PoseBone constraints (IK, COPY_ROTATION, etc.),
    and deterministic ENVELOPE_KDTREE / RIGID_BONE / AUTO_HEAT mesh skinning.
    """
    return _call_native(
        "kit_rig_build_armature",
        {
            "armature_name": armature_name,
            "collection_name": collection_name,
            "bones": bones,
            "constraints": constraints,
            "bind_meshes": bind_meshes,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def anim_pro_motion(
    armature_name: str,
    clip_name: str = "idle_loop",
    motion_type: str = "overlapping_wave",
    frame_start: int = 1,
    frame_end: int = 48,
    amplitude_deg: float = 12.0,
    phase_step_rad: float = 0.65,
    set_scene_range: bool = False,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """Author pro animations ('overlapping_wave', 'floating_idle', 'attack_anticipation') on an armature."""
    return _call_native(
        "kit_pro_motion",
        {
            "armature_name": armature_name,
            "clip_name": clip_name,
            "motion_type": motion_type,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "amplitude_deg": amplitude_deg,
            "phase_step_rad": phase_step_rad,
            "set_scene_range": set_scene_range,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def mesh_clean_and_strip_shells(
    obj_name: str,
    weld_dist: float = 0.0005,
    strip_inner_shells: bool = True,
    shell_ray_dist: float = 0.015,
    flat_shade: bool = True,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """Weld seams, raycast to strip laminated inner duplicate shells, and clear custom split normals."""
    return _call_native(
        "kit_clean_and_strip_shells",
        {
            "obj_name": obj_name,
            "weld_dist": weld_dist,
            "strip_inner_shells": strip_inner_shells,
            "shell_ray_dist": shell_ray_dist,
            "flat_shade": flat_shade,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def topo_optimize_quads_to_tris(
    obj_name: str,
    planar_angle_deg: float = 2.5,
    preserve_joint_quads: bool = True,
    joint_radius: float = 0.18,
    triangulate_static: bool = True,
    joint_landmarks: Optional[List[List[float]]] = None,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    """Optimize quads/ngons to game-ready triangles while preserving quad rings at joints."""
    return _call_native(
        "kit_optimize_quads_to_tris",
        {
            "obj_name": obj_name,
            "planar_angle_deg": planar_angle_deg,
            "preserve_joint_quads": preserve_joint_quads,
            "joint_radius": joint_radius,
            "triangulate_static": triangulate_static,
            "joint_landmarks": joint_landmarks,
            "agent_role": agent_role,
        },
    )


@mcp.tool()
def audit_run_isolated(
    audit_type: str = "all",
    target_objects: Optional[List[str]] = None,
    target_mode: str = "game_realtime",
    budget: int = 0,
    armature_name: Optional[str] = None,
    ref_aspect_xz: float = 0.0,
    asset_name: str = "Scene",
    texture_px: int = 1024,
    target_density: float = 256.0,
    agent_role: str = "auditor",
) -> Dict[str, Any]:
    """
    Run context-free read-only audits: 'mesh', 'topology', 'uv' (texel density + 0-1 bounds),
    'visual_match', 'rig', 'anim' (loop closure), 'naming', or 'all'.
    Never reads or mutates bpy.context.selected_objects.
    """
    return _call_native(
        "kit_audit_run_isolated",
        {
            "audit_type": audit_type,
            "target_objects": target_objects,
            "target_mode": target_mode,
            "budget": budget,
            "armature_name": armature_name,
            "ref_aspect_xz": ref_aspect_xz,
            "asset_name": asset_name,
            "texture_px": texture_px,
            "target_density": target_density,
            "agent_role": agent_role,
        },
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
