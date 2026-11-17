# Variant: vehicles (cars, bikes, aircraft, boats, spaceships, tanks, mechs)

| Topic | Rule |
|---|---|
| Chassis / hull | Block out one half with `kit_modifier(mod_type="MIRROR")`; use `kit_bmesh_edit(operation="extrude")` and `bevel` for fenders, cockpit, and spoilers |
| Wheels / thrusters / nozzles | Build with `kit_bmesh_edit(operation="spin_lathe")` or `kit_create_primitive(shape="cylinder")` + `inset` for rims and hubcaps |
| Windows / panels | Use `kit_bmesh_edit(operation="inset")` + shallow negative `extrude` (`along_normal=-0.02`) for windshields and doors |
| Separate articulated parts | Wheels, steering, doors, propellers, wings, and turrets must be separate objects or bone groups with pivots at their rotation axle |
| Origin & forward axis | Origin at bottom-center between the wheels (`Z = 0` on ground); forward axis per `docs/blender/engine.md` |
| Pipes / exhausts / roll cages | Use `kit_curve_tube` with `resolution_u=6..8` |
