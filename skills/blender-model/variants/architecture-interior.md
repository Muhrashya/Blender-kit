# Variant: architecture and interior (buildings, rooms, roofs, arches, stairs, furniture)

| Topic | Rule |
|---|---|
| Walls & openings | Extrude wall footprints (`kit_bmesh_edit(operation="extrude")`); cut doors/windows with `subdivide_edges` + `inset` or `kit_modifier(mod_type="BOOLEAN")` followed by quad cleanup |
| Arches, pillars & domes | Use `kit_create_primitive(shape="arch")` for doorways/vaults and `kit_bmesh_edit(operation="spin_lathe")` for columns, balusters, lamps, and vases |
| Stairs, fences & roof tiles | Build 1 unit module and repeat with `kit_modifier(mod_type="ARRAY")` |
| Furniture & cushions | Use `kit_create_primitive(shape="box", bevel_width=0.03, bevel_segments=1)` for cushions, tables, and cabinets |
| Grid & snap | Keep wall thicknesses (`0.15m–0.30m`), door heights (`2.1m–2.4m`), and story heights (`3.0m–4.0m`) on clean metric increments |
| Hidden faces | Delete bottom faces resting on the floor and interior faces between joined beams |
