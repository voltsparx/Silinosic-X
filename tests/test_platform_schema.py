# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: Proprietary
#
# Silinosic-X Intelligence Framework
# Copyright (c) 2026 voltsparx
#
# Author     : voltsparx
# Repository : https://github.com/voltsparx/Silinosic-X
# Contact    : voltsparx@gmail.com
# License    : See LICENSE file in the project root 
#
# This file is part of Silinosic-X and is subject to the terms
# and conditions defined in the LICENSE file.
# ──────────────────────────────────────────────────────────────

import json
import os
import shutil
import unittest

from core.collect.platform_schema import PlatformValidationError, load_default_platform_keys, load_platforms


class TestPlatformSchema(unittest.TestCase):
    def test_repo_platform_manifest_loads(self):
        platforms = load_platforms("platforms")
        self.assertGreater(len(platforms), 0)
        self.assertTrue(all(platform.url for platform in platforms))
        names = {platform.name for platform in platforms}
        expected_new = {
            "HackerRank",
            "Codepen",
            "Replit",
            "Keybase",
            "Unsplash",
            "Vimeo",
            "Quora",
            "ProductHunt",
            "BuyMeACoffee",
            "Steam",
            "Mastodon",
            "Threads",
            "DeviantArt",
        }
        self.assertTrue(expected_new.issubset(names))

    def test_invalid_manifest_rejected(self):
        temp_root = os.path.join(os.getcwd(), ".tmp-tests")
        os.makedirs(temp_root, exist_ok=True)
        temp_dir = os.path.join(temp_root, "platform-schema-invalid")
        shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir, exist_ok=True)

        try:
            bad_file = os.path.join(temp_dir, "bad.json")
            with open(bad_file, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "name": "BrokenPlatform",
                        "url": "https://example.com/profile",  # Missing {username}
                    },
                    handle,
                )

            with self.assertRaises(PlatformValidationError):
                load_platforms(temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_array_manifest_payload_supported(self):
        temp_root = os.path.join(os.getcwd(), ".tmp-tests")
        os.makedirs(temp_root, exist_ok=True)
        temp_dir = os.path.join(temp_root, "platform-schema-array")
        shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir, exist_ok=True)

        try:
            manifest_file = os.path.join(temp_dir, "batch.json")
            with open(manifest_file, "w", encoding="utf-8") as handle:
                json.dump(
                    [
                        {"name": "GitHub", "url": "https://github.com/{}", "errorType": "status_code", "errorCode": 404},
                        {"name": "CustomSite", "url": "https://custom.example/{}", "errorType": "status_code", "errorCode": 404},
                    ],
                    handle,
                )

            platforms = load_platforms(temp_dir)
            self.assertEqual(len(platforms), 2)
            self.assertTrue(all("{username}" in platform.url for platform in platforms))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_default_quickrange_keys_load(self):
        keys = load_default_platform_keys()
        self.assertIn("github", keys)
        self.assertIn("instagram", keys)


if __name__ == "__main__":
    unittest.main()
