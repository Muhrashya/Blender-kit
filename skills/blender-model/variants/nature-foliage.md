# Variant: nature, foliage, rocks and crystals (trees, plants, cliffs, crystals, terrain)

| Topic | Rule |
|---|---|
| Trunks, branches & vines | Use `kit_curve_tube` with `taper_start=1.0, taper_end=0.25` and `convert_to_mesh=True` for organic branching |
| Stylized / low-poly canopies | Cluster 3–7 faceted `kit_create_primitive(shape="icosphere", segments=6)` or `crystal_shard` blobs with slight scale/rotation variation |
| Rocks, boulders & cliffs | Start from `icosphere` or `box`, slice planar facets with `kit_bmesh_edit(operation="bisect", clear_outer=True)`, and bevel sharp ridges |
| Crystals & geodes | Cluster `kit_create_primitive(shape="crystal_shard")` angled outward from a rock base; apply `material_apply_preset(preset="crystal_glow")` + `surface_add_gleam_effect` |
| Origin | Base center slightly below the root/bottom (`-0.02m`) so placement on uneven terrain never floats |
