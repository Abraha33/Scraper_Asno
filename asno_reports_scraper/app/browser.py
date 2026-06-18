from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import Settings


@asynccontextmanager
async def browser_page(settings: Settings) -> AsyncIterator[Page]:
    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(
            headless=settings.headless,
            slow_mo=settings.slow_mo_ms,
        )
        context: BrowserContext = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        page.set_default_timeout(settings.timeout_ms)
        try:
            yield page
        finally:
            await context.close()
            await browser.close()

