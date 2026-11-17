# Variant: weapons and armor (swords, axes, bows, firearms, shields, helmets, armor)

| Topic | Rule |
|---|---|
| Blade / edge | Use `kit_create_primitive(shape="blade_foil")` or `box` + `kit_bmesh_edit(operation="taper_twist")`; keep a crisp central ridge |
| Bevels | Use `kit_bmesh_edit(operation="bevel", selector="sharp")` or `kit_modifier(mod_type="BEVEL", settings={"width": 0.015, "segments": 1})` on guard/pommel silhouettes |
| Hilts / wraps / bowstrings | Use `kit_curve_tube` or `8-12` sided cylinders; lathe pommels and barrels with `kit_bmesh_edit(operation="spin_lathe")` |
| Armor & shields | Model outer shell only or use `kit_modifier(mod_type="SOLIDIFY")` for visible rim thickness; delete hidden inner faces |
| Moving parts | Triggers, bolts, magazines, turrets, and bow limbs get separate objects or bones at their mechanical pivot |
| Gleam / VFX | Add `surface_add_gleam_effect(mode="shader_sweep")` along the blade edge and `mode="starburst_mesh"` at the tip |
| Pivot / origin | Grip center (`(0, 0, 0)` where the hand bone attaches) with blade/barrel aligned to the engine forward/up axis |
