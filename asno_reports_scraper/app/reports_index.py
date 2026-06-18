from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from .config import Settings
from .login import go_to_reports_module
from .report_detector import REPORT_KEYWORDS
from .storage import safe_name, stable_id, write_json


async def discover_reports(page: Page, settings: Settings) -> list[dict[str, Any]]:
    await go_to_reports_module(page, settings)
    keyword_regex = "|".join(REPORT_KEYWORDS)
    items = await page.evaluate(
        """(keywordRegex) => {
            const re = new RegExp(keywordRegex, 'i');
            const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const text = el => (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
            return Array.from(document.querySelectorAll('a,button,[role=button]'))
                .map((el, index) => ({
                    index,
                    name: text(el),
                    href: el.href || el.getAttribute('href') || null,
                    onclick: el.getAttribute('onclick'),
                    id: el.getAttribute('id'),
                    class: el.getAttribute('class'),
                    visible: visible(el)
                }))
                .filter(item => item.visible && item.name && re.test(`${item.name} ${item.href || ''} ${item.onclick || ''}`));
        }""",
        keyword_regex,
    )
    reports: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if item["name"].lower() == "informes":
            continue
        report_id = safe_name(item["name"]).lower() or stable_id(item["name"], item.get("href") or "")
        if report_id in seen:
            continue
        seen.add(report_id)
        reports.append({**item, "id": report_id})
    write_json(settings.raw_dir / "reports_index.json", reports)
    return reports
