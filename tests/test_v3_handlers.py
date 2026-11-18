"""
Unit & Integration Test Suite for blender-kit v3.0 handlers, session vault,
5-role swarm datablock leases, socket alias resolution, and addon signature filtering.
Runs under standard `python -m unittest discover -s tests -v` (with mock fixtures)
or inside headless Blender (`blender -b --factory-startup --python tests/test_v3_handlers.py`).
"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_DIR = ROOT / "mcp" / "blender_kit_mcp"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

from handlers import NATIVE_HANDLER_MAP, session_store, node_graphs  # noqa: E402
import addon  # noqa: E402
import native_handlers  # noqa: E402


class MockSocket:
    def __init__(self, name: str):
        self.name = name
        self.default_value = None


class TestV3HandlersAndSwarmLeases(unittest.TestCase):
    def setUp(self):
        session_store.kit_session_manage(action="reset_leases")

    def tearDown(self):
        session_store.kit_session_manage(action="reset_leases")

    def test_all_18_handlers_and_legacy_aliases_registered(self):
        expected_18 = {
            "kit_session_manage",
            "kit_checkpoint",
            "kit_create_primitive",
            "kit_bmesh_edit",
            "kit_subd_and_loops",
            "kit_compile_target",
            "kit_transform_and_assemble",
            "kit_modifier",
            "kit_curve_tube",
            "kit_node_graph_build",
            "kit_uv_unwrap",
            "kit_material_preset",
            "kit_add_gleam_effect",
            "kit_rig_build_armature",
            "kit_pro_motion",
            "kit_clean_and_strip_shells",
            "kit_optimize_quads_to_tris",
            "kit_audit_run_isolated",
        }
        self.assertEqual(set(NATIVE_HANDLER_MAP.keys()), expected_18)
        for alias in (
            "ensure_checkpoint",
            "mesh_create_part",
            "mesh_clean_and_strip_shells",
            "topo_optimize_quads_to_tris",
            "surface_add_gleam_effect",
            "anim_pro_motion",
        ):
            self.assertTrue(hasattr(native_handlers, alias), f"Missing legacy alias: {alias}")

    def test_zero_footprint_appdata_session_vault_and_checkpoint_pruning(self):
        with tempfile.TemporaryDirectory() as tmp_appdata, tempfile.TemporaryDirectory() as clean_workdir:
            old_cwd = os.getcwd()
            old_env = os.environ.get("LOCALAPPDATA")
            os.environ["LOCALAPPDATA"] = tmp_appdata
            os.chdir(clean_workdir)
            try:
                res = session_store.kit_session_manage(
                    action="init", asset_name="CyberKatana", target_mode="film_cinematic"
                )
                self.assertIn("session_dir", res)
                self.assertTrue(Path(res["config_dir"], "config.md").is_file())
                self.assertTrue(Path(res["config_dir"], "engine.md").is_file())
                self.assertTrue(Path(res["config_dir"], "style.md").is_file())
                # Verify zero files written to the clean working directory
                self.assertEqual(os.listdir(clean_workdir), [])

                # Create 7 checkpoints with keep_last=3 and verify rolling pruning
                for i in range(7):
                    session_store.kit_checkpoint(
                        asset_name="CyberKatana", tag=f"step_{i}", keep_last=3, agent_role="orchestrator"
                    )
                chk_dir = Path(res["asset_dir"]) / "checkpoints"
                self.assertEqual(len(list(chk_dir.glob("*.blend"))), 3)
            finally:
                os.chdir(old_cwd)
                if old_env is None:
                    os.environ.pop("LOCALAPPDATA", None)
                else:
                    os.environ["LOCALAPPDATA"] = old_env

    def test_five_role_swarm_datablock_leases_enforcement(self):
        # Single-agent / empty leases: all calls allowed
        self.assertIsNone(
            session_store.verify_lease({"type": "kit_bmesh_edit", "params": {"obj_name": "SM_Any"}})
        )

        # Acquire Phase 1 leases for modeler, material_maker, rigger_animator
        session_store.kit_session_manage(
            action="acquire_lease",
            agent_role="modeler",
            lease_prefixes=["SM_CyberKatana_Blade", "GN_CyberKatana_Blade"],
        )
        session_store.kit_session_manage(
            action="acquire_lease",
            agent_role="material_maker",
            lease_prefixes=["MAT_CyberKatana_", "T_CyberKatana_"],
        )
        session_store.kit_session_manage(
            action="acquire_lease",
            agent_role="rigger_animator",
            lease_prefixes=["ARM_CyberKatana", "AN_CyberKatana_"],
        )

        # Modeler allowed on SM_CyberKatana_Blade, rejected on MAT_CyberKatana_Steel
        self.assertIsNone(
            session_store.verify_lease({
                "type": "kit_subd_and_loops",
                "params": {"obj_name": "SM_CyberKatana_Blade", "agent_role": "modeler"},
            })
        )
        err_mod = session_store.verify_lease({
            "type": "kit_material_preset",
            "params": {"material_name": "MAT_CyberKatana_Steel", "agent_role": "modeler"},
        })
        self.assertIsNotNone(err_mod)
        self.assertEqual(err_mod["code"], "LEASE_VIOLATION")

        # Auditor allowed on kit_audit_run_isolated, rejected on write tools
        self.assertIsNone(
            session_store.verify_lease({
                "type": "kit_audit_run_isolated",
                "params": {"target_objects": ["SM_CyberKatana_Blade"], "agent_role": "auditor"},
            })
        )
        err_aud = session_store.verify_lease({
            "type": "kit_bmesh_edit",
            "params": {"obj_name": "SM_CyberKatana_Blade", "agent_role": "auditor"},
        })
        self.assertIsNotNone(err_aud)
        self.assertEqual(err_aud["code"], "LEASE_VIOLATION")

        # Raw execute_code rejected while Phase 1 leases are active
        err_exec = session_store.verify_lease({"type": "execute_code", "params": {"code": "print(1)"}})
        self.assertIsNotNone(err_exec)
        self.assertEqual(err_exec["code"], "LEASE_VIOLATION")

    def test_socket_alias_resolution_and_macro_expansion(self):
        sockets_v4 = {"Base Color": MockSocket("Base Color"), "Emission Color": MockSocket("Emission Color"), "Specular IOR Level": MockSocket("Specular IOR Level")}
        self.assertEqual(node_graphs._resolve_socket(sockets_v4, "emission").name, "Emission Color")
        self.assertEqual(node_graphs._resolve_socket(sockets_v4, "specular").name, "Specular IOR Level")

        for macro_name in (
            "triplanar_pbr",
            "edge_cavity_wear",
            "subd_micro_displacement",
            "gn_surface_scatter",
            "gn_curve_profile_sweep",
            "comp_cinematic_glare_grade",
        ):
            m_nodes, m_links = node_graphs._expand_macro_preset(macro_name)
            self.assertTrue(len(m_nodes) >= 2, f"Macro {macro_name} failed to expand nodes")
            self.assertTrue(len(m_links) >= 1, f"Macro {macro_name} failed to expand links")

    def test_addon_handler_registration_list(self):
        keys = addon.install_native_handlers_on_running_server()
        self.assertEqual(len(keys), 18)


if __name__ == "__main__":
    unittest.main()
