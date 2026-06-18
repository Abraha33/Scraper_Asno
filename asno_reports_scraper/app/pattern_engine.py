from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page

from .assisted import assisted_pause
from .config import Settings
from .site_patterns_audit import DANGEROUS_RE


READONLY_PATTERNS = {
    "filter_paginated_table",
    "filter_table",
    "paginated_table",
    "list_table",
    "export_excel",
    "export_pdf",
    "detail_modal",
    "detail_page",
    "crud_list",
    "crud_list_readonly",
    "transaction_form",
    "transaction_form_readonly",
    "document_report",
    "dashboard",
    "settings_page",
}


@dataclass(frozen=True)
class PatternDecision:
    pattern: str
    extractor: str
    read_only: bool
    needs_assisted: bool
    reason: str = ""


def normalize_pattern(pattern: str | None) -> str:
    mapping = {
        "form_transaction": "transaction_form_readonly",
        "transaction_form": "transaction_form_readonly",
        "crud_list": "crud_list_readonly",
        "table": "list_table",
        "report_document": "document_report",
    }
    raw = pattern or "unknown"
    return mapping.get(raw, raw)


def extractor_for_pattern(pattern: str | None) -> str:
    pattern = normalize_pattern(pattern)
    return {
        "filter_paginated_table": "generic_extractors.filter_paginated_table",
        "filter_table": "generic_extractors.filter_table",
        "paginated_table": "generic_extractors.filter_paginated_table",
        "list_table": "generic_extractors.readonly_table",
        "export_excel": "generic_extractors.export_excel",
        "export_pdf": "generic_extractors.export_pdf",
        "detail_modal": "generic_extractors.detail_modal",
        "detail_page": "generic_extractors.detail_page",
        "crud_list_readonly": "generic_extractors.readonly_table",
        "transaction_form_readonly": "generic_extractors.readonly_table",
        "document_report": "generic_extractors.readonly_table",
        "dashboard": "generic_extractors.readonly_table",
        "settings_page": "generic_extractors.readonly_table",
        "unknown": "assisted",
    }.get(pattern, "assisted")


def decide_pattern(page_record: dict[str, Any]) -> PatternDecision:
    pattern = normalize_pattern(page_record.get("pattern"))
    dangerous = bool(page_record.get("dangerous_actions_detected"))
    if pattern == "unknown":
        return PatternDecision(pattern, "assisted", True, True, "unknown pattern")
    if pattern not in READONLY_PATTERNS and pattern not in {"transaction_form_readonly", "crud_list_readonly"}:
        return PatternDecision(pattern, "assisted", True, True, "unsupported pattern")
    extractor = extractor_for_pattern(pattern)
    if dangerous and pattern in {"transaction_form_readonly", "crud_list_readonly", "settings_page"}:
        return PatternDecision(pattern, extractor, True, False, "dangerous actions registered; extractor must stay read-only")
    return PatternDecision(pattern, extractor, True, False, "classified")


async def detect_dangerous_actions_on_page(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """() => {
            const text = (el) => (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const css = (el) => {
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.getAttribute('name')) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.getAttribute('name'))}"]`;
                return el.tagName.toLowerCase();
            };
            return Array.from(document.querySelectorAll('a,button,input[type=button],input[type=submit]'))
                .filter(visible)
                .map(el => ({ label: text(el), href: el.href || el.getAttribute('href'), selector: css(el) }))
                .filter(item => /crear|editar|guardar|actualizar|eliminar|borrar|anular|confirmar|pagar|cerrar caja|facturar|enviar|importar|sincronizar|procesar|aprobar/i.test(`${item.label} ${item.href || ''}`));
        }"""
    )


async def ensure_read_only_or_assist(page: Page, settings: Settings, page_record: dict[str, Any], *, assisted: bool = False) -> list[dict[str, Any]]:
    dangerous = await detect_dangerous_actions_on_page(page)
    if dangerous:
        page_record["dangerous_actions_detected"] = dangerous
    decision = decide_pattern(page_record)
    if decision.needs_assisted and assisted:
        await assisted_pause(
            page,
            settings,
            str(page_record.get("module") or "system"),
            str(page_record.get("name") or page.url),
            f"No pude aplicar patrón automáticamente: {decision.reason}",
        )
    return dangerous
