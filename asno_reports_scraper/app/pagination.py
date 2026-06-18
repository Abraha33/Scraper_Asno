from __future__ import annotations

from playwright.async_api import Page


async def wait_until_loaded(page: Page) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=30_000)
    except Exception:
        pass
    for selector in (".loading", ".loader", ".pace-active", ".dataTables_processing"):
        try:
            await page.locator(selector).wait_for(state="hidden", timeout=5_000)
        except Exception:
            continue


async def handle_pagination(page: Page, max_pages: int = 100) -> None:
    for _ in range(max_pages):
        next_button = page.locator(
            "a.paginate_button.next:not(.disabled), li.next:not(.disabled) a, a:has-text('Siguiente')"
        ).first
        try:
            if not await next_button.count() or not await next_button.is_visible(timeout=1_000):
                return
            await next_button.click()
            await wait_until_loaded(page)
        except Exception:
            return

