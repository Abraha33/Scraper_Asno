from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from .common import read_visible_tables


async def inspect_detail_page(page: Page) -> dict[str, Any]:
    detail_links = await page.evaluate(
        """() => Array.from(document.querySelectorAll('a,button')).map(el => ({
            label: (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' '),
            href: el.href || el.getAttribute('href'),
        })).filter(x => /ver|detalle|detalles|view|show|consultar/i.test(`${x.label} ${x.href || ''}`)).slice(0, 100)"""
    )
    return {"pattern": "detail_page", "tables": await read_visible_tables(page), "detail_links": detail_links, "read_only": True}

