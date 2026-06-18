from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from .common import read_filters, read_visible_tables


async def inspect_filter_table(page: Page) -> dict[str, Any]:
    tables = await read_visible_tables(page)
    return {
        "pattern": "filter_table",
        "filters": await read_filters(page),
        "tables": [{"selector": t["selector"], "headers": t["headers"], "rows_count": t["rows_count"]} for t in tables],
        "read_only": True,
    }

