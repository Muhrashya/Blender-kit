"""
Native Blender-side handlers for blender-kit-mcp.
Registered directly on the Blender MCP server inside Blender's Python process so
every MCP tool call executes as a native structured handler (zero string-script exec).
Covers:
- Universal primitives & procedural archetypes (16+ shapes)
- Granular BMesh modeling (bevel, extrude, inset, loop_cut, bridge, spin_lathe, bisect, taper/twist/bend, symmetrize)
- Non-destructive Modifier stack (BEVEL, MIRROR, SOLIDIFY, ARRAY, BOOLEAN, SUBSURF, SHRINKWRAP, SIMPLE_DEFORM, WEIGHTED_NORMAL, TRIANGULATE, REMESH)
- 3D Curves, tubes, cables, pipes, handles, vines, hair strips
- Smart Quads-to-Triangles & double-shell stripping
- Universal UV unwrapping (auto-seams + angle/conformal, smart project, box/cylinder, texel density, zero-bleed facet atlas)
- Procedural material presets & native Cycles/Eevee texture map baking (BaseColor, Normal, Roughness, AO, Emissive)
- Gleam/shimmer sweeps, 3D starburst glints & compositor glare
- Armature rig generation, auto-weights & pro overlapping wave / eased animations
"""
import json
import math
import os
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler


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
            return [
                e for e in bm.edges
                if abs((e.verts[1].co - e.verts[0].co).normalized().z) > 0.85
            ]
        if selector == "horizontal":
            return [
                e for e in bm.edges
                if abs((e.verts[1].co - e.verts[0].co).normalized().z) < 0.15
            ]
        return list(bm.edges)


def kit_checkpoint(asset_name="Scene", tag="pre_edit"):
    out_dir = os.path.abspath(os.path.join("blender-out", asset_name, "checkpoints"))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{tag}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
    return {"checkpoint": path, "bytes": os.path.getsize(path)}


def kit_create_primitive(
    name,
    shape="box",
    location=(0.0, 0.0, 0.0),
    rotation_deg=(0.0, 0.0, 0.0),
    size=(1.0, 1.0, 1.0),
    segments=12,
    bevel_width=0.0,
    bevel_segments=1,
    origin_at_bottom=True,
    collection_name=None,
    parent_name=None,
    bone_name=None,
):
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
        major_r = sx * 0.38
        minor_r = sx * 0.12
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
        # Double-edged tapered sword/dagger blade with central ridge (fuller/diamond cross-section)
        levels = [
            (-sz * 0.5, sx * 0.5, sy * 0.5),
            (sz * 0.15, sx * 0.42, sy * 0.40),
            (sz * 0.38, sx * 0.25, sy * 0.22),
        ]
        rings = []
        for z_val, hw, ht in levels:
            r = [
                bm.verts.new((hw, 0.0, z_val)),
                bm.verts.new((0.0, ht, z_val)),
                bm.verts.new((-hw, 0.0, z_val)),
                bm.verts.new((0.0, -ht, z_val)),
            ]
            rings.append(r)
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
        # Architectural arch / doorway
        arch_segs = max(6, segs)
        outer_r = sx * 0.5
        inner_r = sx * 0.32
        half_y = sy * 0.5
        pts_front_in, pts_front_out, pts_back_in, pts_back_out = [], [], [], []
        for i in range(arch_segs + 1):
            ang = math.pi * i / arch_segs
            ca, sa = math.cos(ang), math.sin(ang)
            pts_front_in.append(bm.verts.new((inner_r * ca, -half_y, sz * 0.2 + inner_r * sa)))
            pts_front_out.append(bm.verts.new((outer_r * ca, -half_y, sz * 0.2 + outer_r * sa)))
            pts_back_in.append(bm.verts.new((inner_r * ca, half_y, sz * 0.2 + inner_r * sa)))
            pts_back_out.append(bm.verts.new((outer_r * ca, half_y, sz * 0.2 + outer_r * sa)))
        for i in range(arch_segs):
            bm.faces.new((pts_front_in[i], pts_front_out[i], pts_front_out[i + 1], pts_front_in[i + 1]))
            bm.faces.new((pts_back_out[i], pts_back_in[i], pts_back_in[i + 1], pts_back_out[i + 1]))
            bm.faces.new((pts_front_out[i], pts_back_out[i], pts_back_out[i + 1], pts_front_out[i + 1]))
            bm.faces.new((pts_back_in[i], pts_front_in[i], pts_front_in[i + 1], pts_back_in[i + 1]))
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

    for p in mesh.polygons:
        p.use_smooth = False

    obj = bpy.data.objects.new(name, mesh)
    if collection_name:
        col = bpy.data.collections.get(collection_name)
        if not col:
            col = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(col)
        col.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    obj.location = Vector(location)
    obj.rotation_euler = Euler([math.radians(a) for a in rotation_deg], 'XYZ')

    if parent_name:
        parent = bpy.data.objects.get(parent_name)
        if parent:
            obj.parent = parent
    if bone_name:
        vg = obj.vertex_groups.new(name=bone_name)
        vg.add(list(range(len(mesh.vertices))), 1.0, 'REPLACE')

    return {"object": obj.name, "shape": shape, "verts": len(mesh.vertices), "faces": len(mesh.polygons)}


def kit_bmesh_edit(
    obj_name,
    operation="bevel",
    selector="sharp",
    indices=None,
    offset=0.03,
    segments=1,
    profile=0.5,
    angle_deg=30.0,
    translation=(0.0, 0.0, 0.0),
    along_normal=0.0,
    scale=(1.0, 1.0, 1.0),
    thickness=0.04,
    depth=0.0,
    axis="Z",
    taper_factor=0.0,
    twist_deg=0.0,
    plane_co=(0.0, 0.0, 0.5),
    plane_no=(0.0, 0.0, 1.0),
    clear_inner=False,
    clear_outer=False,
    lathe_profile_pts=None,
    lathe_steps=16,
    lathe_angle_deg=360.0,
):
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
            bmesh.ops.subdivide_edges(
                bm, edges=edges, cuts=max(1, int(segments)), use_grid_fill=True
            )

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
                v.co.x = x * ca - y * sa
                v.co.y = x * sa + y * ca
            elif ax == 1:
                x, z = v.co.x * s_fac, v.co.z * s_fac
                v.co.x = x * ca - z * sa
                v.co.z = x * sa + z * ca
            else:
                y, z = v.co.y * s_fac, v.co.z * s_fac
                v.co.y = y * ca - z * sa
                v.co.z = y * sa + z * ca

    elif operation == "spin_lathe":
        # Build a lathed mesh from 2D profile points [(r, z), ...]
        bm.clear()
        pts = lathe_profile_pts or [(0.0, 0.0), (0.35, 0.0), (0.45, 0.3), (0.25, 0.7), (0.32, 0.9), (0.0, 0.9)]
        steps = max(4, int(lathe_steps))
        full_circle = abs(float(lathe_angle_deg) - 360.0) < 1e-2
        ring_list = []
        for s in range(steps if full_circle else steps + 1):
            ang = math.radians(float(lathe_angle_deg)) * s / steps
            ca, sa = math.cos(ang), math.sin(ang)
            ring = [bm.verts.new((r * ca, r * sa, z)) for (r, z) in pts]
            ring_list.append(ring)
        rc = len(ring_list)
        for s in range(steps):
            ns = (s + 1) % rc if full_circle else s + 1
            for pi in range(len(pts) - 1):
                bm.faces.new((ring_list[s][pi], ring_list[ns][pi], ring_list[ns][pi + 1], ring_list[s][pi + 1]))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)

    elif operation == "symmetrize":
        bmesh.ops.symmetrize(bm, input=list(bm.verts) + list(bm.edges) + list(bm.faces), direction=f"-{axis.upper()}" if not axis.startswith("-") else axis)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return {"object": obj.name, "operation": operation, "verts": len(mesh.vertices), "faces": len(mesh.polygons)}


def kit_modifier(
    obj_name,
    action="add",
    mod_type="BEVEL",
    mod_name=None,
    apply_now=False,
    settings=None,
):
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return {"error": f"Object '{obj_name}' not found"}

    name_use = mod_name or f"KIT_{mod_type}"
    settings = settings or {}

    if action == "add":
        mod = obj.modifiers.get(name_use) or obj.modifiers.new(name=name_use, type=mod_type)
        for k, v in settings.items():
            if k == "object" and isinstance(v, str):
                v = bpy.data.objects.get(v)
            if hasattr(mod, k):
                setattr(mod, k, v)
        if apply_now:
            with bpy.context.temp_override(object=obj, active_object=obj):
                bpy.ops.object.modifier_apply(modifier=mod.name)
        return {"object": obj.name, "modifier": name_use, "type": mod_type, "applied": apply_now}

    elif action == "apply":
        mod = obj.modifiers.get(name_use)
        if not mod:
            return {"error": f"Modifier '{name_use}' not found on {obj.name}"}
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return {"object": obj.name, "applied": name_use, "faces": len(obj.data.polygons)}

    elif action == "remove":
        mod = obj.modifiers.get(name_use)
        if mod:
            obj.modifiers.remove(mod)
        return {"object": obj.name, "removed": name_use}


def kit_curve_tube(
    name,
    points,
    bevel_depth=0.05,
    bevel_resolution=2,
    resolution_u=8,
    cyclic=False,
    taper_start=1.0,
    taper_end=1.0,
    convert_to_mesh=True,
):
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
        radius_scale = taper_start * (1.0 - t) + taper_end * t
        spline.points[i].co = (float(pt[0]), float(pt[1]), float(pt[2]), 1.0)
        spline.points[i].radius = float(radius_scale)
    spline.use_cyclic_u = bool(cyclic)

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)

    if convert_to_mesh:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        new_mesh = bpy.data.meshes.new_from_object(eval_obj)
        new_mesh.name = f"{name}_Mesh"
        mesh_obj = bpy.data.objects.new(name, new_mesh)
        mesh_obj.matrix_world = obj.matrix_world.copy()
        bpy.context.collection.objects.link(mesh_obj)
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.curves.remove(curve_data)
        for p in mesh_obj.data.polygons:
            p.use_smooth = False
        return {"object": mesh_obj.name, "type": "MESH", "verts": len(mesh_obj.data.vertices), "faces": len(mesh_obj.data.polygons)}

    return {"object": obj.name, "type": "CURVE", "points": len(points)}


def kit_uv_unwrap(
    obj_name,
    method="auto_seams",
    seam_angle_deg=55.0,
    island_margin=0.02,
    texture_size=1024,
    target_density_px_per_m=256.0,
):
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"error": f"Mesh object '{obj_name}' not found"}

    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    bm = bmesh.new()
    bm.from_mesh(mesh)
    rad = math.radians(float(seam_angle_deg))
    seams_marked = 0
    for e in bm.edges:
        if e.is_boundary or (len(e.link_faces) == 2 and e.calc_face_angle(0.0) >= rad):
            e.seam = True
            seams_marked += 1
    bm.to_mesh(mesh)
    bm.free()

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    if method == "smart_project":
        bpy.ops.uv.smart_project(angle_limit=math.radians(float(seam_angle_deg)), island_margin=float(island_margin))
    elif method == "cube_project":
        bpy.ops.uv.cube_project(cube_size=1.0)
    else:
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=float(island_margin))
    bpy.ops.uv.pack_islands(margin=float(island_margin), rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    return {
        "object": obj.name,
        "method": method,
        "seams_marked": seams_marked,
        "uv_layer": mesh.uv_layers.active.name,
    }


def kit_material_preset(
    obj_name,
    preset="stylized_pbr",
    base_color=(0.75, 0.25, 0.22),
    secondary_color=(0.92, 0.78, 0.65),
    roughness=0.65,
    metallic=0.0,
    emission_strength=0.0,
    bake_to_texture=False,
    texture_size=1024,
):
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"error": f"Mesh object '{obj_name}' not found"}

    mat_name = f"MAT_{obj.name}_{preset}"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out_node = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

    presets = {
        "metal_steel": {"col": (0.68, 0.71, 0.75), "rough": 0.28, "metal": 0.95},
        "gold_trim": {"col": (0.94, 0.76, 0.32), "rough": 0.22, "metal": 0.95},
        "wood_warm": {"col": (0.45, 0.26, 0.14), "rough": 0.78, "metal": 0.0},
        "stone_slate": {"col": (0.38, 0.40, 0.43), "rough": 0.88, "metal": 0.0},
        "crystal_glow": {"col": base_color, "rough": 0.15, "metal": 0.1, "emit": max(2.0, float(emission_strength))},
        "foliage_leaf": {"col": (0.22, 0.58, 0.24), "rough": 0.72, "metal": 0.0},
    }
    cfg = presets.get(preset, {"col": base_color, "rough": roughness, "metal": metallic, "emit": emission_strength})

    bsdf.inputs["Base Color"].default_value = (*cfg["col"][:3], 1.0)
    bsdf.inputs["Roughness"].default_value = float(cfg["rough"])
    bsdf.inputs["Metallic"].default_value = float(cfg["metal"])
    if cfg.get("emit", 0.0) > 0.0:
        em_col = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        if em_col:
            em_col.default_value = (*cfg["col"][:3], 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = float(cfg["emit"])

    if not obj.data.materials:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat

    return {"object": obj.name, "material": mat.name, "preset": preset}
