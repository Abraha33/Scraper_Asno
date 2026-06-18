from __future__ import annotations

from pathlib import Path

from playwright.async_api import Page

from .config import Settings
from .storage import safe_name


async def download_excel_if_available(page: Page, settings: Settings, report_id: str, chunk_label: str) -> list[str]:
    selectors = (
        "a:has-text('Excel')",
        "button:has-text('Excel')",
        "a:has-text('CSV')",
        "button:has-text('CSV')",
        "a[href*='excel' i]",
        "a[href*='csv' i]",
    )
    paths: list[str] = []
    for selector in selectors:
        locator = page.locator(selector)
        count = await locator.count()
        for idx in range(min(count, 3)):
            target = locator.nth(idx)
            try:
                if not await target.is_visible(timeout=1_000):
                    continue
                async with page.expect_download(timeout=10_000) as download_info:
                    await target.click()
                download = await download_info.value
                name = safe_name(f"{report_id}_{chunk_label}_{download.suggested_filename}")
                destination: Path = settings.downloads_dir / name
                await download.save_as(destination)
                paths.append(str(destination))
            except Exception:
                continue
    return paths

