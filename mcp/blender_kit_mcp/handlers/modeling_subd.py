"""
Context-free BMesh, Subdivision Surface, Holding Loops, Edge Creases, Modifiers,
Curves, and Transform/Assembly handlers for blender-kit v3.0.
"""
import math
from typing import Any, Dict, List, Optional, Tuple

try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix, Euler
except ImportError:
    bpy = None
    bmesh = None
    Vector = Matrix = Euler = None


def _get_or_create_collection(collection_name: Optional[str] = None):
    if bpy is None:
        return None
    if collection_name:
        col = bpy.data.collections.get(collection_name)
        if not col:
            col = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(col)
        return col
    return bpy.context.scene.collection


def _select_elements_by_rule(bm, elem_type="FACES", selector="all", indices=None, angle_deg=30.0):
    if elem_type == "FACES":
        bm.faces.ensure_lookup_table()
        if indices:
            return [bm.faces[i] for i in indices if 0 <= i < len(bm.faces)]
        if selector == "all":
            return list(bm.faces)
        dirs = {
            "top": Vector((0, 0, 1)),
            "bottom": Vector((0, 0, -1)),
            "front": Vector((0, -1, 0)),
            "back": Vector((0, 1, 0)),
            "right": Vector((1, 0, 0)),
            "left": Vector((-1, 0, 0)),
        }
        if selector in dirs:
            d = dirs[selector]
            return [f for f in bm.faces if f.normal.dot(d) > 0.65]
        return list(bm.faces)

    elif elem_type == "EDGES":
        bm.edges.ensure_lookup_table()
        if indices:
            return [bm.edges[i] for i in indices if 0 <= i < len(bm.edges)]
        if selector == "all":
            return list(bm.edges)
        if selector == "sharp":
            rad = math.radians(float(angle_deg))
            return [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) >= rad]
        if selector == "boundary":
            return [e for e in bm.edges if e.is_boundary]
        if selector == "top":
            zs = [v.co.z for v in bm.verts]
            z_max = max(zs) if zs else 0.0
            return [e for e in bm.edges if all(abs(v.co.z - z_max) < 0.05 for v in e.verts)]
        if selector == "bottom":
            zs = [v.co.z for v in bm.verts]
            z_min = min(zs) if zs else 0.0
            return [e for e in bm.edges if all(abs(v.co.z - z_min) < 0.05 for v in e.verts)]
        if selector == "vertical":
            return [e for e in bm.edges if abs((e.verts[1].co - e.verts[0].co).normalized().z) > 0.85]
        if selector == "horizontal":
            return [e for e in bm.edges if abs((e.verts[1].co - e.verts[0].co).normalized().z) < 0.15]
        return list(bm.edges)


def kit_create_primitive(
    name: str,
    shape: str = "box",
    location: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    size: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    segments: int = 12,
    bevel_width: float = 0.0,
    bevel_segments: int = 1,
    origin_at_bottom: bool = True,
    collection_name: Optional[str] = None,
    parent_name: Optional[str] = None,
    bone_name: Optional[str] = None,
    target_mode: str = "game_realtime",
    smooth_shading: Optional[bool] = None,
) -> Dict[str, Any]:
    bm = bmesh.new()
    sx, sy, sz = float(size[0]), float(size[1]), float(size[2])
    segs = max(3, int(segments))

    if shape == "box":
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    elif shape == "cylinder":
        bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=False, segments=segs,
            radius1=sx * 0.5, radius2=sx * 0.5, depth=sz
        )
        if abs(sx - sy) > 1e-4:
            bmesh.ops.scale(bm, vec=(1.0, sy / max(sx, 1e-5), 1.0), verts=bm.verts)
    elif shape in ("cone", "fang", "spike", "pyramid"):
        segs_use = 4 if shape == "pyramid" else segs
        bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=True, segments=segs_use,
            radius1=sx * 0.5, radius2=0.001, depth=sz
        )
        if abs(sx - sy) > 1e-4:
            bmesh.ops.scale(bm, vec=(1.0, sy / max(sx, 1e-5), 1.0), verts=bm.verts)
    elif shape == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(4, segs // 2), radius=0.5)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    elif shape == "icosphere":
        bmesh.ops.create_icosphere(bm, subdivisions=min(4, max(1, segs // 4)), radius=0.5)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    elif shape == "capsule":
        bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(6, segs // 2), radius=sx * 0.5)
        half_cyl = max(0.0, (sz - sx) * 0.5)
        for v in bm.verts:
            if v.co.z > 0:
                v.co.z += half_cyl
            elif v.co.z < 0:
                v.co.z -= half_cyl
    elif shape == "torus":
        major_r, minor_r = sx * 0.38, sx * 0.12
        minor_segs = max(4, segs // 2)
        rings = []
        for i in range(segs):
            theta = 2.0 * math.pi * i / segs
            ct, st = math.cos(theta), math.sin(theta)
            ring = []
            for j in range(minor_segs):
                phi = 2.0 * math.pi * j / minor_segs
                r = major_r + minor_r * math.cos(phi)
                z = minor_r * math.sin(phi) * (sz / max(sx, 1e-5))
                ring.append(bm.verts.new((r * ct, r * st, z)))
            rings.append(ring)
        for i in range(segs):
            ni = (i + 1) % segs
            for j in range(minor_segs):
                nj = (j + 1) % minor_segs
                bm.faces.new((rings[i][j], rings[ni][j], rings[ni][nj], rings[i][nj]))
    elif shape == "blade_foil":
        levels = [
            (-sz * 0.5, sx * 0.5, sy * 0.5),
            (sz * 0.15, sx * 0.42, sy * 0.40),
            (sz * 0.38, sx * 0.25, sy * 0.22),
        ]
        rings = []
        for z_val, hw, ht in levels:
            rings.append([
                bm.verts.new((hw, 0.0, z_val)),
                bm.verts.new((0.0, ht, z_val)),
                bm.verts.new((-hw, 0.0, z_val)),
                bm.verts.new((0.0, -ht, z_val)),
            ])
        v_tip = bm.verts.new((0.0, 0.0, sz * 0.5))
        bm.faces.new((rings[0][3], rings[0][2], rings[0][1], rings[0][0]))
        for li in range(len(rings) - 1):
            for k in range(4):
                kn = (k + 1) % 4
                bm.faces.new((rings[li][k], rings[li][kn], rings[li + 1][kn], rings[li + 1][k]))
        for k in range(4):
            kn = (k + 1) % 4
            bm.faces.new((rings[2][k], rings[2][kn], v_tip))
    elif shape == "arch":
        arch_segs = max(6, segs)
        outer_r, inner_r, half_y = sx * 0.5, sx * 0.32, sy * 0.5
        p_fi, p_fo, p_bi, p_bo = [], [], [], []
        for i in range(arch_segs + 1):
            ang = math.pi * i / arch_segs
            ca, sa = math.cos(ang), math.sin(ang)
            p_fi.append(bm.verts.new((inner_r * ca, -half_y, sz * 0.2 + inner_r * sa)))
            p_fo.append(bm.verts.new((outer_r * ca, -half_y, sz * 0.2 + outer_r * sa)))
            p_bi.append(bm.verts.new((inner_r * ca, half_y, sz * 0.2 + inner_r * sa)))
            p_bo.append(bm.verts.new((outer_r * ca, half_y, sz * 0.2 + outer_r * sa)))
        for i in range(arch_segs):
            bm.faces.new((p_fi[i], p_fo[i], p_fo[i + 1], p_fi[i + 1]))
            bm.faces.new((p_bo[i], p_bi[i], p_bi[i + 1], p_bo[i + 1]))
            bm.faces.new((p_fo[i], p_bo[i], p_bo[i + 1], p_fo[i + 1]))
            bm.faces.new((p_bi[i], p_fi[i], p_fi[i + 1], p_bi[i + 1]))
    elif shape == "crystal_shard":
        ring_low, ring_mid = [], []
        for i in range(segs):
            ang = 2.0 * math.pi * i / segs
            ring_low.append(bm.verts.new((math.cos(ang) * sx * 0.35, math.sin(ang) * sy * 0.35, -sz * 0.25)))
            ring_mid.append(bm.verts.new((math.cos(ang) * sx * 0.5, math.sin(ang) * sy * 0.5, sz * 0.1)))
        v_bot = bm.verts.new((0.0, 0.0, -sz * 0.5))
        v_top = bm.verts.new((0.0, 0.0, sz * 0.5))
        for i in range(segs):
            n = (i + 1) % segs
            bm.faces.new((ring_low[n], ring_low[i], v_bot))
            bm.faces.new((ring_low[i], ring_low[n], ring_mid[n], ring_mid[i]))
            bm.faces.new((ring_mid[i], ring_mid[n], v_top))
    elif shape == "starburst_glint":
        points = max(4, int(segments))
        v_front = bm.verts.new((0.0, -sy * 0.12, 0.0))
        v_back = bm.verts.new((0.0, sy * 0.12, 0.0))
        ring = []
        for i in range(points * 2):
            ang = math.pi * i / points
            r = (sx * 0.5) if (i % 2 == 0) else (sx * 0.12)
            ring.append(bm.verts.new((math.cos(ang) * r, 0.0, math.sin(ang) * r)))
        for i in range(points * 2):
            n = (i + 1) % (points * 2)
            bm.faces.new((ring[i], ring[n], v_front))
            bm.faces.new((ring[n], ring[i], v_back))
    else:
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)

    if bevel_width > 0.0:
        bmesh.ops.bevel(
            bm, geom=list(bm.edges), offset=float(bevel_width),
            offset_type='OFFSET', segments=max(1, int(bevel_segments)),
            profile=0.5, affect='EDGES', clamp_overlap=True
        )

    if origin_at_bottom and bm.verts:
        min_z = min(v.co.z for v in bm.verts)
        bmesh.ops.translate(bm, vec=(0.0, 0.0, -min_z), verts=bm.verts)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    use_smooth = (target_mode == "film_cinematic") if smooth_shading is None else bool(smooth_shading)
    for p in mesh.polygons:
        p.use_smooth = use_smooth

    obj = bpy.data.objects.new(name, mesh)
    col = _get_or_create_collection(collection_name)
    col.objects.link(obj)

    obj.location = Vector(location)
    obj.rotation_euler = Euler([math.radians(a) for a in rotation_deg], 'XYZ')

    if parent_name:
        parent = bpy.data.objects.get(parent_name)
        if parent:
            obj.parent = parent
    if bone_name:
        vg = obj.vertex_groups.new(name=bone_name)
        vg.add(list(range(len(mesh.vertices))), 1.0, 'REPLACE')

    return {"object": obj.name, "shape": shape, "verts": len(mesh.vertices), "faces": len(mesh.polygons), "smooth": use_smooth}


mesh_create_part = kit_create_primitive


def kit_bmesh_edit(
    obj_name: str,
    operation: str = "bevel",
    selector: str = "sharp",
    indices: Optional[List[int]] = None,
    offset: float = 0.03,
    segments: int = 1,
    profile: float = 0.5,
    angle_deg: float = 30.0,
    translation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    along_normal: float = 0.0,
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    thickness: float = 0.04,
    depth: float = 0.0,
    axis: str = "Z",
    taper_factor: float = 0.0,
    twist_deg: float = 0.0,
    plane_co: Tuple[float, float, float] = (0.0, 0.0, 0.5),
    plane_no: Tuple[float, float, float] = (0.0, 0.0, 1.0),
    clear_inner: bool = False,
    clear_outer: bool = False,
    lathe_profile_pts: Optional[List[List[float]]] = None,
    lathe_steps: int = 16,
    lathe_angle_deg: float = 360.0,
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
    bm.normal_update()

    if operation == "bevel":
        edges = _select_elements_by_rule(bm, "EDGES", selector, indices, angle_deg)
        if edges:
            bmesh.ops.bevel(
                bm, geom=edges, offset=float(offset), offset_type='OFFSET',
                segments=max(1, int(segments)), profile=float(profile),
                affect='EDGES', clamp_overlap=True
            )
    elif operation == "extrude":
        faces = _select_elements_by_rule(bm, "FACES", selector, indices, angle_deg)
        if faces:
            avg_no = Vector((0.0, 0.0, 0.0))
            for f in faces:
                avg_no += f.normal
            if avg_no.length > 1e-5:
                avg_no.normalize()
            res = bmesh.ops.extrude_face_region(bm, geom=faces)
            ext_verts = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
            bmesh.ops.delete(bm, geom=faces, context='FACES_ONLY')
            move_vec = Vector(translation) + avg_no * float(along_normal)
            if move_vec.length > 1e-6:
                bmesh.ops.translate(bm, vec=move_vec, verts=ext_verts)
            if tuple(scale) != (1.0, 1.0, 1.0) and ext_verts:
                center = sum((v.co for v in ext_verts), Vector((0, 0, 0))) / len(ext_verts)
                for v in ext_verts:
                    rel = v.co - center
                    v.co = center + Vector((rel.x * scale[0], rel.y * scale[1], rel.z * scale[2]))
    elif operation == "inset":
        faces = _select_elements_by_rule(bm, "FACES", selector, indices, angle_deg)
        if faces:
            bmesh.ops.inset_region(
                bm, faces=faces, thickness=float(thickness), depth=float(depth),
                use_boundary=True, use_even_offset=True
            )
    elif operation == "subdivide_edges":
        edges = _select_elements_by_rule(bm, "EDGES", selector, indices, angle_deg)
        if edges:
            bmesh.ops.subdivide_edges(bm, edges=edges, cuts=max(1, int(segments)), use_grid_fill=True)
    elif operation == "bisect":
        geom_all = list(bm.verts) + list(bm.edges) + list(bm.faces)
        res = bmesh.ops.bisect_plane(
            bm, geom=geom_all, dist=0.0001,
            plane_co=Vector(plane_co), plane_no=Vector(plane_no),
            clear_inner=bool(clear_inner), clear_outer=bool(clear_outer)
        )
        cut_edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if cut_edges and (clear_inner or clear_outer):
            bmesh.ops.contextual_create(bm, geom=cut_edges)
    elif operation == "taper_twist":
        ax = {"X": 0, "Y": 1, "Z": 2}.get(axis.upper(), 2)
        coords = [v.co[ax] for v in bm.verts]
        c_min, c_max = (min(coords), max(coords)) if coords else (0.0, 1.0)
        span = max(1e-5, c_max - c_min)
        for v in bm.verts:
            t = (v.co[ax] - c_min) / span
            s_fac = 1.0 + float(taper_factor) * t
            ang = math.radians(float(twist_deg)) * t
            ca, sa = math.cos(ang), math.sin(ang)
            if ax == 2:
                x, y = v.co.x * s_fac, v.co.y * s_fac
                v.co.x, v.co.y = x * ca - y * sa, x * sa + y * ca
            elif ax == 1:
                x, z = v.co.x * s_fac, v.co.z * s_fac
                v.co.x, v.co.z = x * ca - z * sa, x * sa + z * ca
            else:
                y, z = v.co.y * s_fac, v.co.z * s_fac
                v.co.y, v.co.z = y * ca - z * sa, y * sa + z * ca
    elif operation == "spin_lathe":
        bm.clear()
        pts = lathe_profile_pts or [(0.0, 0.0), (0.35, 0.0), (0.45, 0.3), (0.25, 0.7), (0.32, 0.9), (0.0, 0.9)]
        steps = max(4, int(lathe_steps))
        full_circle = abs(float(lathe_angle_deg) - 360.0) < 1e-2
        ring_list = []
        for s in range(steps if full_circle else steps + 1):
            ang = math.radians(float(lathe_angle_deg)) * s / steps
            ca, sa = math.cos(ang), math.sin(ang)
            # Accept 2D (radius, z) or 3D (x, y, z) profile points; radius = first coord, height = last.
            ring_list.append([bm.verts.new((float(p[0]) * ca, float(p[0]) * sa, float(p[-1]))) for p in pts])
        rc = len(ring_list)
        for s in range(steps):
            ns = (s + 1) % rc if full_circle else s + 1
            for pi in range(len(pts) - 1):
                bm.faces.new((ring_list[s][pi], ring_list[ns][pi], ring_list[ns][pi + 1], ring_list[s][pi + 1]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    elif operation == "symmetrize":
        bmesh.ops.symmetrize(
            bm,
            input=list(bm.verts) + list(bm.edges) + list(bm.faces),
            direction=f"-{axis.upper()}" if not axis.startswith("-") else axis
        )

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return {"object": obj.name, "operation": operation, "verts": len(mesh.vertices), "faces": len(mesh.polygons)}


def kit_subd_and_loops(
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
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"error": f"Mesh object '{obj_name}' not found"}

    if action == "add_holding_loops":
        return kit_bmesh_edit(
            obj_name=obj_name,
            operation="bevel",
            selector=selector,
            indices=edge_indices,
            offset=float(offset),
            segments=2,
            profile=1.0,
            angle_deg=angle_deg,
        )

    elif action == "setup_subsurf":
        for p in obj.data.polygons:
            p.use_smooth = True
        return kit_modifier(
            obj_name=obj_name,
            action="add",
            mod_type="SUBSURF",
            mod_name="KIT_SUBSURF",
            apply_now=False,
            settings={
                "subdivision_type": "CATMULL_CLARK",
                "levels": int(subd_levels),
                "render_levels": int(render_levels),
                "use_creases": True,
                "uv_smooth": "PRESERVE_BOUNDARIES",
            },
        )

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    # Create custom-data layers BEFORE collecting edge references: adding a layer
    # reallocates BMesh element storage and invalidates previously fetched BMEdges.
    layer = None
    if action == "set_crease":
        layer = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
    elif action == "set_bevel_weight":
        layer = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    bm.edges.ensure_lookup_table()
    edges = _select_elements_by_rule(bm, "EDGES", selector, edge_indices, angle_deg)

    if action == "set_crease":
        val = max(0.0, min(1.0, float(crease_value)))
        for e in edges:
            e[layer] = val
    elif action == "set_bevel_weight":
        val = max(0.0, min(1.0, float(bevel_weight)))
        for e in edges:
            e[layer] = val
    elif action == "bridge_loops":
        if len(edges) >= 2:
            bmesh.ops.bridge_loops(bm, edges=edges)
    elif action == "grid_fill":
        if edges:
            bmesh.ops.grid_fill(bm, edges=edges)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return {"object": obj.name, "action": action, "edges_affected": len(edges), "faces": len(mesh.polygons)}


def _apply_single_modifier_depsgraph(obj, target_mod) -> int:
    vis_map = {m.name: m.show_viewport for m in obj.modifiers}
    for m in obj.modifiers:
        m.show_viewport = (m.name == target_mod.name)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    new_mesh = bpy.data.meshes.new_from_object(eval_obj)
    new_mesh.name = obj.data.name
    old_mesh = obj.data
    obj.modifiers.remove(target_mod)
    for m in obj.modifiers:
        if m.name in vis_map:
            m.show_viewport = vis_map[m.name]
    obj.data = new_mesh
    if old_mesh.users == 0:
        bpy.data.meshes.remove(old_mesh)
    return len(obj.data.polygons)


def kit_modifier(
    obj_name: str,
    action: str = "add",
    mod_type: str = "BEVEL",
    mod_name: Optional[str] = None,
    apply_now: bool = False,
    settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return {"error": f"Object '{obj_name}' not found"}

    name_use = mod_name or f"KIT_{mod_type}"
    settings = settings or {}

    if action == "add":
        mod = obj.modifiers.get(name_use) or obj.modifiers.new(name=name_use, type=mod_type)
        unknown_settings = []
        for k, v in settings.items():
            if not hasattr(mod, k):
                unknown_settings.append(k)
                continue
            prop = mod.bl_rna.properties.get(k)
            # Any Object pointer (target, object, mirror_object, offset_object, ...) accepts a name.
            if isinstance(v, str) and prop is not None and prop.type == "POINTER":
                ref = bpy.data.objects.get(v)
                if ref is None:
                    return {"error": f"Setting '{k}': object '{v}' not found"}
                v = ref
            setattr(mod, k, v)
        if apply_now:
            faces_cnt = _apply_single_modifier_depsgraph(obj, mod)
            return {"object": obj.name, "modifier": name_use, "type": mod_type, "applied": True,
                    "faces": faces_cnt, "unknown_settings": unknown_settings}
        return {"object": obj.name, "modifier": name_use, "type": mod_type, "applied": False,
                "unknown_settings": unknown_settings}

    elif action == "apply":
        mod = obj.modifiers.get(name_use)
        if not mod:
            return {"error": f"Modifier '{name_use}' not found on {obj.name}"}
        faces_cnt = _apply_single_modifier_depsgraph(obj, mod)
        return {"object": obj.name, "applied": name_use, "faces": faces_cnt}

    elif action == "remove":
        mod = obj.modifiers.get(name_use)
        if mod:
            obj.modifiers.remove(mod)
        return {"object": obj.name, "removed": name_use}

    return {"error": f"Unknown modifier action '{action}'"}


def kit_curve_tube(
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
) -> Dict[str, Any]:
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = float(bevel_depth)
    curve_data.bevel_resolution = max(0, int(bevel_resolution))
    curve_data.resolution_u = max(2, int(resolution_u))
    curve_data.use_fill_caps = True

    spline = curve_data.splines.new(type='POLY')
    spline.points.add(len(points) - 1)
    n_pts = max(1, len(points) - 1)
    for i, pt in enumerate(points):
        t = i / n_pts
        spline.points[i].co = (float(pt[0]), float(pt[1]), float(pt[2]), 1.0)
        spline.points[i].radius = float(taper_start * (1.0 - t) + taper_end * t)
    spline.use_cyclic_u = bool(cyclic)

    col = _get_or_create_collection(collection_name)
    obj = bpy.data.objects.new(name, curve_data)
    col.objects.link(obj)

    if convert_to_mesh:
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        new_mesh = bpy.data.meshes.new_from_object(eval_obj)
        new_mesh.name = f"{name}_Mesh"
        obj.name = f"{name}__curve_tmp"  # free the requested name for the mesh object
        mesh_obj = bpy.data.objects.new(name, new_mesh)
        mesh_obj.matrix_world = obj.matrix_world.copy()
        col.objects.link(mesh_obj)
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.curves.remove(curve_data)
        use_smooth = (target_mode == "film_cinematic")
        for p in mesh_obj.data.polygons:
            p.use_smooth = use_smooth
        return {"object": mesh_obj.name, "type": "MESH", "verts": len(mesh_obj.data.vertices), "faces": len(mesh_obj.data.polygons)}

    return {"object": obj.name, "type": "CURVE", "points": len(points)}


def kit_transform_and_assemble(
    obj_name: str,
    apply_location: bool = False,
    apply_rotation: bool = True,
    apply_scale: bool = True,
    set_origin: Optional[str] = None,
    join_objects: Optional[List[str]] = None,
    assign_materials: Optional[List[str]] = None,
    target_collection: Optional[str] = None,
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"error": f"Mesh object '{obj_name}' not found"}

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # 1. Join additional mesh objects in pure BMesh
    if join_objects:
        inv_target = obj.matrix_world.inverted()
        for src_name in join_objects:
            src_obj = bpy.data.objects.get(src_name)
            if not src_obj or src_obj.type != 'MESH' or src_obj == obj:
                continue
            rel_mat = inv_target @ src_obj.matrix_world
            temp_bm = bmesh.new()
            temp_bm.from_mesh(src_obj.data)
            bmesh.ops.transform(temp_bm, matrix=rel_mat, verts=temp_bm.verts)
            temp_mesh = bpy.data.meshes.new("_tmp_join")
            temp_bm.to_mesh(temp_mesh)
            temp_bm.free()
            bm.from_mesh(temp_mesh)
            bpy.data.meshes.remove(temp_mesh)
            old_src_mesh = src_obj.data
            bpy.data.objects.remove(src_obj, do_unlink=True)
            if old_src_mesh.users == 0:
                bpy.data.meshes.remove(old_src_mesh)

    # 2. Apply scale / rotation / location in pure BMesh
    loc, rot, sca = obj.matrix_world.decompose()
    mat_apply = Matrix.Identity(4)
    if apply_location:
        mat_apply = Matrix.Translation(loc) @ mat_apply
        obj.location = Vector((0.0, 0.0, 0.0))
    if apply_rotation:
        mat_apply = mat_apply @ rot.to_matrix().to_4x4()
        obj.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
    if apply_scale:
        mat_sca = Matrix.Diagonal((sca.x, sca.y, sca.z, 1.0))
        mat_apply = mat_apply @ mat_sca
        obj.scale = Vector((1.0, 1.0, 1.0))

    if mat_apply != Matrix.Identity(4):
        bmesh.ops.transform(bm, matrix=mat_apply, verts=bm.verts)

    # 3. Set origin ("BOTTOM_CENTER" | "GEOMETRY_CENTER" | "WORLD_ORIGIN")
    if set_origin and bm.verts:
        xs = [v.co.x for v in bm.verts]
        ys = [v.co.y for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        if set_origin == "BOTTOM_CENTER":
            pivot = Vector((0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), min(zs)))
            bmesh.ops.translate(bm, vec=-pivot, verts=bm.verts)
            obj.location += pivot
        elif set_origin == "GEOMETRY_CENTER":
            pivot = Vector((0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.5 * (min(zs) + max(zs))))
            bmesh.ops.translate(bm, vec=-pivot, verts=bm.verts)
            obj.location += pivot
        elif set_origin == "WORLD_ORIGIN":
            bmesh.ops.translate(bm, vec=obj.location, verts=bm.verts)
            obj.location = Vector((0.0, 0.0, 0.0))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    # 4. Bind material slots
    if assign_materials:
        mesh.materials.clear()
        for mat_name in assign_materials:
            mat = bpy.data.materials.get(mat_name)
            if mat:
                mesh.materials.append(mat)

    # 5. Move to target collection
    if target_collection:
        col = _get_or_create_collection(target_collection)
        if obj.name not in col.objects:
            for c in list(obj.users_collection):
                c.objects.unlink(obj)
            col.objects.link(obj)

    return {"object": obj.name, "verts": len(mesh.vertices), "faces": len(mesh.polygons)}
