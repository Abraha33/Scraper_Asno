from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from .common import read_visible_tables


async def inspect_detail_modal(page: Page) -> dict[str, Any]:
    modals = await page.evaluate(
        """() => {
            const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const clean = value => (value || '').toString().replace(/\\s+/g, ' ').trim();
            return Array.from(document.querySelectorAll('.modal,.swal2-container,.bootbox,[role="dialog"]')).filter(visible).map(el => ({
                selector: el.id ? `#${CSS.escape(el.id)}` : '.modal',
                text_sample: clean(el.innerText).slice(0, 500),
            }));
        }"""
    )
    return {"pattern": "detail_modal", "tables": await read_visible_tables(page), "modals": modals, "read_only": True}

