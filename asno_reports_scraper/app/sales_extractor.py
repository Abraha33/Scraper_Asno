from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from playwright.async_api import Page

from .assisted import assisted_pause
from .config import Settings
from .human_learning import enter_learning_mode, load_learned_recipe, replay_recipe
from .pagination import wait_until_loaded
from .report_configs import ReportConfig, load_report_config
from .storage import avoid_duplicates, now_iso, save_evidence, stable_id, write_json


def chunk_key(start: date) -> str:
    return f"{start.year:04d}-{start.month:02d}"


def absolute_report_url(settings: Settings, config: ReportConfig) -> str:
    base = (settings.reports_url or "").split("/admin/reports")[0].rstrip("/")
    if not base:
        base = settings.asno_url.split("/admin/auth/login")[0].split("/login")[0].rstrip("/")
    if config.url_path.startswith("http"):
        return config.url_path
    return f"{base}{config.url_path}"


def format_report_date(value: date, config: ReportConfig) -> str:
    return value.strftime(config.date_format)


async def sales_filter_state(page: Page, config: ReportConfig) -> dict[str, Any]:
    """Capture the exact client-side filter state that ASNO will submit."""
    return await page.evaluate(
        """(config) => {
            const text = (el) => (el?.textContent || '').replace(/\\s+/g, ' ').trim();
            const valueOf = (selector) => document.querySelector(selector)?.value ?? null;
            const selectedOption = (selector) => {
                const el = document.querySelector(selector);
                if (!el) return null;
                const option = el.options?.[el.selectedIndex];
                return {
                    selector,
                    value: el.value ?? null,
                    text: text(option),
                    exists: true,
                };
            };
            const lengthSelect = document.querySelector("select[name$='_length'], .dataTables_length select");
            const info = document.querySelector('.dataTables_info');
            const table = Array.from(document.querySelectorAll('table')).find((item) => {
                const visible = !!(item.offsetWidth || item.offsetHeight || item.getClientRects().length);
                const isCalendar = !!item.closest('.datetimepicker, .datepicker, #ui-datepicker-div');
                return visible && !isCalendar;
            });
            return {
                url: window.location.href,
                date_from_selector: config.date_from_selector,
                date_to_selector: config.date_to_selector,
                date_from_value: valueOf(config.date_from_selector),
                date_to_value: valueOf(config.date_to_selector),
                range_selector: config.range_selector,
                range_selected: config.range_selector ? selectedOption(config.range_selector) : null,
                range_is_rango_fechas: config.range_selector ? /rango/i.test(`${selectedOption(config.range_selector)?.text || ''} ${selectedOption(config.range_selector)?.value || ''}`) : null,
                page_size_value: lengthSelect?.value ?? null,
                page_size_text: text(lengthSelect?.selectedOptions?.[0]),
                datatables_info: text(info),
                visible_table_rows: table ? table.querySelectorAll('tbody tr').length : 0,
            };
        }""",
        {
            "date_from_selector": config.date_from_selector,
            "date_to_selector": config.date_to_selector,
            "range_selector": config.range_selector,
        },
    )


async def sales_pagination_snapshot(page: Page, config: ReportConfig) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
            const text = (el) => (el?.textContent || '').replace(/\\s+/g, ' ').trim();
            const info = document.querySelector('.dataTables_info');
            const nextCandidates = [
                'a.paginate_button.next',
                'li.next a',
                'button.next',
                'a[aria-controls][data-dt-idx]:last-child',
            ];
            let next = null;
            for (const selector of nextCandidates) {
                next = document.querySelector(selector);
                if (next) break;
            }
            if (!next) {
                next = Array.from(document.querySelectorAll('a,button')).find((el) => /siguiente|next/i.test(text(el)));
            }
            const paginate = document.querySelector('.dataTables_paginate, .pagination');
            const active = document.querySelector('.dataTables_paginate .current, .pagination .active');
            const numericButtons = Array.from(document.querySelectorAll('.dataTables_paginate a.paginate_button, .pagination a, .pagination button'))
                .map((el) => text(el))
                .filter(Boolean);
            const infoText = text(info);
            const totalMatch = infoText.match(/(?:total de|of)\\s+([\\d.,]+)/i);
            const numbers = Array.from(infoText.matchAll(/[\\d.,]+/g)).map((match) => Number(match[0].replace(/[.,]/g, '')));
            return {
                info_text: infoText,
                total_records_reported: totalMatch ? Number(totalMatch[1].replace(/[.,]/g, '')) : (numbers.length ? numbers[numbers.length - 1] : null),
                next_exists: !!next,
                next_visible: next ? !!(next.offsetWidth || next.offsetHeight || next.getClientRects().length) : false,
                next_class: next?.className || null,
                next_parent_class: next?.parentElement?.className || null,
                next_disabled: next ? /disabled/i.test(`${next.className || ''} ${next.parentElement?.className || ''}`) : null,
                active_page_text: text(active),
                pagination_text: text(paginate),
                numeric_buttons: numericButtons,
            };
        }"""
    )


async def _set_date_input(page: Page, selector: str, value: str) -> None:
    locator = page.locator(selector).first
    await locator.wait_for(state="attached", timeout=20_000)
    await locator.evaluate(
        """(el, value) => {
            el.removeAttribute('readonly');
            el.removeAttribute('disabled');
            el.value = value;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        value,
    )


async def select_date_range_if_available(page: Page, config: ReportConfig) -> None:
    if not config.range_selector:
        return
    locator = page.locator(config.range_selector).first
    if not await locator.count():
        return
    try:
        await locator.wait_for(state="attached", timeout=5_000)
        changed_with_js = await locator.evaluate(
            """(el, wanted) => {
                const options = Array.from(el.options || []);
                const option = options.find((item) => `${item.textContent || ''} ${item.value || ''}`.toLowerCase().includes((wanted || '').toLowerCase()));
                if (!option) return false;
                el.value = option.value;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                if (window.jQuery) {
                    const $el = window.jQuery(el);
                    if ($el.select2) {
                        $el.select2('val', option.value).trigger('change');
                    } else {
                        $el.trigger('change');
                    }
                }
                return true;
            }""",
            config.range_value_contains or "Rango",
        )
        if changed_with_js:
            await wait_until_loaded(page)
            return
        if config.range_value_contains:
            options = await locator.locator("option").all()
            for option in options:
                text = " ".join((await option.inner_text()).split())
                value = await option.get_attribute("value")
                if config.range_value_contains.lower() in f"{text} {value}".lower():
                    await locator.select_option(value=value)
                    await wait_until_loaded(page)
                    return
        await locator.select_option(index=await locator.locator("option").count() - 1)
        await wait_until_loaded(page)
    except Exception:
        logging.info("Date range selector was present but could not be changed: %s", config.range_selector)


async def apply_sales_date_range(page: Page, config: ReportConfig, start: date, end: date) -> None:
    await select_date_range_if_available(page, config)
    await _set_date_input(page, config.date_from_selector, format_report_date(start, config))
    await _set_date_input(page, config.date_to_selector, format_report_date(end, config))
    await page.evaluate(
        """() => {
            if (window.jQuery) {
                window.jQuery('.datetimepicker, .datepicker, #ui-datepicker-div').hide();
                window.jQuery('#start_date_dh, #end_date_dh').trigger('change').trigger('blur');
            }
            const active = document.activeElement;
            if (active && active.blur) active.blur();
        }"""
    )


async def click_sales_submit(page: Page) -> str:
    config = load_report_config("sales")
    selectors = tuple(
        selector
        for selector in (
            config.submit_selector,
            "#submit_filter",
            "button#submit_filter",
            "#submit_report",
            "input[name='submit_report']",
            "button:has-text('Consultar')",
            "button:has-text('Generar')",
            "button:has-text('Guardar')",
            "input[type='submit']:visible",
            "button[type='submit']:visible",
            "a:has-text('Consultar')",
            "a:has-text('Generar')",
        )
        if selector
    )
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if not await locator.count():
                continue
            await locator.wait_for(state="attached", timeout=3_000)
            await locator.evaluate("(el) => { el.removeAttribute('disabled'); }")
            if await locator.is_visible(timeout=1_000):
                await locator.click()
            else:
                await locator.evaluate("(el) => el.click()")
            await wait_for_sales_table(page)
            return selector
        except Exception:
            continue
    raise RuntimeError("No se encontró botón usable para ejecutar Informe de Ventas")


async def wait_for_sales_table(page: Page) -> None:
    await wait_until_loaded(page)
    await page.wait_for_function(
        """() => {
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const isCalendar = (table) => !!table.closest('.datetimepicker, .datepicker, #ui-datepicker-div');
            const salesLike = (table) => /Fecha|Número|Numero|Total|Subtotal|Pagado|Saldo/i.test(table.innerText || '');
            return Array.from(document.querySelectorAll('table')).some((table) => visible(table) && !isCalendar(table) && salesLike(table));
        }""",
        timeout=45_000,
    )
    try:
        await page.locator(".dataTables_processing").wait_for(state="hidden", timeout=15_000)
    except Exception:
        pass
    try:
        await page.locator(".dataTables_paginate, .pagination").first.wait_for(state="attached", timeout=10_000)
    except Exception:
        pass


async def extract_visible_table_rows(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => {
            const normalize = (value) => (value || '').toString().replace(/\\s+/g, ' ').trim();
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const isCalendar = (table) => !!table.closest('.datetimepicker, .datepicker, #ui-datepicker-div');
            const tables = Array.from(document.querySelectorAll('table')).filter((table) => visible(table) && !isCalendar(table));
            const salesLike = (table) => /Fecha|Número|Numero|Total|Subtotal|Pagado|Saldo/i.test(table.innerText || '');
            const table = tables.find((t) => salesLike(t) && t.querySelectorAll('tbody tr td').length) || tables.find(t => t.querySelectorAll('tbody tr td').length);
            if (!table) return [];
            let headers = Array.from(table.querySelectorAll('thead th')).map(th => normalize(th.innerText)).filter(Boolean);
            if (!headers.length) {
                headers = Array.from(table.querySelectorAll('tr:first-child th, tr:first-child td')).map(th => normalize(th.innerText)).filter(Boolean);
            }
            return Array.from(table.querySelectorAll('tbody tr, tr')).map((tr) => {
                const cells = Array.from(tr.querySelectorAll('td')).map(td => normalize(td.innerText));
                if (!cells.length) return null;
                const row = {};
                cells.forEach((cell, index) => {
                    const key = headers[index] || `col_${index + 1}`;
                    row[key] = cell;
                });
                return row;
            }).filter(Boolean);
        }"""
    )


async def pagination_state(page: Page) -> str:
    try:
        return await page.locator(".dataTables_info, .pagination").first.inner_text(timeout=2_000)
    except Exception:
        return ""


async def next_page(page: Page, config: ReportConfig) -> bool:
    advanced, _reason = await next_page_detail(page, config)
    return advanced


async def next_page_detail(page: Page, config: ReportConfig) -> tuple[bool, str]:
    next_button = page.locator(config.pagination_next_selector).first
    try:
        if not await next_button.count() or not await next_button.is_visible(timeout=1_000):
            return False, "next_button_missing_or_hidden"
        class_name = await next_button.get_attribute("class") or ""
        parent_class = await next_button.evaluate("(el) => el.parentElement ? el.parentElement.className : ''")
        if "disabled" in f"{class_name} {parent_class}".lower():
            return False, "next_button_disabled"
        before = await pagination_state(page)
        await next_button.click()
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
        await wait_for_sales_table(page)
        after = await pagination_state(page)
        if before and after == before:
            return True, "clicked_next_but_info_unchanged"
        return True, "advanced"
    except Exception:
        return False, "next_page_exception"


async def collect_all_sales_pages(
    page: Page,
    config: ReportConfig,
    max_pages: int = 200,
    debug: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    page_number = 1
    if debug is not None:
        debug.setdefault("pagination", {})
        debug["pagination"]["max_pages_guard"] = max_pages
        debug["pagination"]["pages"] = []
    while page_number <= max_pages:
        snapshot_before = await sales_pagination_snapshot(page, config) if debug is not None else {}
        visible_rows = await extract_visible_table_rows(page)
        for row in visible_rows:
            row["_source_page"] = page_number
        rows.extend(visible_rows)
        advanced, reason = await next_page_detail(page, config)
        if debug is not None:
            debug["pagination"]["pages"].append(
                {
                    "page_number": page_number,
                    "rows_on_page": len(visible_rows),
                    "info_before_next": snapshot_before,
                    "advance_result": advanced,
                    "advance_reason": reason,
                }
            )
            debug["pagination"]["pages_detected_from_info"] = snapshot_before.get("total_records_reported")
        if not advanced:
            if debug is not None:
                debug["pagination"]["termination_reason"] = reason
                debug["pagination"]["pages_walked"] = page_number
                debug["pagination"]["rows_before_dedupe"] = len(rows)
            break
        page_number += 1
    else:
        if debug is not None:
            debug["pagination"]["termination_reason"] = "max_pages_guard_reached"
            debug["pagination"]["pages_walked"] = max_pages
            debug["pagination"]["rows_before_dedupe"] = len(rows)
    return rows


def _dedupe_rows(rows: list[dict[str, Any]], report_id: str, start: date, end: date) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        clean_row = dict(row)
        fingerprint = stable_id(*[str(value) for key, value in sorted(row.items()) if key != "_row_id"])
        clean_row["_row_id"] = stable_id(report_id, start.isoformat(), end.isoformat(), fingerprint)
        clean_row["_report_id"] = report_id
        clean_row["_chunk_start"] = start.isoformat()
        clean_row["_chunk_end"] = end.isoformat()
        clean_row["_extracted_at"] = now_iso()
        enriched.append(clean_row)
    return avoid_duplicates(enriched, ("_row_id",))


def _write_outputs(settings: Settings, config: ReportConfig, start: date, end: date, html: str, rows: list[dict[str, Any]]) -> dict[str, str]:
    month = chunk_key(start)
    raw_dir = settings.raw_dir / config.output_id / month
    processed_dir = settings.processed_dir / config.output_id / month
    logs_dir = settings.logs_dir
    raw_html = raw_dir / "raw.html"
    json_path = processed_dir / f"{config.output_id}.json"
    xlsx_path = processed_dir / f"{config.output_id}.xlsx"
    log_path = logs_dir / f"{config.output_id}_{month}.log"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    raw_html.write_text(html, encoding="utf-8")
    write_json(json_path, rows)
    pd.DataFrame(rows).to_excel(xlsx_path, index=False)
    log_path.write_text(
        "\n".join(
            [
                f"report={config.report_id}",
                f"name={config.name}",
                f"chunk_start={start.isoformat()}",
                f"chunk_end={end.isoformat()}",
                f"rows={len(rows)}",
                f"created_at={now_iso()}",
            ]
        ),
        encoding="utf-8",
    )
    return {"raw_html": str(raw_html), "json": str(json_path), "xlsx": str(xlsx_path), "log": str(log_path)}


def _write_debug_report(
    settings: Settings,
    config: ReportConfig,
    start: date,
    end: date,
    mode: str,
    debug: dict[str, Any],
) -> str:
    debug_dir = settings.debug_dir / "sales_compare"
    debug_dir.mkdir(parents=True, exist_ok=True)
    safe_timestamp = now_iso().replace(":", "_")
    path = debug_dir / f"{config.report_id}_{start.isoformat()}_{end.isoformat()}_{mode}_{safe_timestamp}.json"
    write_json(path, debug)
    return str(path)


def _append_debug_to_log(log_path: str, debug_path: str, debug: dict[str, Any]) -> None:
    filters = debug.get("filters_after_apply") or debug.get("filters_after_recipe") or {}
    filters_after_submit = debug.get("filters_after_submit") or {}
    pagination = debug.get("pagination", {})
    counts = debug.get("counts", {})
    selected_range = filters.get("range_selected") or {}
    lines = [
        "",
        "[debug]",
        f"debug_path={debug_path}",
        f"mode={debug.get('mode')}",
        f"url={filters.get('url') or debug.get('url_expected')}",
        f"date_from_selector={filters.get('date_from_selector')}",
        f"date_to_selector={filters.get('date_to_selector')}",
        f"date_from_value={filters.get('date_from_value')}",
        f"date_to_value={filters.get('date_to_value')}",
        f"range_selector={filters.get('range_selector')}",
        f"range_selected_value={selected_range.get('value')}",
        f"range_selected_text={selected_range.get('text')}",
        f"range_is_rango_fechas={filters.get('range_is_rango_fechas')}",
        f"page_size_value={filters_after_submit.get('page_size_value') or filters.get('page_size_value')}",
        f"pages_walked={pagination.get('pages_walked')}",
        f"rows_per_page={[item.get('rows_on_page') for item in pagination.get('pages', [])]}",
        f"rows_before_dedupe={counts.get('rows_before_dedupe')}",
        f"rows_after_dedupe={counts.get('rows_after_dedupe')}",
        f"unique_ids_after_dedupe={counts.get('unique_ids_after_dedupe')}",
        f"termination_reason={pagination.get('termination_reason')}",
    ]
    Path(log_path).write_text(Path(log_path).read_text(encoding="utf-8") + "\n".join(lines) + "\n", encoding="utf-8")


async def extract_sales_report(
    page: Page,
    settings: Settings,
    start: date,
    end: date,
    *,
    learn: bool = False,
    assisted: bool = False,
    prefer_recipe: bool = False,
    debug_pagination: bool = False,
    debug_filters: bool = False,
    debug_counts: bool = False,
) -> dict[str, Any]:
    config = load_report_config("sales")
    debug_enabled = debug_pagination or debug_filters or debug_counts
    debug: dict[str, Any] | None = (
        {
            "report_id": config.report_id,
            "report_name": config.name,
            "mode": "assisted" if assisted else "normal",
            "range": {"from": start.isoformat(), "to": end.isoformat()},
            "url_expected": absolute_report_url(settings, config),
            "flags": {
                "assisted": assisted,
                "learn": learn,
                "prefer_recipe": prefer_recipe,
                "debug_pagination": debug_pagination,
                "debug_filters": debug_filters,
                "debug_counts": debug_counts,
            },
            "events": [],
        }
        if debug_enabled
        else None
    )
    summary: dict[str, Any] = {
        "report_id": config.report_id,
        "name": config.name,
        "chunk_start": start.isoformat(),
        "chunk_end": end.isoformat(),
        "status": "pending",
        "row_count": 0,
        "outputs": {},
        "error": None,
    }
    try:
        await page.goto(absolute_report_url(settings, config), wait_until="domcontentloaded")
        await wait_until_loaded(page)
        if debug is not None:
            debug["events"].append({"event": "report_opened", "url": page.url, "at": now_iso()})
            debug["filters_before_apply"] = await sales_filter_state(page, config)
        submit_selector = None
        recipe = load_learned_recipe(config.report_id)
        if recipe:
            try:
                await replay_recipe(page, recipe, start, end)
                await wait_for_sales_table(page)
                submit_selector = "learned_recipe"
                if debug is not None:
                    debug["filters_after_recipe"] = await sales_filter_state(page, config)
            except Exception:
                if prefer_recipe:
                    raise
                logging.exception("Learned recipe failed; falling back to built-in sales flow")
                if learn:
                    raise
                await apply_sales_date_range(page, config, start, end)
                if debug is not None:
                    debug["filters_after_apply"] = await sales_filter_state(page, config)
                submit_selector = await click_sales_submit(page)
        else:
            if prefer_recipe:
                raise RuntimeError(f"No learned recipe found for report: {config.report_id}")
            await apply_sales_date_range(page, config, start, end)
            if debug is not None:
                debug["filters_after_apply"] = await sales_filter_state(page, config)
            submit_selector = await click_sales_submit(page)
        if debug is not None:
            debug["submit_selector"] = submit_selector
            debug["filters_after_submit"] = await sales_filter_state(page, config)
            debug["pagination_before_collect"] = await sales_pagination_snapshot(page, config)
        rows = await collect_all_sales_pages(page, config, debug=debug)
        rows_before_dedupe = len(rows)
        rows = _dedupe_rows(rows, config.report_id, start, end)
        if debug is not None:
            debug["counts"] = {
                "rows_before_dedupe": rows_before_dedupe,
                "rows_after_dedupe": len(rows),
                "unique_ids_after_dedupe": len({row.get("_row_id") for row in rows}),
                "source_pages_seen": sorted({row.get("_source_page") for row in rows if row.get("_source_page") is not None}),
            }
        outputs = _write_outputs(settings, config, start, end, await page.content(), rows)
        if debug is not None:
            outputs["debug"] = _write_debug_report(settings, config, start, end, "assisted" if assisted else "normal", debug)
            _append_debug_to_log(outputs["log"], outputs["debug"], debug)
        summary.update(
            {
                "status": "success",
                "row_count": len(rows),
                "submit_selector": submit_selector,
                "outputs": outputs,
                "debug": debug,
            }
        )
    except Exception as exc:
        logging.exception("Sales extraction failed")
        if assisted:
            try:
                assisted_result = await assisted_pause(page, settings, config.report_id, config.name, repr(exc))
                summary["assisted"] = {
                    "decision": assisted_result.decision,
                    "event_path": str(assisted_result.event_path),
                    "detected_after_user_action": assisted_result.detected_after_user_action,
                }
                if assisted_result.decision == "retry":
                    return await extract_sales_report(page, settings, start, end, learn=False, assisted=False, prefer_recipe=False)
                if assisted_result.decision == "enter":
                    await wait_for_sales_table(page)
                    rows = await collect_all_sales_pages(page, config)
                    rows = _dedupe_rows(rows, config.report_id, start, end)
                    outputs = _write_outputs(settings, config, start, end, await page.content(), rows)
                    summary.update({"status": "success", "row_count": len(rows), "submit_selector": "assisted_manual", "outputs": outputs})
                    return summary
                if assisted_result.decision == "skip":
                    summary.update({"status": "skipped", "error": repr(exc)})
                    return summary
            except Exception as assisted_exc:
                logging.exception("Assisted mode failed")
                exc = assisted_exc
        if learn:
            try:
                recipe = await enter_learning_mode(
                    page,
                    settings,
                    config.report_id,
                    config.name,
                    repr(exc),
                    start,
                    end,
                )
                await wait_for_sales_table(page)
                rows = await collect_all_sales_pages(page, config)
                rows = _dedupe_rows(rows, config.report_id, start, end)
                outputs = _write_outputs(settings, config, start, end, await page.content(), rows)
                summary.update(
                    {
                        "status": "success",
                        "row_count": len(rows),
                        "submit_selector": "manual_learning",
                        "recipe_saved": str((Path("configs") / "learned_recipes" / f"{config.report_id}.yaml")),
                        "learned_steps": len(recipe.get("steps", [])),
                        "outputs": outputs,
                    }
                )
                return summary
            except Exception as learn_exc:
                logging.exception("Learning mode failed")
                exc = learn_exc
        evidence = await save_evidence(page, settings, f"sales_error_{chunk_key(start)}")
        log_path = settings.logs_dir / f"sales_{chunk_key(start)}.log"
        log_path.write_text(f"status=error\nerror={repr(exc)}\nevidence={evidence}\ncreated_at={now_iso()}\n", encoding="utf-8")
        summary.update({"status": "error", "error": repr(exc), "evidence": evidence, "outputs": {"log": str(log_path)}})
    return summary
