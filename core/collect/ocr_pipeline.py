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

"""Multi-engine OCR pipeline helpers."""

from __future__ import annotations

import importlib.util
import io
import re
import threading
from typing import Any


_EASYOCR_READERS: dict[tuple[str, ...], Any] = {}
_EASYOCR_LOCK = threading.Lock()


def _get_easyocr_reader(languages: list[str]) -> Any:
    """Return one EasyOCR reader per normalized language set.

    Constructing a reader loads its detection and recognition models.  Keeping
    it process-local avoids repeatedly loading those models for image batches,
    while the lock prevents concurrent first-use races.
    """

    key = tuple(sorted({str(language).strip() for language in languages if str(language).strip()}))
    if not key:
        key = ("en",)
    with _EASYOCR_LOCK:
        reader = _EASYOCR_READERS.get(key)
        if reader is None:
            import easyocr

            reader = easyocr.Reader(list(key), gpu=False)
            _EASYOCR_READERS[key] = reader
        return reader


def preprocess_for_ocr(image_bytes: bytes, intensity: str = "balanced") -> bytes:
    """Apply OCR-oriented preprocessing to an image payload."""

    normalized = str(intensity or "balanced").strip().lower()
    if normalized not in {"off", "light", "balanced", "aggressive"}:
        normalized = "balanced"
    if normalized == "off":
        return image_bytes

    try:
        from PIL import Image, ImageEnhance, ImageFilter

        with Image.open(io.BytesIO(image_bytes)) as image_handle:
            working = image_handle.convert("L")
            # Prefer OpenCV when available: its adaptive thresholding preserves
            # text in unevenly lit screenshots and photographs much better than
            # the former global 1-bit conversion.
            try:
                import cv2
                import numpy as np

                pixels = np.array(working)
                denoised = cv2.fastNlMeansDenoising(pixels, h=10)
                if normalized == "light":
                    processed = denoised
                elif normalized == "balanced":
                    enlarged = cv2.resize(denoised, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
                    processed = cv2.adaptiveThreshold(
                        enlarged, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
                    )
                else:
                    enlarged = cv2.resize(denoised, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
                    smoothed = cv2.bilateralFilter(enlarged, 7, 50, 50)
                    processed = cv2.adaptiveThreshold(
                        smoothed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 11
                    )
                working = Image.fromarray(processed)
            except ImportError:
                # Keep the OCR lane operational without OpenCV. Median filtering
                # is genuine denoising and deliberately precedes any sharpening.
                working = working.filter(ImageFilter.MedianFilter(size=3))
                if normalized != "light":
                    working = working.filter(ImageFilter.SHARPEN)
                    working = working.resize(
                        (working.width * 2, working.height * 2),
                        Image.Resampling.LANCZOS,
                    )
                if normalized == "aggressive":
                    working = ImageEnhance.Contrast(working).enhance(1.6)
            buffer = io.BytesIO()
            working.save(buffer, format="PNG")
            return buffer.getvalue()
    except Exception:
        return image_bytes


def ocr_with_tesseract(
    image_bytes: bytes,
    lang: str = "eng",
    config: str = "--oem 3 --psm 6",
) -> dict[str, Any]:
    """Run OCR with pytesseract when available."""

    if importlib.util.find_spec("pytesseract") is None:
        return {
            "text": "",
            "engine": "tesseract",
            "available": False,
            "avg_confidence": 0.0,
            "word_count": 0,
            "error": "pytesseract not installed",
        }

    try:
        import pytesseract
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as image_handle:
            data = pytesseract.image_to_data(
                image_handle,
                lang=lang,
                config=config,
                output_type=pytesseract.Output.DICT,
            )
            text = str(pytesseract.image_to_string(image_handle, lang=lang, config=config) or "").strip()
    except Exception as exc:
        return {
            "text": "",
            "engine": "tesseract",
            "available": True,
            "avg_confidence": 0.0,
            "word_count": 0,
            "error": str(exc),
        }

    confidences: list[float] = []
    words = data.get("text", []) if isinstance(data, dict) else []
    conf_rows = data.get("conf", []) if isinstance(data, dict) else []
    for word, conf in zip(words, conf_rows):
        try:
            score = float(conf)
        except (TypeError, ValueError):
            continue
        if score > 0 and str(word or "").strip():
            confidences.append(score)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return {
        "text": text,
        "engine": "tesseract",
        "available": True,
        "avg_confidence": avg_confidence,
        "word_count": len(confidences),
        "error": None,
    }


def ocr_with_easyocr(
    image_bytes: bytes,
    languages: list[str] | None = None,
) -> dict[str, Any]:
    """Run OCR with EasyOCR when available."""

    if importlib.util.find_spec("easyocr") is None:
        return {
            "text": "",
            "engine": "easyocr",
            "available": False,
            "avg_confidence": 0.0,
            "word_count": 0,
            "detections": [],
            "error": "easyocr not installed",
        }

    try:
        import numpy as np
        from PIL import Image

        langs = languages or ["en"]
        reader = _get_easyocr_reader(langs)
        with Image.open(io.BytesIO(image_bytes)) as image_handle:
            np_array = np.array(image_handle)
        rows = reader.readtext(np_array, detail=1)
    except Exception as exc:
        return {
            "text": "",
            "engine": "easyocr",
            "available": True,
            "avg_confidence": 0.0,
            "word_count": 0,
            "detections": [],
            "error": str(exc),
        }

    texts: list[str] = []
    confidences: list[float] = []
    detections: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 3:
            continue
        text = str(row[1] or "").strip()
        try:
            confidence = float(row[2])
        except (TypeError, ValueError):
            confidence = 0.0
        if text:
            texts.append(text)
            confidences.append(confidence)
            detections.append({"text": text, "confidence": confidence})

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return {
        "text": " ".join(texts).strip(),
        "engine": "easyocr",
        "available": True,
        "avg_confidence": avg_confidence,
        "word_count": len(texts),
        "detections": detections,
        "error": None,
    }


def extract_ocr_signals(text: str) -> dict[str, Any]:
    """Extract OSINT-style signals from arbitrary text."""

    body = str(text or "")
    emails = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}", body)))
    urls = sorted(set(re.findall(r"https?://[^\s<>'\"]{4,}", body)))
    phones = sorted(set(re.findall(r"(?:\+?\d[\d\-\s().]{6,}\d)", body)))
    mentions = sorted(set(re.findall(r"(?<!\w)@([A-Za-z0-9_.\-]{2,32})", body)))
    hashtags = sorted(set(re.findall(r"(?<!\w)#([A-Za-z][A-Za-z0-9_]{1,31})", body)))
    ips = sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", body)))
    signal_count = sum(len(values) for values in (emails, urls, phones, mentions, hashtags, ips))
    return {
        "emails": emails,
        "urls": urls,
        "phones": phones,
        "mentions": mentions,
        "hashtags": hashtags,
        "ips": ips,
        "signal_count": signal_count,
    }


def merge_ocr_engine_results(tesseract_result: dict, easyocr_result: dict) -> dict[str, Any]:
    """Merge tesseract and EasyOCR outputs into one text result."""

    t_text = str((tesseract_result or {}).get("text", "") or "").strip()
    e_text = str((easyocr_result or {}).get("text", "") or "").strip()
    t_used = bool((tesseract_result or {}).get("available"))
    e_used = bool((easyocr_result or {}).get("available"))

    def _confidence(result: dict[str, Any], *, scale: float = 1.0) -> float:
        try:
            return max(0.0, float(result.get("avg_confidence", 0.0) or 0.0) * scale)
        except (TypeError, ValueError):
            return 0.0

    if not t_text and not e_text:
        base_text, short_text, primary_engine = "", "", "none"
    elif t_text and not e_text:
        base_text, short_text, primary_engine = t_text, "", "tesseract"
    elif e_text and not t_text:
        base_text, short_text, primary_engine = e_text, "", "easyocr"
    elif _confidence(tesseract_result) >= _confidence(easyocr_result, scale=100.0):
        base_text, short_text, primary_engine = t_text, e_text, "tesseract"
    else:
        base_text, short_text, primary_engine = e_text, t_text, "easyocr"

    base_words = {token.casefold() for token in base_text.split()}
    addendum = [token for token in short_text.split() if token.casefold() not in base_words]
    merged_text = base_text if not addendum else f"{base_text} | {' '.join(addendum)}"

    return {
        "merged_text": merged_text,
        "tesseract_used": t_used,
        "easyocr_used": e_used,
        "primary_engine": primary_engine,
        "merged_word_count": len(merged_text.split()),
    }


def run_ocr_pipeline(
    image_bytes: bytes,
    preprocess_intensity: str = "balanced",
    use_tesseract: bool = True,
    use_easyocr: bool = True,
    tesseract_lang: str = "eng",
    tesseract_config: str = "--oem 3 --psm 6",
    easyocr_langs: list[str] | None = None,
) -> dict[str, Any]:
    """Run the full OCR pipeline."""

    processed_bytes = preprocess_for_ocr(image_bytes, intensity=preprocess_intensity)
    engines_run: list[str] = []

    if use_tesseract:
        tesseract_result = ocr_with_tesseract(
            processed_bytes,
            lang=tesseract_lang,
            config=tesseract_config,
        )
        engines_run.append("tesseract")
    else:
        tesseract_result = {
            "text": "",
            "engine": "tesseract",
            "available": False,
            "avg_confidence": 0.0,
            "word_count": 0,
            "error": None,
        }

    if use_easyocr:
        easyocr_result = ocr_with_easyocr(processed_bytes, languages=easyocr_langs)
        engines_run.append("easyocr")
    else:
        easyocr_result = {
            "text": "",
            "engine": "easyocr",
            "available": False,
            "avg_confidence": 0.0,
            "word_count": 0,
            "detections": [],
            "error": None,
        }

    merged = merge_ocr_engine_results(tesseract_result, easyocr_result)
    signals = extract_ocr_signals(merged["merged_text"])
    return {
        "tesseract_result": tesseract_result,
        "easyocr_result": easyocr_result,
        "merged": merged,
        "signals": signals,
        "merged_text": merged["merged_text"],
        "preprocess_intensity": preprocess_intensity,
        "image_size_bytes": len(image_bytes),
        "engines_run": engines_run,
    }
