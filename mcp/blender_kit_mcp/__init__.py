"""
Blender-Kit Native Creation & Editing MCP Server.
Calls native structured handlers registered inside Blender's MCP server
(zero script-string generation per call):
- Universal Primitives & Archetypes (11+ parametric shapes)
- Granular BMesh Modeling (bevel, extrude, inset, subdivide_edges, bisect, taper_twist, spin_lathe, symmetrize)
- Non-Destructive Modifiers (BEVEL, MIRROR, SOLIDIFY, ARRAY, BOOLEAN, SUBSURF, SHRINKWRAP, SIMPLE_DEFORM, WEIGHTED_NORMAL, TRIANGULATE, REMESH)
- 3D Curves, Tubes, Cables, Pipes, Vines & Hair Strips
- Smart Quads-to-Triangles & Double-Shell Stripper
- Universal UV Unwrapping, Seams, Island Packing & Zero-Bleed Facet Atlas
- Material Presets, Gleam/Shimmer Sweeps & 3D Starburst Glints
- Pro Overlapping Wave & Eased Keyframe Animation
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
        # One-time bootstrap of native handlers into the live Blender server
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
def workflow_checkpoint(asset_name: str = "Scene", tag: str = "pre_edit") -> Dict[str, Any]:
    """Save a non-destructive .blend checkpoint natively before creating or editing."""
    return _call_native("kit_checkpoint", {"asset_name": asset_name, "tag": tag})


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
) -> Dict[str, Any]:
    """
    Create a parametric 3D mesh natively inside Blender without scripts.
    Supported shapes: 'box', 'cylinder', 'cone', 'pyramid', 'sphere', 'icosphere',
    'capsule', 'torus', 'blade_foil' (swords/daggers), 'arch' (architecture),
    'crystal_shard', 'starburst_glint', 'fang', 'spike'.
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
) -> Dict[str, Any]:
    """
    Run native BMesh modeling operations on any mesh:
    - 'bevel': Bevel edges ('all', 'sharp', 'top', 'bottom', 'vertical', 'horizontal', or indices)
    - 'extrude': Extrude faces ('top', 'bottom', 'front', 'back', 'left', 'right', or indices) with translation/normal/scale
    - 'inset': Inset faces with thickness and depth
    - 'subdivide_edges': Loop-cut / subdivide edges
    - 'bisect': Slice mesh with a plane and optionally remove inner/outer half and cap
    - 'taper_twist': Taper and/or twist progressively along X, Y, or Z
    - 'spin_lathe': Lathe a 2D (radius, z) profile into 3D bottles, vases, goblets, pillars, wheels, barrels
    - 'symmetrize': Mirror and weld across X, Y, or Z
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
) -> Dict[str, Any]:
    """
    Manage Blender modifiers natively (add, apply, remove):
    Supports 'BEVEL', 'MIRROR', 'SOLIDIFY', 'ARRAY', 'BOOLEAN', 'SUBSURF',
    'SHRINKWRAP', 'SIMPLE_DEFORM', 'WEIGHTED_NORMAL', 'WIREFRAME', 'DECIMATE', 'REMESH', 'TRIANGULATE'.
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
) -> Dict[str, Any]:
    """
    Create 3D tubes, cables, pipes, handles, horns, vines, tree branches, or stylized hair strips
    from a list of 3D control points with start-to-end radius taper.
    """
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
) -> Dict[str, Any]:
    """
    Automatically mark UV seams by angle + boundaries, unwrap ('auto_seams', 'smart_project', 'cube_project'),
    and pack UV islands cleanly into 0-1 space.
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
        },
    )


@mcp.tool()
def material_apply_preset(
    obj_name: str,
    preset: str = "stylized_pbr",
    base_color: List[float] = [0.75, 0.25, 0.22],
    secondary_color: List[float] = [0.92, 0.78, 0.65],
    roughness: float = 0.65,
    metallic: float = 0.0,
    emission_strength: float = 0.0,
) -> Dict[str, Any]:
    """
    Apply an export-ready Principled BSDF material preset ('metal_steel', 'gold_trim',
    'wood_warm', 'stone_slate', 'crystal_glow', 'foliage_leaf', 'stylized_pbr').
    """
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
        },
    )


@mcp.tool()
def mesh_clean_and_strip_shells(
    obj_name: str,
    weld_dist: float = 0.0005,
    strip_inner_shells: bool = True,
    shell_ray_dist: float = 0.015,
    flat_shade: bool = True,
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
        },
    )


@mcp.tool()
def topo_optimize_quads_to_tris(
    obj_name: str,
    planar_angle_deg: float = 2.5,
    preserve_joint_quads: bool = True,
    joint_radius: float = 0.18,
    triangulate_static: bool = True,
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
        },
    )


@mcp.tool()
def surface_add_gleam_effect(
    obj_name: str,
    mode: str = "shader_sweep",
    gleam_color: List[float] = [0.85, 0.98, 1.0],
    strength: float = 3.5,
    frame_start: int = 1,
    frame_end: int = 60,
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
) -> Dict[str, Any]:
    """Author pro overlapping-wave or floating-idle animations natively on an armature."""
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
        },
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
