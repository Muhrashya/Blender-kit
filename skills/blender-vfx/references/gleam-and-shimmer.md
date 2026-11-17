# Gleam, Shimmer, Rim Glow & Starburst VFX Recipes

Contents: 1 gleam types | 2 shader gleam sweep | 3 3D starburst glint mesh | 4 viewport bloom & engine export

## 1. Gleam types
| Effect | Best for | Method | Engine export |
|---|---|---|---|
| Diagonal Gleam Sweep | Crystals, blades, pets, armor, coins | Animated Mapping ramp on Emission (`surface_add_gleam_effect(mode="shader_sweep")`) | Bake ramp texture + UV scroll in engine |
| 3D Starburst Glint | Weapon tips, gem peaks, rare pet aura | Low-poly 4/6-point diamond star (`surface_add_gleam_effect(mode="starburst_mesh")`) | Export mesh + scale/rotate animation clip |
| Fresnel Rim Shimmer | Ethereal guardians, shields, ghosts | Layer Weight / Fresnel -> ColorRamp -> Emission | Engine rim-lighting shader or inverted hull |

## 2. Shader gleam sweep (`surface_add_gleam_effect(mode="shader_sweep")`)
- Creates `ShaderNodeTexCoord (Generated)` -> `ShaderNodeMapping (GleamSweepMapping)` rotated `(0°, 35°, 25°)` -> `SeparateXYZ (X)` -> `ColorRamp (EASE)` with a tight highlight band (`0.42 -> 0.50 -> 0.58`) -> Principled BSDF `Emission Color` (`Emission Strength = 3.0–5.0`).
- Keyframes `Mapping.Location.X` from `-1.2` to `+1.2` across the clip frame range so a crisp light bar sweeps diagonally across the low-poly facets.

## 3. 3D starburst glint mesh (`surface_add_gleam_effect(mode="starburst_mesh")`)
- Builds a 16-triangle 4-point or 24-triangle 6-point double-sided diamond star (`shape="starburst_glint"`) parented to the hero highlight point.
- Keyframes scale `0.01 -> 1.0 -> 0.01` with a `90°–180°` roll over `20–40` frames for a snappy anime/Roblox-style glint pop.

## 4. Viewport bloom & engine export
- In Blender 4.x/5.x, enable realtime viewport compositor glare (`CompositorNodeGlare` with `FOG_GLOW` or `STREAKS`) for presentation renders (`look(shading="rendered")`).
- Before `blender-export`, keep exported materials strictly Principled BSDF + baked textures (or export the `FX_<Asset>_GleamStar` mesh animation).
