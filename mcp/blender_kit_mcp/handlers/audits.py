"""
Context-Free Isolated Audit Engine for blender-kit v3.0.
Evaluates mesh, dual-target topology (game_realtime vs film_cinematic), UV bleed,
visual match, rig weights, and animation loop closure on explicit object lists
without reading or mutating bpy.context.selected_objects or active_object.
"""
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None
    bmesh = None
    Vector = None

try:
    from .session_store import resolve_session_dir
except ImportError:
    from session_store import resolve_session_dir


def _resolve_target_meshes(target_objects: Optional[List[str]] = None) -> List[Any]:
    if bpy is None or not getattr(bpy, "context", None):
        return []
    if target_objects:
        return [
            bpy.data.objects[name]
            for name in target_objects
            if name in bpy.data.objects and bpy.data.objects[name].type == "MESH"
        ]
    return [o for o in bpy.context.scene.objects if o.type == "MESH" and o.visible_get()]


def _audit_mesh_isolated(objs: List[Any], budget: int = 0) -> Dict[str, Any]:
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    total_tris = 0
    for o in objs:
        bm = bmesh.new()
        bm.from_object(o, dg)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        tris = sum(len(f.verts) - 2 for f in bm.faces)
        ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
        non_manifold = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        loose_verts = sum(1 for v in bm.verts if not v.link_edges)
        total_tris += tris
        bm.free()

        scale_ok = all(abs(s - 1.0) < 1e-4 for s in o.scale)
        rot_ok = all(abs(r) < 1e-4 for r in o.rotation_euler)
        obj_pass = (ngons == 0 and non_manifold == 0 and loose_verts == 0 and scale_ok and rot_ok)
        rows.append({
            "object": o.name,
            "tris": tris,
            "ngons": ngons,
            "non_manifold": non_manifold,
            "loose_verts": loose_verts,
            "transforms_applied": scale_ok and rot_ok,
            "pass": obj_pass,
        })

    budget_ok = (budget <= 0) or (total_tris <= budget)
    return {
        "audit": "mesh",
        "total_tris": total_tris,
        "budget": budget,
        "budget_ok": budget_ok,
        "objects": rows,
        "pass": all(r["pass"] for r in rows) and budget_ok,
    }


def _audit_topology_isolated(
    objs: List[Any],
    target_mode: str = "game_realtime",
    armature_name: Optional[str] = None,
) -> Dict[str, Any]:
    curved_angle_rad = math.radians(2.5)
    rows = []
    for o in objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        quads = sum(1 for f in bm.faces if len(f.verts) == 4)
        tris = sum(1 for f in bm.faces if len(f.verts) == 3)
        ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
        curved_surface_tris = sum(
            1 for f in bm.faces
            if len(f.verts) == 3 and any(
                len(e.link_faces) == 2 and e.calc_face_angle(0.0) > curved_angle_rad
                for e in f.edges
            )
        )
        closed_manifold = all(e.is_manifold for e in bm.edges)
        all_quads = (tris == 0 and ngons == 0)
        pole_balance = sum(4 - len(v.link_edges) for v in bm.verts)
        pole_balance_ok = (pole_balance % 8 == 0) if (closed_manifold and all_quads) else True

        joint_poles = 0
        arm = bpy.data.objects.get(armature_name) if armature_name else (o.parent if o.parent and o.parent.type == "ARMATURE" else None)
        if arm is not None and arm.type == "ARMATURE":
            m_to_obj = o.matrix_world.inverted() @ arm.matrix_world
            jpts = [m_to_obj @ b.head_local for b in arm.data.bones if b.parent]
            for v in bm.verts:
                if not v.is_boundary and len(v.link_edges) != 4:
                    if any((v.co - jp).length <= 0.08 for jp in jpts):
                        joint_poles += 1

        bm.free()

        if target_mode == "film_cinematic":
            has_subd = any(m.type == "SUBSURF" for m in o.modifiers)
            obj_pass = (ngons == 0 and curved_surface_tris == 0 and pole_balance_ok and has_subd)
        else:
            obj_pass = (ngons == 0 and joint_poles == 0)

        rows.append({
            "object": o.name,
            "target_mode": target_mode,
            "quads": quads,
            "tris": tris,
            "ngons": ngons,
            "curved_surface_tris": curved_surface_tris,
            "pole_balance": pole_balance,
            "pole_balance_multiple_of_8": pole_balance_ok,
            "poles_near_joints": joint_poles,
            "pass": obj_pass,
        })

    return {"audit": "topology", "target_mode": target_mode, "objects": rows, "pass": all(r["pass"] for r in rows)}


def _audit_visual_match_isolated(objs: List[Any], ref_aspect_xz: float = 0.0) -> Dict[str, Any]:
    rows = []
    for obj in objs:
        mesh = obj.data
        bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        xs = [v.x for v in bbox]
        ys = [v.y for v in bbox]
        zs = [v.z for v in bbox]
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        dz = max(zs) - min(zs)
        aspect_xz = round(dx / max(dz, 1e-5), 3)
        aspect_yz = round(dy / max(dz, 1e-5), 3)

        bleed_faces = 0
        uv_layer = mesh.uv_layers.active
        img = None
        if mesh.materials:
            mat = mesh.materials[0]
            if mat and mat.use_nodes:
                for n in mat.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image:
                        img = n.image
                        break

        if uv_layer and img and img.size[0] > 0 and img.size[1] > 0:
            W, H = img.size
            px = img.pixels[:]
            uv_data = uv_layer.data
            for poly in mesh.polygons:
                cols = []
                for li in poly.loop_indices:
                    uv = uv_data[li].uv
                    ix = min(W - 1, max(0, int(uv[0] * W)))
                    iy = min(H - 1, max(0, int(uv[1] * H)))
                    base = (iy * W + ix) * 4
                    cols.append((px[base], px[base + 1], px[base + 2]))
                if cols:
                    r_span = max(c[0] for c in cols) - min(c[0] for c in cols)
                    g_span = max(c[1] for c in cols) - min(c[1] for c in cols)
                    b_span = max(c[2] for c in cols) - min(c[2] for c in cols)
                    if max(r_span, g_span, b_span) > 0.25:
                        bleed_faces += 1

        bleed_ratio = round(bleed_faces / max(1, len(mesh.polygons)), 4)
        aspect_ok = True
        if ref_aspect_xz > 0:
            aspect_ok = abs(aspect_xz - ref_aspect_xz) <= 0.25 * ref_aspect_xz

        rows.append({
            "object": obj.name,
            "dimensions_m": [round(dx, 3), round(dy, 3), round(dz, 3)],
            "aspect_xz": aspect_xz,
            "aspect_yz": aspect_yz,
            "bleed_faces": bleed_faces,
            "bleed_ratio": bleed_ratio,
            "has_custom_normals": mesh.has_custom_normals,
            "pass": (bleed_ratio <= 0.05) and aspect_ok,
        })

    return {"audit": "visual_match", "objects": rows, "pass": all(r["pass"] for r in rows)}


def _audit_uv_isolated(
    objs: List[Any],
    texture_px: int = 1024,
    target_density: float = 256.0,
    tolerance: float = 0.20,
) -> Dict[str, Any]:
    rows = []
    for obj in objs:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        uv = bm.loops.layers.uv.active
        if uv is None:
            rows.append({
                "object": obj.name,
                "has_uv": False,
                "pass": False,
                "failed": ["no_uv"],
            })
            bm.free()
            continue

        s = obj.matrix_world.to_scale()
        scale_factor = abs(s.x * s.y * s.z) ** (2.0 / 3.0) if (s.x and s.y and s.z) else 1.0
        world_area = 0.0
        uv_area = 0.0
        out_of_bounds = 0
        for f in bm.faces:
            world_area += f.calc_area() * scale_factor
            pts = [l[uv].uv.copy() for l in f.loops]
            for p in pts:
                if p.x < -1e-3 or p.x > 1.001 or p.y < -1e-3 or p.y > 1.001:
                    out_of_bounds += 1
            a = 0.0
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]
                a += x1 * y2 - x2 * y1
            uv_area += abs(a) * 0.5
        bm.free()

        density = float(texture_px) * math.sqrt(uv_area / world_area) if (world_area > 0 and uv_area > 0) else 0.0
        density_ok = (target_density <= 0) or (target_density * (1.0 - tolerance) <= density <= target_density * (1.0 + tolerance))
        bounds_ok = (out_of_bounds == 0)
        failed = []
        if not density_ok:
            failed.append("texel_density_out_of_tolerance")
        if not bounds_ok:
            failed.append("uv_out_of_0_1_bounds")
        rows.append({
            "object": obj.name,
            "has_uv": True,
            "uv_area_sum": round(uv_area, 4),
            "world_area_m2": round(world_area, 4),
            "texel_density_px_per_m": round(density, 1),
            "target_density_px_per_m": target_density,
            "out_of_bounds_uvs": out_of_bounds,
            "failed": failed,
            "pass": density_ok and bounds_ok,
        })
    return {"audit": "uv", "objects": rows, "pass": bool(rows) and all(r["pass"] for r in rows)}


def _audit_anim_isolated(loop_suffix: str = "_loop", root_bone: Optional[str] = None) -> Dict[str, Any]:
    fps = bpy.context.scene.render.fps if (bpy and getattr(bpy, "context", None)) else 30
    actions_out = []
    for a in getattr(bpy.data, "actions", []):
        f0, f1 = a.frame_range
        row: Dict[str, Any] = {
            "action": a.name,
            "frame_start": f0,
            "frame_end": f1,
            "frames": int(f1 - f0) + 1,
            "duration_s": round((f1 - f0) / max(1, fps), 3),
        }
        if a.name.endswith(loop_suffix) and hasattr(a, "fcurves"):
            bad = []
            for fc in a.fcurves:
                d = abs(fc.evaluate(f0) - fc.evaluate(f1))
                if d > 1e-3:
                    bad.append({"channel": f"{fc.data_path}[{fc.array_index}]", "diff": round(d, 4)})
            row["loop_open_channels"] = bad[:20]
            row["loop_closed"] = not bad
        if root_bone and hasattr(a, "fcurves"):
            p = f'pose.bones["{root_bone}"].location'
            row["root_location_drift_xyz"] = [round(fc.evaluate(f1) - fc.evaluate(f0), 4) for fc in a.fcurves if fc.data_path == p]
        actions_out.append(row)
    return {
        "audit": "anim",
        "fps": fps,
        "actions": actions_out,
        "pass": all(r.get("loop_closed", True) for r in actions_out) and len(actions_out) > 0,
    }


def _audit_naming_isolated(objs: List[Any]) -> Dict[str, Any]:
    bad = []
    for o in objs:
        if o.type == "MESH" and not o.name.startswith(("SM_", "SK_", ".kit_cage_")):
            bad.append({"kind": "object", "name": o.name, "expected_prefix": ["SM_", "SK_"]})
        for slot in getattr(o, "material_slots", []):
            if slot.material and not slot.material.name.startswith("MAT_"):
                bad.append({"kind": "material", "name": slot.material.name, "expected_prefix": ["MAT_"]})
    return {"audit": "naming", "violations": bad, "pass": len(bad) == 0}


def _audit_rig_isolated(objs: List[Any], armature_name: Optional[str] = None, target_mode: str = "game_realtime") -> Dict[str, Any]:
    arm = bpy.data.objects.get(armature_name) if armature_name else next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if not arm or arm.type != "ARMATURE":
        return {"audit": "rig", "pass": False, "error": "No armature found"}

    max_inf_limit = 8 if target_mode == "film_cinematic" else 4
    deform_names = {b.name for b in arm.data.bones if b.use_deform}
    over_inf_total = 0
    unweighted_total = 0

    for m in objs:
        gnames = {g.index: g.name for g in m.vertex_groups}
        for v in m.data.vertices:
            w = [g.weight for g in v.groups if g.group in gnames and gnames[g.group] in deform_names and g.weight > 1e-4]
            if not w:
                unweighted_total += 1
            if len(w) > max_inf_limit:
                over_inf_total += 1

    passed = (unweighted_total == 0 and over_inf_total == 0)
    return {
        "audit": "rig",
        "armature": arm.name,
        "bones": len(arm.data.bones),
        "deform_bones": len(deform_names),
        "max_influences_limit": max_inf_limit,
        "unweighted_verts": unweighted_total,
        "over_influence_verts": over_inf_total,
        "pass": passed,
    }


def kit_audit_run_isolated(
    audit_type: str = "all",
    target_objects: Optional[List[str]] = None,
    target_mode: str = "game_realtime",
    budget: int = 0,
    armature_name: Optional[str] = None,
    ref_aspect_xz: float = 0.0,
    asset_name: str = "Scene",
    texture_px: int = 1024,
    target_density: float = 256.0,
) -> Dict[str, Any]:
    objs = _resolve_target_meshes(target_objects)
    atype = audit_type.lower()
    results: Dict[str, Any] = {}

    if atype in ("mesh", "all"):
        results["mesh"] = _audit_mesh_isolated(objs, budget=budget)
    if atype in ("topology", "all"):
        results["topology"] = _audit_topology_isolated(objs, target_mode=target_mode, armature_name=armature_name)
    if atype == "uv":
        results["uv"] = _audit_uv_isolated(objs, texture_px=texture_px, target_density=target_density)
    if atype in ("visual_match", "all"):
        results["visual_match"] = _audit_visual_match_isolated(objs, ref_aspect_xz=ref_aspect_xz)
    if atype == "rig" or (atype == "all" and armature_name):
        results["rig"] = _audit_rig_isolated(objs, armature_name=armature_name, target_mode=target_mode)
    if atype == "anim":
        results["anim"] = _audit_anim_isolated()
    if atype == "naming":
        results["naming"] = _audit_naming_isolated(objs)

    overall_pass = all(sub.get("pass", True) for sub in results.values())
    payload = {
        "asset_name": asset_name,
        "audit_type": atype,
        "target_mode": target_mode,
        "pass": overall_pass,
        "results": results,
    }

    try:
        asset_dir = Path(resolve_session_dir(asset_name, target_mode=target_mode))
        audit_file = asset_dir / "audit" / f"audit_{atype}.json"
        audit_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["report_path"] = str(audit_file)
    except Exception:
        pass

    return payload
