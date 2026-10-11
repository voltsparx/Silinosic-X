"""Safe, per-target persistence for public media reconnaissance assets."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

from core.foundation.output_config import get_output_settings


_SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._-]+")


def _safe_segment(value: object, *, fallback: str) -> str:
    candidate = _SAFE_SEGMENT.sub("-", str(value or "").strip()).strip(".-_")
    return candidate[:80] or fallback


def _extension(content_type: str, source_url: str) -> str:
    suffix = Path(urlparse(source_url).path).suffix.lower()
    if suffix and re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
        return suffix
    return {
        "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
        "image/gif": ".gif", "image/bmp": ".bmp", "image/tiff": ".tiff",
    }.get(content_type.lower().split(";", 1)[0].strip(), ".bin")


def persist_image_asset(
    *,
    target: str,
    source_url: str,
    content_type: str,
    sha256: str,
    media_bytes: bytes,
    metadata: dict[str, Any],
) -> dict[str, str]:
    """Store one raw public asset plus JSON manifest/EXIF sidecars.

    Directory and file components are generated solely from sanitised target,
    URL, and digest values, preventing URL-controlled path traversal.
    """

    root = get_output_settings().output_root
    target_segment = _safe_segment(target, fallback="unknown-target")
    url_leaf = _safe_segment(Path(urlparse(source_url).path).stem, fallback="image")
    digest = _safe_segment(sha256[:16], fallback="unknown")
    directory = root / target_segment / "images" / f"{url_leaf}-{digest}"
    directory.mkdir(parents=True, exist_ok=True)
    asset_path = directory / f"asset{_extension(content_type, source_url)}"
    manifest_path = directory / "manifest.json"
    exif_path = directory / "exif.json"
    if not asset_path.exists():
        asset_path.write_bytes(media_bytes)
    captured_at = datetime.now(UTC).isoformat()
    manifest_path.write_text(
        json.dumps({
            "source_url": source_url, "content_type": content_type,
            "sha256": sha256, "size_bytes": len(media_bytes), "captured_at": captured_at,
            "asset": asset_path.name,
        }, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    exif_path.write_text(
        json.dumps({"exif": metadata.get("exif", {}), "gps": metadata.get("gps")}, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return {"directory": str(directory), "asset": str(asset_path), "manifest": str(manifest_path), "exif": str(exif_path)}
