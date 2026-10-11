"""Plugin: identify public wallet-address candidates without balance or transaction lookups."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from core.foundation.privacy import sensitive_information_enabled
from plugins.crypto._shared import collect_crypto_payloads, resolve_crypto_config


PLUGIN_SPEC = {
    "id": "crypto_wallet_address_intel",
    "title": "Wallet Address Intelligence",
    "description": "Recognizes Bitcoin and Ethereum address candidates; no wallet access, balance lookup, or transaction activity occurs.",
    "scopes": ["profile", "surface", "fusion"],
    "aliases": ["wallet_address", "crypto_wallet", "wallet_intel"],
    "version": "1.0",
}

_BTC_BASE58 = re.compile(r"\b[13][1-9A-HJ-NP-Za-km-z]{25,34}\b")
_BTC_BECH32 = re.compile(r"\bbc1[ac-hj-np-z02-9]{11,71}\b", re.IGNORECASE)
_ETH = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58decode(value: str) -> bytes:
    number = 0
    for character in value:
        number = number * 58 + _B58_ALPHABET.index(character)
    return b"\0" * (len(value) - len(value.lstrip("1"))) + number.to_bytes((number.bit_length() + 7) // 8, "big")


def _bitcoin_valid(value: str) -> bool:
    try:
        raw = _b58decode(value)
    except (ValueError, OverflowError):
        return False
    return len(raw) >= 5 and hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4] == raw[-4:]


def _ethereum_checksum(value: str) -> str:
    body = value[2:]
    if body.islower() or body.isupper():
        return "not_applicable"
    try:
        from Crypto.Hash import keccak
    except ImportError:
        return "unverified_keccak_unavailable"
    digest = keccak.new(digest_bits=256, data=body.lower().encode()).hexdigest()
    valid = all(not char.isalpha() or (char.isupper() == (int(digest[index], 16) >= 8)) for index, char in enumerate(body))
    return "valid" if valid else "invalid"


def run(context: dict[str, Any]) -> dict[str, Any]:
    config = resolve_crypto_config(context, crypto_kind="wallet_identifier")
    rows, sources = collect_crypto_payloads(context, source_fields=list(config["source_fields"]), max_items=int(config["max_items"]))
    sensitive = sensitive_information_enabled(context.get("sensitive_information"))
    candidates: list[dict[str, str]] = []
    for row in rows:
        for value in _BTC_BASE58.findall(row):
            candidates.append({"wallet_address": value if sensitive else "[REDACTED]", "network": "bitcoin_legacy", "checksum": "valid" if _bitcoin_valid(value) else "invalid"})
        for value in _BTC_BECH32.findall(row):
            candidates.append({"wallet_address": value if sensitive else "[REDACTED]", "network": "bitcoin_bech32", "checksum": "format_candidate"})
        for value in _ETH.findall(row):
            candidates.append({"wallet_address": value if sensitive else "[REDACTED]", "network": "ethereum", "checksum": _ethereum_checksum(value)})
    return {"severity": "INFO", "summary": f"Identified {len(candidates)} wallet-address candidate(s); no balances, transactions, or wallet access were requested.", "highlights": [f"sensitive_information={sensitive}", "format identification only"], "data": {"candidates": candidates, "source_summary": sources, "crypto_profile": config}}
