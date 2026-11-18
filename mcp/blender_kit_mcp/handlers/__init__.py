"""
Unified Handler Registry for blender-kit v3.0.
Exports NATIVE_HANDLER_MAP (all 18 kit_* RPC command handlers) and backward-compatible
aliases for both live MCP Mode and offline Script Mode.
"""
try:
    from .session_store import (
        resolve_session_dir,
        mirror_state_to_blend,
        restore_state_from_blend,
        verify_lease,
        atomic_context_guard,
        kit_checkpoint,
        ensure_checkpoint,
        kit_session_manage,
    )
    from .modeling_subd import (
        kit_create_primitive,
        mesh_create_part,
        kit_bmesh_edit,
        kit_subd_and_loops,
        kit_modifier,
        kit_curve_tube,
        kit_transform_and_assemble,
    )
    from .target_compile import (
        kit_clean_and_strip_shells,
        mesh_clean_and_strip_shells,
        kit_optimize_quads_to_tris,
        topo_optimize_quads_to_tris,
        kit_compile_target,
    )
    from .node_graphs import (
        kit_uv_unwrap,
        kit_material_preset,
        kit_add_gleam_effect,
        surface_add_gleam_effect,
        kit_node_graph_build,
    )
    from .rigging_anim import (
        kit_rig_build_armature,
        kit_pro_motion,
        anim_pro_motion,
    )
    from .audits import kit_audit_run_isolated
except ImportError:
    from session_store import (
        resolve_session_dir,
        mirror_state_to_blend,
        restore_state_from_blend,
        verify_lease,
        atomic_context_guard,
        kit_checkpoint,
        ensure_checkpoint,
        kit_session_manage,
    )
    from modeling_subd import (
        kit_create_primitive,
        mesh_create_part,
        kit_bmesh_edit,
        kit_subd_and_loops,
        kit_modifier,
        kit_curve_tube,
        kit_transform_and_assemble,
    )
    from target_compile import (
        kit_clean_and_strip_shells,
        mesh_clean_and_strip_shells,
        kit_optimize_quads_to_tris,
        topo_optimize_quads_to_tris,
        kit_compile_target,
    )
    from node_graphs import (
        kit_uv_unwrap,
        kit_material_preset,
        kit_add_gleam_effect,
        surface_add_gleam_effect,
        kit_node_graph_build,
    )
    from rigging_anim import (
        kit_rig_build_armature,
        kit_pro_motion,
        anim_pro_motion,
    )
    from audits import kit_audit_run_isolated

NATIVE_HANDLER_MAP = {
    "kit_session_manage": kit_session_manage,
    "kit_checkpoint": kit_checkpoint,
    "kit_create_primitive": kit_create_primitive,
    "kit_bmesh_edit": kit_bmesh_edit,
    "kit_subd_and_loops": kit_subd_and_loops,
    "kit_compile_target": kit_compile_target,
    "kit_transform_and_assemble": kit_transform_and_assemble,
    "kit_modifier": kit_modifier,
    "kit_curve_tube": kit_curve_tube,
    "kit_node_graph_build": kit_node_graph_build,
    "kit_uv_unwrap": kit_uv_unwrap,
    "kit_material_preset": kit_material_preset,
    "kit_add_gleam_effect": kit_add_gleam_effect,
    "kit_rig_build_armature": kit_rig_build_armature,
    "kit_pro_motion": kit_pro_motion,
    "kit_clean_and_strip_shells": kit_clean_and_strip_shells,
    "kit_optimize_quads_to_tris": kit_optimize_quads_to_tris,
    "kit_audit_run_isolated": kit_audit_run_isolated,
}
