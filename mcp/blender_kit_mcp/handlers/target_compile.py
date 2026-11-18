"""
Dual-Target Compiler (game_realtime, film_cinematic, dual_cage), Double-Shell Stripper,
and Smart Quads-to-Triangles Optimizer for blender-kit v3.0.
Snapshots un-triangulated source quad control cages into .kit_cage_<obj_name> before
game_realtime optimization so cages can be non-destructively restored or re-compiled.
"""
import math
from typing import Any, Dict, List, Optional

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None
    bmesh = None
    Vector = None


def kit_clean_and_strip_shells(
    obj_name: str,
    weld_dist: float = 0.0005,
    strip_inner_shells: bool = True,
    shell_ray_dist: float = 0.015,
    flat_shade: bool = True,
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"error": f"Mesh object '{obj_name}' not found"}

    mesh = obj.data
    orig_verts, orig_faces = len(mesh.vertices), len(mesh.polygons)

    bm = bmesh.new()
    bm.from_mesh(mesh)
    if weld_dist > 0:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=float(weld_dist))
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()

    stripped_shells = 0
    if strip_inner_shells:
        from mathutils.bvhtree import BVHTree
        bvh = BVHTree.FromBMesh(bm, epsilon=1e-5)
        visited = set()
        comps = []
        for f in bm.faces:
            if f.index in visited:
                continue
            comp = []
            q = [f]
            visited.add(f.index)
            while q:
                curr = q.pop()
                comp.append(curr)
                for e in curr.edges:
                    for nf in e.link_faces:
                        if nf.index not in visited:
                            visited.add(nf.index)
                            q.append(nf)
            comps.append(comp)

        del_faces = []
        for comp in comps:
            if len(comp) > 60 or len(comp) < 4:
                continue
            comp_indices = {f.index for f in comp}
            buried_count = 0
            for f in comp:
                no = f.normal
                if no.length < 1e-6:
                    continue
                origin = f.calc_center_median() + no * 0.0006
                loc, norm, idx, dist = bvh.ray_cast(origin, no, shell_ray_dist)
                if loc is not None and idx not in comp_indices:
                    buried_count += 1
            if buried_count >= len(comp) * 0.55:
                del_faces.extend(comp)
                stripped_shells += 1

        if del_faces:
            bmesh.ops.delete(bm, geom=del_faces, context='FACES')

    degen = [f for f in bm.faces if f.calc_area() < 1e-7]
    if degen:
        bmesh.ops.delete(bm, geom=degen, context='FACES')

    loose_v = [v for v in bm.verts if not v.link_faces]
    if loose_v:
        bmesh.ops.delete(bm, geom=loose_v, context='VERTS')

    bm.to_mesh(mesh)
    bm.free()

    if "custom_normal" in mesh.attributes:
        mesh.attributes.remove(mesh.attributes["custom_normal"])

    for p in mesh.polygons:
        p.use_smooth = not bool(flat_shade)

    mesh.update()
    return {
        "object": obj.name,
        "orig_verts": orig_verts,
        "orig_faces": orig_faces,
        "verts": len(mesh.vertices),
        "faces": len(mesh.polygons),
        "stripped_inner_shells": stripped_shells,
    }


mesh_clean_and_strip_shells = kit_clean_and_strip_shells


def _resolve_joint_positions(obj, joint_landmarks: Optional[List[List[float]]] = None) -> List[Any]:
    joint_positions = []
    if joint_landmarks:
        inv_obj = obj.matrix_world.inverted()
        for pt in joint_landmarks:
            joint_positions.append(inv_obj @ Vector((float(pt[0]), float(pt[1]), float(pt[2]))))
        return joint_positions

    arm = None
    if obj.parent and obj.parent.type == 'ARMATURE':
        arm = obj.parent
    else:
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and getattr(mod, "object", None):
                arm = mod.object
                break

    if arm is not None:
        mat_to_obj = obj.matrix_world.inverted() @ arm.matrix_world
        for bone in arm.data.bones:
            if bone.parent:
                joint_positions.append(mat_to_obj @ bone.head_local)
    return joint_positions


def kit_optimize_quads_to_tris(
    obj_name: str,
    planar_angle_deg: float = 2.5,
    preserve_joint_quads: bool = True,
    joint_radius: float = 0.18,
    triangulate_static: bool = True,
    joint_landmarks: Optional[List[List[float]]] = None,
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"error": f"Mesh object '{obj_name}' not found"}

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    joint_positions = _resolve_joint_positions(obj, joint_landmarks) if preserve_joint_quads else []

    def in_joint_zone(co):
        return any((co - jp).length <= joint_radius for jp in joint_positions)

    if planar_angle_deg > 0:
        rad_limit = math.radians(planar_angle_deg)
        dissolve_edges = []
        for e in bm.edges:
            if len(e.link_faces) == 2 and not e.seam and e.smooth:
                if in_joint_zone(e.verts[0].co) or in_joint_zone(e.verts[1].co):
                    continue
                if e.calc_face_angle(999.0) < rad_limit:
                    dissolve_edges.append(e)
        if dissolve_edges:
            bmesh.ops.dissolve_edges(bm, edges=dissolve_edges, use_verts=True, use_face_split=False)

    bm.faces.ensure_lookup_table()
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, quad_method='BEAUTY', ngon_method='BEAUTY')

    if triangulate_static:
        bm.faces.ensure_lookup_table()
        static_quads = [
            f for f in bm.faces
            if len(f.verts) == 4 and not in_joint_zone(f.calc_center_median())
        ]
        if static_quads:
            bmesh.ops.triangulate(bm, faces=static_quads, quad_method='BEAUTY', ngon_method='BEAUTY')

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    quads = sum(1 for p in mesh.polygons if len(p.vertices) == 4)
    tris = sum(1 for p in mesh.polygons if len(p.vertices) == 3)
    ngon_cnt = sum(1 for p in mesh.polygons if len(p.vertices) > 4)
    total_tris = sum(len(p.vertices) - 2 for p in mesh.polygons)

    return {
        "object": obj.name,
        "quads": quads,
        "tris": tris,
        "ngons": ngon_cnt,
        "total_triangles": total_tris,
    }


topo_optimize_quads_to_tris = kit_optimize_quads_to_tris


def _backup_or_restore_quad_cage(obj, restore: bool = False) -> str:
    cage_name = f".kit_cage_{obj.name}"
    existing_cage = bpy.data.meshes.get(cage_name)
    if restore and existing_cage is not None:
        old_mesh = obj.data
        obj.data = existing_cage.copy()
        obj.data.name = f"{obj.name}_Mesh"
        if old_mesh.users == 0 and old_mesh != existing_cage:
            bpy.data.meshes.remove(old_mesh)
        return cage_name

    if existing_cage is None:
        backup = obj.data.copy()
        backup.name = cage_name
        backup.use_fake_user = True
    return cage_name


def kit_compile_target(
    obj_name: str,
    target_mode: str = "game_realtime",
    tri_budget: int = 2500,
    subd_levels: int = 2,
    render_levels: int = 3,
    preserve_joint_quads: bool = True,
    joint_radius: float = 0.18,
    joint_landmarks: Optional[List[List[float]]] = None,
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"error": f"Mesh object '{obj_name}' not found"}

    if target_mode == "film_cinematic":
        _backup_or_restore_quad_cage(obj, restore=True)
        for p in obj.data.polygons:
            p.use_smooth = True

        # Add weight-driven holding-loop bevel + Catmull-Clark SUBSURF if not present
        bev = obj.modifiers.get("KIT_SUBD_BEVEL") or obj.modifiers.new(name="KIT_SUBD_BEVEL", type="BEVEL")
        bev.limit_method = 'WEIGHT'
        bev.segments = 2
        bev.profile = 1.0
        bev.use_clamp_overlap = True

        sub = obj.modifiers.get("KIT_SUBSURF") or obj.modifiers.new(name="KIT_SUBSURF", type="SUBSURF")
        sub.subdivision_type = 'CATMULL_CLARK'
        sub.levels = int(subd_levels)
        sub.render_levels = int(render_levels)
        sub.use_creases = True
        if hasattr(sub, "uv_smooth"):
            sub.uv_smooth = 'PRESERVE_BOUNDARIES'

        quads = sum(1 for p in obj.data.polygons if len(p.vertices) == 4)
        tris = sum(1 for p in obj.data.polygons if len(p.vertices) == 3)
        ngons = sum(1 for p in obj.data.polygons if len(p.vertices) > 4)
        return {
            "object": obj.name,
            "target_mode": "film_cinematic",
            "cage_quads": quads,
            "cage_tris": tris,
            "cage_ngons": ngons,
            "subd_levels": subd_levels,
            "pass": ngons == 0,
        }

    elif target_mode == "game_realtime":
        cage_name = _backup_or_restore_quad_cage(obj, restore=True)
        for m in list(obj.modifiers):
            if m.type in ("SUBSURF", "BEVEL") and m.name.startswith("KIT_"):
                obj.modifiers.remove(m)

        clean_res = kit_clean_and_strip_shells(obj.name, flat_shade=True)
        opt_res = kit_optimize_quads_to_tris(
            obj.name,
            planar_angle_deg=2.5,
            preserve_joint_quads=preserve_joint_quads,
            joint_radius=joint_radius,
            triangulate_static=True,
            joint_landmarks=joint_landmarks,
        )
        total_tris = opt_res["total_triangles"]
        budget_ok = (tri_budget <= 0) or (total_tris <= tri_budget)
        return {
            "object": obj.name,
            "target_mode": "game_realtime",
            "backup_cage": cage_name,
            "stripped_inner_shells": clean_res["stripped_inner_shells"],
            "quads": opt_res["quads"],
            "tris": opt_res["tris"],
            "ngons": opt_res["ngons"],
            "total_triangles": total_tris,
            "tri_budget": tri_budget,
            "pass": opt_res["ngons"] == 0 and budget_ok,
        }

    elif target_mode == "dual_cage":
        base_stem = obj.name.removesuffix("_HP").removesuffix("_LP")
        hp_name = f"{base_stem}_HP"
        lp_name = f"{base_stem}_LP"

        hp_obj = bpy.data.objects.get(hp_name)
        if not hp_obj:
            hp_mesh = obj.data.copy()
            hp_mesh.name = f"{hp_name}_Mesh"
            hp_obj = bpy.data.objects.new(hp_name, hp_mesh)
            hp_obj.matrix_world = obj.matrix_world.copy()
            for c in obj.users_collection:
                c.objects.link(hp_obj)

        lp_obj = bpy.data.objects.get(lp_name)
        if not lp_obj:
            lp_mesh = obj.data.copy()
            lp_mesh.name = f"{lp_name}_Mesh"
            lp_obj = bpy.data.objects.new(lp_name, lp_mesh)
            lp_obj.matrix_world = obj.matrix_world.copy()
            for c in obj.users_collection:
                c.objects.link(lp_obj)

        hp_res = kit_compile_target(hp_obj.name, target_mode="film_cinematic", subd_levels=subd_levels, render_levels=render_levels)
        lp_res = kit_compile_target(
            lp_obj.name,
            target_mode="game_realtime",
            tri_budget=tri_budget,
            preserve_joint_quads=preserve_joint_quads,
            joint_radius=joint_radius,
            joint_landmarks=joint_landmarks,
        )
        return {
            "target_mode": "dual_cage",
            "hp": hp_res,
            "lp": lp_res,
            "pass": hp_res.get("pass", False) and lp_res.get("pass", False),
        }

    return {"error": f"Unknown target_mode '{target_mode}'"}
