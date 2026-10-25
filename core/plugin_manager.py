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

"""Async-capable plugin orchestration manager."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import importlib
import importlib.util
from typing import Any

from core.extensions.selector_keys import selector_keys
from core.extensions.signal_forge import list_plugin_discovery_errors, list_plugin_specs
from core.engines.thread_engine import run_blocking, run_blocking_batch
from core.foundation.privacy import sensitive_information_enabled


@dataclass(frozen=True)
class PluginDescriptor:
    """Plugin inventory metadata used by the orchestration manager."""

    module_name: str
    plugin_id: str
    title: str
    description: str
    scopes: tuple[str, ...]
    version: str
    author: str
    aliases: tuple[str, ...]


class PluginManager:
    """Discover, validate, and execute plugins with optional chaining."""

    def __init__(self, plugin_dir: str = "plugins/", *, max_concurrency: int = 8) -> None:
        self.plugin_dir = plugin_dir
        self.max_concurrency = max(1, int(max_concurrency))
        self.plugins, self.discovery_errors = self.discover_plugins()

    @staticmethod
    def _chain_priority(plugin: PluginDescriptor) -> tuple[int, str]:
        """Keep known data-producer extensions ahead of their consumers."""

        priority = {
            "media_recon_engine": 10,
            "exif_metadata_extractor": 20,
            "geo_location_intel": 30,
        }.get(plugin.plugin_id, 50)
        return priority, plugin.plugin_id

    def discover_plugins(self) -> tuple[list[PluginDescriptor], list[str]]:
        """Discover plugin metadata without importing plugin modules.

        Importing every extension during startup makes unrelated commands pay
        for optional dependencies and turns one bad extension import into a
        global startup problem. Requirements are checked when a selected
        plugin is prepared for execution instead.
        """

        descriptors: list[PluginDescriptor] = []
        errors = list_plugin_discovery_errors()

        for spec in list_plugin_specs():
            descriptors.append(
                PluginDescriptor(
                    module_name=spec.module_name,
                    plugin_id=spec.plugin_id,
                    title=spec.title,
                    description=spec.description,
                    scopes=tuple(spec.scopes),
                    version=spec.version,
                    author=spec.author,
                    aliases=tuple(spec.aliases),
                )
            )

        descriptors.sort(key=lambda item: item.plugin_id)
        return descriptors, errors

    @staticmethod
    def _missing_requirements(module: Any) -> list[str]:
        requires = getattr(module, "REQUIRES", [])
        if not isinstance(requires, list):
            return []
        return [
            package
            for package in requires
            if isinstance(package, str)
            and package.strip()
            and importlib.util.find_spec(package.strip()) is None
        ]

    def _resolve_plugins(
        self,
        *,
        scope: str,
        requested_plugins: list[str] | None,
        include_all: bool,
    ) -> tuple[list[PluginDescriptor], list[str]]:
        candidates = [plugin for plugin in self.plugins if scope in plugin.scopes]
        if include_all:
            return candidates, []

        by_key: dict[str, PluginDescriptor] = {}
        for plugin in candidates:
            for key in selector_keys(plugin.plugin_id):
                by_key.setdefault(key, plugin)
            for key in selector_keys(plugin.title):
                by_key.setdefault(key, plugin)
            for alias in plugin.aliases:
                for key in selector_keys(alias):
                    by_key.setdefault(key, plugin)

        selected: list[PluginDescriptor] = []
        unknown: list[str] = []
        seen: set[str] = set()
        for raw in requested_plugins or []:
            keys = selector_keys(raw)
            if not keys:
                continue
            match: PluginDescriptor | None = None
            for key in keys:
                match = by_key.get(key)
                if match is not None:
                    break
            if match is None:
                unknown.append(raw)
                continue
            if match.plugin_id in seen:
                continue
            selected.append(match)
            seen.add(match.plugin_id)
        return selected, unknown

    async def run_plugins(
        self,
        target_data: dict[str, Any],
        *,
        scope: str = "fusion",
        requested_plugins: list[str] | None = None,
        include_all: bool = False,
        chain: bool = True,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Execute plugins for a workflow scope.

        When `chain=True`, each plugin receives previous plugin output via
        `previous_plugin_data` in the context.
        """

        selected, unknown = self._resolve_plugins(
            scope=scope,
            requested_plugins=requested_plugins,
            include_all=include_all,
        )
        errors = list(self.discovery_errors)
        errors.extend(f"Unknown plugin requested: {name}" for name in unknown)

        if not selected:
            return [], errors

        base_context: dict[str, Any] = dict(target_data)
        base_context.setdefault("mode", scope)
        base_context.setdefault("target", target_data.get("target") if isinstance(target_data, dict) else None)
        base_context.setdefault("sensitive_information", sensitive_information_enabled())

        prepared: list[tuple[PluginDescriptor, Callable[..., Any]]] = []
        for plugin in selected:
            try:
                module = importlib.import_module(f"plugins.{plugin.module_name}")
                missing = self._missing_requirements(module)
                if missing:
                    errors.append(
                        f"Plugin '{plugin.plugin_id}' missing dependencies: {', '.join(sorted(missing))}"
                    )
                    continue
                run_fn = getattr(module, "run", None)
                if not callable(run_fn):
                    errors.append(f"Plugin '{plugin.plugin_id}' has no callable run(context).")
                    continue
                prepared.append((plugin, run_fn))
            except Exception as exc:  # pragma: no cover - plugin safety guard
                errors.append(f"Plugin '{plugin.plugin_id}' failed: {exc}")

        if not prepared:
            return [], errors

        if chain:
            prepared.sort(key=lambda item: self._chain_priority(item[0]))

        results: list[dict[str, Any]] = []
        previous_plugin_data: dict[str, Any] = {}

        if not chain:
            calls: list[tuple[Callable[..., Any], tuple[object, ...], dict[str, object]]] = [
                (run_fn, (dict(base_context),), {})
                for _, run_fn in prepared
            ]
            batch = await run_blocking_batch(
                calls,
                concurrency_limit=min(self.max_concurrency, len(calls)),
            )
            for (plugin, _), payload in zip(prepared, batch):
                if isinstance(payload, Exception):
                    errors.append(f"Plugin '{plugin.plugin_id}' failed: {payload}")
                    continue
                if not isinstance(payload, dict):
                    errors.append(f"Plugin '{plugin.plugin_id}' returned non-dict payload.")
                    continue
                results.append(
                    {
                        "id": plugin.plugin_id,
                        "title": plugin.title,
                        "description": plugin.description,
                        "scope": scope,
                        "summary": str(payload.get("summary") or "No plugin summary."),
                        "severity": str(payload.get("severity") or "INFO").upper(),
                        "highlights": [str(item) for item in (payload.get("highlights") or [])],
                        "data": payload.get("data") if isinstance(payload.get("data"), dict) else {},
                    }
                )
            return results, errors

        for plugin, run_fn in prepared:
            context = dict(base_context)
            context["previous_plugin_data"] = dict(previous_plugin_data)
            context["plugins"] = list(results)
            try:
                payload = await run_blocking(run_fn, context)
            except Exception as exc:  # pragma: no cover - plugin safety guard
                errors.append(f"Plugin '{plugin.plugin_id}' failed: {exc}")
                continue
            if not isinstance(payload, dict):
                errors.append(f"Plugin '{plugin.plugin_id}' returned non-dict payload.")
                continue

            result: dict[str, Any] = {
                "id": plugin.plugin_id,
                "title": plugin.title,
                "description": plugin.description,
                "scope": scope,
                "summary": str(payload.get("summary") or "No plugin summary."),
                "severity": str(payload.get("severity") or "INFO").upper(),
                "highlights": [str(item) for item in (payload.get("highlights") or [])],
                "data": payload.get("data") if isinstance(payload.get("data"), dict) else {},
            }
            results.append(result)
            previous_plugin_data[plugin.plugin_id] = result["data"]

        return results, errors
