from __future__ import annotations

from typing import Any

from playwright.async_api import Page


async def detect_state_after_manual_action(page: Page, url_before: str | None = None) -> dict[str, Any]:
    return await page.evaluate(
        """(urlBefore) => {
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const isCalendar = (table) => !!table.closest('.datetimepicker, .datepicker, #ui-datepicker-div')
                || /\\b(Lu|Ma|Mi|Ju|Vi|Sá|Do|Hoy)\\b/i.test(table.innerText || '');
            const usefulTable = Array.from(document.querySelectorAll('table')).find((table) =>
                visible(table)
                && !isCalendar(table)
                && table.querySelectorAll('tbody tr td, tr td').length >= 5
                && /Fecha|Número|Numero|Total|Subtotal|Pagado|Saldo|Cliente|Proveedor|Producto|Cantidad/i.test(table.innerText || '')
            );
            const pagination = document.querySelector('.dataTables_paginate, .pagination, a.paginate_button, li.next');
            const pdf = Array.from(document.querySelectorAll('a,button')).find((el) =>
                visible(el) && /pdf/i.test(`${el.innerText || ''} ${el.href || ''}`)
            );
            const excel = Array.from(document.querySelectorAll('a,button')).find((el) =>
                visible(el) && /excel|xls|xlsx|csv/i.test(`${el.innerText || ''} ${el.href || ''}`)
            );
            const modal = Array.from(document.querySelectorAll('.modal, .swal2-container, .bootbox')).find(visible);
            const loader = Array.from(document.querySelectorAll('.loading, .loader, .pace-active, .dataTables_processing')).find(visible);
            const alert = Array.from(document.querySelectorAll('.alert-danger, .alert-warning, .swal2-popup')).find(visible);
            return {
                table_visible: !!usefulTable,
                pagination_visible: !!pagination && visible(pagination),
                pdf_visible: !!pdf,
                excel_visible: !!excel,
                download_detected: false,
                url_changed: !!urlBefore && location.href !== urlBefore,
                modal_visible: !!modal,
                loader_visible: !!loader,
                alert_visible: !!alert,
                current_url: location.href,
                table_text_sample: usefulTable ? (usefulTable.innerText || '').replace(/\\s+/g, ' ').slice(0, 300) : null,
            };
        }""",
        url_before,
    )


def can_continue_after_state(state: dict[str, Any]) -> bool:
    return bool(
        state.get("table_visible")
        or state.get("pdf_visible")
        or state.get("excel_visible")
        or state.get("download_detected")
        or state.get("url_changed")
    )
