from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Page

from ..assisted import assisted_pause
from ..config import Settings
from ..storage import now_iso, safe_name, save_evidence, write_json
from .common import (
    click_safe_filter_button_if_present,
    dedupe_rows,
    detect_dangerous_actions,
    fill_date_range_if_available,
    go_next_page,
    pagination_snapshot,
    read_filters,
    read_pagination,
    read_visible_tables,
    select_largest_safe_page_size,
    wait_until_loaded,
    write_package_chunk,
    write_standard_outputs,
)


@dataclass(frozen=True)
class FilterPaginatedTarget:
    target_id: str
    name: str
    url: str
    module: str
    package_module: str | None = None
    pattern: str = "filter_paginated_table"
    read_only_safe: bool = True


async def detect_page_identity(page: Page, expected_pattern: str) -> dict[str, Any]:
    identity = await page.evaluate(
        """(expectedPattern) => {
            const clean = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const heading = Array.from(document.querySelectorAll('h1,h2,h3,.page-title,.content-header h1')).find(visible);
            const filters = Array.from(document.querySelectorAll('input,select,textarea')).filter(visible).length;
            const tables = Array.from(document.querySelectorAll('table')).filter(t => visible(t) && !t.closest('.datetimepicker, .datepicker, #ui-datepicker-div')).length;
            const pagination = Array.from(document.querySelectorAll('.dataTables_paginate,.pagination,.dataTables_length select,select[name$="_length"]')).filter(visible).length;
            let detected = 'unknown';
            if (tables && filters && pagination) detected = 'filter_paginated_table';
            else if (tables && pagination) detected = 'paginated_table';
            else if (tables && filters) detected = 'filter_table';
            else if (tables) detected = 'list_table';
            return {
                title: clean(document.title),
                heading: clean(heading ? heading.innerText : ''),
                detected_pattern: detected,
                expected_pattern: expectedPattern,
            };
        }""",
        expected_pattern,
    )
    return identity


def _path_matches(expected_url: str, actual_url: str) -> bool:
    expected = urlparse(expected_url)
    actual = urlparse(actual_url)
    return actual.path.rstrip("/") == expected.path.rstrip("/") or actual.path.rstrip("/").endswith(expected.path.rstrip("/"))


def _chunk_name(start: date | None, end: date | None) -> str:
    if start and end and start.year == end.year and start.month == end.month:
        return f"{start.year:04d}-{start.month:02d}"
    if start and end:
        return f"{start.isoformat()}_{end.isoformat()}"
    return f"snapshot_{now_iso().replace(':', '-')}"


def _target_chunk_name(target: FilterPaginatedTarget, start: date | None, end: date | None) -> str:
    return f"{safe_name(target.target_id or target.name)}_{_chunk_name(start, end)}"


async def inspect_filter_paginated_table(page: Page) -> dict[str, Any]:
    tables = await read_visible_tables(page)
    return {
        "pattern": "filter_paginated_table",
        "filters": await read_filters(page),
        "pagination": await read_pagination(page),
        "tables": [{"selector": t["selector"], "headers": t["headers"], "rows_count": t["rows_count"]} for t in tables],
        "read_only": True,
    }


async def extract_current_table_page(page: Page, *, page_number: int) -> list[dict[str, Any]]:
    tables = await read_visible_tables(page)
    if not tables:
        return []
    table = max(tables, key=lambda item: item.get("rows_count", 0))
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(table.get("rows", []), start=1):
        if not any(str(value).strip() for value in row.values()):
            continue
        enriched = dict(row)
        enriched["_source_page"] = page_number
        enriched["_source_row_index"] = index
        rows.append(enriched)
    return rows


async def collect_paginated_rows(page: Page, *, max_pages: int | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {
        "pages": [],
        "termination_reason": None,
        "max_pages": max_pages,
    }
    page_number = 1
    while True:
        if max_pages is not None and page_number > max_pages:
            diagnostics["termination_reason"] = "explicit_limit_pages_reached"
            diagnostics["pages_walked"] = max_pages
            diagnostics["rows_before_dedupe"] = len(rows)
            break
        await wait_until_loaded(page)
        snapshot_before = await pagination_snapshot(page)
        visible_rows = await extract_current_table_page(page, page_number=page_number)
        rows.extend(visible_rows)
        advanced, reason = await go_next_page(page)
        diagnostics["pages"].append(
            {
                "page_number": page_number,
                "rows_on_page": len(visible_rows),
                "pagination_before_next": snapshot_before,
                "advance_result": advanced,
                "advance_reason": reason,
            }
        )
        if not advanced:
            diagnostics["termination_reason"] = reason
            diagnostics["pages_walked"] = page_number
            diagnostics["rows_before_dedupe"] = len(rows)
            break
        page_number += 1
    return rows, diagnostics


async def extract_filter_paginated_table(
    page: Page,
    settings: Settings,
    target: FilterPaginatedTarget,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    max_pages: int | None = None,
    assisted: bool = False,
    optimize_page_size: bool = False,
    package_root: Path | None = None,
) -> dict[str, Any]:
    """Extract one filter+paginated table page in READ-ONLY mode.

    The extractor only clicks safe filtering/search controls and pagination next buttons.
    Dangerous actions are registered but never executed.
    """
    package_root = package_root or settings.data_dir / "export" / "asno_data_package"
    chunk_name = _target_chunk_name(target, date_from, date_to)
    summary: dict[str, Any] = {
        "status": "pending",
        "pattern": target.pattern,
        "extractor": "generic_filter_paginated_table_extractor",
        "target_id": target.target_id,
        "module": target.module,
        "package_module": target.package_module or target.module,
        "name": target.name,
        "url": target.url,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "row_count": 0,
        "outputs": {},
        "diagnostics": {},
        "errors": [],
    }
    try:
        await page.goto(target.url, wait_until="domcontentloaded")
        await wait_until_loaded(page)
        identity = await detect_page_identity(page, target.pattern)
        identity["expected_url"] = target.url
        identity["actual_url"] = page.url
        if not _path_matches(target.url, page.url):
            raise RuntimeError(f"Target URL mismatch: expected={target.url} actual={page.url}")
        if identity.get("detected_pattern") != "unknown" and identity.get("detected_pattern") not in {target.pattern, "filter_paginated_table", "paginated_table"}:
            raise RuntimeError(f"Target pattern mismatch: expected={target.pattern} detected={identity.get('detected_pattern')}")
        dangerous = await detect_dangerous_actions(page)
        summary["diagnostics"]["target_validation"] = identity
        summary["diagnostics"]["dangerous_actions_detected"] = dangerous
        if dangerous and not target.read_only_safe:
            summary["diagnostics"]["read_only_warning"] = "dangerous actions visible; extractor will avoid them"

        filters_before = await read_filters(page)
        pagination_before = await read_pagination(page)
        date_result = await fill_date_range_if_available(page, date_from, date_to)
        safe_submit = {"clicked": False, "reason": "not_needed"}
        if date_result.get("applied"):
            safe_submit = await click_safe_filter_button_if_present(page)
        page_size_result = {"changed": False, "reason": "not_requested"}
        if optimize_page_size:
            page_size_result = await select_largest_safe_page_size(page)
            if page_size_result.get("changed"):
                await wait_until_loaded(page)
        await page.wait_for_function(
            """() => Array.from(document.querySelectorAll('table')).some(t => {
                const visible = !!(t.offsetWidth || t.offsetHeight || t.getClientRects().length);
                const isCalendar = !!t.closest('.datetimepicker, .datepicker, #ui-datepicker-div');
                return visible && !isCalendar;
            })""",
            timeout=30_000,
        )
        identity_after_load = await detect_page_identity(page, target.pattern)
        identity_after_load["expected_url"] = target.url
        identity_after_load["actual_url"] = page.url
        rows, pagination_diagnostics = await collect_paginated_rows(page, max_pages=max_pages)
        rows_before_dedupe = len(rows)
        rows = dedupe_rows(rows, source_url=page.url, module=target.package_module or target.module)
        pages_detected_values = [
            item.get("pagination_before_next", {}).get("estimated_pages")
            for item in pagination_diagnostics.get("pages", [])
            if item.get("pagination_before_next", {}).get("estimated_pages")
        ]
        pages_detected = max(pages_detected_values) if pages_detected_values else None
        diagnostics = {
            "filters_before": filters_before,
            "pagination_before": pagination_before,
            "date_filter": date_result,
            "safe_submit": safe_submit,
            "page_size": page_size_result,
            "pagination": pagination_diagnostics,
            "counts": {
                "pages_detected": pages_detected,
                "pages_walked": pagination_diagnostics.get("pages_walked"),
                "visible_rows_total": rows_before_dedupe,
                "rows_before_dedupe": rows_before_dedupe,
                "rows_after_dedupe": len(rows),
                "unique_ids": len({row.get("_row_id") for row in rows}),
            },
            "dangerous_actions_detected": dangerous,
            "target_validation": {**identity, "after_load": identity_after_load},
        }
        outputs = write_package_chunk(
            package_root,
            module=target.package_module or target.module,
            source_url=page.url,
            chunk_name=chunk_name,
            records=rows,
            html=await page.content(),
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            diagnostics=diagnostics,
        )
        standard_summary = {**summary, "status": "success", "row_count": len(rows), "diagnostics": diagnostics, "url": page.url}
        standard_outputs = write_standard_outputs(
            settings.data_dir,
            module=target.package_module or target.module,
            chunk_name=chunk_name,
            records=rows,
            html=await page.content(),
            summary=standard_summary,
        )
        debug_path = settings.debug_dir / "generic_filter_paginated_table" / f"{safe_name(target.module)}_{safe_name(target.name)}_{safe_name(chunk_name)}.json"
        write_json(debug_path, {**summary, "diagnostics": diagnostics, "row_count": len(rows), "outputs": {**outputs, **standard_outputs}})
        summary.update(
            {
                "status": "success",
                "row_count": len(rows),
                "outputs": {**outputs, **standard_outputs, "debug": str(debug_path)},
                "diagnostics": diagnostics,
            }
        )
        return summary
    except Exception as exc:
        logging.exception("Generic filter_paginated_table extraction failed for %s", target.url)
        summary["status"] = "failed"
        summary["errors"].append(repr(exc))
        try:
            evidence = await save_evidence(page, settings, f"generic_filter_paginated_error_{target.module}_{target.name}")
            summary["outputs"]["evidence_html"] = evidence.get("html")
            summary["outputs"]["evidence_screenshot"] = evidence.get("screenshot")
        except Exception:
            pass
        if assisted:
            assisted_result = await assisted_pause(
                page,
                settings,
                safe_name(target.module),
                target.name,
                "No pude extraer esta tabla paginada genérica. Revisá el navegador abierto y mostrámelo si hace falta.",
            )
            summary["assisted"] = {
                "decision": assisted_result.decision,
                "event_path": str(assisted_result.event_path),
            }
        return summary
