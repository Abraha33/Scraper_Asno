from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from ..storage import now_iso, safe_name, stable_id, write_json
from ..storage import read_json


DANGEROUS_ACTION_RE = r"crear|editar|guardar|actualizar|eliminar|borrar|anular|confirmar|pagar|cerrar caja|facturar|enviar|importar|sincronizar|procesar|aprobar"


async def wait_until_loaded(page: Page, timeout: int = 30_000) -> None:
    """Wait for real page/table stability without relying on blind sleeps."""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    except Exception:
        pass
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    for selector in (
        ".dataTables_processing",
        ".blockUI",
        ".loading",
        ".loader",
        ".spinner",
        "[aria-busy='true']",
    ):
        try:
            await page.locator(selector).first.wait_for(state="hidden", timeout=3_000)
        except Exception:
            pass


async def detect_dangerous_actions(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        f"""() => {{
            const clean = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const css = (el) => {{
                if (el.id) return `#${{CSS.escape(el.id)}}`;
                if (el.getAttribute('name')) return `${{el.tagName.toLowerCase()}}[name="${{CSS.escape(el.getAttribute('name'))}}"]`;
                return el.tagName.toLowerCase();
            }};
            const dangerous = new RegExp({DANGEROUS_ACTION_RE!r}, 'i');
            return Array.from(document.querySelectorAll('a,button,input[type=button],input[type=submit]'))
                .filter(visible)
                .map(el => ({{
                    selector: css(el),
                    label: clean(el.innerText || el.value || el.textContent),
                    href: el.href || el.getAttribute('href'),
                    tag: el.tagName.toLowerCase(),
                    disabled: !!el.disabled || /disabled/i.test(`${{el.className || ''}} ${{el.parentElement?.className || ''}}`),
                }}))
                .filter(item => dangerous.test(`${{item.label}} ${{item.href || ''}}`));
        }}"""
    )


async def select_largest_safe_page_size(page: Page) -> dict[str, Any]:
    """Select the largest DataTables page size unless it is 'all' or absurdly large."""
    return await page.evaluate(
        """() => {
            const clean = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const select = Array.from(document.querySelectorAll('.dataTables_length select, select[name$="_length"]'))
                .find(el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length));
            if (!select) return {changed: false, reason: 'page_size_select_missing'};
            const options = Array.from(select.options || [])
                .map(o => ({value: o.value, text: clean(o.innerText || o.value), numeric: Number(o.value)}))
                .filter(o => Number.isFinite(o.numeric) && o.numeric > 0 && o.numeric <= 500);
            if (!options.length) return {changed: false, reason: 'no_safe_numeric_page_size'};
            options.sort((a, b) => b.numeric - a.numeric);
            const chosen = options[0];
            if (select.value === chosen.value) return {changed: false, reason: 'already_largest_safe', value: chosen.value, text: chosen.text};
            select.value = chosen.value;
            select.dispatchEvent(new Event('change', {bubbles: true}));
            if (window.jQuery) window.jQuery(select).trigger('change');
            return {changed: true, value: chosen.value, text: chosen.text};
        }"""
    )


async def detect_date_inputs(page: Page) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
            const clean = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const css = (el) => {
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.getAttribute('name')) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.getAttribute('name'))}"]`;
                return el.tagName.toLowerCase();
            };
            const labelFor = (el) => {
                if (el.id) {
                    const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                    if (label) return clean(label.innerText);
                }
                return clean(el.closest('label')?.innerText || el.placeholder || el.name || el.id);
            };
            const inputs = Array.from(document.querySelectorAll('input,select'))
                .filter(visible)
                .map(el => ({
                    selector: css(el),
                    id: el.id || null,
                    name: el.getAttribute('name'),
                    type: el.getAttribute('type') || el.tagName.toLowerCase(),
                    label: labelFor(el),
                    value: el.value || '',
                    options: el.tagName.toLowerCase() === 'select' ? Array.from(el.options || []).map(o => ({value: o.value, text: clean(o.innerText || o.value)})) : [],
                }));
            const dateLike = inputs.filter(x => /date|fecha|desde|hasta|inicio|final|start|end/i.test(`${x.selector} ${x.id || ''} ${x.name || ''} ${x.type || ''} ${x.label || ''}`));
            const start = dateLike.find(x => /start|inicio|desde|from|initial|inicial/i.test(`${x.selector} ${x.id || ''} ${x.name || ''} ${x.label || ''}`)) || dateLike[0] || null;
            const end = dateLike.find(x => /end|final|hasta|to|fin/i.test(`${x.selector} ${x.id || ''} ${x.name || ''} ${x.label || ''}`)) || dateLike[1] || null;
            const rangeSelect = inputs.find(x => x.options && x.options.some(o => /rango/i.test(`${o.text} ${o.value}`))) || null;
            return {date_like: dateLike, start, end, range_select: rangeSelect};
        }"""
    )


def format_for_input(value: date, input_info: dict[str, Any] | None) -> str:
    if input_info and str(input_info.get("type") or "").lower() == "date":
        return value.isoformat()
    return value.strftime("%d/%m/%Y")


async def fill_date_range_if_available(page: Page, start: date | None, end: date | None) -> dict[str, Any]:
    detected = await detect_date_inputs(page)
    if not start or not end or not detected.get("start") or not detected.get("end"):
        return {"applied": False, "reason": "date_range_not_requested_or_not_detected", "detected": detected}
    range_select = detected.get("range_select")
    if range_select:
        await page.evaluate(
            """(selector) => {
                const select = document.querySelector(selector);
                if (!select) return;
                const option = Array.from(select.options || []).find(o => /rango/i.test(`${o.textContent || ''} ${o.value || ''}`));
                if (!option) return;
                select.value = option.value;
                select.dispatchEvent(new Event('change', {bubbles: true}));
                if (window.jQuery) window.jQuery(select).trigger('change');
            }""",
            range_select["selector"],
        )
        await wait_until_loaded(page, timeout=10_000)
    start_value = format_for_input(start, detected["start"])
    end_value = format_for_input(end, detected["end"])
    await page.evaluate(
        """({startSelector, endSelector, startValue, endValue}) => {
            const setValue = (selector, value) => {
                const el = document.querySelector(selector);
                if (!el) return false;
                el.value = value;
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.dispatchEvent(new Event('blur', {bubbles: true}));
                if (window.jQuery) window.jQuery(el).trigger('change').trigger('blur');
                return true;
            };
            setValue(startSelector, startValue);
            setValue(endSelector, endValue);
            if (window.jQuery) window.jQuery('.datetimepicker, .datepicker, #ui-datepicker-div').hide();
            const active = document.activeElement;
            if (active && active.blur) active.blur();
        }""",
        {
            "startSelector": detected["start"]["selector"],
            "endSelector": detected["end"]["selector"],
            "startValue": start_value,
            "endValue": end_value,
        },
    )
    return {
        "applied": True,
        "start_selector": detected["start"]["selector"],
        "end_selector": detected["end"]["selector"],
        "start_value": start_value,
        "end_value": end_value,
        "range_selector": range_select.get("selector") if range_select else None,
        "detected": detected,
    }


async def click_safe_filter_button_if_present(page: Page) -> dict[str, Any]:
    """Click only non-dangerous query/filter/search buttons; never save/delete/etc."""
    result = await page.evaluate(
        f"""() => {{
            const clean = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const css = (el) => {{
                if (el.id) return `#${{CSS.escape(el.id)}}`;
                if (el.getAttribute('name')) return `${{el.tagName.toLowerCase()}}[name="${{CSS.escape(el.getAttribute('name'))}}"]`;
                return null;
            }};
            const dangerous = new RegExp({DANGEROUS_ACTION_RE!r}, 'i');
            const safe = /buscar|filtrar|consultar|generar|search|filter|query/i;
            const candidates = Array.from(document.querySelectorAll('button,input[type=button],input[type=submit],a.btn'))
                .filter(visible)
                .map(el => ({{
                    selector: css(el),
                    label: clean(el.innerText || el.value || el.textContent),
                    disabled: !!el.disabled || /disabled/i.test(`${{el.className || ''}} ${{el.parentElement?.className || ''}}`),
                }}))
                .filter(item => item.selector && safe.test(item.label) && !dangerous.test(item.label) && !item.disabled);
            return candidates[0] || null;
        }}"""
    )
    if not result:
        return {"clicked": False, "reason": "safe_filter_button_missing"}
    before = await pagination_state(page)
    await page.locator(result["selector"]).first.click()
    await wait_until_loaded(page)
    try:
        await page.wait_for_function(
            """(before) => {
                const info = document.querySelector('.dataTables_info, .pagination');
                const table = Array.from(document.querySelectorAll('table')).find(t => !!(t.offsetWidth || t.offsetHeight || t.getClientRects().length));
                return table && (!info || (info.innerText || '') !== before || table.querySelectorAll('tbody tr, tr').length > 0);
            }""",
            before,
            timeout=15_000,
        )
    except Exception:
        pass
    return {"clicked": True, **result}

async def read_visible_tables(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => {
            const clean = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const isCalendar = (table) => !!table.closest('.datetimepicker, .datepicker, #ui-datepicker-div');
            return Array.from(document.querySelectorAll('table')).filter(table => visible(table) && !isCalendar(table)).map((table, index) => {
                let headers = Array.from(table.querySelectorAll('thead th')).map(th => clean(th.innerText)).filter(Boolean);
                if (!headers.length) headers = Array.from(table.querySelectorAll('tr:first-child th, tr:first-child td')).map(td => clean(td.innerText)).filter(Boolean);
                const rows = Array.from(table.querySelectorAll('tbody tr, tr')).map(tr => {
                    const cells = Array.from(tr.querySelectorAll('td')).map(td => clean(td.innerText));
                    if (!cells.length) return null;
                    const row = {};
                    cells.forEach((cell, i) => row[headers[i] || `col_${i+1}`] = cell);
                    return row;
                }).filter(Boolean);
                return {
                    index,
                    selector: table.id ? `#${CSS.escape(table.id)}` : 'table',
                    headers,
                    rows_count: rows.length,
                    rows,
                };
            });
        }"""
    )


async def read_filters(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => {
            const clean = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const css = (el) => {
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.name) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.name)}"]`;
                return el.tagName.toLowerCase();
            };
            const labelFor = (el) => {
                if (el.id) {
                    const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                    if (label) return clean(label.innerText);
                }
                const label = el.closest('label');
                if (label) return clean(label.innerText);
                return clean(el.placeholder || el.name || el.id);
            };
            return Array.from(document.querySelectorAll('input,select,textarea')).filter(visible).map(el => ({
                selector: css(el),
                label: labelFor(el),
                tag: el.tagName.toLowerCase(),
                type: el.getAttribute('type') || el.tagName.toLowerCase(),
                name: el.getAttribute('name'),
                id: el.id || null,
                value: /password|secret|token/i.test(`${el.type} ${el.name} ${el.id}`) ? '[REDACTED]' : el.value,
                options: el.tagName.toLowerCase() === 'select' ? Array.from(el.options || []).map(o => clean(o.innerText || o.value)).filter(Boolean) : [],
            }));
        }"""
    )


async def read_pagination(page: Page) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
            const clean = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const containers = Array.from(document.querySelectorAll('.dataTables_paginate, .pagination')).filter(visible);
            const length = Array.from(document.querySelectorAll('.dataTables_length select, select[name$="_length"]')).find(visible);
            const info = document.querySelector('.dataTables_info');
            return {
                has_pagination: containers.length > 0 || !!length,
                containers: containers.map(el => clean(el.innerText)),
                page_size: length ? length.value : null,
                info: info ? clean(info.innerText) : null,
            };
        }"""
    )


async def pagination_snapshot(page: Page) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
            const text = (el) => (el?.textContent || el?.innerText || '').replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
            const nextCandidates = [
                'a.paginate_button.next',
                'li.next a',
                'button.next',
                '.pagination-next a',
                'a[aria-controls][data-dt-idx]:last-child',
            ];
            let next = null;
            for (const selector of nextCandidates) {
                next = document.querySelector(selector);
                if (next && visible(next)) break;
            }
            if (!next || !visible(next)) {
                next = Array.from(document.querySelectorAll('a,button')).find((el) => visible(el) && /siguiente|next/i.test(text(el)));
            }
            const info = document.querySelector('.dataTables_info');
            const paginate = document.querySelector('.dataTables_paginate, .pagination');
            const active = document.querySelector('.dataTables_paginate .current, .pagination .active');
            const infoText = text(info);
            const numbers = (infoText.match(/[\\d.,]+/g) || []).map(x => Number(x.replace(/[.,]/g, ''))).filter(Number.isFinite);
            const totalRecords = numbers.length ? numbers[numbers.length - 1] : null;
            const visibleRows = Array.from(document.querySelectorAll('table')).filter(t => !!(t.offsetWidth || t.offsetHeight || t.getClientRects().length) && !t.closest('.datetimepicker, .datepicker, #ui-datepicker-div'))[0]?.querySelectorAll('tbody tr').length || null;
            return {
                info_text: infoText,
                total_records_reported: totalRecords,
                visible_rows_current_page: visibleRows,
                estimated_pages: totalRecords && visibleRows ? Math.ceil(totalRecords / visibleRows) : null,
                pagination_text: text(paginate),
                active_page_text: text(active),
                next_selector: next ? (next.id ? `#${CSS.escape(next.id)}` : (next.getAttribute('aria-controls') ? `a[aria-controls="${CSS.escape(next.getAttribute('aria-controls'))}"].next` : null)) : null,
                next_exists: !!next,
                next_visible: visible(next),
                next_disabled: next ? /disabled/i.test(`${next.className || ''} ${next.parentElement?.className || ''}`) : null,
            };
        }"""
    )


async def pagination_state(page: Page) -> str:
    try:
        return await page.locator(".dataTables_info, .pagination").first.inner_text(timeout=2_000)
    except Exception:
        return ""


async def go_next_page(page: Page) -> tuple[bool, str]:
    snapshot = await pagination_snapshot(page)
    if not snapshot.get("next_exists") or not snapshot.get("next_visible"):
        return False, "next_button_missing_or_hidden"
    if snapshot.get("next_disabled"):
        return False, "next_button_disabled"
    before = await pagination_state(page)
    selectors = [
        "a.paginate_button.next",
        "li.next a",
        "button.next",
        ".pagination-next a",
    ]
    clicked = False
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible(timeout=500):
                class_name = await locator.get_attribute("class") or ""
                parent_class = await locator.evaluate("(el) => el.parentElement ? el.parentElement.className : ''")
                if "disabled" in f"{class_name} {parent_class}".lower():
                    return False, "next_button_disabled"
                await locator.click()
                clicked = True
                break
        except Exception:
            continue
    if not clicked:
        candidates = page.get_by_text("Siguiente", exact=False)
        try:
            if await candidates.count():
                await candidates.first.click()
                clicked = True
        except Exception:
            pass
    if not clicked:
        return False, "next_button_click_failed"
    await wait_until_loaded(page)
    try:
        await page.wait_for_function(
            """(before) => {
                const el = document.querySelector('.dataTables_info, .pagination');
                return !el || (el.innerText || '') !== before;
            }""",
            before,
            timeout=10_000,
        )
    except Exception:
        pass
    after = await pagination_state(page)
    if before and after == before:
        return False, "clicked_next_but_info_unchanged"
    return True, "advanced"


def dedupe_rows(rows: list[dict[str, Any]], *, source_url: str, module: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    clean: list[dict[str, Any]] = []
    for row in rows:
        fingerprint = stable_id(source_url, module, *[str(value) for key, value in sorted(row.items()) if key != "_row_id"])
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        row = dict(row)
        row["_row_id"] = fingerprint
        clean.append(row)
    return clean


def package_paths(package_root: Path, module: str, chunk_name: str) -> dict[str, Path]:
    module_slug = safe_name(module.lower())
    chunk_slug = safe_name(chunk_name)
    return {
        "module_dir": package_root / "modules" / module_slug,
        "chunk": package_root / "modules" / module_slug / "chunks" / f"{chunk_slug}.json",
        "raw": package_root / "modules" / module_slug / "raw" / f"{chunk_slug}.html",
        "metadata": package_root / "modules" / module_slug / "metadata.json",
        "index": package_root / "modules" / module_slug / "index.json",
        "manifest": package_root / "manifest.json",
        "root_index": package_root / "index.json",
    }


def standard_output_paths(data_dir: Path, module: str, chunk_name: str) -> dict[str, Path]:
    module_slug = safe_name(module.lower())
    chunk_slug = safe_name(chunk_name)
    return {
        "raw_html": data_dir / "raw" / "generic" / module_slug / chunk_slug / "raw.html",
        "json": data_dir / "processed" / "generic" / module_slug / chunk_slug / f"{module_slug}.json",
        "xlsx": data_dir / "processed" / "generic" / module_slug / chunk_slug / f"{module_slug}.xlsx",
        "log": data_dir / "logs" / f"generic_{module_slug}_{chunk_slug}.log",
    }


def write_xlsx(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pandas as pd

        pd.DataFrame(records).to_excel(path, index=False)
        return
    except Exception:
        pass
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "records"
    headers = sorted({key for row in records for key in row.keys()})
    sheet.append(headers)
    for row in records:
        sheet.append([row.get(header) for header in headers])
    workbook.save(path)


def write_standard_outputs(
    data_dir: Path,
    *,
    module: str,
    chunk_name: str,
    records: list[dict[str, Any]],
    html: str,
    summary: dict[str, Any],
) -> dict[str, str]:
    paths = standard_output_paths(data_dir, module, chunk_name)
    paths["raw_html"].parent.mkdir(parents=True, exist_ok=True)
    paths["raw_html"].write_text(html, encoding="utf-8")
    write_json(paths["json"], {**summary, "records": records, "records_count": len(records)})
    write_xlsx(paths["xlsx"], records)
    counts = summary.get("diagnostics", {}).get("counts", {})
    pagination = summary.get("diagnostics", {}).get("pagination", {})
    validation = summary.get("diagnostics", {}).get("target_validation", {})
    lines = [
        f"target_id={summary.get('target_id')}",
        f"module={module}",
        f"status={summary.get('status')}",
        f"expected_url={validation.get('expected_url')}",
        f"actual_url={validation.get('actual_url') or summary.get('url')}",
        f"title={validation.get('title')}",
        f"heading={validation.get('heading')}",
        f"expected_pattern={validation.get('expected_pattern')}",
        f"detected_pattern={validation.get('detected_pattern')}",
        f"date_from={summary.get('date_from')}",
        f"date_to={summary.get('date_to')}",
        f"pages_detected={counts.get('pages_detected')}",
        f"pages_walked={pagination.get('pages_walked')}",
        f"visible_rows_total={counts.get('visible_rows_total')}",
        f"rows_before_dedupe={counts.get('rows_before_dedupe')}",
        f"rows_after_dedupe={counts.get('rows_after_dedupe')}",
        f"unique_ids={counts.get('unique_ids')}",
        f"termination_reason={pagination.get('termination_reason')}",
    ]
    paths["log"].parent.mkdir(parents=True, exist_ok=True)
    paths["log"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def write_package_chunk(
    package_root: Path,
    *,
    module: str,
    source_url: str,
    chunk_name: str,
    records: list[dict[str, Any]],
    html: str,
    date_from: str | None = None,
    date_to: str | None = None,
    pattern: str = "filter_paginated_table",
    strategy: str = "generic_filter_paginated_table_extractor",
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, str]:
    paths = package_paths(package_root, module, chunk_name)
    for key in ("chunk", "raw", "metadata", "index", "manifest", "root_index"):
        paths[key].parent.mkdir(parents=True, exist_ok=True)
    previous_payload = read_json(paths["chunk"], {}) if paths["chunk"].exists() else {}
    previous_count = int(previous_payload.get("records_count") or 0)
    payload = chunk_payload(module, source_url, records, date_from=date_from, date_to=date_to)
    payload["pattern_used"] = pattern
    payload["strategy"] = strategy
    payload["diagnostics"] = diagnostics or {}
    paths["chunk"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["raw"].write_text(html, encoding="utf-8")
    metadata = {
        "module_name": module,
        "source_urls": [source_url],
        "pattern_used": pattern,
        "extraction_strategy": strategy,
        "date_range": {"from": date_from, "to": date_to},
        "chunks": [str(paths["chunk"])],
        "rows": len(records),
        "errors": [],
        "raw_files": [str(paths["raw"])],
        "processed_files": [str(paths["chunk"])],
        "updated_at": now_iso(),
    }
    write_json(paths["metadata"], metadata)
    write_json(paths["index"], {"module": module, "chunks": [str(paths["chunk"])], "rows": len(records), "updated_at": now_iso()})
    root_index = read_json(paths["root_index"], {})
    root_modules = dict(root_index.get("modules") or {})
    root_modules[module] = str(paths["index"])
    root_files = list(dict.fromkeys((root_index.get("files") or []) + [str(paths["chunk"]), str(paths["raw"])]))
    counts = dict(root_index.get("counts_summary") or {})
    counts[module] = max(0, int(counts.get(module) or 0) - previous_count) + len(records)
    manifest = read_json(paths["manifest"], {})
    modules = sorted(set((manifest.get("modules_extracted") or []) + [module]))
    write_json(
        paths["manifest"],
        {
            "system_name": manifest.get("system_name") or "ASNO/Wappsi",
            "extraction_date": now_iso(),
            "historical_range": {"from": date_from, "to": date_to},
            "modules_extracted": modules,
            "files_count": len(root_files),
            "records_count": sum(int(value or 0) for value in counts.values()),
            "errors": manifest.get("errors") or [],
            "extractor_version": "generic-filter-paginated-v1",
        },
    )
    write_json(
        paths["root_index"],
        {
            "modules": root_modules,
            "files": root_files,
            "relationships": root_index.get("relationships") or [],
            "schemas": root_index.get("schemas") or [],
            "counts_summary": counts,
        },
    )
    return {key: str(value) for key, value in paths.items()}


def chunk_payload(module: str, source_url: str, records: list[dict[str, Any]], date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    from datetime import datetime

    return {
        "module": module,
        "source_url": source_url,
        "date_from": date_from,
        "date_to": date_to,
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "records_count": len(records),
        "records": records,
    }
