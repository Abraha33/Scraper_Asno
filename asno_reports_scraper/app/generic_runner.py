from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from .assisted import assisted_pause
from .config import Settings
from .extraction_targets import (
    ExtractionTarget,
    absolute_target_url,
    list_targets_rows,
    load_extraction_targets,
    targets_by_module,
)
from .generic_extractors.filter_paginated_table import FilterPaginatedTarget, extract_filter_paginated_table
from .pattern_engine import normalize_pattern
from .report_extractor import month_chunks
from .storage import read_json, safe_name, write_json


PATTERNS_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "patterns.yaml"


def _candidate_pages(settings: Settings) -> list[dict[str, Any]]:
    system = read_json(settings.audit_dir / "system_map.json", {})
    pages = system.get("pages", [])
    if pages:
        return pages
    plan = read_json(settings.data_dir / "plans" / "extraction_plan.json", {})
    return [page for module in plan.get("modules", []) for page in module.get("pages", [])]


def read_patterns_config() -> dict[str, Any]:
    """Read configs/patterns.yaml as source evidence without depending on PyYAML."""
    if not PATTERNS_CONFIG.exists():
        return {"path": str(PATTERNS_CONFIG), "exists": False, "patterns": []}
    text = PATTERNS_CONFIG.read_text(encoding="utf-8", errors="ignore")
    patterns: list[str] = []
    for line in text.splitlines():
        if line.startswith("  ") and line.strip().endswith(":") and not line.startswith("    "):
            patterns.append(line.strip().rstrip(":"))
    return {"path": str(PATTERNS_CONFIG), "exists": True, "patterns": patterns}


def read_extraction_plan(settings: Settings) -> dict[str, Any]:
    path = settings.data_dir / "plans" / "extraction_plan.json"
    plan = read_json(path, {})
    plan["_path"] = str(path)
    return plan


def filter_target_from_extraction_target(settings: Settings, target: ExtractionTarget) -> FilterPaginatedTarget:
    return FilterPaginatedTarget(
        target_id=target.target_id,
        name=target.name,
        url=absolute_target_url(settings, target),
        module=target.module,
        package_module=target.module,
        pattern=target.pattern,
        read_only_safe=target.safe_read_only,
    )


def resolve_generic_target(
    settings: Settings,
    *,
    pattern: str,
    module: str | None = None,
    name: str | None = None,
    url: str | None = None,
) -> FilterPaginatedTarget:
    normalized = normalize_pattern(pattern)
    pages = _candidate_pages(settings)
    if url:
        page = next((item for item in pages if str(item.get("url")).rstrip("/") == url.rstrip("/")), None)
        if page:
            return FilterPaginatedTarget(
                target_id=safe_name(str(page.get("name") or name or url).lower()),
                name=str(page.get("name") or name or url),
                url=str(page.get("url")),
                module=str(page.get("module") or module or "unknown"),
                package_module=str(page.get("module") or module or "unknown"),
                pattern=normalized,
                read_only_safe=bool(page.get("read_only_safe", True)),
            )
        return FilterPaginatedTarget(target_id=safe_name(name or url), name=name or url, url=url, module=module or "manual", package_module=module or "manual", pattern=normalized)

    matches = [
        item
        for item in pages
        if normalize_pattern(str(item.get("pattern") or "")) == normalized
        and (not module or str(item.get("module") or "").lower() == module.lower())
        and (not name or name.lower() in str(item.get("name") or "").lower())
    ]
    matches.sort(key=lambda item: (not bool(item.get("read_only_safe", True)), str(item.get("name") or "")))
    if not matches:
        raise SystemExit(
            "No encontré una página compatible en system_map.json. "
            "Usá --url explícito o corré audit-system --patterns primero."
        )
    item = matches[0]
    return FilterPaginatedTarget(
        target_id=safe_name(str(item.get("name") or item.get("url")).lower()),
        name=str(item.get("name") or item.get("url")),
        url=str(item.get("url")),
        module=str(item.get("module") or module or "unknown"),
        package_module=str(item.get("module") or module or "unknown"),
        pattern=normalized,
        read_only_safe=bool(item.get("read_only_safe", True)),
    )


async def extract_generic_pattern(
    page: Page,
    settings: Settings,
    *,
    pattern: str,
    module: str | None = None,
    name: str | None = None,
    url: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    max_pages: int | None = None,
    assisted: bool = False,
    optimize_page_size: bool = False,
) -> dict[str, Any]:
    normalized = normalize_pattern(pattern)
    target = resolve_generic_target(settings, pattern=normalized, module=module, name=name, url=url)
    if normalized not in {"filter_paginated_table", "paginated_table"}:
        if assisted:
            await assisted_pause(
                page,
                settings,
                safe_name(module or target.module),
                target.name,
                f"El extractor genérico para `{normalized}` todavía no está implementado.",
            )
        raise SystemExit(f"Extractor genérico no implementado todavía para pattern={normalized}")

    summary = await extract_filter_paginated_table(
        page,
        settings,
        target,
        date_from=date_from,
        date_to=date_to,
        max_pages=max_pages,
        assisted=assisted,
        optimize_page_size=optimize_page_size,
    )
    summary_path = settings.data_dir / "debug" / "generic_extract_pattern_summary.json"
    write_json(summary_path, summary)
    summary.setdefault("outputs", {})["summary"] = str(summary_path)
    return summary


def resolve_module_filter_paginated_targets(settings: Settings, module: str) -> list[FilterPaginatedTarget]:
    plan = read_extraction_plan(settings)
    pages: list[dict[str, Any]] = []
    for module_plan in plan.get("modules", []):
        module_name = str(module_plan.get("module") or "")
        package_name = str(module_plan.get("package_module") or module_name)
        if module_name.lower() == module.lower() or package_name.lower() == module.lower():
            pages.extend(module_plan.get("pages", []))
    if not pages:
        pages = [
            item
            for item in _candidate_pages(settings)
            if str(item.get("module") or "").lower() == module.lower()
        ]
    targets: list[FilterPaginatedTarget] = []
    for item in pages:
        pattern = normalize_pattern(str(item.get("pattern") or ""))
        if pattern not in {"filter_paginated_table", "paginated_table"}:
            continue
        targets.append(
            FilterPaginatedTarget(
                target_id=safe_name(str(item.get("name") or item.get("url")).lower()),
                name=str(item.get("name") or item.get("url")),
                url=str(item.get("url")),
                module=str(item.get("module") or module),
                package_module=module,
                pattern=pattern,
                read_only_safe=bool(item.get("read_only_safe", True)),
            )
        )
    targets.sort(key=lambda target: (not target.read_only_safe, target.name))
    return targets


async def extract_generic_module(
    page: Page,
    settings: Settings,
    *,
    module: str,
    target_id: str | None = None,
    date_from: date,
    date_to: date,
    limit_pages: int | None = None,
    assisted: bool = False,
    debug_counts: bool = False,
    optimize_page_size: bool = False,
) -> dict[str, Any]:
    patterns_config = read_patterns_config()
    plan = read_extraction_plan(settings)
    registry = load_extraction_targets(settings)
    if target_id == "sales_report":
        from .sales_extractor import extract_sales_report

        chunks = month_chunks(date_from, date_to)
        summaries = []
        for chunk_start, chunk_end in chunks:
            item = await extract_sales_report(
                page,
                settings,
                chunk_start,
                chunk_end,
                assisted=assisted,
                debug_counts=debug_counts,
            )
            item["target_id"] = "sales_report"
            item["target_validation"] = {
                "expected_url": absolute_target_url(settings, registry["sales_report"]),
                "actual_url": item.get("url") or "see outputs/debug",
                "target_name": registry["sales_report"].name,
                "expected_pattern": registry["sales_report"].pattern,
                "delegated_extractor": "sales_extractor",
            }
            summaries.append(item)
        totals: dict[str, Any] = defaultdict(int)
        for item in summaries:
            counts = item.get("debug", {}).get("counts", {})
            pagination = item.get("debug", {}).get("pagination", {})
            totals["rows"] += int(item.get("row_count") or 0)
            totals["rows_before_dedupe"] += int(counts.get("rows_before_dedupe") or 0)
            totals["rows_after_dedupe"] += int(counts.get("rows_after_dedupe") or item.get("row_count") or 0)
            totals["unique_ids"] += int(counts.get("unique_ids_after_dedupe") or item.get("row_count") or 0)
            totals["pages_walked"] += int(pagination.get("pages_walked") or 0)
            totals["failed_chunks"] += 1 if item.get("status") != "success" else 0
        result = {
            "module": "sales",
            "target_id": "sales_report",
            "status": "success" if not totals["failed_chunks"] else "partial",
            "targets_registry_path": str(Path(__file__).resolve().parents[1] / "configs" / "extraction_targets.yaml"),
            "patterns_config": patterns_config,
            "extraction_plan_path": plan.get("_path"),
            "targets_count": 1,
            "chunks_count": len(chunks),
            "limit_pages": limit_pages,
            "debug_counts": debug_counts,
            "totals": dict(totals),
            "summaries": summaries,
        }
        output_path = settings.debug_dir / "generic_extract" / f"sales_report_{date_from.isoformat()}_{date_to.isoformat()}.json"
        write_json(output_path, result)
        result["summary_path"] = str(output_path)
        return result
    if target_id:
        target_config = registry.get(target_id)
        if not target_config:
            available = ", ".join(sorted(registry.keys())[:50])
            raise SystemExit(f"Target no encontrado: {target_id}. Disponibles: {available}")
        targets = [filter_target_from_extraction_target(settings, target_config)]
        module = target_config.module
    else:
        module_targets = targets_by_module(registry, module)
        extractable = [item for item in module_targets if normalize_pattern(item.pattern) in {"filter_paginated_table", "paginated_table"}]
        if len(extractable) > 1:
            lines = [
                f"El module={module} es ambiguo. No voy a elegir un target silenciosamente.",
                "Usá --target con uno de estos targets:",
            ]
            for item in extractable:
                lines.append(f"  - {item.target_id}: {item.name} ({absolute_target_url(settings, item)})")
            raise SystemExit("\n".join(lines))
        targets = [filter_target_from_extraction_target(settings, extractable[0])] if extractable else resolve_module_filter_paginated_targets(settings, module)
    if not targets:
        raise SystemExit(f"No hay páginas filter_paginated_table para module={module} en {plan.get('_path')}")
    chunks = month_chunks(date_from, date_to)
    summaries: list[dict[str, Any]] = []
    for target in targets:
        for chunk_start, chunk_end in chunks:
            summaries.append(
                await extract_filter_paginated_table(
                    page,
                    settings,
                    target,
                    date_from=chunk_start,
                    date_to=chunk_end,
                    max_pages=limit_pages,
                    assisted=assisted,
                    optimize_page_size=optimize_page_size,
                )
            )
    totals: dict[str, Any] = defaultdict(int)
    for item in summaries:
        diagnostics = item.get("diagnostics", {})
        counts = diagnostics.get("counts", {})
        pagination = diagnostics.get("pagination", {})
        totals["rows"] += int(item.get("row_count") or 0)
        totals["rows_before_dedupe"] += int(counts.get("rows_before_dedupe") or 0)
        totals["rows_after_dedupe"] += int(counts.get("rows_after_dedupe") or 0)
        totals["unique_ids"] += int(counts.get("unique_ids") or 0)
        totals["pages_walked"] += int(pagination.get("pages_walked") or 0)
        totals["failed_chunks"] += 1 if item.get("status") != "success" else 0
    result = {
        "module": module,
        "target_id": target_id,
        "status": "success" if not totals["failed_chunks"] else "partial",
        "targets_registry_path": str(Path(__file__).resolve().parents[1] / "configs" / "extraction_targets.yaml"),
        "patterns_config": patterns_config,
        "extraction_plan_path": plan.get("_path"),
        "targets_count": len(targets),
        "chunks_count": len(chunks),
        "limit_pages": limit_pages,
        "debug_counts": debug_counts,
        "totals": dict(totals),
        "summaries": summaries,
    }
    summary_stem = safe_name(target_id or module)
    output_path = settings.debug_dir / "generic_extract" / f"{summary_stem}_{date_from.isoformat()}_{date_to.isoformat()}.json"
    write_json(output_path, result)
    result["summary_path"] = str(output_path)
    return result
