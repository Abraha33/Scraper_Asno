from __future__ import annotations

import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

from playwright.async_api import Page

from .assisted import AssistedAbort, assisted_pause
from .config import ROOT_DIR, Settings
from .dom_utils import detect_action_buttons, detect_date_range_controls, detect_export_buttons, detect_filters, detect_pagination, detect_table
from .storage import now_iso, safe_name, save_evidence, write_json


DANGEROUS_RE = re.compile(
    r"\b(guardar|eliminar|borrar|anular|confirmar|pagar|cerrar caja|facturar|actualizar|enviar|crear|editar|procesar|aprobar|importar|sincronizar)\b",
    re.I,
)
DETAIL_RE = re.compile(r"\b(ver|detalle|detalles|view|show|consultar)\b", re.I)
SETTINGS_RE = re.compile(r"\b(config|settings|ajustes|par[aá]metros|preferencias|perfil|empresa)\b", re.I)
TRANSACTION_RE = re.compile(r"\b(venta|compra|pago|factura|pedido|orden|traslado|ajuste|egreso|recibo|nota)\b", re.I)
DOCUMENT_RE = re.compile(r"\b(reporte|informe|comprobante|documento|pdf|imprimir|zeta|balance|estado)\b", re.I)


PATTERN_DESCRIPTIONS = {
    "list_table": "Página con tabla simple.",
    "paginated_table": "Página con tabla + paginación.",
    "filter_table": "Página con filtros + tabla.",
    "filter_paginated_table": "Página con filtros + tabla + paginación.",
    "export_excel": "Página con botón/flujo Excel.",
    "export_pdf": "Página que genera PDF.",
    "report_document": "Página documental o reporte imprimible.",
    "crud_list": "Listado con acciones de ver/editar.",
    "detail_modal": "Detalles en modal/popup.",
    "detail_page": "Filas o acciones abren página de detalle.",
    "form_transaction": "Formulario transaccional; solo auditar.",
    "transaction_form": "Formulario transaccional; solo auditar.",
    "settings_page": "Página de configuración; solo lectura.",
    "dashboard": "Dashboard o tablero de indicadores.",
    "document_report": "Página documental o reporte imprimible.",
    "unknown": "Página no clasificada.",
}

RECOMMENDED_EXTRACTORS = {
    "list_table": "generic_table_extractor",
    "paginated_table": "generic_paginated_table_extractor",
    "filter_table": "generic_filter_table_extractor",
    "filter_paginated_table": "generic_filter_paginated_table_extractor",
    "export_excel": "generic_excel_download_detector",
    "export_pdf": "generic_pdf_document_detector",
    "report_document": "generic_document_report_detector",
    "crud_list": "generic_crud_list_reader",
    "detail_modal": "generic_detail_modal_reader",
    "detail_page": "generic_detail_page_reader",
    "form_transaction": "manual_review_transaction_form",
    "transaction_form": "manual_review_transaction_form",
    "settings_page": "manual_review_settings_reader",
    "dashboard": "generic_dashboard_reader",
    "document_report": "generic_document_report_detector",
    "unknown": "inspect_manually",
}

MODULE_KEYWORDS = {
    "ventas": ("sale", "sales", "venta", "factura", "pos", "quote", "budget"),
    "compras": ("purchase", "purchases", "compra", "proveedor", "quote"),
    "inventario": ("product", "products", "inventario", "stock", "warehouse", "bodega", "kardex", "marca", "category"),
    "traslados": ("transfer", "transfers", "traslado"),
    "clientes": ("customer", "customers", "cliente"),
    "proveedores": ("supplier", "suppliers", "proveedor"),
    "cartera": ("portfolio", "cartera", "debt", "debts", "credito", "credit"),
    "pagos": ("payment", "payments", "pago"),
    "caja": ("cash", "register", "caja", "pos_register"),
    "usuarios": ("user", "users", "staff", "usuario"),
    "configuración": ("setting", "settings", "config", "ajuste", "parametro", "parámetro"),
    "reportes": ("report", "reports", "informe"),
}


def _same_origin(url: str, base_url: str) -> bool:
    parsed = urlparse(url)
    base = urlparse(base_url)
    return parsed.scheme in {"http", "https"} and parsed.netloc == base.netloc


def _is_safe_internal_url(url: str, settings: Settings) -> bool:
    clean_url = urldefrag(url)[0]
    if not clean_url or clean_url.endswith("#"):
        return False
    if not _same_origin(clean_url, settings.asno_url):
        return False
    lowered = clean_url.lower()
    blocked = (
        "logout",
        "log_out",
        "delete",
        "remove",
        "destroy",
        "anular",
        "cancel",
        "pay",
        "pagar",
        "close_register",
        "cerrar",
        "facturar",
        "create",
        "new",
        "edit",
        "update",
        "store",
    )
    return not any(token in lowered for token in blocked)


def _module_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    lowered = path.lower()
    for module, tokens in MODULE_KEYWORDS.items():
        if any(token in lowered for token in tokens):
            return module
    parts = [part for part in path.split("/") if part and part not in {"holamigo", "admin"}]
    return parts[0] if parts else "root"


def _name_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    last = path.split("/")[-1] or "home"
    return last.replace("_", " ").replace("-", " ").title()


def system_root_url(settings: Settings) -> str:
    parsed = urlparse(settings.asno_url)
    path = parsed.path
    if "/admin" in path:
        path = path.split("/admin", 1)[0]
    return f"{parsed.scheme}://{parsed.netloc}{path.rstrip('/')}"


async def discover_internal_pages(page: Page, settings: Settings, *, start_url: str | None = None) -> list[dict[str, Any]]:
    """Collect internal URLs from current ASNO chrome without clicking dangerous controls."""
    crawl_start = start_url or settings.reports_url or system_root_url(settings)
    await page.goto(crawl_start, wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception:
        pass
    raw_links = await page.evaluate(
        """() => {
            const text = (el) => (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const items = [];
            for (const el of Array.from(document.querySelectorAll('a[href]'))) {
                items.push({
                    name: text(el),
                    href: el.href || el.getAttribute('href'),
                    visible: visible(el),
                    source: el.closest('aside,.sidebar,.navbar,.topbar,.menu,nav') ? 'navigation' : 'page',
                    class: el.getAttribute('class'),
                    id: el.getAttribute('id'),
                });
            }
            return items;
        }"""
    )
    pages_by_url: dict[str, dict[str, Any]] = {}
    for item in raw_links:
        href = str(item.get("href") or "")
        absolute = urldefrag(urljoin(settings.asno_url, href))[0]
        if not _is_safe_internal_url(absolute, settings):
            continue
        name = str(item.get("name") or "").strip() or _name_from_url(absolute)
        if absolute not in pages_by_url:
            pages_by_url[absolute] = {
                "name": name,
                "url": absolute,
                "module": _module_from_url(absolute),
                "source": item.get("source"),
                "visible_in_menu": bool(item.get("visible")),
            }
        elif item.get("visible"):
            pages_by_url[absolute]["visible_in_menu"] = True
            if name and len(name) > len(str(pages_by_url[absolute].get("name") or "")):
                pages_by_url[absolute]["name"] = name
    return sorted(pages_by_url.values(), key=lambda item: (item.get("module") or "", item.get("name") or "", item.get("url") or ""))


async def _detect_page_features(page: Page) -> dict[str, Any]:
    filters = await detect_filters(page)
    actions = await detect_action_buttons(page)
    exports = await detect_export_buttons(page, actions)
    table = await detect_table(page)
    pagination = await detect_pagination(page)
    date_filter = await detect_date_range_controls(page, filters)
    extra = await page.evaluate(
        """() => {
            const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            const text = (el) => (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
            const css = (el) => {
                if (!el || !el.tagName) return null;
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.getAttribute('name')) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.getAttribute('name'))}"]`;
                return el.tagName.toLowerCase();
            };
            const allActions = Array.from(document.querySelectorAll('button,input[type=button],input[type=submit],a.btn,a')).map((el, index) => ({
                index,
                label: text(el),
                href: el.href || el.getAttribute('href'),
                selector: css(el),
                tag: el.tagName.toLowerCase(),
                visible: visible(el),
                enabled: !el.disabled && !el.classList.contains('disabled')
            })).filter(x => x.visible && (x.label || x.href));
            const modals = Array.from(document.querySelectorAll('.modal, .swal2-container, .bootbox, [role="dialog"]')).filter(visible).map(el => ({
                selector: css(el),
                text: text(el).slice(0, 250),
            }));
            const detailLinks = allActions.filter(x => /detalle|detalles|ver|view|show|consultar/i.test(`${x.label} ${x.href || ''}`)).slice(0, 50);
            const forms = Array.from(document.querySelectorAll('form')).map((form, index) => ({
                index,
                selector: css(form),
                method: form.getAttribute('method'),
                action: form.getAttribute('action'),
                inputs: form.querySelectorAll('input,select,textarea').length,
                visible: visible(form),
                text: text(form).slice(0, 250),
            }));
            return { all_actions: allActions, modals, detail_links: detailLinks, forms };
        }"""
    )
    dangerous = [
        action
        for action in extra.get("all_actions", [])
        if DANGEROUS_RE.search(f"{action.get('label', '')} {action.get('href', '')}")
    ]
    return {
        "filters": filters,
        "actions": actions,
        "exports": exports,
        "table": table,
        "pagination": pagination,
        "date_filter": date_filter,
        "extra": extra,
        "dangerous_actions": dangerous,
    }


def _classify_page(page_info: dict[str, Any], features: dict[str, Any]) -> tuple[str, str, bool]:
    url = str(page_info.get("url") or "")
    name = str(page_info.get("name") or "")
    text_hint = f"{url} {name}".lower()
    filters = features.get("filters", [])
    table = features.get("table", {})
    pagination = features.get("pagination", {})
    exports = features.get("exports", {})
    extra = features.get("extra", {})
    dangerous = features.get("dangerous_actions", [])
    has_filters = any(item.get("visible") and item.get("enabled") for item in filters)
    has_table = bool(table.get("visible_table_count") or table.get("has_table"))
    has_pagination = bool(pagination.get("has_pagination"))
    has_modal = bool(extra.get("modals"))
    detail_links = extra.get("detail_links", [])
    forms = [form for form in extra.get("forms", []) if form.get("visible") and form.get("inputs", 0) > 1]
    has_dangerous_form = bool(forms and dangerous)

    if re.search(r"\b(dashboard|tablero|inicio|calendar|calendario)\b", text_hint):
        return "dashboard", "medium", False
    if SETTINGS_RE.search(text_hint):
        return "settings_page", "medium", False
    if forms and not has_table:
        return "form_transaction", "high" if has_dangerous_form else "medium", False
    if has_dangerous_form and not has_table:
        return "form_transaction", "high", False
    if exports.get("has_print") and not has_table:
        return "report_document", "medium", False
    if has_modal:
        return "detail_modal", "medium", False
    if detail_links and has_table:
        if any(str(link.get("href") or "").startswith("http") and str(link.get("href") or "") != url for link in detail_links):
            return "detail_page", "medium", False
        return "crud_list", "medium", False
    if has_table and has_filters and has_pagination:
        return "filter_paginated_table", "high", False
    if has_table and has_filters:
        return "filter_table", "high", False
    if has_table and has_pagination:
        return "paginated_table", "high", False
    if has_table:
        return "list_table", "high", False
    if exports.get("has_excel"):
        return "export_excel", "medium", False
    if exports.get("has_pdf"):
        return "export_pdf", "medium", False
    if DOCUMENT_RE.search(text_hint) and (exports.get("has_print") or forms):
        return "report_document", "medium", False
    if TRANSACTION_RE.search(text_hint) and forms:
        return "form_transaction", "medium", False
    return "unknown", "low", True


def _recommended_strategy(pattern: str, dangerous: list[dict[str, Any]]) -> str:
    if dangerous:
        return "read_only_manual_review_before_extractor"
    if pattern == "unknown":
        return "inspect_manually"
    if pattern in {"form_transaction", "settings_page"}:
        return "read_only_audit_only"
    return "use_generic_pattern_extractor"


async def audit_one_site_page(page: Page, settings: Settings, page_info: dict[str, Any], *, assisted: bool = False) -> dict[str, Any]:
    name = str(page_info.get("name") or _name_from_url(str(page_info.get("url"))))
    url = str(page_info.get("url"))
    slug = safe_name(f"site_pattern_{name}_{urlparse(url).path}")
    result: dict[str, Any] = {
        "name": name,
        "url": url,
        "module": page_info.get("module") or _module_from_url(url),
        "pattern": "unknown",
        "confidence": "low",
        "has_filters": False,
        "has_date_filter": False,
        "has_table": False,
        "has_pagination": False,
        "has_excel": False,
        "has_pdf": False,
        "has_modal": False,
        "dangerous_actions_detected": [],
        "recommended_strategy": "inspect_manually",
        "needs_manual_review": True,
        "screenshot_path": None,
        "html_path": None,
        "diagnostics": {},
    }
    try:
        await page.goto(url, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        evidence = await save_evidence(page, settings, slug)
        features = await _detect_page_features(page)
        pattern, confidence, needs_manual_review = _classify_page(page_info, features)
        exports = features["exports"]
        table = features["table"]
        pagination = features["pagination"]
        extra = features["extra"]
        date_filter = features["date_filter"]
        dangerous = features["dangerous_actions"]
        result.update(
            {
                "name": name,
                "url": page.url,
                "module": page_info.get("module") or _module_from_url(page.url),
                "pattern": pattern,
                "confidence": confidence,
                "has_filters": bool(features["filters"]),
                "has_date_filter": bool(date_filter.get("has_date_filter")),
                "has_table": bool(table.get("visible_table_count") or table.get("has_table")),
                "has_pagination": bool(pagination.get("has_pagination")),
                "has_excel": bool(exports.get("has_excel")),
                "has_pdf": bool(exports.get("has_pdf")),
                "has_modal": bool(extra.get("modals")),
                "dangerous_actions_detected": dangerous,
                "recommended_strategy": _recommended_strategy(pattern, dangerous),
                "needs_manual_review": bool(needs_manual_review or dangerous),
                "screenshot_path": evidence.get("screenshot"),
                "html_path": evidence.get("html"),
                "diagnostics": {
                    "filters_count": len(features["filters"]),
                    "actions_count": len(features["actions"]),
                    "forms_count": len(extra.get("forms", [])),
                    "detail_links_count": len(extra.get("detail_links", [])),
                    "visible_table_count": table.get("visible_table_count"),
                    "data_tables_count": table.get("data_tables_count"),
                    "pagination": pagination,
                    "exports": exports,
                },
            }
        )
        if assisted and pattern == "unknown":
            assisted_result = await assisted_pause(page, settings, slug, name, "No pude clasificar esta página.")
            result["assisted"] = {
                "decision": assisted_result.decision,
                "event_path": str(assisted_result.event_path),
                "detected_after_user_action": assisted_result.detected_after_user_action,
            }
            if assisted_result.decision == "retry":
                return await audit_one_site_page(page, settings, page_info, assisted=False)
            if assisted_result.decision == "abort":
                raise AssistedAbort("audit-site-patterns aborted by user")
    except AssistedAbort:
        raise
    except Exception as exc:
        logging.exception("Site pattern audit failed for %s", url)
        result["diagnostics"]["error"] = repr(exc)
        result["needs_manual_review"] = True
        try:
            evidence = await save_evidence(page, settings, f"site_pattern_error_{slug}")
            result["screenshot_path"] = evidence.get("screenshot")
            result["html_path"] = evidence.get("html")
        except Exception:
            pass
    return result


def _summarize_patterns(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        grouped[str(page.get("pattern") or "unknown")].append(page)
    patterns: list[dict[str, Any]] = []
    for pattern, items in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        patterns.append(
            {
                "pattern_id": pattern,
                "description": PATTERN_DESCRIPTIONS.get(pattern, PATTERN_DESCRIPTIONS["unknown"]),
                "pages_count": len(items),
                "sample_pages": [{"name": item.get("name"), "url": item.get("url")} for item in items[:5]],
                "recommended_extractor": RECOMMENDED_EXTRACTORS.get(pattern, "inspect_manually"),
                "confidence": "high" if all(item.get("confidence") == "high" for item in items) else "medium",
            }
        )
    return patterns


def generate_site_patterns_markdown(audit: dict[str, Any], path: Path) -> None:
    pages = audit.get("pages", [])
    patterns = audit.get("patterns", [])
    lines: list[str] = [
        "# Auditoría de patrones ASNO",
        "",
        "## Resumen",
        "",
        f"- Total páginas detectadas: **{audit.get('total_pages', 0)}**",
        f"- Total patrones encontrados: **{audit.get('total_patterns', 0)}**",
        f"- Páginas clasificadas: **{sum(1 for item in pages if item.get('pattern') != 'unknown')}**",
        f"- Páginas desconocidas: **{len(audit.get('unknown_pages', []))}**",
        f"- Páginas con acciones peligrosas: **{len(audit.get('dangerous_pages', []))}**",
        "",
        "## Patrones encontrados",
        "",
        "| Patrón | Cantidad páginas | Ejemplos | Extractor recomendado |",
        "|---|---:|---|---|",
    ]
    for pattern in patterns:
        examples = ", ".join(str(item.get("name") or item.get("url")) for item in pattern.get("sample_pages", [])[:3])
        lines.append(
            f"| `{pattern.get('pattern_id')}` | {pattern.get('pages_count')} | {examples or '-'} | `{pattern.get('recommended_extractor')}` |"
        )
    lines.extend(["", "## Páginas por patrón", ""])
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        grouped[str(page.get("pattern") or "unknown")].append(page)
    for pattern, items in sorted(grouped.items()):
        lines.append(f"### {pattern}")
        lines.append("")
        for item in items:
            danger = " ⚠️" if item.get("dangerous_actions_detected") else ""
            lines.append(f"- {item.get('name')}{danger}: `{item.get('url')}`")
        lines.append("")
    lines.extend(["## Excepciones", ""])
    if audit.get("unknown_pages"):
        lines.append("### Páginas unknown")
        for item in audit["unknown_pages"]:
            lines.append(f"- {item.get('name')}: `{item.get('url')}`")
        lines.append("")
    if audit.get("dangerous_pages"):
        lines.append("### Páginas con acciones peligrosas")
        for item in audit["dangerous_pages"]:
            labels = ", ".join(str(action.get("label") or action.get("href")) for action in item.get("dangerous_actions_detected", [])[:8])
            lines.append(f"- {item.get('name')}: `{item.get('url')}` — {labels}")
        lines.append("")
    if not audit.get("unknown_pages") and not audit.get("dangerous_pages"):
        lines.append("- No se detectaron excepciones críticas.")
        lines.append("")
    next_pattern = next(
        (pattern for pattern in patterns if pattern.get("pattern_id") in {"filter_paginated_table", "paginated_table", "filter_table", "list_table"}),
        patterns[0] if patterns else None,
    )
    lines.extend(["## Próximo paso recomendado", ""])
    if next_pattern:
        lines.append(
            f"Construir primero `{next_pattern.get('recommended_extractor')}` para el patrón `{next_pattern.get('pattern_id')}`, "
            f"porque cubre {next_pattern.get('pages_count')} página(s) y permite reutilización segura read-only."
        )
    else:
        lines.append("Repetir auditoría con más páginas visibles; no hay patrón dominante suficiente.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def audit_site_patterns(
    page: Page,
    settings: Settings,
    *,
    assisted: bool = False,
    limit_pages: int | None = None,
) -> dict[str, Any]:
    settings.ensure_dirs()
    started_at = now_iso()
    discovered = await discover_internal_pages(page, settings)
    selected = discovered[:limit_pages] if limit_pages else discovered
    audited_pages: list[dict[str, Any]] = []
    for item in selected:
        audited_pages.append(await audit_one_site_page(page, settings, item, assisted=assisted))
    patterns = _summarize_patterns(audited_pages)
    audit = {
        "audit_started_at": started_at,
        "audit_finished_at": now_iso(),
        "assisted": assisted,
        "total_pages": len(discovered),
        "total_pages_audited": len(selected),
        "total_patterns": len(patterns),
        "patterns": patterns,
        "pages": audited_pages,
        "unknown_pages": [item for item in audited_pages if item.get("pattern") == "unknown"],
        "dangerous_pages": [item for item in audited_pages if item.get("dangerous_actions_detected")],
    }
    write_json(settings.audit_dir / "site_patterns.json", audit)
    generate_site_patterns_markdown(audit, ROOT_DIR / "docs" / "audits" / "asno_site_patterns_audit.md")
    return audit


def _system_pattern(pattern: str) -> str:
    return {
        "report_document": "document_report",
        "form_transaction": "transaction_form",
    }.get(pattern, pattern)


def _system_page(page: dict[str, Any]) -> dict[str, Any]:
    pattern = _system_pattern(str(page.get("pattern") or "unknown"))
    dangerous = page.get("dangerous_actions_detected", [])
    return {
        "name": page.get("name"),
        "url": page.get("url"),
        "module": page.get("module") or _module_from_url(str(page.get("url") or "")),
        "pattern": pattern,
        "read_only_safe": not bool(dangerous),
        "has_filters": page.get("has_filters", False),
        "has_date_filter": page.get("has_date_filter", False),
        "has_table": page.get("has_table", False),
        "has_pagination": page.get("has_pagination", False),
        "has_modal": page.get("has_modal", False),
        "has_excel": page.get("has_excel", False),
        "has_pdf": page.get("has_pdf", False),
        "dangerous_actions_detected": dangerous,
        "recommended_strategy": RECOMMENDED_EXTRACTORS.get(pattern, RECOMMENDED_EXTRACTORS.get(str(page.get("pattern")), "inspect_manually")),
        "needs_assisted_review": bool(page.get("pattern") == "unknown" or page.get("needs_manual_review")),
        "screenshot_path": page.get("screenshot_path"),
        "html_path": page.get("html_path"),
    }


def _summarize_system_patterns(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        grouped[str(page.get("pattern") or "unknown")].append(page)
    return [
        {
            "pattern_id": pattern,
            "description": PATTERN_DESCRIPTIONS.get(pattern, PATTERN_DESCRIPTIONS.get("unknown")),
            "pages_count": len(items),
            "sample_pages": [{"name": item.get("name"), "url": item.get("url")} for item in items[:5]],
            "recommended_extractor": RECOMMENDED_EXTRACTORS.get(pattern, "inspect_manually"),
        }
        for pattern, items in sorted(grouped.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]


def generate_system_markdown(audit: dict[str, Any], path: Path) -> None:
    pages = audit.get("pages", [])
    modules = audit.get("modules_detected", [])
    patterns = audit.get("patterns_detected", [])
    lines = [
        "# Auditoría completa ASNO",
        "",
        "## Resumen",
        "",
        f"- URLs detectadas: **{audit.get('total_urls_detected', 0)}**",
        f"- Páginas auditadas: **{audit.get('total_pages_audited', 0)}**",
        f"- Módulos encontrados: **{len(modules)}**",
        f"- Patrones encontrados: **{len(patterns)}**",
        f"- Páginas seguras: **{sum(1 for page in pages if page.get('read_only_safe'))}**",
        f"- Páginas peligrosas: **{len(audit.get('dangerous_pages', []))}**",
        f"- Páginas desconocidas: **{len(audit.get('unknown_pages', []))}**",
        "",
        "## Módulos detectados",
        "",
    ]
    for module in modules:
        count = sum(1 for page in pages if page.get("module") == module)
        lines.append(f"- `{module}`: {count} página(s)")
    lines.extend(["", "## Patrones detectados", "", "| Patrón | Páginas | Extractor recomendado |", "|---|---:|---|"])
    for pattern in patterns:
        lines.append(f"| `{pattern.get('pattern_id')}` | {pattern.get('pages_count')} | `{pattern.get('recommended_extractor')}` |")
    lines.extend(["", "## Páginas por módulo", ""])
    by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        by_module[str(page.get("module") or "desconocido")].append(page)
    for module, items in sorted(by_module.items()):
        lines.append(f"### {module}")
        lines.append("")
        for item in items:
            danger = " ⚠️" if item.get("dangerous_actions_detected") else ""
            lines.append(f"- `{item.get('pattern')}` — {item.get('name')}{danger}: `{item.get('url')}`")
        lines.append("")
    lines.extend(["## Páginas por patrón", ""])
    by_pattern: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        by_pattern[str(page.get("pattern") or "unknown")].append(page)
    for pattern, items in sorted(by_pattern.items()):
        lines.append(f"### {pattern}")
        lines.append("")
        for item in items:
            lines.append(f"- {item.get('name')}: `{item.get('url')}`")
        lines.append("")
    lines.extend(["## Acciones peligrosas detectadas", ""])
    if audit.get("dangerous_pages"):
        for page in audit["dangerous_pages"]:
            labels = ", ".join(str(action.get("label") or action.get("href")) for action in page.get("dangerous_actions_detected", [])[:10])
            lines.append(f"- {page.get('name')}: `{page.get('url')}` — {labels}")
    else:
        lines.append("- No se detectaron acciones peligrosas visibles.")
    lines.extend(["", "## Extractores recomendados", ""])
    for pattern in patterns:
        lines.append(f"- `{pattern.get('pattern_id')}` → `{pattern.get('recommended_extractor')}`")
    lines.extend(["", "## Próximo paso", ""])
    next_pattern = next((p for p in patterns if p.get("pattern_id") == "filter_paginated_table"), patterns[0] if patterns else None)
    if next_pattern:
        lines.append(
            f"Construir primero `{next_pattern.get('recommended_extractor')}` porque el patrón "
            f"`{next_pattern.get('pattern_id')}` cubre {next_pattern.get('pages_count')} página(s)."
        )
    else:
        lines.append("Repetir auditoría con más navegación asistida; no hay patrones suficientes.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def audit_system(
    page: Page,
    settings: Settings,
    *,
    assisted: bool = False,
    limit_pages: int | None = None,
    patterns: bool = False,
) -> dict[str, Any]:
    settings.ensure_dirs()
    started_at = now_iso()
    base_url = system_root_url(settings)
    discovered = await discover_internal_pages(page, settings, start_url=base_url)
    selected = discovered[:limit_pages] if limit_pages else discovered
    raw_pages: list[dict[str, Any]] = []
    for index, item in enumerate(selected, start=1):
        raw_pages.append(await audit_one_site_page(page, settings, item, assisted=assisted))
        partial_system_pages = [_system_page(raw_item) for raw_item in raw_pages]
        write_json(
            settings.audit_dir / "system_map.partial.json",
            {
                "audit_type": "system_partial",
                "audit_started_at": started_at,
                "audit_updated_at": now_iso(),
                "base_url": base_url,
                "assisted": assisted,
                "patterns_config_used": patterns,
                "total_urls_detected": len(discovered),
                "total_pages_target": len(selected),
                "total_pages_audited": index,
                "pages": partial_system_pages,
                "unknown_pages": [page_item for page_item in partial_system_pages if page_item.get("pattern") == "unknown"],
                "dangerous_pages": [page_item for page_item in partial_system_pages if page_item.get("dangerous_actions_detected")],
            },
        )
    system_pages = [_system_page(item) for item in raw_pages]
    patterns = _summarize_system_patterns(system_pages)
    modules = sorted({str(item.get("module") or "desconocido") for item in system_pages})
    audit = {
        "audit_type": "system",
        "audit_started_at": started_at,
        "audit_finished_at": now_iso(),
        "base_url": base_url,
        "assisted": assisted,
        "patterns_config_used": patterns,
        "total_urls_detected": len(discovered),
        "total_pages_audited": len(selected),
        "patterns_detected": patterns,
        "modules_detected": modules,
        "pages": system_pages,
        "unknown_pages": [item for item in system_pages if item.get("pattern") == "unknown"],
        "dangerous_pages": [item for item in system_pages if item.get("dangerous_actions_detected")],
    }
    write_json(settings.audit_dir / "system_map.json", audit)
    generate_system_markdown(audit, ROOT_DIR / "docs" / "audits" / "asno_system_audit.md")
    return audit
