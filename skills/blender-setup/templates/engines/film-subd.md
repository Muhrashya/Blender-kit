---
engine: film-subd
version: USD / Alembic / Blender 4.x-5.x
source: https://openusd.org/
verified: never
status: SEED
---
# Engine profile: film-subd (Catmull-Clark Subdivision Surface & Cinematic Render Pipeline)

Use when `target_mode: film_cinematic` is active for film, animation, broadcast, turntable renders, or high-poly SubD asset authoring.

## Import
| Item | Value | Label |
|---|---|---|
| Preferred mesh format | USD (`.usdc` / `.usda`) or native `.blend` asset | [START] |
| Other accepted formats | Alembic (`.abc`), multi-pass OpenEXR (`.exr`) | [START] |
| Import path / tool | DCC / renderer dependent | UNVERIFIED |

## Coordinates and scale
| Item | Value | Label |
|---|---|---|
| Up axis | +Z in Blender (`+Y` or `+Z` in USD stage) | [RECALLED] |
| Forward axis | -Y in Blender | [RECALLED] |
| Handedness | right-handed | [RECALLED] |
| 1 unit = | 1 meter | [RECALLED] |
| Blender export setting | `bpy.ops.wm.usd_export` or native `.blend` save | [START] |

## Limits
| Item | Value | Label |
|---|---|---|
| Max triangles per mesh | governed by control-cage quad budget in config.md | [START] |
| Max bones | unrestricted (full IK/FK + bendy-bone control rigs allowed) | [START] |
| Max bone influences per vertex | 8 | [START] |
| Max texture size | 4096 (single tile or UDIM 1001..100N) | [START] |
| Max materials per mesh | unrestricted | [START] |

## Mesh rules
| Item | Value | Label |
|---|---|---|
| Triangulate on export | False (keep 100% quad Catmull-Clark control cage) | [START] |
| Custom normals | False (use smooth normals + SubD holding loops and `crease_edge`) | [START] |
| Collision / LOD | n/a | [START] |
| Pivot | bottom-center or mechanical hinge pivot | [ASSUMED] |
| Modifiers | keep non-destructive `SUBSURF` (`levels=2, render_levels=3`) live on cage | [START] |

## Naming
Follow `config.md` prefixes (`SM_<Asset>_HP`, `MAT_<Asset>_*`, `GN_<Asset>_*`, `ARM_<Asset>`). [START]

## Rig
| Item | Value | Label |
|---|---|---|
| Skeleton type | full IK/FK control rig with pole targets and bendy bones (`bbone_segments`) | [START] |
| Bone naming | symmetric `.L` / `.R` suffixes | [START] |
| Root bone | single master root bone | [START] |
| Deform-only export | False when delivering `.blend`, True for baked USD/Alembic cache | [START] |

## Animation
| Item | Value | Label |
|---|---|---|
| Frame rate | 24 fps (film standard) or 30/60 fps per brief | [START] |
| Clip source | Blender Actions (`AN_<Asset>_*`) and NLA tracks | [START] |
| Loop flag | closed Bezier F-curves (`AUTO_CLAMPED`) for cyclic clips | [START] |
| Root motion | per shot list | [START] |

## Materials
| Item | Value | Label |
|---|---|---|
| Workflow | declarative Shader Node graphs (`kit_node_graph_build`), Principled BSDF + procedural masks/displacement | [START] |
| Channel packing | uncompressed linear EXR/PNG maps or live procedural node trees | [START] |
| Normal map | OpenGL (+Y) + procedural bump/micro-displacement | [START] |
| Color spaces | AgX / Filmic view transform; base color sRGB, data maps Non-Color | [START] |
| Vertex color | supported as shader attributes | [START] |
| Transparency | Raytraced transmission / alpha blend | [START] |

## VFX
Live Geometry Nodes (`GN_<Asset>_*`), volumetric shaders, animated gleam sweeps, and Compositor glare (`comp_cinematic_glare_grade`) are supported directly. [START]

## Camera
| Item | Value | Label |
|---|---|---|
| Camera animation import | native Blender camera + USD camera export | [START] |
| In-engine cinematic tool | Blender Camera Rig (`camera_rig.py`) + Compositor | [START] |
| FOV convention (vertical or horizontal) | focal length in mm (35mm full-frame sensor default) | [START] |
| Sensor / physical camera | 36mm x 24mm physical sensor with DOF blades | [START] |
| Depth of field | enabled on hero shots | [START] |
| Motion blur | shutter 0.5 (180-degree shutter rule) | [START] |

## Export call
```python
# bpy.ops.wm.usd_export(filepath=out_path, selected_objects_only=True, export_materials=True)
```

## Import test
1. Inspect the SubD cage in wireframe + rendered shading (`look(mode="angles", shading="rendered")`).
2. Confirm `audit_run_isolated(target_mode="film_cinematic")` passes (`ngons == 0`, `curved_surface_tris == 0`, `pole_balance % 8 == 0`).
3. Record in `assets.md`.
