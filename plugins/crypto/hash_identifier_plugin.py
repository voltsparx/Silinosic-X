"""Plugin: identify hash-shaped strings only; it never attempts cracking."""

from __future__ import annotations

import re
from typing import Any

from plugins.crypto._shared import collect_crypto_payloads, resolve_crypto_config


PLUGIN_SPEC = {
    "id": "crypto_hash_identifier",
    "title": "Hash Identifier",
    "description": "Classifies likely cryptographic hash formats without cracking, lookup, or recovery attempts.",
    "scopes": ["profile", "surface", "fusion"],
    "aliases": ["hash_identifier", "hash_id"],
    "version": "1.0",
}

_HASHES = ((32, "md5"), (40, "sha1"), (64, "sha256"), (96, "sha384"), (128, "sha512"))


def run(context: dict[str, Any]) -> dict[str, Any]:
    config = resolve_crypto_config(context, crypto_kind="hash_identifier")
    rows, sources = collect_crypto_payloads(context, source_fields=list(config["source_fields"]), max_items=int(config["max_items"]))
    findings: list[dict[str, str]] = []
    for row in rows:
        for token in re.findall(r"\b[0-9a-fA-F]{32,128}\b", row):
            kinds = [name for size, name in _HASHES if len(token) == size]
            if kinds:
                findings.append({"value": token.lower(), "possible_types": ",".join(kinds)})
    return {"severity": "INFO", "summary": f"Identified {len(findings)} hash-shaped value(s); no cracking was attempted.", "highlights": ["classification only", "no cracking or recovery"], "data": {"findings": findings, "source_summary": sources, "crypto_profile": config}}
