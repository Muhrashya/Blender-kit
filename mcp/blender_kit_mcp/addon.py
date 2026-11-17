"""
Blender Addon for blender-kit-mcp.
Registers native structured creation, BMesh surgical editing, modifier stack,
curve/tube, UV unwrap, material preset, topology quad-to-tri, gleam VFX,
and pro animation handlers directly inside Blender's MCP server so agents
call native JSON RPC commands instead of sending raw script strings.
"""
import os
import sys
import bpy

bl_info = {
    "name": "Blender-Kit Native Creation & Editing MCP Extension",
    "author": "blender-kit",
    "version": (2, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MCP for Blender",
    "description": "Native structured modeling, bevel/extrude/modifier, UV, topology, gleam VFX, and pro animation handlers for blender-kit",
    "category": "Interface",
}


def install_native_handlers_on_running_server():
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)

    repo_scripts = os.path.abspath(
        os.path.join(addon_dir, "..", "..", "skills", "blender-setup", "templates", "scripts")
    )
    if os.path.isdir(repo_scripts) and repo_scripts not in sys.path:
        sys.path.insert(0, repo_scripts)

    import native_handlers
    import blender_kit_ops

    native_map = {
        "kit_checkpoint": native_handlers.kit_checkpoint,
        "kit_create_primitive": native_handlers.kit_create_primitive,
        "kit_bmesh_edit": native_handlers.kit_bmesh_edit,
        "kit_modifier": native_handlers.kit_modifier,
        "kit_curve_tube": native_handlers.kit_curve_tube,
        "kit_uv_unwrap": native_handlers.kit_uv_unwrap,
        "kit_material_preset": native_handlers.kit_material_preset,
        "kit_clean_and_strip_shells": blender_kit_ops.mesh_clean_and_strip_shells,
        "kit_optimize_quads_to_tris": blender_kit_ops.topo_optimize_quads_to_tris,
        "kit_add_gleam_effect": blender_kit_ops.surface_add_gleam_effect,
        "kit_pro_motion": blender_kit_ops.anim_pro_motion,
    }

    bpy.types.blender_kit_native_handlers = native_map
    srv = getattr(bpy.types, "blendermcp_server", None)
    if srv is not None and not getattr(srv, "_kit_native_patched", False):
        orig_exec = srv._execute_command_internal

        def _patched_execute(command):
            cmd_type = command.get("type")
            params = command.get("params", {}) or {}
            handlers = getattr(bpy.types, "blender_kit_native_handlers", {})
            if cmd_type in handlers:
                res = handlers[cmd_type](**params)
                return {"status": "success", "result": res}
            return orig_exec(command)

        srv._execute_command_internal = _patched_execute
        srv._kit_native_patched = True
    return list(native_map.keys())


def register():
    try:
        install_native_handlers_on_running_server()
    except Exception as exc:
        print(f"[blender-kit-mcp] Deferred native handler registration: {exc}")


def unregister():
    if hasattr(bpy.types, "blender_kit_native_handlers"):
        delattr(bpy.types, "blender_kit_native_handlers")
