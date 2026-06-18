from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from .config import Settings
from .state_detector import detect_state_after_manual_action
from .storage import append_jsonl, now_iso, safe_name, write_json


MODULES: dict[str, dict[str, str]] = {
    "transfers": {"name": "Informe de traslados", "url": "/admin/reports/transfers"},
}

SENSITIVE_RE = re.compile(r"(password|passwd|pass|secret|token|credential|api[_-]?key)", re.I)
DANGEROUS_RE = re.compile(
    r"\b(guardar|eliminar|borrar|anular|confirmar|pagar|cerrar caja|facturar|actualizar)\b",
    re.I,
)


@dataclass(frozen=True)
class TeachTarget:
    slug: str
    name: str
    url: str


def resolve_teach_target(settings: Settings, module: str | None, url: str | None, name: str | None) -> TeachTarget:
    if module:
        item = MODULES.get(module)
        if not item:
            known = ", ".join(sorted(MODULES)) or "none"
            raise SystemExit(f"Unknown teach module: {module}. Known modules: {known}")
        return TeachTarget(slug=safe_name(module), name=item["name"], url=_absolute_url(settings, item["url"]))
    if not url:
        raise SystemExit("teach requires --module or --url")
    display_name = name or url.rstrip("/").split("/")[-1].replace("_", " ").title()
    return TeachTarget(slug=safe_name(name or url), name=display_name, url=_absolute_url(settings, url))


def _absolute_url(settings: Settings, url: str) -> str:
    if url.startswith("http"):
        return url
    base = (settings.reports_url or "").split("/admin/reports")[0].rstrip("/")
    if not base:
        base = settings.asno_url.split("/admin/auth/login")[0].split("/login")[0].rstrip("/")
    return f"{base}/{url.lstrip('/')}"


def _timestamp_for_path() -> str:
    return now_iso().replace(":", "_")


def _redact_text(value: Any, hint: str = "") -> Any:
    if value is None:
        return None
    text = str(value)
    if SENSITIVE_RE.search(hint) or SENSITIVE_RE.search(text):
        return "[REDACTED]"
    if len(text) > 500:
        return text[:500] + "...[TRUNCATED]"
    return text


def _redact_html(html: str) -> str:
    html = re.sub(
        r'(?is)(<input[^>]+type=["\']?password["\']?[^>]*value=["\'])(.*?)(["\'])',
        r"\1[REDACTED]\3",
        html,
    )
    html = re.sub(
        r'(?i)("?(?:password|secret|token|key)"?\s*[:=]\s*["\']?)([^"\'<>,} ]+)',
        r"\1[REDACTED]",
        html,
    )
    return html


async def _save_html_and_screenshot(page: Page, directory: Path, prefix: str) -> dict[str, str]:
    html_path = directory / f"{prefix}.html"
    png_path = directory / f"{prefix}.png"
    if page.is_closed():
        return {"html": "", "screenshot": "", "error": "page_closed"}
    try:
        html_path.write_text(_redact_html(await page.content()), encoding="utf-8")
    except Exception as exc:
        return {"html": "", "screenshot": "", "error": f"content_unavailable: {type(exc).__name__}: {exc}"}
    try:
        await page.screenshot(path=png_path, full_page=True, timeout=20_000)
    except Exception as exc:
        return {"html": str(html_path), "screenshot": "", "error": f"screenshot_unavailable: {type(exc).__name__}: {exc}"}
    return {"html": str(html_path), "screenshot": str(png_path)}


async def inject_finish_button(page: Page) -> None:
    await page.evaluate(
        """() => {
            const existing = document.getElementById('__asno_teach_finish_button');
            if (existing) existing.remove();
            const button = document.createElement('button');
            button.id = '__asno_teach_finish_button';
            button.type = 'button';
            button.textContent = 'Finalizar enseñanza';
            button.style.position = 'fixed';
            button.style.top = '12px';
            button.style.right = '12px';
            button.style.zIndex = '2147483647';
            button.style.background = '#dc2626';
            button.style.color = 'white';
            button.style.border = '2px solid white';
            button.style.borderRadius = '10px';
            button.style.padding = '10px 14px';
            button.style.fontSize = '14px';
            button.style.fontWeight = '700';
            button.style.boxShadow = '0 6px 18px rgba(0,0,0,.25)';
            button.style.cursor = 'pointer';
            button.style.opacity = '0.94';
            button.addEventListener('click', async () => {
                button.textContent = 'Finalizando...';
                button.disabled = true;
                if (window.finishTeachMode) await window.finishTeachMode();
            });
            document.documentElement.appendChild(button);
        }"""
    )


async def _inject_event_recorder(page: Page) -> None:
    await page.evaluate(
        """() => {
            if (window.__ASNO_TEACH_RECORDER_INSTALLED__) return;
            window.__ASNO_TEACH_RECORDER_INSTALLED__ = true;
            const visible = (el) => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
            const clean = (value, max = 300) => (value || '').toString().replace(/\\s+/g, ' ').trim().slice(0, max);
            const cssPath = (el) => {
                if (!el || !el.tagName) return null;
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.name) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.name)}"]`;
                const parts = [];
                let cur = el;
                while (cur && cur.nodeType === 1 && parts.length < 5) {
                    let part = cur.tagName.toLowerCase();
                    if (cur.className && typeof cur.className === 'string') {
                        const cls = cur.className.split(/\\s+/).filter(Boolean)[0];
                        if (cls) part += `.${CSS.escape(cls)}`;
                    }
                    const parent = cur.parentElement;
                    if (parent) {
                        const same = Array.from(parent.children).filter(x => x.tagName === cur.tagName);
                        if (same.length > 1) part += `:nth-of-type(${same.indexOf(cur) + 1})`;
                    }
                    parts.unshift(part);
                    cur = parent;
                }
                return parts.join(' > ');
            };
            const xpath = (el) => {
                if (!el || !el.tagName) return null;
                if (el.id) return `//*[@id="${el.id}"]`;
                const parts = [];
                let cur = el;
                while (cur && cur.nodeType === 1) {
                    let ix = 1;
                    let sib = cur.previousElementSibling;
                    while (sib) {
                        if (sib.tagName === cur.tagName) ix++;
                        sib = sib.previousElementSibling;
                    }
                    parts.unshift(`${cur.tagName.toLowerCase()}[${ix}]`);
                    cur = cur.parentElement;
                }
                return '/' + parts.join('/');
            };
            const labelFor = (el) => {
                if (!el) return '';
                if (el.id) {
                    const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                    if (label) return clean(label.innerText);
                }
                const label = el.closest('label');
                if (label) return clean(label.innerText);
                const group = el.closest('.form-group, .control-group, .row, td, th');
                return group ? clean(group.querySelector('label')?.innerText || '') : '';
            };
            const payload = (type, el) => {
                const hint = `${el?.id || ''} ${el?.name || ''} ${el?.type || ''} ${labelFor(el)}`;
                const rawValue = el && 'value' in el ? String(el.value || '') : null;
                return {
                    type,
                    url: location.href,
                    tag: el?.tagName ? el.tagName.toLowerCase() : null,
                    input_type: el?.getAttribute ? el.getAttribute('type') : null,
                    selector: cssPath(el),
                    xpath: xpath(el),
                    id: el?.id || null,
                    name: el?.getAttribute ? el.getAttribute('name') : null,
                    role: el?.getAttribute ? el.getAttribute('role') : null,
                    aria_label: el?.getAttribute ? el.getAttribute('aria-label') : null,
                    label: labelFor(el),
                    text: clean(el?.innerText || el?.textContent || rawValue),
                    value: /password|secret|token|credential|key/i.test(hint) ? '[REDACTED]' : clean(rawValue, 500),
                    checked: el && 'checked' in el ? !!el.checked : null,
                    dangerous: /guardar|eliminar|borrar|anular|confirmar|pagar|cerrar caja|facturar|actualizar/i.test(`${el?.innerText || ''} ${el?.value || ''} ${labelFor(el)}`),
                };
            };
            const send = (event) => {
                try {
                    if (window.__asnoTeachRecordEvent) window.__asnoTeachRecordEvent(event);
                } catch (_) {}
            };
            document.addEventListener('click', (ev) => {
                if (ev.target && ev.target.id === '__asno_teach_finish_button') return;
                send(payload('click', ev.target));
            }, true);
            document.addEventListener('change', (ev) => send(payload('change', ev.target)), true);
            document.addEventListener('input', (ev) => {
                const el = ev.target;
                if (el && ['INPUT', 'TEXTAREA'].includes(el.tagName)) send(payload('input', el));
            }, true);
            let lastState = '';
            const inspectDom = () => {
                const tables = Array.from(document.querySelectorAll('table')).filter(visible).map((table) => ({
                    selector: table.id ? `#${CSS.escape(table.id)}` : cssPath(table),
                    columns: Array.from(table.querySelectorAll('thead th, tr:first-child th')).map(th => clean(th.innerText)).filter(Boolean),
                    rows_visible: table.querySelectorAll('tbody tr, tr').length,
                    text_sample: clean(table.innerText, 250),
                })).slice(0, 5);
                const modals = Array.from(document.querySelectorAll('.modal, .swal2-container, .bootbox, [role="dialog"]')).filter(visible)
                    .map(el => ({ selector: el.id ? `#${CSS.escape(el.id)}` : cssPath(el), text: clean(el.innerText, 250) })).slice(0, 5);
                const exports = Array.from(document.querySelectorAll('a,button,input[type="button"],input[type="submit"]')).filter(visible)
                    .filter(el => /pdf|excel|xls|xlsx|csv|imprimir|guardar|consultar|generar/i.test(`${el.innerText || ''} ${el.value || ''} ${el.href || ''}`))
                    .map(el => payload('dom_action_visible', el)).slice(0, 20);
                const pagination = Array.from(document.querySelectorAll('.dataTables_paginate, .pagination, a.paginate_button, li.next')).filter(visible)
                    .map(el => ({ selector: el.id ? `#${CSS.escape(el.id)}` : cssPath(el), text: clean(el.innerText, 250) })).slice(0, 5);
                const state = JSON.stringify({ url: location.href, tables, modals, exports, pagination });
                if (state !== lastState) {
                    lastState = state;
                    send({ type: 'dom_state', url: location.href, tables, modals, exports, pagination });
                }
            };
            const observer = new MutationObserver(() => window.clearTimeout(window.__ASNO_TEACH_DOM_TIMER__) || (window.__ASNO_TEACH_DOM_TIMER__ = window.setTimeout(inspectDom, 400)));
            observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true });
            window.setInterval(inspectDom, 3000);
            inspectDom();
        }"""
    )


async def record_browser_events(page: Page, events_path: Path, dom_snapshots_path: Path) -> None:
    events_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.touch(exist_ok=True)
    dom_snapshots_path.touch(exist_ok=True)

    def append_event(payload: dict[str, Any]) -> None:
        clean_payload = _sanitize_event(payload)
        clean_payload["recorded_at"] = now_iso()
        if clean_payload.get("type") == "dom_state":
            append_jsonl(dom_snapshots_path, clean_payload)
        else:
            append_jsonl(events_path, clean_payload)

    try:
        await page.expose_function("__asnoTeachRecordEvent", append_event)
    except Exception:
        pass
    page.on(
        "download",
        lambda download: append_event(
            {
                "type": "download_started",
                "url": page.url,
                "suggested_filename": _redact_text(download.suggested_filename),
            }
        ),
    )
    page.on("framenavigated", lambda frame: append_event({"type": "url_changed", "url": frame.url}) if frame == page.main_frame else None)
    await _inject_event_recorder(page)


def _sanitize_event(payload: dict[str, Any]) -> dict[str, Any]:
    clean = dict(payload)
    hint = " ".join(str(clean.get(key) or "") for key in ("id", "name", "label", "selector", "input_type"))
    for key in ("value", "text", "label", "aria_label", "name", "id"):
        clean[key] = _redact_text(clean.get(key), hint)
    if DANGEROUS_RE.search(" ".join(str(clean.get(key) or "") for key in ("text", "label", "value"))):
        clean["dangerous"] = True
    return clean


async def _wait_for_finish(page: Page, directory: Path) -> str:
    loop = asyncio.get_running_loop()
    finish_future: asyncio.Future[str] = loop.create_future()

    async def finish_teach_mode() -> None:
        if not finish_future.done():
            finish_future.set_result("button")

    def finish_on_page_close() -> None:
        if not finish_future.done():
            finish_future.set_result("page_closed")

    page.on("close", lambda: finish_on_page_close())
    try:
        await page.expose_function("finishTeachMode", finish_teach_mode)
    except Exception:
        pass
    await inject_finish_button(page)
    auto_finish = os.getenv("ASNO_TEACH_AUTO_FINISH_SECONDS", "").strip()
    if auto_finish:
        async def auto() -> str:
            await asyncio.sleep(float(auto_finish))
            return "auto_finish"
        tasks = [asyncio.create_task(auto())]
    else:
        tasks = []

    async def terminal() -> str:
        try:
            await asyncio.to_thread(input, "Fallback: presioná ENTER acá para finalizar enseñanza si el botón no funciona...")
            return "terminal_enter"
        except EOFError:
            finish_file = directory / "FINISH"
            print(f"Terminal no interactiva. Fallback: creá este archivo para finalizar: {finish_file}")
            while not finish_file.exists():
                await asyncio.sleep(1)
            return "finish_file"

    tasks.extend([asyncio.ensure_future(finish_future), asyncio.create_task(terminal())])
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    return next(iter(done)).result()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def infer_recipe_from_events(target: TeachTarget, events: list[dict[str, Any]], dom_states: list[dict[str, Any]]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for event in events:
        etype = event.get("type")
        tag = event.get("tag")
        selector = event.get("selector")
        if not selector or etype not in {"input", "change", "click"}:
            continue
        action = "click"
        if etype in {"input", "change"} and tag in {"input", "textarea"}:
            action = "fill"
        elif etype == "change" and tag == "select":
            action = "select"
        key = (action, selector)
        if key in seen:
            # Keep recipe short. For a field, last value is not critical because date templates are inferred.
            continue
        seen.add(key)
        value = event.get("value")
        label = event.get("label") or event.get("text") or selector
        step: dict[str, Any] = {
            "action": action,
            "selector": selector,
            "label": label,
            "candidates": {
                "css": selector,
                "text": event.get("text"),
                "aria_label": event.get("aria_label"),
                "name": event.get("name"),
                "id": event.get("id"),
                "xpath": event.get("xpath"),
                "role": event.get("role"),
            },
        }
        if action in {"fill", "select"}:
            step["value_template" if _looks_like_date_field(event) else "value"] = _template_value(event, value)
        if event.get("dangerous"):
            step["dangerous"] = True
        steps.append(step)
    if any(state.get("tables") for state in dom_states):
        first_table = next((table for state in dom_states for table in state.get("tables", [])), {})
        steps.append({"action": "wait_for", "target": "table", "selector": first_table.get("selector") or "table"})
        steps.append({"action": "extract_table", "selector": first_table.get("selector") or "table"})
    if any(state.get("pagination") for state in dom_states):
        steps.append({"action": "paginate", "strategy": "datatable_next", "selector": "a.paginate_button.next:not(.disabled), li.next:not(.disabled) a"})
    return {
        "module": target.slug,
        "name": target.name,
        "url": target.url,
        "learned_at": now_iso(),
        "steps": steps,
    }


def _looks_like_date_field(event: dict[str, Any]) -> bool:
    hint = " ".join(str(event.get(key) or "").lower() for key in ("selector", "label", "name", "id", "text"))
    return any(token in hint for token in ("fecha", "date", "start", "end", "inicio", "final"))


def _template_value(event: dict[str, Any], value: Any) -> Any:
    if value is None:
        return None
    if not _looks_like_date_field(event):
        return value
    hint = " ".join(str(event.get(key) or "").lower() for key in ("selector", "label", "name", "id"))
    has_time = bool(re.search(r"\d{1,2}:\d{2}", str(value)))
    if any(token in hint for token in ("start", "inicio", "from")):
        return "{date_from_ddmmyyyy_hhmmss}" if has_time else "{date_from_ddmmyyyy}"
    if any(token in hint for token in ("end", "final", "to")):
        return "{date_to_ddmmyyyy_hhmmss}" if has_time else "{date_to_ddmmyyyy}"
    return "{date_from_ddmmyyyy}"


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    def scalar(value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        text = str(value).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{text}"'

    lines = [
        f"module: {scalar(data.get('module'))}",
        f"name: {scalar(data.get('name'))}",
        f"url: {scalar(data.get('url'))}",
        f"learned_at: {scalar(data.get('learned_at'))}",
        "steps:",
    ]
    for step in data.get("steps", []):
        lines.append(f"  - action: {scalar(step.get('action'))}")
        for key in ("selector", "label", "value", "value_template", "target", "strategy", "dangerous"):
            if key in step:
                lines.append(f"    {key}: {scalar(step.get(key))}")
        candidates = step.get("candidates") or {}
        if candidates:
            lines.append("    candidates:")
            for key, value in candidates.items():
                if value:
                    lines.append(f"      {key}: {scalar(value)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _classify_output(dom_states: list[dict[str, Any]]) -> str:
    has_table = any(state.get("tables") for state in dom_states)
    has_pagination = any(state.get("pagination") for state in dom_states)
    has_excel = any("excel" in json.dumps(state, ensure_ascii=False).lower() or "xls" in json.dumps(state, ensure_ascii=False).lower() for state in dom_states)
    has_pdf = any("pdf" in json.dumps(state, ensure_ascii=False).lower() for state in dom_states)
    has_modal = any(state.get("modals") for state in dom_states)
    if has_table and has_pagination:
        return "paginated_table"
    if has_table:
        return "table"
    if has_excel:
        return "excel"
    if has_pdf:
        return "pdf"
    if has_modal:
        return "modal"
    return "unknown"


def generate_module_diagnosis(
    target: TeachTarget,
    directory: Path,
    started_at: str,
    ended_at: str,
    finish_reason: str,
    events: list[dict[str, Any]],
    dom_states: list[dict[str, Any]],
    final_state: dict[str, Any],
) -> str:
    output_type = _classify_output(dom_states)
    dangerous = [event for event in events if event.get("dangerous")]
    filters = [event for event in events if event.get("type") in {"input", "change"} and event.get("tag") in {"input", "select", "textarea"}]
    buttons = [event for event in events if event.get("type") == "click" and event.get("tag") in {"button", "a", "input"}]
    tables = [table for state in dom_states for table in state.get("tables", [])]
    modals = [modal for state in dom_states for modal in state.get("modals", [])]
    exports = [item for state in dom_states for item in state.get("exports", [])]
    strategy = "inspect_manually"
    if output_type == "paginated_table":
        strategy = "table_monthly_chunks"
    elif output_type == "table":
        strategy = "table_quarterly_chunks"
    elif output_type == "excel":
        strategy = "excel_full_or_chunked"
    elif output_type == "pdf":
        strategy = "pdf_full_range_once"
    risk = "high" if dangerous or output_type == "unknown" else "medium"
    flow = [event for event in events if event.get("type") in {"click", "input", "change", "download_started", "url_changed"}][:80]
    lines = [
        f"# Diagnóstico módulo: {target.name}",
        "",
        "## Resumen",
        "",
        f"* URL inicial: `{target.url}`",
        f"* URL final: `{final_state.get('current_url') or target.url}`",
        f"* Inicio: `{started_at}`",
        f"* Fin: `{ended_at}`",
        f"* Finalización: `{finish_reason}`",
        f"* Eventos capturados: **{len(events)}**",
        f"* Tablas detectadas: **{len(tables)}**",
        f"* Paginación detectada: **{'sí' if any(state.get('pagination') for state in dom_states) else 'no'}**",
        f"* Modales detectados: **{len(modals)}**",
        f"* Botones de exportación/acción: **{len(exports)}**",
        f"* Tipo de salida inferido: `{output_type}`",
        f"* Riesgo: `{risk}`",
        f"* Estrategia recomendada: `{strategy}`",
        "",
        "## Flujo observado",
        "",
    ]
    if flow:
        for index, event in enumerate(flow, 1):
            label = event.get("label") or event.get("text") or event.get("selector") or event.get("url")
            lines.append(f"{index}. `{event.get('type')}` sobre `{label}`")
    else:
        lines.append("- No se capturaron acciones manuales relevantes.")
    lines.extend(["", "## Filtros detectados", "", "| Label | Tipo | Selector | Valor usado |", "|---|---|---|---|"])
    for event in filters[:80]:
        lines.append(f"| {event.get('label') or ''} | {event.get('tag') or ''}/{event.get('input_type') or ''} | `{event.get('selector') or ''}` | `{event.get('value') or ''}` |")
    if not filters:
        lines.append("| - | - | - | - |")
    lines.extend(["", "## Botones detectados", "", "| Texto | Selector | Tipo | Riesgo |", "|---|---|---|---|"])
    for event in buttons[:80]:
        lines.append(f"| {event.get('text') or event.get('label') or ''} | `{event.get('selector') or ''}` | {event.get('tag') or ''} | {'peligroso' if event.get('dangerous') else 'normal'} |")
    if not buttons:
        lines.append("| - | - | - | - |")
    lines.extend(["", "## Tablas detectadas", "", "| Selector | Columnas | Paginación | Filas visibles |", "|---|---|---|---:|"])
    for table in tables[:20]:
        lines.append(f"| `{table.get('selector') or ''}` | {', '.join(table.get('columns') or []) or '-'} | {'sí' if any(state.get('pagination') for state in dom_states) else 'no'} | {table.get('rows_visible') or 0} |")
    if not tables:
        lines.append("| - | - | - | 0 |")
    lines.extend(["", "## Modales / popups", "", "| Momento | Selector | Descripción |", "|---|---|---|"])
    for index, modal in enumerate(modals[:20], 1):
        lines.append(f"| {index} | `{modal.get('selector') or ''}` | {modal.get('text') or ''} |")
    if not modals:
        lines.append("| - | - | - |")
    lines.extend(
        [
            "",
            "## Receta sugerida",
            "",
            f"Usar `inferred_recipe.yaml` en `{directory}` como base. La estrategia recomendada es `{strategy}`.",
            "",
            "## Dudas pendientes",
            "",
        ]
    )
    if dangerous:
        lines.append("- Se observaron acciones potencialmente peligrosas; revisar antes de automatizar.")
    if output_type == "unknown":
        lines.append("- No se pudo inferir salida estable; repetir sesión mostrando tabla/exportación.")
    if not dangerous and output_type != "unknown":
        lines.append("- No hay dudas críticas detectadas en esta sesión.")
    return "\n".join(lines) + "\n"


async def start_teach_mode(page: Page, settings: Settings, target: TeachTarget) -> dict[str, Any]:
    directory = settings.teach_dir / target.slug / _timestamp_for_path()
    directory.mkdir(parents=True, exist_ok=True)
    events_path = directory / "events.jsonl"
    dom_snapshots_path = directory / "dom_snapshots.jsonl"
    started_at = now_iso()
    await page.goto(target.url, wait_until="domcontentloaded")
    await record_browser_events(page, events_path, dom_snapshots_path)
    await inject_finish_button(page)
    start_evidence = await _save_html_and_screenshot(page, directory, "start")
    print("")
    print("MODO ENSEÑANZA ACTIVADO")
    print("Abraham, maneja la página manualmente.")
    print("Muestra filtros, botones, popups, tablas, paginación y exportaciones.")
    print('Cuando termines, presiona el botón "Finalizar enseñanza" arriba a la derecha.')
    print(f"Sesión: {directory}")
    finish_reason = await _wait_for_finish(page, directory)
    ended_at = now_iso()
    end_evidence = await _save_html_and_screenshot(page, directory, "end")
    if page.is_closed():
        final_state = {
            "table_visible": False,
            "pagination_visible": False,
            "pdf_visible": False,
            "excel_visible": False,
            "download_detected": False,
            "url_changed": False,
            "modal_visible": False,
            "loader_visible": False,
            "alert_visible": False,
            "current_url": target.url,
            "table_text_sample": None,
            "error": "page_closed_before_final_state",
        }
        url_final = target.url
    else:
        try:
            final_state = await detect_state_after_manual_action(page, target.url)
        except Exception as exc:
            final_state = {"current_url": target.url, "error": f"final_state_unavailable: {type(exc).__name__}: {exc}"}
        url_final = page.url
    events = _read_jsonl(events_path)
    dom_states = _read_jsonl(dom_snapshots_path)
    recipe = infer_recipe_from_events(target, events, dom_states)
    recipe_path = directory / "inferred_recipe.yaml"
    _write_yaml(recipe_path, recipe)
    diagnosis = generate_module_diagnosis(target, directory, started_at, ended_at, finish_reason, events, dom_states, final_state)
    diagnosis_path = directory / "module_diagnosis.md"
    diagnosis_path.write_text(diagnosis, encoding="utf-8")
    session = {
        "module": target.slug,
        "name": target.name,
        "url_initial": target.url,
        "url_final": url_final,
        "started_at": started_at,
        "ended_at": ended_at,
        "finish_reason": finish_reason,
        "events_count": len(events),
        "dom_snapshots_count": len(dom_states),
        "final_state": final_state,
        "start": start_evidence,
        "end": end_evidence,
        "paths": {
            "directory": str(directory),
            "events": str(events_path),
            "dom_snapshots": str(dom_snapshots_path),
            "teach_session": str(directory / "teach_session.json"),
            "inferred_recipe": str(recipe_path),
            "module_diagnosis": str(diagnosis_path),
        },
    }
    write_json(directory / "teach_session.json", session)
    return session
