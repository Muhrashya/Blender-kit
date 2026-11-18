"""
Blender Addon for blender-kit-mcp v3.0.
Registers all 18 unified native handlers (NATIVE_HANDLER_MAP) and enforces
5-role swarm datablock leases (verify_lease) directly inside Blender's MCP server.
"""
import inspect
import os
import sys

try:
    import bpy
except ImportError:
    bpy = None

bl_info = {
    "name": "Blender-Kit v3.0 Native Creation, SubD, Node-Graph & Swarm MCP Extension",
    "author": "blender-kit",
    "version": (3, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MCP for Blender",
    "description": "Context-free native modeling, SubD, declarative node graphs, rigging, isolated audits, and swarm lease protection for blender-kit",
    "category": "Interface",
}


def _load_handlers_package():
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
    try:
        from .handlers import NATIVE_HANDLER_MAP
        from .handlers import session_store
    except ImportError:
        from handlers import NATIVE_HANDLER_MAP
        from handlers import session_store
    return NATIVE_HANDLER_MAP, session_store


def install_native_handlers_on_running_server():
    native_map, session_store = _load_handlers_package()
    if bpy is None:
        return list(native_map.keys())

    bpy.types.blender_kit_native_handlers = native_map
    srv = getattr(bpy.types, "blendermcp_server", None)
    if srv is not None:
        orig_exec = getattr(srv, "_kit_orig_execute", srv._execute_command_internal)
        srv._kit_orig_execute = orig_exec

        def _patched_execute(command):
            lease_err = session_store.verify_lease(command)
            if lease_err is not None:
                return lease_err

            cmd_type = command.get("type")
            raw_params = dict(command.get("params") or {})
            handlers = getattr(bpy.types, "blender_kit_native_handlers", {})
            if cmd_type in handlers:
                fn = handlers[cmd_type]
                sig = inspect.signature(fn)
                accepts_var_kw = any(
                    p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
                )
                if accepts_var_kw:
                    call_params = raw_params
                else:
                    call_params = {k: v for k, v in raw_params.items() if k in sig.parameters}
                res = fn(**call_params)
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
    if bpy is not None and hasattr(bpy.types, "blender_kit_native_handlers"):
        delattr(bpy.types, "blender_kit_native_handlers")
