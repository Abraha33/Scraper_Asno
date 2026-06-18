from __future__ import annotations

from typing import Any

from playwright.async_api import Page


REPORT_KEYWORDS = (
    "informe",
    "ventas",
    "compras",
    "kardex",
    "inventario",
    "cartera",
    "cliente",
    "proveedor",
    "producto",
    "balance",
    "gastos",
    "egresos",
    "cuentas",
    "flujo",
    "cierre",
    "bodega",
    "categor",
)


async def detect_filters(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => Array.from(document.querySelectorAll('input,select,textarea')).map((el, index) => ({
            index,
            tag: el.tagName.toLowerCase(),
            type: el.getAttribute('type'),
            name: el.getAttribute('name'),
            id: el.getAttribute('id'),
            placeholder: el.getAttribute('placeholder'),
            value: el.tagName.toLowerCase() === 'select' ? '' : el.value,
            visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
        }))"""
    )


async def detect_date_inputs(page: Page) -> list[dict[str, Any]]:
    filters = await detect_filters(page)
    hints = ("fecha", "desde", "hasta", "inicio", "fin", "date", "fch")
    return [
        item
        for item in filters
        if item.get("type") in {"date", "datetime-local"}
        or any(h in " ".join(str(item.get(k, "")).lower() for k in ("name", "id", "placeholder")) for h in hints)
    ]


async def detect_export_buttons(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => Array.from(document.querySelectorAll('a,button,input[type=button],input[type=submit]'))
            .map((el, index) => ({
                index,
                text: (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' '),
                href: el.href || el.getAttribute('href'),
                id: el.getAttribute('id'),
                class: el.getAttribute('class'),
                visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
            }))
            .filter(x => x.visible && /excel|csv|pdf|export|descargar|imprimir/i.test(`${x.text} ${x.href || ''}`))"""
    )


async def detect_tables(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => Array.from(document.querySelectorAll('table')).map((table, index) => ({
            index,
            id: table.getAttribute('id'),
            class: table.getAttribute('class'),
            row_count: table.querySelectorAll('tr').length,
            headers: Array.from(table.querySelectorAll('th')).map(th => (th.innerText || '').trim())
        }))"""
    )


async def inspect_report(page: Page, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "report": report,
        "url": page.url,
        "title": await page.title(),
        "filters": await detect_filters(page),
        "date_inputs": await detect_date_inputs(page),
        "export_buttons": await detect_export_buttons(page),
        "tables": await detect_tables(page),
    }

