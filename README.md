# Blender-kit

Universal agent skills and bundled **Native Creation & Editing MCP** for Blender 3D game asset pipelines: interactive `Q1..Qn` decision interviews, hybrid Image-to-3D & native BMesh modeling (bevels, extrudes, insets, lathes, curves, modifiers), smart quads-to-triangles topology optimization, double-shell stripping, auto-seam UV unwrapping, zero-bleed per-facet palette atlases, PBR material presets, gleam/shimmer VFX, rigging, pro overlapping-wave animation, cinematic cameras, and closed-loop AI vision verification (`look`).

Contains **21 specialized skills** and **9 universal object archetypes** coordinated through a single router command: `/blender`.

- **Supported Engines:** `generic-gltf`, `roblox`, `unity`, `unreal`, `godot`, `web-three`
- **Supported Art Styles:** `voxel`, `lowpoly`, `stylized`, `realistic`
- **Supported Archetypes:** Props, Hard-Surface/Sci-Fi, Weapons & Armor, Vehicles & Mechs, Architecture & Interiors, Modular Environment Kits, Nature/Foliage/Rocks/Crystals, Characters & Hands, Creatures & Pets

---

## Key Capabilities (v2.0)

1. **Bundled Native Creation & Editing MCP (`mcp/blender_kit_mcp/`)**:
   Executes structured modeling, BMesh editing (`bevel`, `extrude`, `inset`, `subdivide_edges`, `bisect`, `taper_twist`, `spin_lathe`, `symmetrize`), non-destructive modifiers, 3D curves/tubes, UV unwrapping, gleam shaders, and pro animations **natively inside Blender via JSON RPC handlers** — without generating fragile raw Python scripts on every call.
2. **Matt Pocock-Style Decision List Protocol (`Q1, Q2, Q3...`)**:
   Before executing any stage with open design choices, `/blender` inspects the live scene and reference images first, then presents a concise numbered `Q1, Q2, Q3` decision list with `(Recommended)` defaults and locks your answers into `state.md`.
3. **Hybrid Image-to-3D & Closed-Loop AI Vision Verification**:
   Supports both direct procedural BMesh construction from reference images and AI Image-to-3D generation (`generate_3d` via Meshy/Tripo/Hyper3D/Hunyuan3D) followed by automatic double-shell stripping (`mesh_clean_and_strip_shells`), surgical appendage repair, and mandatory multi-angle + wireframe `look` comparisons (`audit_visual_match.py`).
4. **Smart Quads-to-Triangles & Zero-Bleed Texture Atlases**:
   Preserves 3-ring quad loops around deforming joints, dissolves flat coplanar interior edges, beauty-triangulates static facets (`optimize_quads_to_tris.py`), and packs zero-bleed per-facet UV cells (`bleed_faces == 0`).
5. **Gleam/Shimmer VFX & Pro Overlapping Animation Engine**:
   Authors animated diagonal emission gleam sweeps, 3D diamond starburst glints (`surface_add_gleam_effect`), and phase-shifted overlapping sine-wave / floating-idle animations (`anim_pro_motion`) verified via frame strips (`look(mode="frames")`).

---

## Installation

A complete installation consists of four steps: system prerequisites, skill installation, Blender addon setup, and MCP server registration.

### 1. Prerequisites

- **Blender 4.x or 5.x** installed and accessible.
- **Node.js (v18+)** for running `npx` and skill validation.
- **Python tool runner `uv`**:
  - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows (PowerShell): `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### 2. Install Skills

Install the skill package into your coding agent:

| Environment | Command |
|---|---|
| Project directory (default) | `npx skills@latest add Muhrashya/blender-kit` |
| Global install | `npx skills@latest add Muhrashya/blender-kit -g` |
| Specific agent only | `npx skills@latest add Muhrashya/blender-kit -a claude-code` (or `cursor`, `codex`, `antigravity`) |
| Select skills only | `npx skills@latest add Muhrashya/blender-kit --skill blender --skill blender-setup --skill blender-topology` |
| Local repository copy | `npx skills add ./blender-kit` |
| Claude Code plugin | `/plugin marketplace add Muhrashya/blender-kit` |
| ChatGPT / Web LLM | Run `npm run bundle:chatgpt`, then use `dist/chatgpt-instructions.md` and `dist/chatgpt-knowledge.md` |

### 3. Blender Addon Setup

1. In Blender, go to **Edit > Preferences > Add-ons > Install** and enable the **MCP for Blender** addon (port `9876`) and/or `mcp/blender_kit_mcp/addon.py`.
2. In the 3D Viewport sidebar (press `N`), open the **MCP for Blender** tab and click **Connect / Start Server**.
3. `blender-kit-mcp` automatically registers its native `kit_*` handlers onto the running Blender server on first connection.

### 4. Register MCP Servers in Your Agent

Register both the core `blender` bridge (for `look` viewport vision and `generate_3d`) and the bundled `blender-kit` native creation server:

- **Claude Code**:
  ```bash
  claude mcp add blender -- uvx blender-mcp
  claude mcp add blender-kit -- uv run --directory ./mcp/blender_kit_mcp blender-kit-mcp
  ```

- **Cursor** (`.cursor/mcp.json`) / **Claude Desktop** (`claude_desktop_config.json`):
  ```json
  {
    "mcpServers": {
      "blender": {
        "command": "uvx",
        "args": ["blender-mcp"]
      },
      "blender-kit": {
        "command": "uv",
        "args": ["run", "--directory", "./mcp/blender_kit_mcp", "blender-kit-mcp"]
      }
    }
  }
  ```

- **Codex** (`~/.codex/config.toml`):
  ```toml
  [mcp_servers.blender]
  command = "uvx"
  args = ["blender-mcp"]

  [mcp_servers.blender_kit]
  command = "uv"
  args = ["run", "--directory", "./mcp/blender_kit_mcp", "blender-kit-mcp"]
  ```

- **Antigravity**:
  Configure `blender` (`uvx blender-mcp`) and `blender-kit` (`uv run --directory <path>/mcp/blender_kit_mcp blender-kit-mcp`).

> **Note for Windows users:** If `uvx` or `uv` is not directly resolved by your agent shell, wrap the command with `cmd` and `["/c", "uvx", "blender-mcp"]`. If no MCP server is connected, skills automatically fall back to offline Script Mode.

---

## Native MCP Tools (`mcp/blender_kit_mcp/`)

| Tool | Native Blender Capability |
|---|---|
| `workflow_checkpoint` | Saves a non-destructive `.blend` checkpoint before creating or editing geometry. |
| `mesh_create_primitive` | Creates parametric parts (`box`, `cylinder`, `cone`, `pyramid`, `sphere`, `icosphere`, `capsule`, `torus`, `blade_foil`, `arch`, `crystal_shard`, `starburst_glint`, `fang`, `spike`) with native bevels, bottom-center origins, and bone vertex groups. |
| `mesh_bmesh_edit` | Runs native BMesh modeling operations: `bevel` (`all`, `sharp`, `top`, `bottom`, `vertical`, `horizontal`, or indices), `extrude` (along normal/vector + scale), `inset`, `subdivide_edges` (loop cuts), `bisect` (planar cut + fill), `taper_twist` (progressive taper/twist along X/Y/Z), `spin_lathe` (360° lathe for bottles, vases, wheels, pillars, barrels), and `symmetrize`. |
| `mesh_modifier` | Adds, configures, applies, or removes non-destructive modifiers: `BEVEL`, `MIRROR`, `SOLIDIFY`, `ARRAY`, `BOOLEAN`, `SUBSURF`, `SHRINKWRAP`, `SIMPLE_DEFORM`, `WEIGHTED_NORMAL`, `WIREFRAME`, `DECIMATE`, `REMESH`, `TRIANGULATE`. |
| `curve_create_tube` | Builds 3D spline tubes, cables, pipes, sword hilts, horns, tree trunks/vines, or stylized hair strips with start-to-end radius taper and mesh conversion. |
| `mesh_clean_and_strip_shells` | Welds open seams (`0.5mm`), raycasts along face normals to strip hidden inner duplicate AI shells, deletes degenerate faces, and clears corrupted custom split normals. |
| `topo_optimize_quads_to_tris` | Preserves 3-ring quad loops around deforming joints, dissolves flat coplanar interior edges, and beauty-triangulates static facets. |
| `uv_unwrap_and_pack` | Automatically marks seams by angle threshold + boundaries, unwraps (`auto_seams`, `smart_project`, `cube_project`), and packs UV islands into `0–1` space. |
| `material_apply_preset` | Builds export-ready Principled BSDF materials (`metal_steel`, `gold_trim`, `wood_warm`, `stone_slate`, `crystal_glow`, `foliage_leaf`, `stylized_pbr`). |
| `surface_add_gleam_effect` | Adds an animated diagonal emission sweep (`shader_sweep`) or a 3D low-poly diamond glint flare (`starburst_mesh`). |
| `anim_pro_motion` | Authors phase-offset `overlapping_wave` and `floating_idle` animations across bone chains with closed cyclic loops. |

---

## How to Use

### Standard Workflow

1. **Initialize Project (`/blender-setup`)**:
   Creates `docs/blender/`, configures your target engine profile, art style, decision interview mode (`ask_mode`), and verifies the Blender MCP connection.
2. **Decision List Interview (`Q1, Q2, Q3...`)**:
   When you invoke `/blender`, the router classifies your request, inspects any reference images or scene objects, and presents a numbered `Q1..Qn` decision list with `(Recommended)` defaults before executing stages with design choices.
3. **Create, Edit & Visually Verify (`/blender <mode>`)**:
   Each stage uses native MCP tools, captures multi-angle shaded + wireframe + animation frame strips via `look`, and runs automated audits (`audit_mesh.py`, `audit_topology.py`, `optimize_quads_to_tris.py`, `audit_visual_match.py`, `audit_uv.py`, `audit_rig.py`, `audit_anim.py`).
4. **QA & Export (`/blender qa` and `/blender export`)**:
   Verifies geometry, topology, zero UV bleed (`bleed_faces == 0`), visual match against reference images, and engine limits to grant a `SHIP` verdict before exporting to FBX or glTF/GLB.

### Common Commands

| Target / Task | Example Command |
|---|---|
| Initialize project | `/blender-setup` |
| Create any asset from reference image | `/blender match "CrimsonSandworm" ref=sandworm.png role=creature style=lowpoly` |
| Weapon or armor with gleam | `/blender prop "EmeraldSword" ref=sword.png role=prop-hero style=stylized` |
| Vehicle with wheel pivots | `/blender prop "DesertBuggy" role=prop-hero style=lowpoly` |
| Building / interior piece | `/blender env "StoneArchway" role=env-structure style=stylized` |
| Nature / crystals / foliage | `/blender prop "CrystalCluster" role=prop-mid style=lowpoly` |
| Animated character | `/blender char "EmeraldGuardian" role=char-hero rig anim=idle,attack` |
| Character hands / gloves | `/blender hands "GuardianHands" style=stylized` |
| Repair AI mesh / strip double shells | `/blender fix` |
| Optimize quads to triangles | `/blender optimize` |
| Gleam / slash / burst VFX | `/blender fx "GleamSweep" fx=stylized` |
| Cinematic camera sequence | `/blender cam "HeroReveal" shots=3` |
| Quality & visual match audit | `/blender qa` |
| Game engine export | `/blender export` |

---

## Skills Reference

The 21 skills are organized into 7 architectural layers:

### 1. Intelligence & Routing
| Skill | Trigger / Command | Description |
|---|---|---|
| `blender` | `/blender` | Master router, `Q1..Qn` decision interviewer, and state manager across all 21 skills. |
| `blender-setup` | `/blender-setup` | Initializes workspace configuration, engine limits, art style rules, and MCP connection. |
| `blender-diagnose` | `/blender diagnose` | Diagnoses shading artifacts, flipped normals, UV bleed, rig tearing, and 3D concepts. |

### 2. Geometry & Topology
| Skill | Trigger / Command | Description |
|---|---|---|
| `blender-ref` | `/blender ref` | Measures reference images (aspect ratios, silhouette bounds, RGB quantiles) and asks `Q1..Q3` creation decisions. |
| `blender-model` | `/blender model` | Universal native modeling across 9 archetypes (`prop`, `hard-surface`, `weapons-armor`, `vehicles`, `architecture-interior`, `env-kit`, `nature-foliage`, `character`, `creature`) + AI vision compare loop. |
| `blender-topology` | `/blender topology` | Enforces quad rings at joints, strips hidden double shells, and optimizes static quads to triangles (`optimize_quads_to_tris.py`). |
| `blender-topology-fix` | `/blender fix` | Repairs ngons, non-planar quads, joint poles, double shells, and asymmetrical density. |
| `blender-retopo` | `/blender retopo` | Converts high-poly sculpts, scans, or raw AI meshes into clean game-ready models. |
| `blender-hands` | `/blender hands` | Builds anatomical or stylized hands, fingers, gloves, and claws with joint loops. |

### 3. Surface, UVs & Materials
| Skill | Trigger / Command | Description |
|---|---|---|
| `blender-uv-bake` | `/blender uv` | Auto-marks seams, unwraps and packs UV islands, equalizes texel density, builds zero-bleed facet atlases, and bakes maps. |
| `blender-material` | `/blender material` | Authors export-compliant Principled BSDF materials, zero-bleed palette atlases, and animated gleam sweeps. |

### 4. Motion (Rigging & Pro Animation)
| Skill | Trigger / Command | Description |
|---|---|---|
| `blender-rig` | `/blender rig` | Generates armatures, bone hierarchies, clean skin weights, and deform-only export skeletons. |
| `blender-animate` | `/blender anim` | Authors pro animations with phase-offset overlapping waves, floating idles, anticipation/overshoot easing, and `look(mode="frames")` verification. |

### 5. Visual Effects & Gleam
| Skill | Trigger / Command | Description |
|---|---|---|
| `blender-vfx` | `/blender fx` | Master VFX orchestrator for gleam sweeps, 3D starburst glints, slashes, beams, shockwaves, and explosions. |
| `blender-vfx-mesh` | `vfx-mesh` | Generates mesh-based effects (slashes, cones, shockwaves, shields, starbursts) with scrolling UVs. |
| `blender-vfx-flipbook` | `vfx-flipbook` | Renders simulation sequences and bursts into power-of-two transparent sprite sheets. |
| `blender-vfx-texture` | `vfx-texture` | Bakes channel-packed mask textures, gradient ramps, noise fields, and dissolve patterns. |
| `blender-vfx-sim` | `vfx-sim` | Simulates smoke, fire, fluids, and rigid-body fractures, baking output to engine-ready assets. |

### 6. Cinematics
| Skill | Trigger / Command | Description |
|---|---|---|
| `blender-camera` | `/blender cam` | Creates shot lists, turntables, hero reveals, and animated camera rigs. |

### 7. Delivery & Visual QA
| Skill | Trigger / Command | Description |
|---|---|---|
| `blender-qa` | `/blender qa` | Runs all geometry, topology, UV bleed, visual reference match (`audit_visual_match.py`), rig, and animation audits for a `SHIP` or `NO-SHIP` verdict. |
| `blender-export` | `/blender export` | Packages `SHIP`-verified assets into FBX or glTF/GLB files with applied modifiers, transforms, and packed textures. |

---

## Configuration, Decision Interviews & Rigor

Pipeline behavior is configured via `docs/blender/config.md`:

- **Decision Interview Mode (`ask_mode`)**:
  - `stage_decisions` *(default)*: Presents a Matt Pocock-style `Q1, Q2, Q3` decision list with `(Recommended)` defaults before every stage that has unresolved design choices.
  - `every_call`: Asks before every single Blender stage call.
  - `upfront_grill`: Runs a complete upfront decision interview before chaining stages.
- **Creation Mode (`creation_mode`)**:
  - `hybrid` *(default)*: Combines native procedural BMesh/Modifier modeling with optional AI Image-to-3D generation + surgical cleanup.
  - `procedural`: Pure native BMesh, curve, and modifier modeling inside Blender.
  - `ai_retopo`: AI Image-to-3D generation followed by automated shell stripping, retopo, and UV/palette repair.
- **Rigor Levels (`rigor`)**:
  - `strict`: Executes one pipeline stage per turn, requiring approval before proceeding.
  - `balanced`: Chains sequential stages that pass gate audits and have no unresolved stage decisions.
  - `flex`: Chains execution continuously until an audit check fails.

---

## Development & Validation

Run development tasks via npm:

```bash
npm run validate         # Lint all 21 skill definition files and cross-references
npm run check            # Lint skills and compile all Python audit & MCP scripts
npm run bundle:chatgpt   # Build bundled documentation files for ChatGPT
npm run figures          # Regenerate architectural and visual guide figures
```

## License

MIT
