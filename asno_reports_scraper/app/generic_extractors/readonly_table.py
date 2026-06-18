from __future__ import annotations

from typing import Any

from playwright.async_api import Page

from .common import read_filters, read_pagination, read_visible_tables


async def inspect_readonly_table(page: Page) -> dict[str, Any]:
    return {
        "pattern": "readonly_table",
        "filters": await read_filters(page),
        "pagination": await read_pagination(page),
        "tables": await read_visible_tables(page),
        "read_only": True,
    }
