from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from .assisted import AssistedAbort, assisted_pause
from .chatgpt_audit_report import generate_chatgpt_audit_markdown
from .config import Settings, ROOT_DIR
from .dom_utils import (
    detect_action_buttons,
    detect_date_range_controls,
    detect_export_buttons,
    detect_filters,
    detect_pagination,
    detect_table,
)
from .login import go_to_reports_module
from .reports_index import discover_reports
from .storage import now_iso, safe_name, save_evidence, write_json


CATEGORY_KEYWORDS = {
    "ventas": ("venta", "sales", "ingreso", "comision", "recaudo"),
    "compras": ("compra", "purchase", "proveedor", "solicitud"),
    "inventario": ("inventario", "producto", "bodega", "kardex", "stock", "marca", "ajuste", "traslado", "caducidad"),
    "financiero": ("cartera", "cuentas por pagar", "gasto", "egreso", "impuesto", "flujo", "cierre", "zeta", "diario"),
    "rentabilidad": ("rentabilidad", "profitability"),
    "clientes": ("cliente", "customer"),
    "proveedores": ("proveedor", "supplier"),
    "operativo": ("usuario", "agendamiento", "orden", "produccion", "confección", "confeccion"),
}

PRIORITY_KEYWORDS = [
    ("ventas detalladas", 1),
    ("informe de ventas", 1),
    ("compras detalladas", 2),
    ("informe de compras", 2),
    ("kardex", 3),
    ("movimiento de productos", 3),
    ("cartera", 4),
    ("cuentas por pagar", 5),
    ("gastos", 6),
    ("egresos", 6),
    ("estado de resultados", 7),
    ("balance", 8),
    ("productos", 9),
    ("clientes", 10),
    ("proveedor", 11),
]


def infer_report_category(name: str) -> str:
    lowered = name.lower()
    for category, tokens in CATEGORY_KEYWORDS.items():
        if any(token in lowered for token in tokens):
            return category
    return "desconocido"


def infer_priority(name: str) -> int:
    lowered = name.lower()
    for token, priority in PRIORITY_KEYWORDS:
        if token in lowered:
            return priority
    return 99


def infer_report_type(table_info: dict[str, Any], pagination: dict[str, Any], exports: dict[str, Any]) -> str:
    has_export = exports.get("has_pdf") or exports.get("has_excel")
    if table_info.get("has_table") and has_export:
        return "mixed"
    if exports.get("has_pdf") and not table_info.get("has_table"):
        return "pdf_document"
    if exports.get("has_excel") and not table_info.get("has_table"):
        return "excel_download"
    if table_info.get("has_table") and pagination.get("has_pagination"):
        return "paginated_table"
    if table_info.get("has_table"):
        return "table"
    if exports.get("has_pdf"):
        return "pdf_document"
    if exports.get("has_excel"):
        return "excel_download"
    return "unknown"


def infer_extraction_strategy(result_type: str, date_filter: dict[str, Any], pagination: dict[str, Any], name: str) -> dict[str, Any]:
    reasons: list[str] = []
    level = "low"
    if date_filter.get("has_date_filter"):
        reasons.append("requiere rango de fechas")
    if pagination.get("has_pagination"):
        reasons.append("usa paginación")
        level = "medium"
    if any(token in name.lower() for token in ("ventas", "compras", "movimiento", "inventario", "cartera")):
        reasons.append("posible reporte pesado")
        level = "medium"
    if result_type == "pdf_document":
        reasons.append("exporta PDF")
        return {"level": level, "reasons": reasons, "recommended_strategy": "pdf_full_range_once"}
    if result_type == "mixed":
        reasons.append("tiene tabla y exportación")
        if pagination.get("has_pagination"):
            return {"level": "high" if "posible reporte pesado" in reasons else "medium", "reasons": reasons, "recommended_strategy": "table_monthly_chunks"}
        return {"level": level, "reasons": reasons, "recommended_strategy": "excel_full_or_chunked"}
    if result_type == "paginated_table":
        return {"level": "high" if "posible reporte pesado" in reasons else "medium", "reasons": reasons, "recommended_strategy": "table_monthly_chunks"}
    if result_type == "table":
        return {"level": level, "reasons": reasons, "recommended_strategy": "table_quarterly_chunks" if date_filter.get("has_date_filter") else "full_range_if_light"}
    if result_type == "excel_download":
        return {"level": level, "reasons": reasons + ["priorizar Excel"], "recommended_strategy": "excel_full_or_chunked"}
    return {"level": "high", "reasons": reasons + ["no se pudo clasificar"], "recommended_strategy": "inspect_manually"}


async def open_report(page: Page, report: dict[str, Any]) -> None:
    href = str(report.get("href") or "")
    if href.startswith("http") and "/admin/reports/" in href:
        await page.goto(href, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass
        return
    locator = page.get_by_text(report.get("name", ""), exact=True).first
    if not await locator.count():
        locator = page.get_by_text(report.get("name", ""), exact=False).first
    await locator.click()
    try:
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception:
        pass


def report_is_auditable(report: dict[str, Any]) -> bool:
    return "/admin/reports/" in str(report.get("href") or "")


async def audit_report_page(page: Page, settings: Settings, report: dict[str, Any], *, assisted: bool = False) -> dict[str, Any]:
    name = str(report.get("name") or "unknown")
    slug = str(report.get("id") or safe_name(name).lower())
    result: dict[str, Any] = {
        "name": name,
        "slug": slug,
        "url": report.get("href"),
        "source": "menu_lateral",
        "category_inferred": infer_report_category(name),
        "priority_inferred": infer_priority(name),
        "opened_successfully": False,
        "filters_detected": [],
        "date_filter": {
            "has_date_filter": False,
            "has_range_option": False,
            "range_option_label": None,
            "date_from_selector": None,
            "date_to_selector": None,
            "date_format_detected": "unknown",
        },
        "actions_detected": [],
        "exports_detected": {
            "has_pdf": False,
            "has_excel": False,
            "has_print": False,
            "pdf_selector": None,
            "excel_selector": None,
            "print_selector": None,
        },
        "result_type_inferred": "unknown",
        "pagination": {
            "has_pagination": False,
            "next_selector": None,
            "page_count_detected": None,
            "page_size_selector": None,
        },
        "risk": {
            "level": "high",
            "reasons": ["no auditado"],
            "recommended_strategy": "inspect_manually",
        },
        "diagnostics": {
            "screenshot_path": None,
            "html_path": None,
            "error": None,
        },
    }
    try:
        if not report_is_auditable(report):
            result["diagnostics"]["error"] = "Ítem no auditable: no apunta a /admin/reports/."
            if assisted:
                assisted_result = await assisted_pause(
                    page,
                    settings,
                    slug,
                    name,
                    "Ítem no auditable o reporte padre sin URL /admin/reports/.",
                )
                result["assisted"] = {
                    "decision": assisted_result.decision,
                    "event_path": str(assisted_result.event_path),
                    "detected_after_user_action": assisted_result.detected_after_user_action,
                }
            return result

        await open_report(page, report)
        result["opened_successfully"] = "login" not in page.url.lower()
        result["url"] = page.url

        evidence = await save_evidence(page, settings, f"audit_{slug}")
        result["diagnostics"]["html_path"] = evidence.get("html")
        result["diagnostics"]["screenshot_path"] = evidence.get("screenshot")

        filters = await detect_filters(page)
        actions = await detect_action_buttons(page)
        exports = await detect_export_buttons(page, actions)
        table_info = await detect_table(page)
        pagination = await detect_pagination(page)
        date_filter = await detect_date_range_controls(page, filters)
        result_type = infer_report_type(table_info, pagination, exports)
        risk = infer_extraction_strategy(result_type, date_filter, pagination, name)

        result["filters_detected"] = filters
        result["date_filter"] = date_filter
        result["actions_detected"] = actions
        result["exports_detected"] = exports
        result["result_type_inferred"] = result_type
        result["pagination"] = pagination
        result["risk"] = risk
        result["table_diagnostics"] = table_info
        if assisted and result_type == "unknown":
            assisted_result = await assisted_pause(page, settings, slug, name, "Reporte clasificado como unknown")
            result["assisted"] = {
                "decision": assisted_result.decision,
                "event_path": str(assisted_result.event_path),
                "detected_after_user_action": assisted_result.detected_after_user_action,
            }
            if assisted_result.decision == "retry":
                return await audit_report_page(page, settings, report, assisted=False)
            if assisted_result.decision == "skip":
                return result
            filters = await detect_filters(page)
            actions = await detect_action_buttons(page)
            exports = await detect_export_buttons(page, actions)
            table_info = await detect_table(page)
            pagination = await detect_pagination(page)
            date_filter = await detect_date_range_controls(page, filters)
            result_type = infer_report_type(table_info, pagination, exports)
            result["filters_detected"] = filters
            result["date_filter"] = date_filter
            result["actions_detected"] = actions
            result["exports_detected"] = exports
            result["result_type_inferred"] = result_type
            result["pagination"] = pagination
            result["risk"] = infer_extraction_strategy(result_type, date_filter, pagination, name)
            result["table_diagnostics"] = table_info
    except Exception as exc:
        logging.exception("Audit failed for report %s", name)
        result["diagnostics"]["error"] = repr(exc)
        if assisted:
            try:
                assisted_result = await assisted_pause(page, settings, slug, name, f"Error durante auditoría: {repr(exc)}")
                result["assisted"] = {
                    "decision": assisted_result.decision,
                    "event_path": str(assisted_result.event_path),
                    "detected_after_user_action": assisted_result.detected_after_user_action,
                }
                if assisted_result.decision == "retry":
                    return await audit_report_page(page, settings, report, assisted=False)
            except AssistedAbort:
                raise
            except Exception:
                logging.exception("Assisted pause failed for report %s", name)
        try:
            evidence = await save_evidence(page, settings, f"audit_error_{slug}")
            result["diagnostics"]["html_path"] = evidence.get("html")
            result["diagnostics"]["screenshot_path"] = evidence.get("screenshot")
        except Exception:
            pass
    return result


def generate_audit_markdown(audit: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Auditoría técnica módulo Informes ASNO/Wappsi")
    lines.append("")
    lines.append(f"Inicio: `{audit.get('audit_started_at')}`")
    lines.append(f"Fin: `{audit.get('audit_finished_at')}`")
    lines.append(f"URL informes: `{audit.get('reports_url')}`")
    lines.append(f"Total detectados: **{audit.get('total_reports_detected')}**")
    lines.append("")
    counts: dict[str, int] = {}
    for report in audit.get("reports", []):
        counts[report.get("result_type_inferred", "unknown")] = counts.get(report.get("result_type_inferred", "unknown"), 0) + 1
    lines.append("## Resumen por tipo")
    lines.append("")
    for key, value in sorted(counts.items()):
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    lines.append("## Informes")
    lines.append("")
    lines.append("| # | Informe | Categoría | Tipo | Riesgo | Estrategia | Filtros | Fecha | Export | Error |")
    lines.append("|---:|---|---|---|---|---|---:|---|---|---|")
    for idx, report in enumerate(audit.get("reports", []), start=1):
        exports = report.get("exports_detected", {})
        export_label = ", ".join(k for k, v in (("PDF", exports.get("has_pdf")), ("Excel", exports.get("has_excel")), ("Print", exports.get("has_print"))) if v) or "-"
        lines.append(
            "| {idx} | {name} | {cat} | {rtype} | {risk} | {strategy} | {filters} | {date} | {exports} | {error} |".format(
                idx=idx,
                name=str(report.get("name", "")).replace("|", "\\|"),
                cat=report.get("category_inferred"),
                rtype=report.get("result_type_inferred"),
                risk=report.get("risk", {}).get("level"),
                strategy=report.get("risk", {}).get("recommended_strategy"),
                filters=len(report.get("filters_detected", [])),
                date="sí" if report.get("date_filter", {}).get("has_date_filter") else "no",
                exports=export_label,
                error=(report.get("diagnostics", {}).get("error") or "").replace("|", "\\|")[:80],
            )
        )
    lines.append("")
    lines.append("## Decisión técnica")
    lines.append("")
    lines.append("- No se hizo extracción masiva.")
    lines.append("- No se consultaron rangos históricos de 4 años.")
    lines.append("- La auditoría abre pantallas y clasifica estructura/filtros/salidas.")
    lines.append("- La extracción futura debe respetar la estrategia recomendada por informe.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


async def audit_reports(page: Page, settings: Settings, *, assisted: bool = False, limit_reports: int | None = None) -> dict[str, Any]:
    settings.ensure_dirs()
    audit_start = now_iso()
    reports = await discover_reports(page, settings)
    audit_reports_list: list[dict[str, Any]] = []
    selected_reports = reports[:limit_reports] if limit_reports else reports
    for report in selected_reports:
        audit_reports_list.append(await audit_report_page(page, settings, report, assisted=assisted))

    audit = {
        "audit_started_at": audit_start,
        "audit_finished_at": now_iso(),
        "reports_url": settings.reports_url,
        "total_reports_detected": len(reports),
        "total_reports_audited": len(selected_reports),
        "assisted": assisted,
        "reports": audit_reports_list,
    }
    write_json(settings.audit_dir / "reports_audit.json", audit)
    generate_audit_markdown(audit, ROOT_DIR / "docs" / "audits" / "asno_reports_audit.md")
    generate_chatgpt_audit_markdown(audit, ROOT_DIR / "ASNO_REPORTS_AUDIT_FOR_CHATGPT.md")
    return audit
