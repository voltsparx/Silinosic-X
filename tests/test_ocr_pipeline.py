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
# ──────────────────────────────────────────────────────────────

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.collect.ocr_pipeline import (
    _EASYOCR_READERS,
    _EASYOCR_READER_CACHE_LIMIT,
    _get_easyocr_reader,
    extract_ocr_signals,
    merge_ocr_engine_results,
    preprocess_for_ocr,
    run_ocr_pipeline,
)
from core.foundation.operator_config import load_operator_config


class TestOcrPipeline(unittest.TestCase):
    def test_preprocess_off_unchanged(self):
        payload = b"x" * 100
        self.assertEqual(preprocess_for_ocr(payload, "off"), payload)

    def test_merge_both_empty(self):
        self.assertEqual(merge_ocr_engine_results({}, {})["merged_text"], "")

    def test_merge_only_tesseract(self):
        tesseract = {"text": "hello world", "engine": "tesseract", "available": True}
        self.assertEqual(merge_ocr_engine_results(tesseract, {})["merged_text"], "hello world")

    def test_merge_prefers_confidence_over_text_length(self):
        tesseract = {"text": "clean", "available": True, "avg_confidence": 91}
        easyocr = {"text": "longer noisy uncertain output", "available": True, "avg_confidence": 0.2}
        merged = merge_ocr_engine_results(tesseract, easyocr)
        self.assertEqual(merged["primary_engine"], "tesseract")
        self.assertTrue(merged["merged_text"].startswith("clean"))

    def test_easyocr_readers_are_cached_by_normalized_language_set(self):
        fake_reader = Mock()
        fake_easyocr = SimpleNamespace(Reader=fake_reader)
        _EASYOCR_READERS.clear()
        with patch.dict("sys.modules", {"easyocr": fake_easyocr}):
            first = _get_easyocr_reader(["en", "fr"])
            second = _get_easyocr_reader(["fr", "en"])
        self.assertIs(first, second)
        fake_reader.assert_called_once_with(["en", "fr"], gpu=False)

    def test_easyocr_reader_cache_is_bounded(self):
        fake_easyocr = SimpleNamespace(Reader=Mock(side_effect=lambda languages, gpu: tuple(languages)))
        _EASYOCR_READERS.clear()
        with patch.dict("sys.modules", {"easyocr": fake_easyocr}):
            for index in range(_EASYOCR_READER_CACHE_LIMIT + 1):
                _get_easyocr_reader([f"lang{index}"])
        self.assertEqual(len(_EASYOCR_READERS), _EASYOCR_READER_CACHE_LIMIT)

    def test_extract_signals_email(self):
        result = extract_ocr_signals("contact me at test@example.com today")
        self.assertIn("test@example.com", result["emails"])

    def test_pipeline_returns_dict(self):
        result = run_ocr_pipeline(b"fakebytes", use_tesseract=False, use_easyocr=False)
        self.assertIsInstance(result, dict)
        self.assertIn("merged_text", result)

    def test_config_defaults(self):
        result = load_operator_config("/nonexistent/path.yml")
        self.assertIsInstance(result, dict)
        self.assertIn("surface_probe", result)


if __name__ == "__main__":
    unittest.main()
