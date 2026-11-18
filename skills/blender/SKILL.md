---
name: blender
description: Use for ANY Blender or 3D asset request (game_realtime or film_cinematic SubD) and EVERY follow-up message - props, weapons, vehicles, architecture, nature, characters, hands, creatures, VFX, gleam, retopo, rigging, animation, export. Classifies intent, runs Q1..Qn decision interviews, coordinates the 5-role swarm in an OS App-Data Session Vault, and verifies visually.
---
# /blender - router & multi-agent swarm orchestrator

## Requires
- Session Vault initialized via `session_manage(action="init")` (seeds `docs/blender/config.md`, `docs/blender/ground-rules.md`, `docs/blender/assets.md` into OS App-Data when absent in the workspace, keeping the working directory clean).
- Blender MCP connected (`blender` / `blender-kit-mcp` + `docs/blender/scripts/blender_kit_ops.py`), or SCRIPT MODE (ground-rules.md section 7).

## Inputs
`/blender <mode> "<what>" [target=game_realtime|film_cinematic|dual_cage] [swarm=auto|single|swarm] [ref=<file>] [role=<budget row>] [tris=<n>] [style=<name>] [engine=<name>] [platform=pc|mobile]`
Modes: `prop char hands env match rig anim fx cam retopo fix optimize export audit ask doctor`. No mode: classify with `references/intents.md`. Argument grammar: `references/arguments.md`.

## Steps
1. PRE-FLIGHT once per session: call `session_manage(action="init")` (or read `docs/blender/config.md`, `docs/blender/ground-rules.md`, `docs/blender/assets.md` from the resolved Session Vault). Run `docs/blender/scripts/scene_info.py`. Quote Blender version.
2. RIGOR & TARGET: read `rigor`, `ask_mode`, `target_mode`, and `swarm_mode` from `config.md` and follow ground-rules.md section 10.
2b. CLASSIFY every user message with `references/intents.md` BEFORE acting. Output one line: `INTENT: <intent> -> <skill>`.
2c. DECISION INTERVIEW (Matt Pocock Q1, Q2, Q3 style): before executing any stage with open design branches, read `references/decision-interview.md` and present a numbered `Q1, Q2, Q3` Decision List with `(Recommended)` first. Lock answers into `state.md` `Decisions` with `[USER]`.
3. SAME TOPIC as current stage: continue. DIFFERENT TOPIC: push current stage to `paused` in `state.md`, load the matching skill, answer, then print `BACK TO: <stage>`.
4. NEW ASSET: print the matching card of `docs/blender/reference/build-guide.md` as at most 5 short plan lines (diagram: `docs/blender/reference/figures/pipeline.png`), then write `brief.md` from `docs/blender/templates/brief.md` and `state.md` from `docs/blender/templates/state.md` inside the resolved Session Vault (`<session_dir>/assets/<asset>/`), with the chain from `references/routes.md`.
5. RUN STAGE OR 5-ROLE SWARM (`references/swarm-protocol.md`):
   - **Single-Agent Mode:** load the active stage skill, execute context-free native MCP tools (`blender-kit-mcp` / `docs/blender/scripts/blender_kit_ops.py`), inspect via `look`, and run `audit_run_isolated` (`docs/blender/scripts/audit_visual_match.py`).
   - **Swarm Mode (`swarm=swarm` or multi-part asset):** execute Phase 1 (acquire datablock leases via `session_manage` and run Modeler, Material Maker, and Rigger/Animator in parallel on `SM_*`, `MAT_*`, `ARM_*`) followed by Phase 2 (reset leases, assemble/bind via `mesh_transform_and_assemble`, `mesh_compile_target`, `rig_build_armature`, and verify via the read-only Isolated Auditor).
6. REPORT with the Stage report format below. Update `state.md` and `assets.md`.
7. INVALIDATE: when a stage changed the mesh/rig/UV, mark every later stage STALE using `references/routes.md`.
8. GATE: PASS -> next stage in chain. FAIL -> follow that skill's On fail table. Never skip a failed stage.

## Stage report format (no other prose)
```
STAGE: <skill> | ASSET: <name> | TARGET: <game_realtime|film_cinematic|dual_cage>
RESULT: PASS | FAIL
NUMBERS: <key>=<value> [MEASURED] ...
SCREENS: <file names or none>
VISUAL MATCH: <comparison vs reference / silhouette / UV bleed check>
OPEN ASSUMPTIONS: <list or none>
NEXT: <skill or Q1..Qn decision list>
```

## Hard rules
| Rule | Detail |
|---|---|
| No fluff | No greeting, praise, recap or explanation of what you are about to do. Report format only |
| Zero workspace pollution | Unless `./docs/blender/config.md` sets `session_storage: workspace`, keep all checkpoints, audits, and state inside the OS App-Data Session Vault |
| Decision list first | Before any stage with open design branches, ask `Q1, Q2, Q3` per `references/decision-interview.md` with `(Recommended)` first |
| Context-free native MCP | Use native MCP handlers (`blender_kit_ops.py` / `blender-kit-mcp`) with explicit object/datablock names; never rely on `bpy.context.selected_objects` |
| Visual & isolated audit | Every visual stage must inspect via `look` and run `audit_run_isolated` (`docs/blender/scripts/audit_visual_match.py`) |
| Evidence | Every number in a report is [MEASURED] from an audit of this session |
| No export without SHIP | blender-export requires a PASS from blender-qa for the same asset version |

## Done when
state.md `status` = SHIP and blender-export produced a verified file, or the user ends the task.

## On fail
| Situation | Action |
|---|---|
| Session Vault uninitialized | run `session_manage(action="init")` (or `blender-setup init` if workspace mode requested) |
| MCP not connected | script mode; show `docs/blender/` mcp-setup note via blender-setup |
| Lease violation in Swarm Mode | check `PartSpec` prefix ownership in `references/swarm-protocol.md` or call `session_manage(action="reset_leases")` at Phase 2 barrier |
| Audit or visual match fails | print the defect, dispatch surgical repair (`blender_kit_ops.py`), re-verify with `look` |
| User asks to skip an audit | refuse; offer to run it |

## Next
The next stage in `references/routes.md` for the asset mode, or the stage popped from `paused`.
