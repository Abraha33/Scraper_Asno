from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
from playwright.async_api import Page

from .config import Settings
from .downloads import download_excel_if_available
from .normalizer import table_rows_from_html
from .pagination import wait_until_loaded
from .report_detector import inspect_report
from .reports_index import discover_reports
from .storage import append_jsonl, avoid_duplicates, now_iso, save_evidence, safe_name, write_json


def month_chunks(start: date, end: date) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        next_month = date(cursor.year + (cursor.month // 12), (cursor.month % 12) + 1, 1)
        chunk_start = max(cursor, start)
        chunk_end = min(next_month - timedelta(days=1), end)
        chunks.append((chunk_start, chunk_end))
        cursor = next_month
    return chunks


async def open_modal_if_needed(page: Page, report: dict[str, Any]) -> None:
    if report.get("href") and str(report["href"]).startswith("http"):
        await page.goto(report["href"], wait_until="domcontentloaded")
    else:
        locator = page.get_by_text(report["name"], exact=True).first
        if not await locator.count():
            locator = page.get_by_text(report["name"], exact=False).first
        await locator.click()
    await wait_until_loaded(page)


async def apply_date_range(page: Page, start: date, end: date) -> None:
    values = (start.strftime("%d/%m/%Y 00:00:00"), end.strftime("%d/%m/%Y 23:59:59"))
    inputs = page.locator("input")
    candidates: list[int] = []
    for idx in range(await inputs.count()):
        item = inputs.nth(idx)
        attrs = " ".join(
            str(await item.get_attribute(attr) or "").lower()
            for attr in ("name", "id", "placeholder", "type")
        )
        if any(h in attrs for h in ("fecha", "desde", "hasta", "inicio", "fin", "date")):
            candidates.append(idx)
    for idx, value in zip(candidates[:2], values):
        target = inputs.nth(idx)
        await target.click()
        await target.press("Control+A")
        await target.type(value, delay=20)


async def click_consult(page: Page) -> None:
    for selector in (
        "button:has-text('Consultar')",
        "button:has-text('Buscar')",
        "button:has-text('Generar')",
        "a:has-text('Consultar')",
        "input[type='submit']",
    ):
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible(timeout=1_000):
                await locator.click()
                await wait_until_loaded(page)
                return
        except Exception:
            continue


async def extract_table_if_no_excel(page: Page, settings: Settings, report_id: str, chunk_label: str) -> list[dict[str, Any]]:
    rows = table_rows_from_html(await page.content())
    if rows:
        json_path = settings.raw_dir / f"{safe_name(report_id)}_{chunk_label}_table.json"
        write_json(json_path, rows)
        csv_path = settings.raw_dir / f"{safe_name(report_id)}_{chunk_label}_table.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
    return rows


async def extract_report(page: Page, settings: Settings, report: dict[str, Any], start: date, end: date) -> dict[str, Any]:
    report_id = report["id"]
    summary = {"report_id": report_id, "name": report["name"], "chunks": [], "errors": []}
    for chunk_start, chunk_end in month_chunks(start, end):
        chunk_label = f"{chunk_start.isoformat()}_{chunk_end.isoformat()}"
        try:
            await open_modal_if_needed(page, report)
            structure = await inspect_report(page, report)
            write_json(settings.raw_dir / f"{safe_name(report_id)}_structure.json", structure)
            await apply_date_range(page, chunk_start, chunk_end)
            await click_consult(page)
            downloads = await download_excel_if_available(page, settings, report_id, chunk_label)
            rows = [] if downloads else await extract_table_if_no_excel(page, settings, report_id, chunk_label)
            append_jsonl(
                settings.processed_dir / "records_partial.jsonl",
                {
                    "report_id": report_id,
                    "report_name": report["name"],
                    "chunk_start": chunk_start.isoformat(),
                    "chunk_end": chunk_end.isoformat(),
                    "downloads": downloads,
                    "row_count": len(rows),
                    "created_at": now_iso(),
                },
            )
            summary["chunks"].append({"chunk": chunk_label, "downloads": downloads, "row_count": len(rows)})
        except Exception as exc:
            logging.exception("Report failed: %s %s", report_id, chunk_label)
            evidence = await save_evidence(page, settings, f"error_{report_id}_{chunk_label}")
            summary["errors"].append({"chunk": chunk_label, "error": repr(exc), "evidence": evidence})
            continue
    write_json(settings.processed_dir / f"{safe_name(report_id)}_summary.json", summary)
    return summary


async def extract_all(page: Page, settings: Settings, start: date, end: date) -> dict[str, Any]:
    reports = await discover_reports(page, settings)
    summaries = []
    for report in reports:
        summaries.append(await extract_report(page, settings, report, start, end))
    final = {
        "created_at": now_iso(),
        "reports_detected": len(reports),
        "reports_extracted": sum(1 for item in summaries if item["chunks"]),
        "reports_failed": sum(1 for item in summaries if item["errors"] and not item["chunks"]),
        "summaries": summaries,
    }
    write_json(settings.processed_dir / "run_summary.json", final)
    return final

