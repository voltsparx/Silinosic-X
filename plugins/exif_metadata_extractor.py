"""Plugin: privacy-aware EXIF and GPS extraction from collected public images."""

from __future__ import annotations

from typing import Any

from core.foundation.privacy import sensitive_information_enabled
from plugins.media_recon_shared import resolve_media_recon_payload


PLUGIN_SPEC = {
    "id": "exif_metadata_extractor",
    "title": "EXIF Metadata Extractor",
    "description": "Extracts image metadata and makes precise GPS coordinates available only with sensitive-information opt-in.",
    "scopes": ["profile", "fusion"],
    "aliases": ["exif", "image_metadata", "gps_metadata"],
    "version": "1.0",
}


def run(context: dict[str, Any]) -> dict[str, Any]:
    result = resolve_media_recon_payload(context)
    reveal_sensitive = sensitive_information_enabled(context.get("sensitive_information"))
    images: list[dict[str, Any]] = []
    gps_count = 0
    for asset in result.image_assets:
        metadata = asset.metadata if isinstance(asset.metadata, dict) else {}
        gps = metadata.get("gps")
        if isinstance(gps, dict):
            gps_count += 1
        images.append({
            "url": asset.url,
            "sha256": asset.sha256,
            "format": metadata.get("format", ""),
            "dimensions": {"width": asset.width, "height": asset.height},
            "exif": dict(metadata.get("exif") or {}),
            "gps": dict(gps) if reveal_sensitive and isinstance(gps, dict) else ("[REDACTED]" if gps else None),
            "storage": dict(metadata.get("storage") or {}),
        })
    return {
        "severity": "MEDIUM" if gps_count else "INFO",
        "summary": f"EXIF metadata extracted from {len(images)} public image asset(s); GPS metadata was present on {gps_count} asset(s).",
        "highlights": [f"images={len(images)}", f"gps_assets={gps_count}", f"sensitive_information={reveal_sensitive}"],
        "data": {"images": images, "gps_asset_count": gps_count, "sensitive_information": reveal_sensitive},
    }
