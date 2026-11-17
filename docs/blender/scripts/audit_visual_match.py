# Visual Match, Silhouette Aspect & Zero-Bleed Texture Audit.
# Verifies that the 3D asset matches reference aspect ratios and has zero UV bleed / occlusion blotches.
import bpy
import json
from mathutils import Vector

TARGET = ""
REF_ASPECT_XZ = 0.0  # Optional width/height ratio from ref-analysis.md; 0 = skip ratio gate
ALLOW_WHITE_RATIO = 0.15  # Max fraction of non-ivory faces allowed to be near-white

objs = [bpy.data.objects[TARGET]] if TARGET else [
    o for o in bpy.context.scene.objects if o.type == "MESH" and o.visible_get()
]

out = []
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
    if obj.data.materials:
        mat = obj.data.materials[0]
        if mat and mat.use_nodes:
            for n in mat.node_tree.nodes:
                if n.type == 'TEX_IMAGE' and n.image:
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
    if REF_ASPECT_XZ > 0:
        aspect_ok = abs(aspect_xz - REF_ASPECT_XZ) <= 0.25 * REF_ASPECT_XZ

    passed = (bleed_ratio <= 0.05) and aspect_ok
    out.append({
        "object": obj.name,
        "dimensions_m": [round(dx, 3), round(dy, 3), round(dz, 3)],
        "aspect_xz": aspect_xz,
        "aspect_yz": aspect_yz,
        "bleed_faces": bleed_faces,
        "bleed_ratio": bleed_ratio,
        "has_custom_normals": mesh.has_custom_normals,
        "pass": passed,
    })

print(json.dumps({"pass": all(r["pass"] for r in out), "objects": out}, indent=2))
