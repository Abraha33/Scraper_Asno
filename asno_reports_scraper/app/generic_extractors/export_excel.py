from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from .common import read_filters


async def inspect_export_excel(page: Page) -> dict[str, Any]:
    exports = await page.evaluate(
        """() => Array.from(document.querySelectorAll('a,button,input[type=button],input[type=submit]')).map(el => ({
            label: (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' '),
            href: el.href || el.getAttribute('href'),
            id: el.id || null,
            name: el.getAttribute('name'),
        })).filter(x => /excel|xls|xlsx|csv/i.test(`${x.label} ${x.href || ''}`))"""
    )
    return {"pattern": "export_excel", "filters": await read_filters(page), "exports": exports, "read_only": True}

