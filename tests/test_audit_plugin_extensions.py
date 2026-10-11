"""Regression coverage for the audit-driven media and crypto extensions."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.foundation.image_storage import persist_image_asset
from core.foundation.output_config import clear_session_output_base_dir, set_session_output_base_dir
from core.intel.recon_sources import build_surface_recipe_plan, load_recursive_module_reference
from core.collect.media_recon import _gps_coordinate
from plugins.crypto.hash_identifier_plugin import run as run_hash_identifier
from plugins.crypto.wallet_address_intel_plugin import run as run_wallet_identifier


class TestAuditPluginExtensions(unittest.TestCase):
    def tearDown(self) -> None:
        clear_session_output_base_dir()

    def test_image_archive_is_target_scoped_and_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            set_session_output_base_dir(directory)
            stored = persist_image_asset(
                target="../alice",
                source_url="https://example.test/a/../portrait.jpg",
                content_type="image/jpeg",
                sha256="a" * 64,
                media_bytes=b"public-image",
                metadata={"exif": {"Make": "Camera"}, "gps": {"latitude": 1.2}},
            )
            root = Path(directory).resolve() / "output"
            self.assertTrue(Path(stored["asset"]).is_file())
            self.assertTrue(Path(stored["manifest"]).is_file())
            self.assertTrue(Path(stored["exif"]).is_file())
            self.assertTrue(Path(stored["asset"]).resolve().is_relative_to(root))

    def test_builtin_recipe_fallback_keeps_surface_kit_usable(self):
        with tempfile.TemporaryDirectory() as directory:
            load_recursive_module_reference.cache_clear()
            plan = build_surface_recipe_plan(domain="example.com", recipe_name="subdomain-enum", reference_root=directory)
        self.assertEqual(plan["recipe"]["name"], "subdomain-enum")
        self.assertEqual(plan["silinosic_x_mapping"]["recon_mode"], "passive")

    def test_hash_identifier_only_classifies(self):
        payload = run_hash_identifier({"target": "alice", "attachments": ["d41d8cd98f00b204e9800998ecf8427e"]})
        self.assertEqual(payload["data"]["findings"][0]["possible_types"], "md5")
        self.assertIn("no cracking", payload["summary"])

    def test_gps_dms_conversion_respects_hemisphere(self):
        self.assertEqual(_gps_coordinate(((12, 1), (30, 1), (0, 1)), "S"), -12.5)

    def test_wallet_identifier_redacts_by_default_and_validates_bitcoin(self):
        payload = run_wallet_identifier({"target": "alice", "attachments": ["1BoatSLRHtKNngkdXEeobR76b53LETtpyT"]})
        candidate = payload["data"]["candidates"][0]
        self.assertEqual(candidate["wallet_address"], "[REDACTED]")
        self.assertEqual(candidate["checksum"], "valid")


if __name__ == "__main__":
    unittest.main()
