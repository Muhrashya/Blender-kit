"""Headless smoke test: calls every kit_* handler inside a real Blender.
Run:  blender --background --factory-startup --python tests/blender_smoke.py
Prints one PASS/FAIL line per call and SMOKE_SUMMARY at the end. Not collected by unittest.
"""
import os, sys, json, tempfile, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mcp", "blender_kit_mcp"))
os.environ.setdefault("LOCALAPPDATA", tempfile.mkdtemp(prefix="bk_smoke_"))

import bpy
from handlers import NATIVE_HANDLER_MAP as H
from handlers import session_store

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

results = []

def run(label, fn, check=None, **kw):
    try:
        res = H[fn](**kw)
        ok = not (isinstance(res, dict) and res.get("error"))
        if ok and check:
            ok = bool(check(res))
        results.append((label, ok, res if not ok else ""))
        print(("PASS " if ok else "FAIL ") + label + ("" if ok else "  -> " + json.dumps(res, default=str)[:400]))
        return res
    except Exception as exc:
        results.append((label, False, repr(exc)))
        print("FAIL " + label + "  -> EXCEPTION " + repr(exc))
        traceback.print_exc(limit=3)
        return None

print("Blender", bpy.app.version_string)

# Session
run("session init", "kit_session_manage", action="init", asset_name="Smoke")
run("session get_state", "kit_session_manage", action="get_state", asset_name="Smoke")

# Primitives (every shape)
for shape in ["box", "cylinder", "cone", "pyramid", "sphere", "icosphere", "capsule", "torus",
              "blade_foil", "arch", "crystal_shard", "starburst_glint", "fang", "spike"]:
    run(f"primitive {shape}", "kit_create_primitive", name=f"SM_{shape}", shape=shape,
        check=lambda r, s=shape: f"SM_{s}" in bpy.data.objects)

# BMesh ops
for op, extra in [("bevel", {}), ("extrude", {"along_normal": 0.1, "selector": "top"}),
                  ("inset", {"selector": "top"}), ("subdivide_edges", {"selector": "all"}),
                  ("bisect", {}), ("taper_twist", {"taper_factor": 0.2, "twist_deg": 15}),
                  ("symmetrize", {})]:
    run(f"bmesh {op}", "kit_bmesh_edit", obj_name="SM_box", operation=op, **extra)
run("bmesh spin_lathe", "kit_bmesh_edit", obj_name="SM_cylinder", operation="spin_lathe",
    lathe_profile_pts=[[0.2, 0, 0], [0.3, 0, 0.5], [0.1, 0, 1.0]])

# SubD
run("primitive SM_Sub", "kit_create_primitive", name="SM_Sub", shape="box", target_mode="film_cinematic")
for act in ["add_holding_loops", "set_crease", "set_bevel_weight", "setup_subsurf"]:
    run(f"subd {act}", "kit_subd_and_loops", obj_name="SM_Sub", action=act)
run("subd grid_fill", "kit_subd_and_loops", obj_name="SM_cylinder", action="grid_fill", selector="boundary")

# Modifiers
run("modifier add BEVEL", "kit_modifier", obj_name="SM_sphere", action="add", mod_type="BEVEL")
run("modifier apply BEVEL", "kit_modifier", obj_name="SM_sphere", action="apply", mod_type="BEVEL",
    check=lambda r: not any(m.type == "BEVEL" for m in bpy.data.objects["SM_sphere"].modifiers))
run("modifier add+apply SHRINKWRAP", "kit_modifier", obj_name="SM_icosphere", action="add",
    mod_type="SHRINKWRAP", apply_now=True, settings={"target": "SM_sphere"})

run("curve tube", "kit_curve_tube", name="SM_Tube", points=[[0, 0, 0], [0, 1, 1], [0, 2, 0]],
    check=lambda r: "SM_Tube" in bpy.data.objects and bpy.data.objects["SM_Tube"].type == "MESH")
run("transform/assemble", "kit_transform_and_assemble", obj_name="SM_cone", set_origin="BOTTOM_CENTER")

# Topology
run("clean shells", "kit_clean_and_strip_shells", obj_name="SM_torus")
run("quads->tris", "kit_optimize_quads_to_tris", obj_name="SM_capsule")
for mode in ["game_realtime", "film_cinematic", "dual_cage"]:
    run(f"primitive SM_T_{mode}", "kit_create_primitive", name=f"SM_T_{mode}", shape="box")
    run(f"compile {mode}", "kit_compile_target", obj_name=f"SM_T_{mode}", target_mode=mode)

# UV - every method
for m in ["auto_seams", "conformal", "smart_project", "cube_project", "cylinder_project",
          "sphere_project", "zero_bleed_facet_atlas"]:
    run(f"primitive SM_UV_{m}", "kit_create_primitive", name=f"SM_UV_{m}", shape="box")
    run(f"uv {m}", "kit_uv_unwrap", obj_name=f"SM_UV_{m}", method=m,
        check=lambda r: r.get("out_of_bounds_uvs", 1) == 0 and r.get("uv_area_sum", 0) > 0)
run("uv density scale", "kit_uv_unwrap", obj_name="SM_UV_auto_seams", scale_to_target_density=True,
    texture_size=1024, target_density_px_per_m=256,
    check=lambda r: abs(r["measured_texel_density_px_per_m"] - 256) < 1)

# Materials / nodes
for p in ["stylized_pbr", "metal_steel", "crystal_glow"]:
    run(f"material {p}", "kit_material_preset", obj_name="SM_box", preset=p)
run("gleam shader_sweep", "kit_add_gleam_effect", obj_name="SM_crystal_shard", mode="shader_sweep")
run("gleam starburst_mesh", "kit_add_gleam_effect", obj_name="SM_crystal_shard", mode="starburst_mesh")
for macro, tt, target in [("triplanar_pbr", "SHADER", "MAT_Tri"), ("edge_cavity_wear", "SHADER", "MAT_Wear"),
                          ("subd_micro_displacement", "SHADER", "MAT_Disp"),
                          ("gn_surface_scatter", "GEOMETRY", "SM_arch"),
                          ("gn_curve_profile_sweep", "GEOMETRY", "SM_fang"),
                          ("comp_cinematic_glare_grade", "COMPOSITOR", "Scene")]:
    run(f"node macro {macro}", "kit_node_graph_build", tree_type=tt, target_name=target, macro=macro)

def _comp_ok(_r):
    sc = bpy.context.scene
    nt = getattr(sc, "compositing_node_group", None) or getattr(sc, "node_tree", None)
    g = nt.nodes.get("glare")
    gt = getattr(g, "glare_type", None) or g.inputs["Type"].default_value
    return len(nt.links) == 2 and str(gt).upper().replace(" ", "_") == "FOG_GLOW"
run("compositor graph wired + glare=FOG_GLOW", "kit_node_graph_build", tree_type="COMPOSITOR",
    target_name="Scene", macro="comp_cinematic_glare_grade", check=_comp_ok)
run("node custom shader", "kit_node_graph_build", tree_type="SHADER", target_name="MAT_Custom",
    nodes=[{"id": "n", "type": "ShaderNodeTexNoise"}, {"id": "b", "type": "ShaderNodeBsdfPrincipled"},
           {"id": "o", "type": "ShaderNodeOutputMaterial"}],
    links=[{"from_node": "n", "from_socket": "Color", "to_node": "b", "to_socket": "base_color"},
           {"from_node": "b", "from_socket": "BSDF", "to_node": "o", "to_socket": "Surface"}])

# Rig + anim
run("primitive SK_Arm", "kit_create_primitive", name="SK_Arm", shape="cylinder", size=[0.3, 0.3, 2.0], segments=8)
run("subdivide SK_Arm", "kit_bmesh_edit", obj_name="SK_Arm", operation="subdivide_edges", selector="vertical", segments=6)
bones = [{"name": "root", "head": [0, 0, 0], "tail": [0, 0, 0.7]},
         {"name": "mid", "head": [0, 0, 0.7], "tail": [0, 0, 1.4], "parent": "root", "use_connect": True},
         {"name": "tip", "head": [0, 0, 1.4], "tail": [0, 0, 2.0], "parent": "mid", "use_connect": True}]
for bm_mode in ["ENVELOPE_KDTREE", "RIGID_BONE", "AUTO_HEAT"]:
    run(f"rig {bm_mode}", "kit_rig_build_armature", armature_name=f"ARM_{bm_mode}", bones=bones,
        constraints=[{"bone": "tip", "type": "IK", "chain_count": 2}],
        bind_meshes=[{"mesh_name": "SK_Arm", "bind_mode": bm_mode}])
for mt in ["overlapping_wave", "floating_idle", "attack_anticipation"]:
    run(f"motion {mt}", "kit_pro_motion", armature_name="ARM_ENVELOPE_KDTREE",
        clip_name=f"AN_Arm_{mt}_loop" if mt != "attack_anticipation" else "AN_Arm_attack", motion_type=mt)

# Audits
for at in ["mesh", "topology", "uv", "visual_match", "anim", "naming", "all"]:
    run(f"audit {at}", "kit_audit_run_isolated", audit_type=at, target_objects=["SM_UV_auto_seams", "SK_Arm"],
        check=lambda r: "results" in r and r["results"])
run("audit rig", "kit_audit_run_isolated", audit_type="rig", target_objects=["SK_Arm"],
    armature_name="ARM_ENVELOPE_KDTREE")

# Checkpoint (needs a saved file path)
tmp_blend = os.path.join(tempfile.mkdtemp(), "smoke.blend")
bpy.ops.wm.save_as_mainfile(filepath=tmp_blend)
run("checkpoint", "kit_checkpoint", asset_name="Smoke", tag="smoke")

# Leases
run("lease acquire modeler", "kit_session_manage", action="acquire_lease", agent_role="modeler", lease_prefixes=["SM_"])
v1 = session_store.verify_lease({"type": "kit_bmesh_edit", "params": {"obj_name": "SK_Arm", "agent_role": "modeler"}})
v2 = session_store.verify_lease({"type": "kit_bmesh_edit", "params": {"obj_name": "SM_box", "agent_role": "modeler"}})
v3 = session_store.verify_lease({"type": "kit_bmesh_edit", "params": {"obj_name": "SM_box", "agent_role": "auditor"}})
for label, ok in [("lease blocks foreign prefix", v1 is not None), ("lease allows own prefix", v2 is None),
                  ("auditor blocked from writes", v3 is not None)]:
    results.append((label, ok, "")); print(("PASS " if ok else "FAIL ") + label)
run("lease reset", "kit_session_manage", action="reset_leases")
v4 = session_store.verify_lease({"type": "kit_bmesh_edit", "params": {"obj_name": "SM_box", "agent_role": "auditor"}})
v5 = session_store.verify_lease({"type": "kit_session_manage", "params": {"action": "reset_leases", "agent_role": "auditor"}})
v6 = session_store.verify_lease({"type": "kit_session_manage", "params": {"action": "get_state", "agent_role": "auditor"}})
for label, ok in [("auditor read-only with no leases", v4 is not None),
                  ("auditor cannot reset leases", v5 is not None),
                  ("auditor may read state", v6 is None)]:
    results.append((label, ok, "")); print(("PASS " if ok else "FAIL ") + label)

fails = [r for r in results if not r[1]]
print(f"SMOKE_SUMMARY total={len(results)} pass={len(results)-len(fails)} fail={len(fails)}")
for f in fails:
    print("  FAILED:", f[0])
