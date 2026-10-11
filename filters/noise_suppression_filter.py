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

"""Filter: identify low-signal findings that can be suppressed for clarity."""

from __future__ import annotations

import re

from core.foundation.operator_config import get_noise_filter_config


FILTER_SPEC = {
    "id": "noise_suppression_filter",
    "title": "Noise Suppression Filter",
    "description": "Marks low-signal rows and placeholder artifacts to improve scan readability.",
    "scopes": ["profile", "surface", "fusion"],
    "aliases": ["noise_filter", "suppress_noise", "quiet"],
    "version": "1.0",
}


LOW_SIGNAL_SUBDOMAIN_PATTERN = re.compile(
    r"^(?:www\d*|m|img\d*|cdn\d*|static\d*|assets?\d*)[.-]",
    re.IGNORECASE,
)


def _ocr_noise_rows(value: object, *, confidence_floor: float) -> list[str]:
    """Find short, low-confidence OCR outputs nested in plugin data."""

    suppressed: list[str] = []

    def _walk(item: object, path: str) -> None:
        if isinstance(item, dict):
            text = str(item.get("text", item.get("merged_text", item.get("raw_text", ""))) or "").strip()
            confidence = item.get("avg_confidence")
            if confidence is not None and text:
                try:
                    normalized_confidence = float(confidence)
                    if normalized_confidence <= 1:
                        normalized_confidence *= 100
                    if normalized_confidence < confidence_floor and len(text.split()) < 3:
                        suppressed.append(path)
                except (TypeError, ValueError):
                    pass
            for key, child in item.items():
                _walk(child, f"{path}.{key}" if path else str(key))
        elif isinstance(item, list):
            for index, child in enumerate(item):
                _walk(child, f"{path}[{index}]")

    _walk(value, "previous_plugin_data")
    return suppressed


def run(context: dict) -> dict:
    results = context.get("results", []) or []
    domain_result = context.get("domain_result") or {}
    settings = get_noise_filter_config()
    confidence_floor = int(settings.get("profile_confidence_floor", 55) or 55)
    severity_suppress_count = int(settings.get("severity_suppress_count", 20) or 20)
    ocr_confidence_floor = float(settings.get("ocr_confidence_floor", 35) or 35)

    suppress_profile: list[str] = []
    keep_profile: list[str] = []
    for row in results:
        platform = str(row.get("platform", "Unknown"))
        status = str(row.get("status", "UNKNOWN"))
        confidence = int(row.get("confidence", 0) or 0)
        has_signal = bool(row.get("bio")) or bool(row.get("links")) or bool((row.get("contacts", {}) or {}).get("emails")) or bool((row.get("contacts", {}) or {}).get("phones")) or bool(row.get("mentions"))

        if status in {"NOT FOUND", "INVALID_USERNAME"}:
            suppress_profile.append(platform)
            continue
        if status == "FOUND" and confidence < confidence_floor and not has_signal:
            suppress_profile.append(platform)
            continue
        keep_profile.append(platform)

    subdomains = [str(item).strip().lower() for item in (domain_result.get("subdomains", []) or []) if str(item).strip()]
    suppress_subdomains = [name for name in subdomains if LOW_SIGNAL_SUBDOMAIN_PATTERN.match(name)]
    keep_subdomains = [name for name in subdomains if name not in suppress_subdomains]
    suppress_ocr = _ocr_noise_rows(
        context.get("previous_plugin_data", {}),
        confidence_floor=ocr_confidence_floor,
    )

    suppress_count = len(suppress_profile) + len(suppress_subdomains) + len(suppress_ocr)
    severity = "MEDIUM" if suppress_count >= severity_suppress_count else "INFO"
    summary = (
        f"Noise suppression identified {suppress_count} low-signal artifact(s) "
        f"({len(suppress_profile)} profile rows, {len(suppress_subdomains)} subdomains, "
        f"{len(suppress_ocr)} OCR artifacts)."
    )
    return {
        "severity": severity,
        "summary": summary,
        "highlights": [
            f"suppress_profile={len(suppress_profile)}",
            f"suppress_subdomains={len(suppress_subdomains)}",
            f"keep_profile={len(keep_profile)}",
            f"keep_subdomains={len(keep_subdomains)}",
            f"suppress_ocr={len(suppress_ocr)}",
        ],
        "data": {
            "suppressed_profiles": sorted(set(suppress_profile)),
            "suppressed_subdomains": suppress_subdomains[:80],
            "recommended_profile_focus": sorted(set(keep_profile)),
            "recommended_subdomain_focus_count": len(keep_subdomains),
            "suppressed_ocr_artifacts": suppress_ocr[:80],
        },
    }
