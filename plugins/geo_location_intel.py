"""Plugin: correlate precise EXIF GPS with explicitly labelled public location leads."""

from __future__ import annotations

import re
from typing import Any

from core.foundation.privacy import sensitive_information_enabled
from plugins.media_recon_shared import resolve_media_recon_payload


PLUGIN_SPEC = {
    "id": "geo_location_intel",
    "title": "Geo-location Intelligence",
    "description": "Correlates EXIF GPS, public text location expressions, and domain registrant-country hints without treating text as verified location.",
    "scopes": ["profile", "surface", "fusion"],
    "aliases": ["geolocation", "geo_intel", "location_intel"],
    "version": "1.0",
}

_LOCATION_RE = re.compile(r"(?:\b(?:based|located|live|living)\s+in\s+|\bfrom\s+)([A-Z][A-Za-z .'-]{2,48})")


def _previous_gps(context: dict[str, Any]) -> list[dict[str, Any]]:
    previous = context.get("previous_plugin_data")
    if not isinstance(previous, dict):
        return []
    exif_data = previous.get("exif_metadata_extractor")
    if not isinstance(exif_data, dict):
        return []
    points = [row.get("gps") for row in exif_data.get("images", []) if isinstance(row, dict) and isinstance(row.get("gps"), dict)]
    if points:
        return points
    return [{} for _ in range(int(exif_data.get("gps_asset_count") or 0))]


def run(context: dict[str, Any]) -> dict[str, Any]:
    reveal_sensitive = sensitive_information_enabled(context.get("sensitive_information"))
    gps_points = _previous_gps(context)
    if not gps_points and context.get("results"):
        payload = resolve_media_recon_payload(context)
        gps_points = [asset.metadata.get("gps") for asset in payload.image_assets if isinstance(asset.metadata.get("gps"), dict)]
    text = "\n".join(
        str(row.get(key) or "")
        for row in context.get("results", []) if isinstance(row, dict)
        for key in ("bio", "about", "description", "location")
    )
    text_leads = list(dict.fromkeys(match.strip(" .") for match in _LOCATION_RE.findall(text)))[:8]
    domain = context.get("domain_result") if isinstance(context.get("domain_result"), dict) else {}
    deep_recon = domain.get("domain_deep_recon") if isinstance(domain.get("domain_deep_recon"), dict) else {}
    whois = deep_recon.get("whois") if isinstance(deep_recon.get("whois"), dict) else domain.get("whois", {})
    registrant_country = (
        domain.get("registrant_country")
        or domain.get("whois_country")
        or (whois.get("registrant_country") if isinstance(whois, dict) else None)
    )
    visible_gps: list[Any] = gps_points if reveal_sensitive else ["[REDACTED]" for _ in gps_points]
    return {
        "severity": "MEDIUM" if gps_points else "INFO",
        "summary": f"Geo-location intelligence found {len(gps_points)} precise GPS point(s) and {len(text_leads)} unverified public-text location lead(s).",
        "highlights": ["Text-derived locations are leads, not verified locations.", f"registrant_country={registrant_country or 'unavailable'}"],
        "data": {
            "gps_points": visible_gps,
            "text_location_leads": [{"value": lead, "confidence": "lead_only"} for lead in text_leads],
            "registrant_country_hint": registrant_country,
        },
    }
