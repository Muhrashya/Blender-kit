"""
Declarative Armature, IK, Bone Constraints, Analytical Envelope/KDTree Weight Binding,
and Pro Overlapping/Eased Animation Handlers for blender-kit v3.0.
"""
import math
from typing import Any, Dict, List, Optional

try:
    import bpy
    from mathutils import Vector
except ImportError:
    bpy = None
    Vector = None

try:
    from .session_store import atomic_context_guard
    from .modeling_subd import _get_or_create_collection
except ImportError:
    from session_store import atomic_context_guard
    from modeling_subd import _get_or_create_collection


def _point_to_segment_dist(p, a, b) -> float:
    ab = b - a
    len_sq = ab.length_squared
    if len_sq < 1e-10:
        return (p - a).length
    t = max(0.0, min(1.0, (p - a).dot(ab) / len_sq))
    proj = a + t * ab
    return (p - proj).length


def _bind_mesh_envelope_kdtree(mesh_obj, arm_obj, max_influences: int = 4) -> Dict[str, Any]:
    mesh = mesh_obj.data
    deform_bones = [b for b in arm_obj.data.bones if b.use_deform]
    if not deform_bones:
        deform_bones = list(arm_obj.data.bones)

    arm_mod = next((m for m in mesh_obj.modifiers if m.type == 'ARMATURE'), None)
    if not arm_mod:
        arm_mod = mesh_obj.modifiers.new(name="KIT_ARMATURE", type='ARMATURE')
    arm_mod.object = arm_obj

    vg_map = {}
    for b in deform_bones:
        vg = mesh_obj.vertex_groups.get(b.name) or mesh_obj.vertex_groups.new(name=b.name)
        vg_map[b.name] = vg

    mat_mesh_to_arm = arm_obj.matrix_world.inverted() @ mesh_obj.matrix_world
    segments = [(b.name, b.head_local.copy(), b.tail_local.copy()) for b in deform_bones]
    max_inf = max(1, int(max_influences))

    for v in mesh.vertices:
        p_arm = mat_mesh_to_arm @ v.co
        dists = []
        for bname, head, tail in segments:
            d = _point_to_segment_dist(p_arm, head, tail)
            dists.append((d, bname))
        dists.sort(key=lambda x: x[0])
        chosen = dists[:max_inf]
        raw_weights = [(1.0 / (max(d, 0.005) ** 2), bname) for d, bname in chosen]
        total_w = sum(w for w, _ in raw_weights)
        if total_w > 1e-8:
            for w, bname in raw_weights:
                norm_w = w / total_w
                if norm_w >= 0.01:
                    vg_map[bname].add([v.index], float(norm_w), 'REPLACE')

    return {"mesh": mesh_obj.name, "bind_mode": "ENVELOPE_KDTREE", "bones_bound": len(deform_bones), "max_influences": max_inf}


def kit_rig_build_armature(
    armature_name: str,
    collection_name: Optional[str] = None,
    bones: Optional[List[Dict[str, Any]]] = None,
    constraints: Optional[List[Dict[str, Any]]] = None,
    bind_meshes: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    bones = bones or []
    constraints = constraints or []
    bind_meshes = bind_meshes or []

    arm_obj = bpy.data.objects.get(armature_name)
    if not arm_obj or arm_obj.type != 'ARMATURE':
        arm_data = bpy.data.armatures.new(armature_name)
        arm_obj = bpy.data.objects.new(armature_name, arm_data)
        col = _get_or_create_collection(collection_name)
        col.objects.link(arm_obj)
    else:
        arm_data = arm_obj.data

    # 1. Batch EditBone creation inside atomic_context_guard
    if bones:
        with atomic_context_guard(arm_obj, mode="EDIT"):
            ebones = arm_data.edit_bones
            created_eb = {}
            for bspec in bones:
                bname = bspec["name"]
                eb = ebones.get(bname) or ebones.new(bname)
                eb.head = Vector(bspec.get("head", (0.0, 0.0, 0.0)))
                eb.tail = Vector(bspec.get("tail", (0.0, 0.0, 0.5)))
                eb.roll = math.radians(float(bspec.get("roll_deg", 0.0)))
                eb.use_deform = bool(bspec.get("use_deform", True))
                if "bbone_segments" in bspec:
                    eb.bbone_segments = max(1, int(bspec["bbone_segments"]))
                created_eb[bname] = eb

            for bspec in bones:
                parent_name = bspec.get("parent")
                if parent_name and parent_name in created_eb:
                    eb = created_eb[bspec["name"]]
                    eb.parent = created_eb[parent_name]
                    eb.use_connect = bool(bspec.get("use_connect", False))

    # 2. Attach PoseBone constraints in OBJECT mode
    bpy.context.view_layer.update()
    constraints_added = 0
    for cspec in constraints:
        bname = cspec.get("bone")
        pb = arm_obj.pose.bones.get(bname)
        if not pb:
            continue
        ctype = cspec.get("type", "IK").upper()
        con = pb.constraints.new(type=ctype)
        target_name = cspec.get("target_obj", armature_name)
        target_obj = bpy.data.objects.get(target_name) if target_name else arm_obj
        if hasattr(con, "target") and target_obj:
            con.target = target_obj
        if hasattr(con, "subtarget") and cspec.get("subtarget"):
            con.subtarget = str(cspec["subtarget"])
        if hasattr(con, "chain_count") and "chain_count" in cspec:
            con.chain_count = int(cspec["chain_count"])
        if hasattr(con, "pole_target") and cspec.get("pole_target"):
            con.pole_target = bpy.data.objects.get(cspec["pole_target"]) or arm_obj
        if hasattr(con, "pole_subtarget") and cspec.get("pole_subtarget"):
            con.pole_subtarget = str(cspec["pole_subtarget"])
        if hasattr(con, "pole_angle") and "pole_angle_deg" in cspec:
            con.pole_angle = math.radians(float(cspec["pole_angle_deg"]))
        if "influence" in cspec:
            con.influence = float(cspec["influence"])
        for sk, sv in (cspec.get("settings") or {}).items():
            if hasattr(con, sk):
                setattr(con, sk, sv)
        constraints_added += 1

    # 3. Bind meshes (Phase 2 Assembly or single-call rig)
    bound_results = []
    for bmesh_spec in bind_meshes:
        mname = bmesh_spec["mesh_name"] if isinstance(bmesh_spec, dict) else str(bmesh_spec)
        bmode = bmesh_spec.get("bind_mode", "ENVELOPE_KDTREE") if isinstance(bmesh_spec, dict) else "ENVELOPE_KDTREE"
        max_inf = int(bmesh_spec.get("max_influences", 4)) if isinstance(bmesh_spec, dict) else 4
        mobj = bpy.data.objects.get(mname)
        if not mobj or mobj.type != 'MESH':
            continue

        if bmode == "RIGID_BONE":
            bone_target = (bmesh_spec.get("bone") if isinstance(bmesh_spec, dict) else None) or (arm_data.bones[0].name if arm_data.bones else "Root")
            vg = mobj.vertex_groups.get(bone_target) or mobj.vertex_groups.new(name=bone_target)
            vg.add(list(range(len(mobj.data.vertices))), 1.0, 'REPLACE')
            arm_mod = next((m for m in mobj.modifiers if m.type == 'ARMATURE'), None) or mobj.modifiers.new(name="KIT_ARMATURE", type='ARMATURE')
            arm_mod.object = arm_obj
            bound_results.append({"mesh": mobj.name, "bind_mode": "RIGID_BONE", "bone": bone_target})
        elif bmode == "AUTO_HEAT":
            try:
                with atomic_context_guard(arm_obj, mode="OBJECT", extra_selected=[mobj]):
                    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
                bound_results.append({"mesh": mobj.name, "bind_mode": "AUTO_HEAT"})
            except Exception:
                bound_results.append(_bind_mesh_envelope_kdtree(mobj, arm_obj, max_influences=max_inf))
        else:
            bound_results.append(_bind_mesh_envelope_kdtree(mobj, arm_obj, max_influences=max_inf))

    return {
        "armature": arm_obj.name,
        "total_bones": len(arm_data.bones),
        "constraints_added": constraints_added,
        "bound_meshes": bound_results,
    }


def kit_pro_motion(
    armature_name: str,
    clip_name: str = "idle_loop",
    motion_type: str = "overlapping_wave",
    frame_start: int = 1,
    frame_end: int = 48,
    amplitude_deg: float = 12.0,
    phase_step_rad: float = 0.65,
    set_scene_range: bool = False,
) -> Dict[str, Any]:
    arm = bpy.data.objects.get(armature_name)
    if not arm or arm.type != 'ARMATURE':
        return {"error": f"Armature '{armature_name}' not found"}

    if set_scene_range:
        bpy.context.scene.frame_start = int(frame_start)
        bpy.context.scene.frame_end = int(frame_end)

    if not arm.animation_data:
        arm.animation_data_create()

    act_name = f"AN_{arm.name}_{clip_name}"
    act = bpy.data.actions.get(act_name) or bpy.data.actions.new(name=act_name)
    act.use_fake_user = True
    arm.animation_data.action = act

    pbones = list(arm.pose.bones)
    duration = max(1, int(frame_end) - int(frame_start))

    if motion_type == "attack_anticipation":
        phases = [
            (0.00, 0.00),
            (0.25, -0.45),
            (0.55, 1.25),
            (0.80, -0.12),
            (1.00, 0.00),
        ]
        for ratio, mult in phases:
            f = int(round(frame_start + duration * ratio))
            for bi, pb in enumerate(pbones):
                pb.rotation_mode = 'XYZ'
                w = min(1.3, 0.4 + 0.15 * bi)
                ang_x = math.radians(amplitude_deg * mult * w)
                pb.rotation_euler = (ang_x, 0.0, 0.0)
                pb.keyframe_insert(data_path="rotation_euler", frame=f)
    else:
        num_steps = 8
        for step in range(num_steps + 1):
            f = int(round(frame_start + (duration * step / num_steps)))
            phase_base = 2.0 * math.pi * (step / num_steps)
            for bi, pb in enumerate(pbones):
                pb.rotation_mode = 'XYZ'
                weight_along_chain = min(1.4, 0.35 + 0.12 * bi)
                ang_z = math.radians(amplitude_deg * weight_along_chain) * math.sin(phase_base - bi * phase_step_rad)
                ang_x = math.radians(amplitude_deg * 0.45 * weight_along_chain) * math.cos(phase_base - bi * phase_step_rad)
                if motion_type == "floating_idle" and bi == 0:
                    pb.location = (0.0, 0.0, 0.06 * math.sin(phase_base))
                    pb.keyframe_insert(data_path="location", frame=f)
                pb.rotation_euler = (ang_x, 0.0, ang_z)
                pb.keyframe_insert(data_path="rotation_euler", frame=f)

    for fc in getattr(act, "fcurves", []):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = 'AUTO_CLAMPED'
            kp.handle_right_type = 'AUTO_CLAMPED'

    return {
        "armature": arm.name,
        "action": act.name,
        "motion_type": motion_type,
        "bones_keyed": len(pbones),
        "frames": [frame_start, frame_end],
        "loop_closed": True,
    }


anim_pro_motion = kit_pro_motion
