from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


PRIORITY_REPORTS = [
    "Informe de Ventas",
    "Informe de Compras",
    "Informe Movimiento de Productos",
    "Cantidades en Bodega",
    "Informe Flujo de Caja Detallado",
    "Rentabilidad por Documento",
    "Rentabilidad por Cliente",
    "Rentabilidad por Producto",
    "Informe de Pagos",
    "Informe de Cliente",
    "Informe de proveedor",
]


def _yes(value: Any) -> str:
    return "sí" if bool(value) else "no"


def _clean(value: Any, default: str = "-") -> str:
    text = str(value).strip() if value is not None else ""
    return text or default


def _md(value: Any) -> str:
    return _clean(value).replace("|", "\\|").replace("\n", " ")


def _button_flags(actions: list[dict[str, Any]], exports: dict[str, Any]) -> dict[str, bool]:
    visible_actions = [item for item in actions if item.get("visible", True)]
    labels = " ".join(f"{item.get('label', '')} {item.get('href', '')}" for item in visible_actions).lower()
    return {
        "consultar": "consultar" in labels or "buscar" in labels or "filtrar" in labels,
        "generar": "generar" in labels,
        "guardar": "guardar" in labels,
        "pdf": bool(exports.get("has_pdf")),
        "excel": bool(exports.get("has_excel")),
        "imprimir": bool(exports.get("has_print")) or "imprimir" in labels or "print" in labels,
    }


def _report_type(report: dict[str, Any]) -> str:
    return str(report.get("result_type_inferred") or "unknown")


def _strategy(report: dict[str, Any]) -> str:
    return str(report.get("risk", {}).get("recommended_strategy") or "inspect_manually")


def _priority_level(report: dict[str, Any]) -> str:
    priority = int(report.get("priority_inferred") or 99)
    risk = str(report.get("risk", {}).get("level") or "high")
    if priority <= 5 or risk == "high":
        return "alta"
    if priority <= 11 or risk == "medium":
        return "media"
    return "baja"


def _find_report(reports: list[dict[str, Any]], wanted: str) -> dict[str, Any] | None:
    wanted_l = wanted.lower()
    exact = [item for item in reports if str(item.get("name", "")).lower() == wanted_l]
    if exact:
        return exact[0]
    contains = [item for item in reports if wanted_l in str(item.get("name", "")).lower()]
    if contains:
        return contains[0]
    reverse = [item for item in reports if str(item.get("name", "")).lower() in wanted_l]
    return reverse[0] if reverse else None


def _filter_names(report: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in report.get("filters_detected", []):
        label = _clean(item.get("label"), "")
        selector = _clean(item.get("selector"), "")
        ftype = _clean(item.get("type"), "unknown")
        fingerprint = f"{label} {selector} {item.get('name', '')} {item.get('id', '')}".lower()
        if any(token in fingerprint for token in ("gift_card", "card_no", "gc_value", "gc_expiry", "número de tarjeta", "numero de tarjeta", "fecha de caducidad")):
            continue
        if selector == "input[name=\"token\"]" or item.get("name") == "token":
            continue
        if label:
            names.append(f"{label} ({ftype})")
        elif selector:
            names.append(f"{selector} ({ftype})")
    return names


def _summary_json(audit: dict[str, Any]) -> dict[str, Any]:
    reports = audit.get("reports", [])
    by_type = lambda t: [r.get("name") for r in reports if _report_type(r) == t]
    unique_excel_reports = []
    seen_excel: set[str] = set()
    for report in reports:
        name = str(report.get("name") or "")
        if (_report_type(report) == "excel_download" or report.get("exports_detected", {}).get("has_excel")) and name not in seen_excel:
            unique_excel_reports.append(name)
            seen_excel.add(name)
    priority_reports = []
    for wanted in PRIORITY_REPORTS:
        found = _find_report(reports, wanted)
        if found:
            priority_reports.append(
                {
                    "name": found.get("name"),
                    "type": _report_type(found),
                    "strategy": _strategy(found),
                    "priority": _priority_level(found),
                }
            )
    recommended = _find_report(reports, "Informe de Ventas") or _find_report(reports, "Informe de Compras")
    return {
        "total_reports": audit.get("total_reports_detected", len(reports)),
        "pdf_reports": by_type("pdf_document"),
        "table_reports": by_type("table") + by_type("mixed"),
        "paginated_reports": by_type("paginated_table") + [r.get("name") for r in reports if _report_type(r) == "mixed" and r.get("pagination", {}).get("has_pagination")],
        "excel_reports": unique_excel_reports,
        "unknown_reports": by_type("unknown"),
        "priority_reports": priority_reports,
        "recommended_next_report": recommended.get("name") if recommended else "",
    }


def generate_chatgpt_audit_markdown(audit: dict[str, Any], path: Path) -> str:
    reports: list[dict[str, Any]] = audit.get("reports", [])
    counts = Counter(_report_type(report) for report in reports)
    opened = sum(1 for report in reports if report.get("opened_successfully"))
    errors = sum(1 for report in reports if report.get("diagnostics", {}).get("error"))
    pdf_count = counts.get("pdf_document", 0)
    table_count = counts.get("table", 0) + counts.get("paginated_table", 0) + counts.get("mixed", 0)
    pagination_count = sum(1 for report in reports if report.get("pagination", {}).get("has_pagination"))
    excel_count = sum(1 for report in reports if report.get("exports_detected", {}).get("has_excel"))
    unknown_count = counts.get("unknown", 0)

    lines: list[str] = []
    lines.append("# Auditoría módulo de informes ASNO/Wappsi")
    lines.append("")
    lines.append("## 1. Resumen general")
    lines.append("")
    lines.append(f"- URL auditada: `{audit.get('reports_url')}`")
    lines.append(f"- Fecha de auditoría: `{audit.get('audit_finished_at') or audit.get('audit_started_at')}`")
    lines.append(f"- Total informes detectados: **{audit.get('total_reports_detected', len(reports))}**")
    lines.append(f"- Informes abiertos correctamente: **{opened}**")
    lines.append(f"- Informes con error: **{errors}**")
    lines.append(f"- Informes tipo PDF: **{pdf_count}**")
    lines.append(f"- Informes tipo tabla: **{table_count}**")
    lines.append(f"- Informes con paginación: **{pagination_count}**")
    lines.append(f"- Informes con Excel: **{excel_count}**")
    lines.append(f"- Informes desconocidos: **{unknown_count}**")
    lines.append("")

    lines.append("## 2. Mapa general de informes detectados")
    lines.append("")
    lines.append("| # | Informe | URL | Categoría | Tipo detectado | Tiene fechas | Tiene rango fechas | Exporta PDF | Exporta Excel | Tiene tabla | Tiene paginación | Riesgo | Estrategia recomendada |")
    lines.append("|---:|---|---|---|---|---|---|---|---|---|---|---|---|")
    for idx, report in enumerate(reports, start=1):
        date_filter = report.get("date_filter", {})
        exports = report.get("exports_detected", {})
        table = report.get("table_diagnostics", {})
        pagination = report.get("pagination", {})
        lines.append(
            f"| {idx} | {_md(report.get('name'))} | {_md(report.get('url'))} | {_md(report.get('category_inferred'))} | {_md(_report_type(report))} | "
            f"{_yes(date_filter.get('has_date_filter'))} | {_yes(date_filter.get('has_range_option'))} | {_yes(exports.get('has_pdf'))} | "
            f"{_yes(exports.get('has_excel'))} | {_yes(table.get('has_table'))} | {_yes(pagination.get('has_pagination'))} | "
            f"{_md(report.get('risk', {}).get('level'))} | {_md(_strategy(report))} |"
        )
    lines.append("")

    lines.append("## 3. Detalle por informe")
    lines.append("")
    for report in reports:
        name = _clean(report.get("name"), "Informe sin nombre")
        date_filter = report.get("date_filter", {})
        actions = report.get("actions_detected", [])
        exports = report.get("exports_detected", {})
        table = report.get("table_diagnostics", {})
        pagination = report.get("pagination", {})
        buttons = _button_flags(actions, exports)
        filters = _filter_names(report)
        error = report.get("diagnostics", {}).get("error")
        reasons = report.get("risk", {}).get("reasons", [])

        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"URL: `{_clean(report.get('url'))}`")
        lines.append(f"Categoría inferida: `{_clean(report.get('category_inferred'))}`")
        lines.append(f"Tipo detectado: `{_report_type(report)}`")
        lines.append(f"Riesgo: `{_clean(report.get('risk', {}).get('level'))}`")
        lines.append(f"Estrategia recomendada: `{_strategy(report)}`")
        lines.append("")
        lines.append("Filtros detectados:")
        if filters:
            for item in filters[:80]:
                lines.append(f"- {item}")
        else:
            lines.append("- No se detectaron filtros visibles.")
        lines.append("")
        lines.append("Fecha:")
        lines.append(f"- Tiene filtro de fecha: {_yes(date_filter.get('has_date_filter'))}")
        lines.append(f"- Tiene opción rango de fechas: {_yes(date_filter.get('has_range_option'))}")
        lines.append(f"- Selector fecha inicial: `{_clean(date_filter.get('date_from_selector'))}`")
        lines.append(f"- Selector fecha final: `{_clean(date_filter.get('date_to_selector'))}`")
        lines.append(f"- Formato de fecha detectado: `{_clean(date_filter.get('date_format_detected'))}`")
        lines.append("")
        lines.append("Botones detectados:")
        lines.append(f"- Consultar: {_yes(buttons['consultar'])}")
        lines.append(f"- Generar: {_yes(buttons['generar'])}")
        lines.append(f"- Guardar: {_yes(buttons['guardar'])}")
        lines.append(f"- PDF: {_yes(buttons['pdf'])}")
        lines.append(f"- Excel: {_yes(buttons['excel'])}")
        lines.append(f"- Imprimir: {_yes(buttons['imprimir'])}")
        lines.append("")
        lines.append("Resultado:")
        lines.append(f"- Muestra tabla: {_yes(table.get('has_table'))}")
        lines.append(f"- Tiene paginación: {_yes(pagination.get('has_pagination'))}")
        lines.append(f"- Genera PDF: {_yes(exports.get('has_pdf'))}")
        lines.append(f"- Descarga Excel: {_yes(exports.get('has_excel'))}")
        lines.append("")
        lines.append("Observaciones:")
        if error:
            lines.append(f"- Error/advertencia: {error}")
        if reasons:
            for reason in reasons:
                lines.append(f"- {reason}")
        if _report_type(report) == "pdf_document":
            lines.append(f"- Regla PDF: en extracción futura generar una sola vez con rango completo `2022-01-01` hasta `{date.today().isoformat()}` y convertir el PDF resultante a JSON.")
        elif pagination.get("has_pagination"):
            lines.append("- Tiene paginación; no conviene usar rango completo si el volumen es alto.")
        elif table.get("has_table"):
            lines.append("- Tiene tabla; evaluar mensual o trimestral según volumen.")
        if not error and not reasons:
            lines.append("- Sin observaciones críticas en la auditoría superficial.")
        lines.append("")

    lines.append("## 4. Informes prioritarios para análisis financiero")
    lines.append("")
    lines.append("| Informe objetivo | Encontrado | Nombre detectado | Tipo | Estrategia recomendada | Prioridad |")
    lines.append("|---|---|---|---|---|---|")
    for wanted in PRIORITY_REPORTS:
        found = _find_report(reports, wanted)
        if found:
            lines.append(f"| {_md(wanted)} | sí | {_md(found.get('name'))} | {_md(_report_type(found))} | {_md(_strategy(found))} | {_priority_level(found)} |")
        else:
            lines.append(f"| {_md(wanted)} | no | - | - | - | baja |")
    lines.append("")

    pdf_reports = [report for report in reports if _report_type(report) == "pdf_document"]
    tabular_reports = [report for report in reports if _report_type(report) in {"table", "paginated_table", "mixed"}]
    excel_reports = [report for report in reports if report.get("exports_detected", {}).get("has_excel") or _report_type(report) == "excel_download"]
    unknown_reports = [report for report in reports if _report_type(report) == "unknown"]

    lines.append("## 5. Reglas recomendadas de extracción")
    lines.append("")
    lines.append("### Informes PDF/documento")
    lines.append("")
    lines.append(f"Estos informes deben extraerse una sola vez con rango completo `2022-01-01` hasta `{date.today().isoformat()}` y luego convertir el PDF a JSON:")
    if pdf_reports:
        for report in pdf_reports:
            lines.append(f"- {report.get('name')} (`pdf_full_range_once`)")
    else:
        lines.append("- No se detectaron informes puramente PDF.")
    lines.append("")

    lines.append("### Informes tabulares")
    lines.append("")
    lines.append("Estos informes no deben consultarse con rango completo si pueden cargar muchos registros. Recomendación: mensual para riesgo alto/paginación; trimestral para tablas livianas:")
    for report in tabular_reports:
        lines.append(f"- {report.get('name')}: `{_strategy(report)}`")
    lines.append("")

    lines.append("### Informes con Excel")
    lines.append("")
    lines.append("Cuando Excel exista, conviene priorizar descarga directa y normalización posterior antes que scraping celda por celda:")
    for report in excel_reports:
        lines.append(f"- {report.get('name')}: `{_strategy(report)}`")
    lines.append("")

    lines.append("### Informes desconocidos")
    lines.append("")
    lines.append("Estos requieren revisión manual o una regla específica adicional antes de automatizar extracción:")
    for report in unknown_reports:
        lines.append(f"- {report.get('name')}: `{_clean(report.get('diagnostics', {}).get('error'), 'sin error explícito; estructura no clasificada')}`")
    lines.append("")

    lines.append("## 6. Riesgos técnicos encontrados")
    lines.append("")
    lines.append("- Riesgo de carga: varios reportes tienen muchos filtros y tablas/paginación; no conviene consultar rangos grandes de una sola vez.")
    lines.append("- Riesgo de paginación: los informes paginados requieren recorrer páginas o descargar Excel si está disponible.")
    lines.append("- Riesgo de rango grande: ventas, compras, inventario, movimientos y cartera pueden pegar la web si se consulta todo el histórico junto.")
    lines.append("- Filtros difíciles: algunos reportes tienen más de 30 controles visibles; hay que mapear selectores estables antes de extraer.")
    lines.append("- Botones ocultos/dinámicos: algunos botones aparecen como links/íconos o se habilitan luego de elegir filtros.")
    lines.append("- Reportes sin exportación clara: los `unknown` no deben automatizarse hasta inspección específica.")
    lines.append("")

    recommended = _find_report(reports, "Informe de Ventas") or _find_report(reports, "Informe de Compras")
    lines.append("## 7. Próximo paso recomendado")
    lines.append("")
    if recommended:
        lines.append(f"El primer extractor real recomendado es **{recommended.get('name')}**.")
        lines.append("")
        lines.append("Motivo: es un informe financiero/comercial prioritario, tiene filtro de fechas y permite validar el patrón base de extracción por chunks mensuales sin sobrecargar ASNO. Una vez probado, el mismo patrón se puede reutilizar para compras, pagos, inventario y rentabilidad.")
    else:
        lines.append("Primero conviene implementar el extractor de un informe tabular con fecha y paginación, porque valida el caso más común y riesgoso.")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(_summary_json(audit), indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")

    content = "\n".join(lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return content
