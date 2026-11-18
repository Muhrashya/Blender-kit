"""
Session Vault, Datablock Lease Table, and Atomic Context Guard for blender-kit v3.0.
Resolves OS App-Data session paths keyed to scene UUID, mirrors state into
bpy.data.texts[".blender_kit_session"], seeds template config files in zero-footprint
mode, enforces 5-role swarm datablock leases, and guards unavoidable EDIT-mode calls.
"""
import contextlib
import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import bpy
except ImportError:
    bpy = None  # Allows unit testing under standard python3 with mock fixtures

LEASE_TTL_SECONDS = 300.0
_DATABLOCK_LEASES: Dict[str, Dict[str, Any]] = {}
_SESSION_TEXT_NAME = ".blender_kit_session"


def _os_appdata_root() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    return Path(base) / "blender-kit" / "sessions"


def _find_templates_dir() -> Optional[Path]:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "skills" / "blender-setup" / "templates",
        Path.cwd() / "skills" / "blender-setup" / "templates",
        Path.cwd() / ".agents" / "skills" / "blender-setup" / "templates",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def _get_or_create_scene_uuid() -> str:
    if bpy is None or not getattr(bpy, "context", None) or not getattr(bpy.context, "scene", None):
        return "headless0001"
    scene = bpy.context.scene
    uid = scene.get("kit_session_uuid")
    if not uid or not isinstance(uid, str):
        uid = uuid.uuid4().hex[:12]
        scene["kit_session_uuid"] = uid
    return str(uid)


def _current_blend_stem() -> str:
    if bpy is not None and getattr(bpy, "data", None) and getattr(bpy.data, "filepath", ""):
        return Path(bpy.data.filepath).stem or "unsaved"
    return "unsaved"


def resolve_session_dir(asset_name: Optional[str] = None, target_mode: str = "game_realtime") -> str:
    local_cfg = Path.cwd() / "docs" / "blender" / "config.md"
    if local_cfg.is_file():
        cfg_text = local_cfg.read_text(encoding="utf-8", errors="ignore")
        if "session_storage: workspace" in cfg_text:
            base = Path.cwd() / "blender-out"
            out = base / asset_name if asset_name else base
            out.mkdir(parents=True, exist_ok=True)
            return str(out.resolve())

    root = _os_appdata_root()
    root.mkdir(parents=True, exist_ok=True)
    uid = _get_or_create_scene_uuid()
    stem = _current_blend_stem()
    desired_dir = root / f"{stem}_{uid}"

    # Match existing directory by *_<uid> suffix to preserve state across save/rename/move
    if not desired_dir.exists():
        for existing in root.glob(f"*_{uid}"):
            if existing.is_dir() and existing != desired_dir:
                try:
                    existing.rename(desired_dir)
                except OSError:
                    desired_dir = existing
                break

    desired_dir.mkdir(parents=True, exist_ok=True)
    _seed_session_config(desired_dir, target_mode=target_mode)

    if asset_name:
        asset_dir = desired_dir / "assets" / asset_name
        for sub in ("audit", "screens", "checkpoints"):
            (asset_dir / sub).mkdir(parents=True, exist_ok=True)
        return str(asset_dir.resolve())

    return str(desired_dir.resolve())


def _seed_session_config(session_dir: Path, target_mode: str = "game_realtime") -> Path:
    cfg_dir = session_dir / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    tpl = _find_templates_dir()
    if tpl is None:
        return cfg_dir

    for fname in ("config.md", "ground-rules.md", "assets.md"):
        src = tpl / fname
        dst = cfg_dir / fname
        if src.is_file() and not dst.exists():
            shutil.copy2(src, dst)

    eng_dst = cfg_dir / "engine.md"
    if not eng_dst.exists():
        eng_name = "film-subd.md" if target_mode == "film_cinematic" else "generic-gltf.md"
        eng_src = tpl / "engines" / eng_name
        if not eng_src.is_file():
            eng_src = tpl / "engines" / "generic-gltf.md"
        if eng_src.is_file():
            shutil.copy2(eng_src, eng_dst)

    style_dst = cfg_dir / "style.md"
    if not style_dst.exists():
        style_name = "realistic.md" if target_mode == "film_cinematic" else "lowpoly.md"
        style_src = tpl / "styles" / style_name
        if style_src.is_file():
            shutil.copy2(style_src, style_dst)

    return cfg_dir


def mirror_state_to_blend(state_update: Dict[str, Any]) -> Dict[str, Any]:
    if bpy is None or not getattr(bpy, "data", None) or not hasattr(bpy.data, "texts"):
        return state_update
    txt = bpy.data.texts.get(_SESSION_TEXT_NAME)
    if txt is None:
        txt = bpy.data.texts.new(_SESSION_TEXT_NAME)
    txt.use_fake_user = True
    current: Dict[str, Any] = {}
    raw = getattr(txt, "as_string", lambda: "")()
    if raw:
        try:
            current = json.loads(raw)
        except json.JSONDecodeError:
            current = {}
    current.update(state_update)
    current["updated_at"] = time.time()
    payload = json.dumps(current, indent=2)
    if hasattr(txt, "clear") and hasattr(txt, "write"):
        txt.clear()
        txt.write(payload)
    return current


def restore_state_from_blend() -> Dict[str, Any]:
    if bpy is None or not getattr(bpy, "data", None) or not hasattr(bpy.data, "texts"):
        return {}
    txt = bpy.data.texts.get(_SESSION_TEXT_NAME)
    if txt is None:
        return {}
    raw = getattr(txt, "as_string", lambda: "")()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _prune_expired_leases() -> None:
    now = time.time()
    expired = [
        role for role, info in _DATABLOCK_LEASES.items()
        if now - info.get("acquired_at", 0.0) > info.get("ttl", LEASE_TTL_SECONDS)
    ]
    for role in expired:
        _DATABLOCK_LEASES.pop(role, None)


def verify_lease(command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    _prune_expired_leases()
    cmd_type = command.get("type", "")
    params = command.get("params") or {}
    agent_role = params.get("agent_role", "orchestrator")

    # The auditor is read-only at all times, not only while leases are active.
    if agent_role == "auditor":
        if cmd_type in ("kit_audit_run_isolated", "get_scene_info", "get_viewport_screenshot", "get_object_info"):
            return None
        if cmd_type == "kit_session_manage" and params.get("action", "get_state") == "get_state":
            return None
        return {
            "status": "error",
            "code": "LEASE_VIOLATION",
            "message": f"Role 'auditor' is READ_ONLY and cannot execute '{cmd_type}' "
                       f"(action={params.get('action')!r}).",
        }

    if not _DATABLOCK_LEASES:
        return None

    if cmd_type == "execute_code":
        return {
            "status": "error",
            "code": "LEASE_VIOLATION",
            "message": "Raw execute_code is blocked while Phase 1 swarm datablock leases are active.",
        }

    if agent_role == "orchestrator":
        return None

    lease_info = _DATABLOCK_LEASES.get(agent_role)
    if not lease_info:
        return {
            "status": "error",
            "code": "LEASE_VIOLATION",
            "message": f"Role '{agent_role}' holds no active datablock lease.",
        }

    prefixes: List[str] = lease_info.get("prefixes", [])
    candidates: List[str] = []
    for key in ("name", "obj_name", "target_name", "material_name", "armature_name"):
        val = params.get(key)
        if isinstance(val, str) and val:
            candidates.append(val)
    for list_key in ("join_objects", "bind_meshes"):
        val_list = params.get(list_key)
        if isinstance(val_list, list):
            for item in val_list:
                if isinstance(item, str) and item:
                    candidates.append(item)
                elif isinstance(item, dict) and item.get("mesh_name"):
                    candidates.append(str(item["mesh_name"]))

    for target in candidates:
        if not any(target.startswith(pfx) for pfx in prefixes):
            return {
                "status": "error",
                "code": "LEASE_VIOLATION",
                "message": f"Role '{agent_role}' lease {prefixes} does not permit modifying '{target}'.",
            }
    return None


@contextlib.contextmanager
def atomic_context_guard(target_obj: Any, mode: str = "EDIT", extra_selected: Optional[List[Any]] = None):
    if bpy is None or target_obj is None or not getattr(bpy, "context", None):
        yield
        return

    view_layer = bpy.context.view_layer
    prev_active_name = view_layer.objects.active.name if view_layer.objects.active else None
    prev_mode = view_layer.objects.active.mode if view_layer.objects.active else "OBJECT"
    prev_selected_names = [o.name for o in bpy.context.selected_objects]

    prev_hide_vp = getattr(target_obj, "hide_viewport", False)
    prev_hide_get = target_obj.hide_get() if hasattr(target_obj, "hide_get") else False

    try:
        if hasattr(target_obj, "hide_viewport"):
            target_obj.hide_viewport = False
        if hasattr(target_obj, "hide_set"):
            target_obj.hide_set(False)

        if view_layer.objects.active and view_layer.objects.active.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.ops.object.select_all(action="DESELECT")
        target_obj.select_set(True)
        if extra_selected:
            for extra in extra_selected:
                if extra is not None and hasattr(extra, "select_set"):
                    extra.select_set(True)
        view_layer.objects.active = target_obj

        if mode != "OBJECT":
            bpy.ops.object.mode_set(mode=mode)
        yield
    finally:
        try:
            if view_layer.objects.active and view_layer.objects.active.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            if hasattr(target_obj, "name") and target_obj.name in bpy.data.objects:
                if hasattr(target_obj, "hide_viewport"):
                    target_obj.hide_viewport = prev_hide_vp
                if hasattr(target_obj, "hide_set"):
                    target_obj.hide_set(prev_hide_get)
            for s_name in prev_selected_names:
                sobj = bpy.data.objects.get(s_name)
                if sobj and sobj.name in view_layer.objects:
                    sobj.select_set(True)
            if prev_active_name and prev_active_name in view_layer.objects:
                view_layer.objects.active = bpy.data.objects.get(prev_active_name)
                if prev_mode != "OBJECT":
                    bpy.ops.object.mode_set(mode=prev_mode)
        except Exception:
            pass


def kit_checkpoint(
    asset_name: str = "Scene",
    tag: str = "pre_edit",
    keep_last: int = 5,
    agent_role: str = "orchestrator",
) -> Dict[str, Any]:
    session_asset_dir = Path(resolve_session_dir(asset_name))
    chk_dir = session_asset_dir / "checkpoints"
    chk_dir.mkdir(parents=True, exist_ok=True)

    # During active Phase 1 specialist leases, avoid blocking main thread with full disk saves
    if _DATABLOCK_LEASES and agent_role not in ("orchestrator", ""):
        mirror_state_to_blend({"last_subagent_tag": f"{agent_role}:{tag}"})
        return {"checkpoint": "in_memory_mirror", "agent_role": agent_role, "tag": tag, "bytes": 0}

    path = chk_dir / f"{tag}.blend"
    if bpy is not None and hasattr(bpy, "ops") and hasattr(bpy.ops, "wm"):
        bpy.ops.wm.save_as_mainfile(filepath=str(path), copy=True)
    else:
        path.write_bytes(b"MOCK_BLEND_CHECKPOINT")

    # Prune oldest checkpoints beyond keep_last
    all_blends = sorted(chk_dir.glob("*.blend"), key=lambda p: p.stat().st_mtime)
    max_keep = max(1, int(keep_last))
    while len(all_blends) > max_keep:
        oldest = all_blends.pop(0)
        try:
            oldest.unlink()
        except OSError:
            pass

    mirror_state_to_blend({"last_checkpoint": str(path), "asset_name": asset_name})
    return {"checkpoint": str(path), "bytes": path.stat().st_size if path.exists() else 0}


ensure_checkpoint = kit_checkpoint


def kit_session_manage(
    action: str = "init",
    asset_name: str = "Scene",
    target_mode: str = "game_realtime",
    agent_role: str = "orchestrator",
    lease_prefixes: Optional[List[str]] = None,
    keep_last: int = 5,
) -> Dict[str, Any]:
    _prune_expired_leases()
    session_root = Path(resolve_session_dir(None, target_mode=target_mode))
    asset_dir = Path(resolve_session_dir(asset_name, target_mode=target_mode))
    cfg_dir = session_root / "config"

    if action == "init":
        state = mirror_state_to_blend({
            "session_dir": str(session_root),
            "asset_dir": str(asset_dir),
            "config_dir": str(cfg_dir),
            "target_mode": target_mode,
        })
        return {
            "action": "init",
            "session_dir": str(session_root),
            "asset_dir": str(asset_dir),
            "config_dir": str(cfg_dir),
            "target_mode": target_mode,
            "state": state,
        }

    elif action == "acquire_lease":
        prefixes = list(lease_prefixes or [])
        _DATABLOCK_LEASES[agent_role] = {
            "prefixes": prefixes,
            "acquired_at": time.time(),
            "ttl": LEASE_TTL_SECONDS,
        }
        return {"action": "acquire_lease", "agent_role": agent_role, "prefixes": prefixes, "active_leases": list(_DATABLOCK_LEASES.keys())}

    elif action == "release_lease":
        _DATABLOCK_LEASES.pop(agent_role, None)
        return {"action": "release_lease", "agent_role": agent_role, "active_leases": list(_DATABLOCK_LEASES.keys())}

    elif action == "reset_leases":
        _DATABLOCK_LEASES.clear()
        return {"action": "reset_leases", "active_leases": []}

    elif action == "prune_checkpoints":
        chk_dir = asset_dir / "checkpoints"
        removed = 0
        if chk_dir.is_dir():
            blends = sorted(chk_dir.glob("*.blend"), key=lambda p: p.stat().st_mtime)
            while len(blends) > max(1, int(keep_last)):
                old = blends.pop(0)
                try:
                    old.unlink()
                    removed += 1
                except OSError:
                    pass
        return {"action": "prune_checkpoints", "removed": removed, "keep_last": keep_last}

    elif action == "get_state":
        restored = restore_state_from_blend()
        return {
            "action": "get_state",
            "session_dir": str(session_root),
            "asset_dir": str(asset_dir),
            "config_dir": str(cfg_dir),
            "active_leases": {k: v["prefixes"] for k, v in _DATABLOCK_LEASES.items()},
            "blend_state": restored,
        }

    return {"error": f"Unknown session_manage action '{action}'"}
