from __future__ import annotations

from typing import Any

from playwright.async_api import Page


async def visible_text(page: Page) -> str:
    return await page.locator("body").inner_text(timeout=10_000)


async def detect_filters(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => {
            const labelFor = (el) => {
                if (el.id) {
                    const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                    if (label) return (label.innerText || '').trim().replace(/\\s+/g, ' ');
                }
                const parentLabel = el.closest('label');
                if (parentLabel) return (parentLabel.innerText || '').trim().replace(/\\s+/g, ' ');
                const group = el.closest('.form-group, .input-group, .col-md-4, .col-sm-4, .col-xs-12, div');
                if (group) {
                    const label = group.querySelector('label');
                    if (label) return (label.innerText || '').trim().replace(/\\s+/g, ' ');
                }
                return el.getAttribute('placeholder') || el.getAttribute('name') || el.getAttribute('id') || '';
            };
            const cssSelector = (el) => {
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.getAttribute('name')) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.getAttribute('name'))}"]`;
                return el.tagName.toLowerCase();
            };
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            return Array.from(document.querySelectorAll('input,select,textarea')).map((el, index) => {
                const tag = el.tagName.toLowerCase();
                const options = tag === 'select'
                    ? Array.from(el.options || []).map(o => (o.innerText || o.value || '').trim()).filter(Boolean).slice(0, 100)
                    : [];
                const typeAttr = el.getAttribute('type') || tag;
                let type = 'unknown';
                if (tag === 'select') type = 'select';
                else if (typeAttr === 'checkbox') type = 'checkbox';
                else if (typeAttr === 'date' || /fecha|date|desde|hasta|inicio|fin/i.test(`${el.name} ${el.id} ${el.placeholder}`)) type = 'date';
                else if (tag === 'input') type = 'input';
                return {
                    index,
                    label: labelFor(el),
                    type,
                    tag,
                    input_type: el.getAttribute('type'),
                    name: el.getAttribute('name'),
                    id: el.getAttribute('id'),
                    selector: cssSelector(el),
                    value: tag === 'select' ? el.value : el.value,
                    visible: visible(el),
                    enabled: !el.disabled,
                    options
                };
            });
        }"""
    )


async def detect_date_range_controls(page: Page, filters: list[dict[str, Any]]) -> dict[str, Any]:
    text = (await visible_text(page)).lower()
    date_candidates = [
        item
        for item in filters
        if item.get("type") == "date"
        or any(token in " ".join(str(item.get(k, "")).lower() for k in ("label", "name", "id", "selector")) for token in ("fecha", "date", "desde", "hasta", "inicio", "fin"))
    ]
    range_options = []
    for item in filters:
        opts = [str(option) for option in item.get("options", [])]
        for option in opts:
            if "rango" in option.lower() or "personalizado" in option.lower():
                range_options.append(option)
    date_from = next(
        (
            item
            for item in date_candidates
            if any(token in " ".join(str(item.get(k, "")).lower() for k in ("label", "name", "id", "selector")) for token in ("start", "desde", "inicio", "from", "initial"))
        ),
        date_candidates[0] if date_candidates else None,
    )
    date_to = next(
        (
            item
            for item in date_candidates
            if any(token in " ".join(str(item.get(k, "")).lower() for k in ("label", "name", "id", "selector")) for token in ("end", "hasta", "fin", "to", "final"))
        ),
        date_candidates[1] if len(date_candidates) > 1 else None,
    )
    fmt = "unknown"
    sample_values = " ".join(str(item.get("value") or "") for item in date_candidates)
    if any("-" in str(item.get("value") or "") for item in date_candidates):
        fmt = "YYYY-MM-DD"
    if "/" in sample_values:
        fmt = "DD/MM/YYYY"
    return {
        "has_date_filter": bool(date_candidates),
        "has_range_option": bool(range_options) or "rango de fechas" in text or "rango personalizado" in text,
        "range_option_label": range_options[0] if range_options else ("Rango de fechas" if "rango de fechas" in text else None),
        "date_from_selector": date_from.get("selector") if date_from else None,
        "date_to_selector": date_to.get("selector") if date_to else None,
        "date_format_detected": fmt,
        "date_controls": date_candidates,
    }


async def detect_action_buttons(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => {
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const textOf = (el) => (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
            const cssSelector = (el) => {
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.getAttribute('name')) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.getAttribute('name'))}"]`;
                return el.tagName.toLowerCase();
            };
            return Array.from(document.querySelectorAll('button,input[type=button],input[type=submit],a.btn,a')).map((el, index) => ({
                index,
                label: textOf(el),
                type: el.tagName.toLowerCase() === 'a' ? 'link' : 'button',
                selector: cssSelector(el),
                href: el.href || el.getAttribute('href'),
                visible: visible(el),
                enabled: !el.disabled && !el.classList.contains('disabled')
            })).filter(x => x.label || x.href)
              .filter(x => /consultar|generar|guardar|exportar|pdf|excel|imprimir|buscar|filtrar|descargar/i.test(`${x.label} ${x.href || ''}`));
        }"""
    )


async def detect_export_buttons(page: Page, actions: list[dict[str, Any]]) -> dict[str, Any]:
    def find(pattern: str) -> dict[str, Any] | None:
        import re

        for action in actions:
            if re.search(pattern, f"{action.get('label', '')} {action.get('href', '')}", re.I):
                return action
        return None

    pdf = find(r"pdf")
    excel = find(r"excel|xls|xlsx|csv")
    print_action = find(r"imprimir|print")
    return {
        "has_pdf": bool(pdf),
        "has_excel": bool(excel),
        "has_print": bool(print_action),
        "pdf_selector": pdf.get("selector") if pdf else None,
        "excel_selector": excel.get("selector") if excel else None,
        "print_selector": print_action.get("selector") if print_action else None,
    }


async def detect_table(page: Page) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
            const tables = Array.from(document.querySelectorAll('table')).map((table, index) => ({
                index,
                id: table.getAttribute('id'),
                class: table.getAttribute('class'),
                visible: !!(table.offsetWidth || table.offsetHeight || table.getClientRects().length),
                rows: table.querySelectorAll('tbody tr, tr').length,
                headers: Array.from(table.querySelectorAll('th')).map(th => (th.innerText || '').trim()).filter(Boolean)
            }));
            const dataTables = tables.filter(t => /dataTable|datatable/i.test(`${t.id || ''} ${t.class || ''}`));
            return {
                has_table: tables.length > 0,
                tables,
                visible_table_count: tables.filter(t => t.visible).length,
                data_tables_count: dataTables.length,
                empty_tables_count: tables.filter(t => t.rows === 0).length
            };
        }"""
    )


async def detect_pagination(page: Page) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const next = Array.from(document.querySelectorAll('a,button')).find(el => /siguiente|next|>|»/i.test((el.innerText || el.textContent || '').trim()));
            const pageSize = Array.from(document.querySelectorAll('select')).find(el => /length|page|per|records|registros/i.test(`${el.id || ''} ${el.name || ''} ${el.className || ''}`));
            const pageLinks = Array.from(document.querySelectorAll('.paginate_button, .pagination a, ul.pagination li')).filter(visible);
            return {
                has_pagination: !!next || pageLinks.length > 0 || !!pageSize,
                next_selector: next ? (next.id ? `#${CSS.escape(next.id)}` : 'a/button text next') : null,
                page_count_detected: pageLinks.length || null,
                page_size_selector: pageSize ? (pageSize.id ? `#${CSS.escape(pageSize.id)}` : `select[name="${pageSize.name}"]`) : null,
                has_datatables_pagination: !!document.querySelector('.dataTables_paginate, .dataTables_length')
            };
        }"""
    )

