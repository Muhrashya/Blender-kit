"""
Declarative Shader, Geometry Nodes & Compositor DAG Builder, Context-Guarded UV Unwrap,
Material Presets, and Gleam/Shimmer VFX Handlers for blender-kit v3.0.
"""
import math
from typing import Any, Dict, List, Optional, Tuple

try:
    import bpy
    import bmesh
    from mathutils import Vector
except ImportError:
    bpy = None
    bmesh = None
    Vector = None

try:
    from .session_store import atomic_context_guard
    from .modeling_subd import kit_create_primitive
except ImportError:
    from session_store import atomic_context_guard
    from modeling_subd import kit_create_primitive


_SOCKET_ALIASES = {
    "base_color": ["Base Color", "Color"],
    "subsurface": ["Subsurface Weight", "Subsurface"],
    "metallic": ["Metallic"],
    "specular": ["Specular IOR Level", "Specular"],
    "roughness": ["Roughness"],
    "transmission": ["Transmission Weight", "Transmission"],
    "coat": ["Coat Weight", "Clearcoat"],
    "emission": ["Emission Color", "Emission"],
    "emission_strength": ["Emission Strength"],
    "alpha": ["Alpha"],
    "normal": ["Normal"],
}


def _resolve_socket(sockets, name_or_alias: str):
    if name_or_alias in sockets:
        return sockets[name_or_alias]
    key = name_or_alias.strip().lower().replace(" ", "_")
    for candidate in _SOCKET_ALIASES.get(key, []):
        if candidate in sockets:
            return sockets[candidate]
    for s in sockets:
        if s.name.lower() == name_or_alias.strip().lower():
            return s
    return None


def kit_uv_unwrap(
    obj_name: str,
    method: str = "auto_seams",
    seam_angle_deg: float = 55.0,
    island_margin: float = 0.02,
    texture_size: int = 1024,
    target_density_px_per_m: float = 256.0,
    scale_to_target_density: bool = False,
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name)
    if not obj or obj.type != 'MESH':
        return {"error": f"Mesh object '{obj_name}' not found"}

    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    uv_lay = bm.loops.layers.uv.active or bm.loops.layers.uv.new("UVMap")

    seams_marked = 0
    if method == "zero_bleed_facet_atlas":
        n_faces = max(1, len(bm.faces))
        grid = max(1, math.ceil(math.sqrt(n_faces)))
        cell_size = 1.0 / grid
        pad_uv = max(6.0 / max(64, int(texture_size)), cell_size * 0.12)
        inner = max(1e-4, cell_size - 2.0 * pad_uv)
        for idx, f in enumerate(bm.faces):
            gx = idx % grid
            gy = idx // grid
            u0 = gx * cell_size + pad_uv
            v0 = gy * cell_size + pad_uv
            n_l = max(1, len(f.loops))
            for li, loop in enumerate(f.loops):
                ang = (2.0 * math.pi * li) / n_l
                loop[uv_lay].uv = (
                    u0 + inner * (0.5 + 0.45 * math.cos(ang)),
                    v0 + inner * (0.5 + 0.45 * math.sin(ang)),
                )
        bm.to_mesh(mesh)
        bm.free()
    else:
        rad = math.radians(float(seam_angle_deg))
        for e in bm.edges:
            if e.is_boundary or (len(e.link_faces) == 2 and e.calc_face_angle(0.0) >= rad):
                e.seam = True
                seams_marked += 1
        bm.to_mesh(mesh)
        bm.free()

        with atomic_context_guard(obj, mode="EDIT"):
            bpy.ops.mesh.select_all(action='SELECT')
            if method == "smart_project":
                bpy.ops.uv.smart_project(angle_limit=math.radians(float(seam_angle_deg)), island_margin=float(island_margin))
            elif method == "cube_project":
                bpy.ops.uv.cube_project(cube_size=1.0)
            elif method == "cylinder_project":
                bpy.ops.uv.cylinder_project(scale_to_bounds=True)
            elif method == "sphere_project":
                bpy.ops.uv.sphere_project(scale_to_bounds=True)
            elif method == "conformal":
                bpy.ops.uv.unwrap(method='CONFORMAL', margin=float(island_margin))
            else:
                bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=float(island_margin))
            bpy.ops.uv.pack_islands(margin=float(island_margin), rotate=True)

    # Measure UV coverage, bounds, and texel density
    bm_m = bmesh.new()
    bm_m.from_mesh(mesh)
    uv_m = bm_m.loops.layers.uv.active
    s = obj.matrix_world.to_scale()
    scale_factor = abs(s.x * s.y * s.z) ** (2.0 / 3.0) if (s.x and s.y and s.z) else 1.0
    world_area = 0.0
    uv_area = 0.0
    out_of_bounds = 0
    if uv_m is not None:
        for f in bm_m.faces:
            world_area += f.calc_area() * scale_factor
            pts = [l[uv_m].uv.copy() for l in f.loops]
            for p in pts:
                if p.x < -1e-3 or p.x > 1.001 or p.y < -1e-3 or p.y > 1.001:
                    out_of_bounds += 1
            a = 0.0
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]
                a += x1 * y2 - x2 * y1
            uv_area += abs(a) * 0.5

        measured_density = float(texture_size) * math.sqrt(uv_area / world_area) if (world_area > 0 and uv_area > 0) else 0.0
        if scale_to_target_density and measured_density > 1e-4 and target_density_px_per_m > 0:
            ratio = float(target_density_px_per_m) / measured_density
            for f in bm_m.faces:
                for l in f.loops:
                    u, v = l[uv_m].uv
                    l[uv_m].uv = (0.5 + (u - 0.5) * ratio, 0.5 + (v - 0.5) * ratio)
            bm_m.to_mesh(mesh)
            uv_area *= ratio * ratio
            measured_density = float(target_density_px_per_m)
    else:
        measured_density = 0.0
    bm_m.free()

    return {
        "object": obj.name,
        "method": method,
        "seams_marked": seams_marked,
        "uv_layer": mesh.uv_layers.active.name if mesh.uv_layers.active else "UVMap",
        "texture_size": texture_size,
        "target_density_px_per_m": target_density_px_per_m,
        "measured_texel_density_px_per_m": round(measured_density, 2),
        "uv_area_sum": round(uv_area, 4),
        "world_area_m2": round(world_area, 4),
        "out_of_bounds_uvs": out_of_bounds,
    }


def kit_material_preset(
    obj_name: Optional[str] = None,
    preset: str = "stylized_pbr",
    base_color: Tuple[float, float, float] = (0.75, 0.25, 0.22),
    secondary_color: Tuple[float, float, float] = (0.92, 0.78, 0.65),
    roughness: float = 0.65,
    metallic: float = 0.0,
    emission_strength: float = 0.0,
    material_name: Optional[str] = None,
    bake_to_texture: bool = False,
    texture_size: int = 1024,
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name) if obj_name else None
    if obj_name and (not obj or obj.type != 'MESH'):
        return {"error": f"Mesh object '{obj_name}' not found"}

    mat_name = material_name or (f"MAT_{obj.name}_{preset}" if obj else f"MAT_{preset}")
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

    _resolve_socket(bsdf.inputs, "base_color").default_value = (*cfg["col"][:3], 1.0)
    _resolve_socket(bsdf.inputs, "roughness").default_value = float(cfg["rough"])
    _resolve_socket(bsdf.inputs, "metallic").default_value = float(cfg["metal"])
    if cfg.get("emit", 0.0) > 0.0:
        em_col = _resolve_socket(bsdf.inputs, "emission")
        if em_col:
            em_col.default_value = (*cfg["col"][:3], 1.0)
        em_str = _resolve_socket(bsdf.inputs, "emission_strength")
        if em_str:
            em_str.default_value = float(cfg["emit"])

    if obj is not None:
        if not obj.data.materials:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

    return {
        "object": obj.name if obj else None,
        "material": mat.name,
        "preset": preset,
        "bake_to_texture": bake_to_texture,
        "texture_size": texture_size,
    }


def kit_add_gleam_effect(
    obj_name: Optional[str] = None,
    mode: str = "shader_sweep",
    gleam_color: Tuple[float, float, float] = (0.85, 0.98, 1.0),
    strength: float = 3.5,
    frame_start: int = 1,
    frame_end: int = 60,
    material_name: Optional[str] = None,
) -> Dict[str, Any]:
    obj = bpy.data.objects.get(obj_name) if obj_name else None
    if mode == "shader_sweep":
        if material_name:
            mat = bpy.data.materials.get(material_name) or bpy.data.materials.new(name=material_name)
            mat.use_nodes = True
        elif obj is not None:
            if not obj.data.materials:
                mat = bpy.data.materials.new(name=f"MAT_{obj.name}_Gleam")
                mat.use_nodes = True
                obj.data.materials.append(mat)
            else:
                mat = obj.data.materials[0]
                mat.use_nodes = True
        else:
            return {"error": "Either obj_name or material_name must be provided for shader_sweep"}

        nt = mat.node_tree
        bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if not bsdf:
            bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")

        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.name = "GleamSweepMapping"
        mapping.inputs["Rotation"].default_value = (0.0, math.radians(35.0), math.radians(25.0))

        sep_xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = 'EASE'
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        mid_el = ramp.color_ramp.elements.new(0.50)
        mid_el.color = (gleam_color[0], gleam_color[1], gleam_color[2], 1.0)
        ramp.color_ramp.elements[1].position = 0.58
        ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

        nt.links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], sep_xyz.inputs["Vector"])
        nt.links.new(sep_xyz.outputs["X"], ramp.inputs["Fac"])

        em_col_sock = _resolve_socket(bsdf.inputs, "emission")
        em_str_sock = _resolve_socket(bsdf.inputs, "emission_strength")
        if em_col_sock:
            nt.links.new(ramp.outputs["Color"], em_col_sock)
        if em_str_sock:
            em_str_sock.default_value = float(strength)

        mapping.inputs["Location"].default_value = (-1.2, 0.0, 0.0)
        mapping.inputs["Location"].keyframe_insert(data_path="default_value", frame=int(frame_start))
        mapping.inputs["Location"].default_value = (1.2, 0.0, 0.0)
        mapping.inputs["Location"].keyframe_insert(data_path="default_value", frame=int(frame_end))

        return {"object": obj.name if obj else None, "material": mat.name, "mode": "shader_sweep", "frames": [frame_start, frame_end]}

    elif mode == "starburst_mesh":
        base_loc = tuple(obj.location + Vector((0.0, -0.5, 0.8))) if obj else (0.0, -0.5, 0.8)
        star_prefix = obj.name if obj else (material_name or "Scene")
        res = kit_create_primitive(
            name=f"FX_{star_prefix}_GleamStar",
            shape="starburst_glint",
            location=base_loc,
            size=(0.45, 0.15, 0.45),
            segments=4,
            parent_name=obj.name if obj else None,
        )
        star_obj = bpy.data.objects.get(res["object"])
        mat = bpy.data.materials.new(name=f"MAT_{star_obj.name}")
        mat.use_nodes = True
        bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            _resolve_socket(bsdf.inputs, "base_color").default_value = (*gleam_color, 1.0)
            em_col = _resolve_socket(bsdf.inputs, "emission")
            if em_col:
                em_col.default_value = (*gleam_color, 1.0)
            em_str = _resolve_socket(bsdf.inputs, "emission_strength")
            if em_str:
                em_str.default_value = float(strength) * 1.5
        star_obj.data.materials.append(mat)

        mid_f = (int(frame_start) + int(frame_end)) // 2
        star_obj.scale = (0.01, 0.01, 0.01)
        star_obj.keyframe_insert(data_path="scale", frame=int(frame_start))
        star_obj.scale = (1.0, 1.0, 1.0)
        star_obj.rotation_euler = (0.0, math.radians(90.0), 0.0)
        star_obj.keyframe_insert(data_path="scale", frame=mid_f)
        star_obj.keyframe_insert(data_path="rotation_euler", frame=mid_f)
        star_obj.scale = (0.01, 0.01, 0.01)
        star_obj.rotation_euler = (0.0, math.radians(180.0), 0.0)
        star_obj.keyframe_insert(data_path="scale", frame=int(frame_end))
        star_obj.keyframe_insert(data_path="rotation_euler", frame=int(frame_end))
        return {"object": star_obj.name, "mode": "starburst_mesh", "frames": [frame_start, mid_f, frame_end]}

    return {"error": f"Unknown gleam mode '{mode}'"}


surface_add_gleam_effect = kit_add_gleam_effect


def _expand_macro_preset(macro: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if macro == "triplanar_pbr":
        return (
            [
                {"id": "coord", "type": "ShaderNodeTexCoord"},
                {"id": "noise", "type": "ShaderNodeTexNoise", "inputs": {"Scale": 12.0, "Detail": 6.0}},
                {"id": "ramp", "type": "ShaderNodeValToRGB"},
                {"id": "bump", "type": "ShaderNodeBump", "inputs": {"Strength": 0.15}},
                {"id": "bsdf", "type": "ShaderNodeBsdfPrincipled", "inputs": {"roughness": 0.55}},
                {"id": "out", "type": "ShaderNodeOutputMaterial"},
            ],
            [
                {"from_node": "coord", "from_socket": "Object", "to_node": "noise", "to_socket": "Vector"},
                {"from_node": "noise", "from_socket": "Fac", "to_node": "ramp", "to_socket": "Fac"},
                {"from_node": "ramp", "from_socket": "Color", "to_node": "bsdf", "to_socket": "base_color"},
                {"from_node": "noise", "from_socket": "Fac", "to_node": "bump", "to_socket": "Height"},
                {"from_node": "bump", "from_socket": "Normal", "to_node": "bsdf", "to_socket": "normal"},
                {"from_node": "bsdf", "from_socket": "BSDF", "to_node": "out", "to_socket": "Surface"},
            ],
        )
    elif macro == "edge_cavity_wear":
        return (
            [
                {"id": "geom", "type": "ShaderNodeNewGeometry"},
                {"id": "ramp", "type": "ShaderNodeValToRGB"},
                {"id": "bsdf", "type": "ShaderNodeBsdfPrincipled", "inputs": {"metallic": 0.85, "roughness": 0.35}},
                {"id": "out", "type": "ShaderNodeOutputMaterial"},
            ],
            [
                {"from_node": "geom", "from_socket": "Pointiness", "to_node": "ramp", "to_socket": "Fac"},
                {"from_node": "ramp", "from_socket": "Color", "to_node": "bsdf", "to_socket": "base_color"},
                {"from_node": "bsdf", "from_socket": "BSDF", "to_node": "out", "to_socket": "Surface"},
            ],
        )
    elif macro == "subd_micro_displacement":
        return (
            [
                {"id": "voronoi", "type": "ShaderNodeTexVoronoi", "inputs": {"Scale": 24.0}},
                {"id": "disp", "type": "ShaderNodeDisplacement", "inputs": {"Scale": 0.04}},
                {"id": "bsdf", "type": "ShaderNodeBsdfPrincipled"},
                {"id": "out", "type": "ShaderNodeOutputMaterial"},
            ],
            [
                {"from_node": "voronoi", "from_socket": "Distance", "to_node": "disp", "to_socket": "Height"},
                {"from_node": "bsdf", "from_socket": "BSDF", "to_node": "out", "to_socket": "Surface"},
                {"from_node": "disp", "from_socket": "Displacement", "to_node": "out", "to_socket": "Displacement"},
            ],
        )
    elif macro in ("gn_surface_scatter", "gn_curve_profile_sweep"):
        return (
            [
                {"id": "in", "type": "NodeGroupInput"},
                {"id": "out", "type": "NodeGroupOutput"},
            ],
            [
                {"from_node": "in", "from_socket": "Geometry", "to_node": "out", "to_socket": "Geometry"},
            ],
        )
    elif macro == "comp_cinematic_glare_grade":
        return (
            [
                {"id": "rl", "type": "CompositorNodeRLayers"},
                {"id": "glare", "type": "CompositorNodeGlare", "properties": {"glare_type": "FOG_GLOW", "quality": "HIGH"}},
                {"id": "comp", "type": "CompositorNodeComposite"},
            ],
            [
                {"from_node": "rl", "from_socket": "Image", "to_node": "glare", "to_socket": "Image"},
                {"from_node": "glare", "from_socket": "Image", "to_node": "comp", "to_socket": "Image"},
            ],
        )
    return ([], [])


def kit_node_graph_build(
    tree_type: str = "SHADER",
    target_name: str = "MAT_Default",
    nodes: Optional[List[Dict[str, Any]]] = None,
    links: Optional[List[Dict[str, Any]]] = None,
    interface_sockets: Optional[List[Dict[str, Any]]] = None,
    macro: Optional[str] = None,
    clear_existing: bool = True,
) -> Dict[str, Any]:
    ttype = tree_type.upper()
    if macro:
        m_nodes, m_links = _expand_macro_preset(macro)
        nodes = m_nodes if not nodes else nodes
        links = m_links if not links else links

    nodes = nodes or []
    links = links or []

    # 1. Resolve or create target NodeTree
    if ttype == "SHADER":
        mat = bpy.data.materials.get(target_name) or bpy.data.materials.new(name=target_name)
        mat.use_nodes = True
        nt = mat.node_tree
    elif ttype == "GEOMETRY":
        nt = bpy.data.node_groups.get(target_name) or bpy.data.node_groups.new(name=target_name, type='GeometryNodeTree')
        if hasattr(nt, "interface"):
            existing_names = {item.name for item in nt.interface.items_tree}
            if "Geometry" not in existing_names:
                nt.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
                nt.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
            for isock in (interface_sockets or []):
                nt.interface.new_socket(
                    name=isock["name"],
                    in_out=isock.get("in_out", "INPUT").upper(),
                    socket_type=isock.get("socket_type", "NodeSocketFloat"),
                )
        obj = bpy.data.objects.get(target_name)
        if obj and obj.type == 'MESH':
            mod = obj.modifiers.get("KIT_GEONODES") or obj.modifiers.new(name="KIT_GEONODES", type="NODES")
            mod.node_group = nt
    elif ttype == "COMPOSITOR":
        scene = bpy.data.scenes.get(target_name) or bpy.context.scene
        if hasattr(scene, "compositing_node_group"):
            # Blender 5.x: compositor is a CompositorNodeTree node group with an Image output.
            nt = scene.compositing_node_group
            if nt is None:
                nt = bpy.data.node_groups.new(name=f"KIT_Compositor_{scene.name}", type="CompositorNodeTree")
                scene.compositing_node_group = nt
            if not any(i.item_type == "SOCKET" and i.in_out == "OUTPUT" and i.name == "Image"
                       for i in nt.interface.items_tree):
                nt.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        else:
            scene.use_nodes = True
            nt = scene.node_tree
    else:
        return {"error": f"Unsupported tree_type '{tree_type}'"}

    if clear_existing:
        nt.nodes.clear()

    created_nodes: Dict[str, Any] = {}
    for nspec in nodes:
        nid = nspec["id"]
        ntype = nspec["type"]
        if ntype == "CompositorNodeComposite" and ttype == "COMPOSITOR" and not hasattr(bpy.types, "CompositorNodeComposite"):
            ntype = "NodeGroupOutput"  # Blender 5.x replacement for the Composite output node
        try:
            node = nt.nodes.new(ntype)
        except Exception as exc:
            return {"error": f"Invalid node type '{ntype}' in {ttype} tree: {exc}"}
        node.name = nid
        if "label" in nspec:
            node.label = str(nspec["label"])
        if "location" in nspec and len(nspec["location"]) >= 2:
            node.location = (float(nspec["location"][0]), float(nspec["location"][1]))
        for prop_k, prop_v in (nspec.get("properties") or {}).items():
            if hasattr(node, prop_k):
                setattr(node, prop_k, prop_v)
                continue
            # Blender 5.x moved many node enums to MENU input sockets (e.g. Glare 'glare_type' -> 'Type').
            sock_name = prop_k.split("_")[-1].title() if prop_k.endswith("_type") else prop_k.replace("_", " ").title()
            sock = node.inputs.get(sock_name)
            if sock is not None:
                val = prop_v.replace("_", " ").title() if (getattr(sock, "type", "") == "MENU" and isinstance(prop_v, str)) else prop_v
                try:
                    sock.default_value = val
                except (TypeError, ValueError):
                    pass
        for inp_k, inp_v in (nspec.get("inputs") or {}).items():
            sock = _resolve_socket(node.inputs, inp_k)
            if sock is None:
                valid_in = [s.name for s in node.inputs]
                return {"error": f"Unknown input socket '{inp_k}' on node '{ntype}'. Valid inputs: {valid_in}"}
            sock.default_value = inp_v
        created_nodes[nid] = node

    for lspec in links:
        fn = created_nodes.get(lspec["from_node"]) or nt.nodes.get(lspec["from_node"])
        tn = created_nodes.get(lspec["to_node"]) or nt.nodes.get(lspec["to_node"])
        if not fn or not tn:
            return {"error": f"Link references missing node: {lspec}"}
        out_sock = _resolve_socket(fn.outputs, lspec["from_socket"])
        if out_sock is None:
            return {"error": f"Unknown output socket '{lspec['from_socket']}' on '{fn.bl_idname}'. Valid: {[s.name for s in fn.outputs]}"}
        in_sock = _resolve_socket(tn.inputs, lspec["to_socket"])
        if in_sock is None:
            return {"error": f"Unknown input socket '{lspec['to_socket']}' on '{tn.bl_idname}'. Valid: {[s.name for s in tn.inputs]}"}
        nt.links.new(out_sock, in_sock)

    return {
        "tree_type": ttype,
        "target_name": target_name,
        "macro": macro,
        "nodes_created": len(created_nodes),
        "links_created": len(links),
    }
