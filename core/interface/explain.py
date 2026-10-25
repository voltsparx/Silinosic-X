# ──────────────────────────────────────────────────────────────
# SPDX-License-Identifier: AAL
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

"""Human-readable explain output for commands, plugins, and filters."""

from __future__ import annotations

from core.foundation.metadata import PROJECT_NAME, VERSION, VERSION_THEME
from core.interface.symbols import symbol
from core.extensions.signal_forge import list_plugin_descriptors
from core.extensions.signal_sieve import list_filter_descriptors
from modules.catalog import ensure_module_catalog, module_display_name, module_execution_mode


COMMAND_EXPLANATIONS: dict[str, str] = {
    "profile": "Checks usernames across platform manifests, extracts public signals, and correlates matches.",
    "surface": "Scans domain-facing assets (HTTP/HTTPS, CT, RDAP, headers) and summarizes exposure risk.",
    "fusion": "Runs profile + surface flows together and outputs one combined intelligence bundle.",
    "investigate": "Runs the progressive investigation pipeline across a profile target and an optional domain target.",
    "ocr": "Scans local image paths or remote image URLs with OCR, preprocessing, structured extraction, and batch reporting.",
    "orchestrate": (
        "Runs the policy-driven layered pipeline (capabilities -> filters -> fusion -> reporting) "
        "using entity contracts."
    ),
    "keywords": "Lists prompt keyword aliases that map casual words to core commands.",
    "plugins": "Lists available internal plugins and their compatible workflow scopes.",
    "filters": "Lists available internal filters and their compatible workflow scopes.",
    "templates": "Lists bundled info-templates (curated plugin/filter/module arrangements; consent-only targets).",
    "modules": (
        "Lists attachable source-intel reference cards from framework source trees under temp/. They guide research "
        "and reporting but do not execute code; plugins and filters are the executable extension types."
    ),
    "frameworks": "Inspects local source-study framework inventories, recipes, flags, modules, and commands under temp/.",
    "surface-kit": "Translates source-study recipes into a native Silinosic-X surface collection plan.",
    "quicktest": (
        "Runs one random built-in victim template (5 total) and generates full JSON/CLI/CSV/HTML reports "
        "without live network collection."
    ),
    "history": "Shows previously scanned targets from local output/json and output/html artifacts.",
    "anonymity": "Checks or updates Tor/proxy routing for current session execution.",
    "doctor": "Checks local dependencies, OCR backends, Tor routing, report backends, and runtime configuration.",
    "live": "Starts the local dashboard for a saved target result bundle.",
    "out-type": "Sets the persisted output formats (cli, html, csv, json, sql, docx, pdf).",
    "out-print": "Sets the output base directory for this session (affects output/...).",
    "default-out-print": "Sets the persisted default output base directory.",
    "help": "Shows the concise command menu; use `<command> --help` for command-specific flags.",
    "wizard": (
        "Guided interactive workflow that can run profile/surface/fusion phases with "
        "preset + extension-control selection and compatibility preflight checks."
    ),
    "about": "Shows framework identity, authorship, and core tool description.",
    "explain": "Shows plain-language command/plugin/filter explanations for quick onboarding.",
    "prompt": "Starts interactive prompt mode with session-level selection and output controls.",
    "version": "Shows the installed framework version and signature.",
    "capability-pack": "Builds local capability-pack folders and report artifacts from the framework inventory.",
}


def build_explain_text() -> str:
    plugins = list_plugin_descriptors(scope=None)
    filters = list_filter_descriptors(scope=None)

    lines: list[str] = []
    lines.append(f"{symbol('major')} {PROJECT_NAME} v{VERSION} [{VERSION_THEME}] - Explain Mode")
    lines.append("-" * 36)
    lines.append("")
    lines.append(f"{symbol('major')} What this tool does")
    lines.append(
        f"{symbol('bullet')} Collects public OSINT signals from usernames and domains, then fuses correlation, exposure, and reporting."
    )
    lines.append("")
    lines.append(f"{symbol('major')} Global flags")
    lines.append(f"{symbol('bullet')} --about: print tool description and identity block.")
    lines.append(f"{symbol('bullet')} --explain: print this explain guide and exit.")
    lines.append("")
    lines.append(f"{symbol('major')} Commands")
    for command, description in sorted(COMMAND_EXPLANATIONS.items()):
        lines.append(f"{symbol('bullet')} {command}: {description}")
    lines.append("")
    lines.append(f"{symbol('major')} Plugins")
    core_plugins = [
        row for row in plugins if str(row.get("plugin_group") or "").strip().lower() != "cryptography"
    ]
    crypto_plugins = [
        row for row in plugins if str(row.get("plugin_group") or "").strip().lower() == "cryptography"
    ]
    lines.append(f"{symbol('tip')} Core Plugin Set ({len(core_plugins)})")
    for row in sorted(core_plugins, key=lambda item: str(item.get("id", ""))):
        scopes = ", ".join(row.get("scopes", []))
        lines.append(f"{symbol('feature')} {row.get('id')}: {row.get('description')} (scopes: {scopes})")
    if crypto_plugins:
        lines.append(f"{symbol('tip')} Cryptography Plugin Set ({len(crypto_plugins)})")
        for row in sorted(crypto_plugins, key=lambda item: str(item.get("id", ""))):
            scopes = ", ".join(row.get("scopes", []))
            crypto_kind = str(row.get("crypto_kind") or "").strip().lower()
            kind_suffix = f", crypto-kind: {crypto_kind}" if crypto_kind else ""
            lines.append(f"{symbol('feature')} {row.get('id')}: {row.get('description')} (scopes: {scopes}{kind_suffix})")
        lines.append(
            f"{symbol('tip')} Crypto output includes config labels and source coverage in CLI/HTML reports."
        )
    lines.append("")
    lines.append(f"{symbol('major')} Filters")
    for row in sorted(filters, key=lambda item: str(item.get("id", ""))):
        scopes = ", ".join(row.get("scopes", []))
        lines.append(f"{symbol('feature')} {row.get('id')}: {row.get('description')} (scopes: {scopes})")
    lines.append("")
    lines.append(f"{symbol('major')} Module Catalog")
    try:
        catalog = ensure_module_catalog(refresh=False, validate_catalog=True)
        module_rows = [row for row in catalog.get("modules", []) if isinstance(row, dict)]
    except Exception as exc:  # pragma: no cover - environment-specific catalog failure
        module_rows = []
        lines.append(f"{symbol('warn')} Module catalog unavailable: {exc}")
    if module_rows:
        lines.append(
            f"{symbol('tip')} {len(module_rows)} catalog references are listed below. They are attachable research context only; "
            "they do not execute like plugins or filters. The 25/50-item views in prompt/CLI are pagination defaults, not a usable-module cap."
        )
        for row in sorted(module_rows, key=lambda item: (module_display_name(item).lower(), str(item.get("id", "")))):
            scopes = ", ".join(str(item) for item in (row.get("scopes") or [])) or "all"
            capabilities = ", ".join(str(item) for item in (row.get("capabilities") or [])[:5]) or "general"
            lines.append(
                f"{symbol('feature')} {module_display_name(row)}: {capabilities} research reference "
                f"(selector: {row.get('id')}; scopes: {scopes}; execution: {module_execution_mode(row)})."
            )
    else:
        lines.append(f"{symbol('warn')} No module catalog entries are available. Run `modules --sync` after adding source-study trees.")
    lines.append("")
    lines.append(f"{symbol('major')} Prompt-only controls")
    lines.append(f"{symbol('bullet')} banner: print the banner again.")
    lines.append(f"{symbol('bullet')} clear: clear terminal only (banner stays hidden until you run banner).")
    lines.append(f"{symbol('bullet')} use profile|surface|fusion: switch active module context.")
    lines.append(f"{symbol('bullet')} select module <name>: alias for use command module switch.")
    lines.append(f"{symbol('bullet')} set plugins ... / set filters ...: module-compatible defaults, supports aliases, comma-separated.")
    lines.append(f"{symbol('bullet')} set modules <selector,...>: attach catalog context by its named selector; `show modules` reveals selectors and pagination.")
    lines.append(f"{symbol('bullet')} set template <id>: apply a bundled info-template to plugin/filter defaults.")
    lines.append(f"{symbol('bullet')} select plugins ... / select filters ...: name-based aliases for set controls.")
    lines.append(f"{symbol('bullet')} select template <id>: alias for set template.")
    lines.append(f"{symbol('bullet')} add/remove plugins ...: incremental plugin control by selector name.")
    lines.append(f"{symbol('bullet')} add/remove filters ...: incremental filter control by selector name.")
    lines.append(f"{symbol('bullet')} set extension_control ...: module default for --extension-control auto|manual|hybrid.")
    lines.append(f"{symbol('bullet')} set orchestrate_extension_control ...: default --extension-control for orchestrate.")
    lines.append(f"{symbol('bullet')} set scan_range quickrange|fullrange: change profile-platform coverage for the prompt session.")
    lines.append(f"{symbol('bullet')} set sensitive_information on|off: opt in to, or force, sensitive-value rendering for the prompt session.")
    lines.append(f"{symbol('bullet')} Prompt format: (console <module> ec=<mode> plugins=<set> filters=<set>)>>")
    lines.append("")
    lines.append(f"{symbol('major')} Flag parity notes")
    lines.append(f"{symbol('bullet')} profile/surface/fusion share plugin/filter flags: --plugin, --list-plugins.")
    lines.append(f"{symbol('bullet')} ocr ships as a dedicated image-scan lane with OCR-only plugins and filters.")
    lines.append(f"{symbol('bullet')} profile/surface/fusion share filter flags: --filter, --list-filters.")
    lines.append(f"{symbol('bullet')} --info-template applies a curated plugin/filter/module arrangement.")
    lines.append(f"{symbol('bullet')} extension controls: --extension-control auto|manual|hybrid with conflict validation.")
    lines.append(f"{symbol('bullet')} explain command and --explain flag produce the same explain output.")
    lines.append(
        f"{symbol('bullet')} wizard supports phase toggles, preset selection, extension preflight validation, and seeded/non-seeded execution."
    )
    lines.append(
        f"{symbol('bullet')} OCR image scanning now ships as a first-class workflow; docs/media-intelligence.md documents the full lane."
    )
    return "\n".join(lines)
