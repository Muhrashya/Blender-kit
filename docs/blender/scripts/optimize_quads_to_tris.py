# Smart Quads-to-Triangles & Double-Shell Optimizer.
# Set TARGET = "ObjectName" (or leave "" for all visible meshes).
import bpy
import bmesh
import json
import math
from mathutils import Vector

TARGET = ""
PLANAR_ANGLE_DEG = 2.5
JOINT_RADIUS = 0.18
STRIP_INNER_SHELLS = True

objs = [bpy.data.objects[TARGET]] if TARGET else [
    o for o in bpy.context.scene.objects if o.type == "MESH" and o.visible_get()
]

results = []
for obj in objs:
    mesh = obj.data
    orig_faces = len(mesh.polygons)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()

    stripped_shells = 0
    if STRIP_INNER_SHELLS:
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
            if 4 <= len(comp) <= 60:
                c_idx = {f.index for f in comp}
                buried = 0
                for f in comp:
                    if f.normal.length < 1e-6:
                        continue
                    loc, _, idx, _ = bvh.ray_cast(f.calc_center_median() + f.normal * 0.0006, f.normal, 0.015)
                    if loc is not None and idx not in c_idx:
                        buried += 1
                if buried >= len(comp) * 0.55:
                    del_faces.extend(comp)
                    stripped_shells += 1
        if del_faces:
            bmesh.ops.delete(bm, geom=del_faces, context='FACES')

    joint_pts = []
    if obj.parent and obj.parent.type == "ARMATURE":
        arm = obj.parent
        m = obj.matrix_world.inverted() @ arm.matrix_world
        for b in arm.data.bones:
            joint_pts.append(m @ b.head_local)

    def near_joint(co):
        return any((co - jp).length <= JOINT_RADIUS for jp in joint_pts)

    if PLANAR_ANGLE_DEG > 0:
        rad = math.radians(PLANAR_ANGLE_DEG)
        dissolve = [
            e for e in bm.edges
            if len(e.link_faces) == 2 and not e.seam
            and not near_joint(e.verts[0].co) and not near_joint(e.verts[1].co)
            and e.calc_face_angle(999.0) < rad
        ]
        if dissolve:
            bmesh.ops.dissolve_edges(bm, edges=dissolve, use_verts=True, use_face_split=False)

    bm.faces.ensure_lookup_table()
    to_tri = [f for f in bm.faces if len(f.verts) > 4 or (len(f.verts) == 4 and not near_joint(f.calc_center_median()))]
    if to_tri:
        bmesh.ops.triangulate(bm, faces=to_tri, quad_method='BEAUTY', ngon_method='BEAUTY')

    bm.to_mesh(mesh)
    bm.free()
    if "custom_normal" in mesh.attributes:
        mesh.attributes.remove(mesh.attributes["custom_normal"])
    mesh.update()

    quads = sum(1 for p in mesh.polygons if len(p.vertices) == 4)
    tris = sum(1 for p in mesh.polygons if len(p.vertices) == 3)
    ngons = sum(1 for p in mesh.polygons if len(p.vertices) > 4)
    results.append({
        "object": obj.name,
        "orig_faces": orig_faces,
        "quads_kept_at_joints": quads,
        "tris": tris,
        "ngons": ngons,
        "stripped_inner_shells": stripped_shells,
        "pass": ngons == 0,
    })

print(json.dumps({"pass": all(r["pass"] for r in results), "objects": results}, indent=2))
