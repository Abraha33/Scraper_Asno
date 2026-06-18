from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .config import ROOT_DIR, Settings
from .site_patterns_audit import DANGEROUS_RE, RECOMMENDED_EXTRACTORS
from .storage import now_iso, read_json, write_json


PATTERN_CONFIG_PATH = ROOT_DIR / "configs" / "patterns.yaml"
LEARNED_AUDIT_PATH = ROOT_DIR / "docs" / "audits" / "learned_patterns_audit.md"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _iter_files(root: Path, pattern: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob(pattern))


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _write_patterns_yaml(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"generated_at: {_yaml_scalar(summary['generated_at'])}",
        "read_only: true",
        "dangerous_actions:",
    ]
    for action in summary["dangerous_actions"]:
        lines.append(f"  - {_yaml_scalar(action)}")
    lines.append("patterns:")
    for pattern in summary["patterns"]:
        lines.append(f"  {pattern['pattern_id']}:")
        lines.append(f"    recommended_extractor: {_yaml_scalar(pattern['recommended_extractor'])}")
        lines.append(f"    pages_count: {pattern['pages_count']}")
        lines.append(f"    confidence: {_yaml_scalar(pattern.get('confidence', 'medium'))}")
        lines.append("    repeated_selectors:")
        for selector, count in pattern.get("repeated_selectors", [])[:20]:
            lines.append(f"      - selector: {_yaml_scalar(selector)}")
            lines.append(f"        count: {count}")
        lines.append("    modules:")
        for module, count in pattern.get("modules", [])[:20]:
            lines.append(f"      - module: {_yaml_scalar(module)}")
            lines.append(f"        count: {count}")
        lines.append("    sample_pages:")
        for page in pattern.get("sample_pages", [])[:10]:
            lines.append(f"      - name: {_yaml_scalar(page.get('name'))}")
            lines.append(f"        url: {_yaml_scalar(page.get('url'))}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _collect_teach(settings: Settings) -> dict[str, Any]:
    sessions: list[dict[str, Any]] = []
    selector_counter: Counter[str] = Counter()
    filter_counter: Counter[str] = Counter()
    table_counter: Counter[str] = Counter()
    modal_counter: Counter[str] = Counter()
    button_counter: Counter[str] = Counter()
    date_counter: Counter[str] = Counter()
    pagination_counter: Counter[str] = Counter()
    for session_path in _iter_files(settings.teach_dir, "teach_session.json"):
        session = read_json(session_path, {})
        directory = session_path.parent
        events = _read_jsonl(directory / "events.jsonl")
        doms = _read_jsonl(directory / "dom_snapshots.jsonl")
        recipe_text = (directory / "inferred_recipe.yaml").read_text(encoding="utf-8", errors="ignore") if (directory / "inferred_recipe.yaml").exists() else ""
        diagnosis = (directory / "module_diagnosis.md").read_text(encoding="utf-8", errors="ignore") if (directory / "module_diagnosis.md").exists() else ""
        sessions.append(
            {
                "path": str(directory),
                "module": session.get("module"),
                "name": session.get("name"),
                "url_initial": session.get("url_initial"),
                "events_count": len(events),
                "dom_snapshots_count": len(doms),
                "has_recipe": bool(recipe_text),
                "has_diagnosis": bool(diagnosis),
            }
        )
        for event in events:
            if event.get("selector"):
                selector_counter[str(event["selector"])] += 1
            if event.get("type") in {"input", "change"}:
                filter_counter[str(event.get("label") or event.get("name") or event.get("selector"))] += 1
                hint = f"{event.get('label', '')} {event.get('name', '')} {event.get('selector', '')}".lower()
                if any(token in hint for token in ("fecha", "date", "inicio", "final", "from", "to")):
                    date_counter[str(event.get("selector") or event.get("label"))] += 1
            if event.get("type") == "click":
                button_counter[str(event.get("text") or event.get("label") or event.get("selector"))] += 1
        for dom in doms:
            for table in dom.get("tables", []):
                table_counter[str(table.get("selector") or "table")] += 1
            for modal in dom.get("modals", []):
                modal_counter[str(modal.get("selector") or "modal")] += 1
            for pagination in dom.get("pagination", []):
                pagination_counter[str(pagination.get("selector") or "pagination")] += 1
            for action in dom.get("exports", []):
                button_counter[str(action.get("text") or action.get("label") or action.get("selector"))] += 1
    return {
        "sessions": sessions,
        "selectors": selector_counter,
        "filters": filter_counter,
        "dates": date_counter,
        "tables": table_counter,
        "modals": modal_counter,
        "buttons": button_counter,
        "pagination": pagination_counter,
    }


def _collect_assisted(settings: Settings) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    reasons: Counter[str] = Counter()
    for event_path in _iter_files(settings.assisted_dir, "assisted_event.json"):
        event = read_json(event_path, {})
        events.append({**event, "path": str(event_path)})
        reasons[str(event.get("reason") or "unknown")] += 1
    return {"events": events, "reasons": reasons}


def _collect_system(settings: Settings) -> dict[str, Any]:
    system = read_json(settings.audit_dir / "system_map.json", {})
    site = read_json(settings.audit_dir / "site_patterns.json", {})
    pages = system.get("pages") or site.get("pages") or []
    pattern_pages: dict[str, list[dict[str, Any]]] = defaultdict(list)
    module_pages: dict[str, list[dict[str, Any]]] = defaultdict(list)
    dangerous: list[dict[str, Any]] = []
    for page in pages:
        pattern_pages[str(page.get("pattern") or "unknown")].append(page)
        module_pages[str(page.get("module") or "desconocido")].append(page)
        if page.get("dangerous_actions_detected"):
            dangerous.append(page)
    return {
        "system": system,
        "pages": pages,
        "pattern_pages": pattern_pages,
        "module_pages": module_pages,
        "dangerous_pages": dangerous,
    }


def build_learned_patterns(settings: Settings) -> dict[str, Any]:
    settings.ensure_dirs()
    teach = _collect_teach(settings)
    assisted = _collect_assisted(settings)
    system = _collect_system(settings)
    recipes = _iter_files(ROOT_DIR / "configs" / "learned_recipes", "*.yaml")
    patterns: list[dict[str, Any]] = []
    for pattern_id, pages in sorted(system["pattern_pages"].items(), key=lambda kv: (-len(kv[1]), kv[0])):
        modules = Counter(str(page.get("module") or "desconocido") for page in pages)
        selectors = Counter()
        for page in pages:
            diagnostics = page.get("diagnostics") or {}
            pagination = diagnostics.get("pagination") or {}
            exports = diagnostics.get("exports") or {}
            for value in (pagination.get("next_selector"), pagination.get("page_size_selector"), exports.get("excel_selector"), exports.get("pdf_selector"), exports.get("print_selector")):
                if value:
                    selectors[str(value)] += 1
        patterns.append(
            {
                "pattern_id": pattern_id,
                "pages_count": len(pages),
                "recommended_extractor": RECOMMENDED_EXTRACTORS.get(pattern_id, "inspect_manually"),
                "confidence": "high" if pattern_id != "unknown" else "low",
                "modules": modules.most_common(),
                "repeated_selectors": selectors.most_common(),
                "sample_pages": [{"name": page.get("name"), "url": page.get("url")} for page in pages[:10]],
            }
        )
    summary = {
        "generated_at": now_iso(),
        "teach_sessions_count": len(teach["sessions"]),
        "assisted_events_count": len(assisted["events"]),
        "learned_recipes_count": len(recipes),
        "system_pages_count": len(system["pages"]),
        "patterns": patterns,
        "modules": sorted(system["module_pages"].keys()),
        "dangerous_pages_count": len(system["dangerous_pages"]),
        "dangerous_actions": [
            "crear",
            "editar",
            "guardar",
            "actualizar",
            "eliminar",
            "borrar",
            "anular",
            "confirmar",
            "pagar",
            "cerrar caja",
            "facturar",
            "enviar",
            "importar",
            "sincronizar",
            "procesar",
            "aprobar",
        ],
        "top_repeated": {
            "selectors": teach["selectors"].most_common(30),
            "filters": teach["filters"].most_common(30),
            "dates": teach["dates"].most_common(30),
            "tables": teach["tables"].most_common(30),
            "pagination": teach["pagination"].most_common(30),
            "buttons": teach["buttons"].most_common(30),
            "modals": teach["modals"].most_common(30),
            "assisted_reasons": teach["buttons"].most_common(0) or assisted["reasons"].most_common(30),
        },
        "teach_sessions": teach["sessions"],
        "recipes": [str(path) for path in recipes],
        "generic_extractors_ready": [
            "filter_paginated_table",
            "filter_table",
            "export_excel",
            "export_pdf",
            "detail_modal",
            "detail_page",
            "crud_list_readonly",
            "transaction_form_readonly",
            "readonly_table",
        ],
        "paths": {
            "patterns_yaml": str(PATTERN_CONFIG_PATH),
            "markdown": str(LEARNED_AUDIT_PATH),
            "summary_json": str(settings.audit_dir / "learned_patterns_summary.json"),
        },
    }
    _write_patterns_yaml(PATTERN_CONFIG_PATH, summary)
    generate_learned_patterns_markdown(summary, LEARNED_AUDIT_PATH)
    write_json(settings.audit_dir / "learned_patterns_summary.json", summary)
    return summary


def _counter_lines(items: list[tuple[str, int]], empty: str = "No se detectó evidencia suficiente.") -> list[str]:
    if not items:
        return [f"- {empty}"]
    return [f"- `{name}`: {count}" for name, count in items[:30]]


def generate_learned_patterns_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Auditoría de patrones aprendidos ASNO",
        "",
        "## Resumen",
        "",
        f"- Generado: `{summary['generated_at']}`",
        f"- Sesiones teach: **{summary['teach_sessions_count']}**",
        f"- Eventos assisted: **{summary['assisted_events_count']}**",
        f"- Recetas aprendidas: **{summary['learned_recipes_count']}**",
        f"- Páginas del sistema mapeadas: **{summary['system_pages_count']}**",
        f"- Páginas con acciones peligrosas: **{summary['dangerous_pages_count']}**",
        "",
        "## 1. Patrones enseñados por Abraham",
        "",
    ]
    if summary["teach_sessions"]:
        for session in summary["teach_sessions"]:
            lines.append(f"- `{session.get('module')}` — {session.get('name')} — eventos: {session.get('events_count')} — DOM snapshots: {session.get('dom_snapshots_count')} — `{session.get('path')}`")
    else:
        lines.append("- No hay sesiones teach registradas.")
    lines.extend(["", "## 2. Páginas/módulos con patrones similares", ""])
    lines.append("| Patrón | Páginas | Extractor recomendado | Módulos principales |")
    lines.append("|---|---:|---|---|")
    for pattern in summary["patterns"]:
        modules = ", ".join(f"{name} ({count})" for name, count in pattern.get("modules", [])[:5])
        lines.append(f"| `{pattern['pattern_id']}` | {pattern['pages_count']} | `{pattern['recommended_extractor']}` | {modules or '-'} |")
    sections = [
        ("## 3. Selectores repetidos", "selectors"),
        ("## 4. Filtros repetidos", "filters"),
        ("## 5. Tipos/campos de fecha repetidos", "dates"),
        ("## 6. Tablas repetidas", "tables"),
        ("## 7. Paginaciones repetidas", "pagination"),
        ("## 8. Botones PDF/Excel/Imprimir/Guardar repetidos", "buttons"),
        ("## 9. Modales/popups repetidos", "modals"),
    ]
    for title, key in sections:
        lines.extend(["", title, ""])
        lines.extend(_counter_lines(summary["top_repeated"].get(key, [])))
    lines.extend(["", "## 10. Acciones peligrosas a evitar", ""])
    for action in summary["dangerous_actions"]:
        lines.append(f"- `{action}`")
    lines.extend(["", "## 11. Extractores genéricos que se pueden crear ya", ""])
    for extractor in summary["generic_extractors_ready"]:
        lines.append(f"- `{extractor}`")
    lines.extend(["", "## Decisión técnica", ""])
    lines.append("El primer extractor reutilizable debe ser `generic_filter_paginated_table_extractor`, porque el sistema ya mostró que ese patrón domina los listados y reportes tabulares.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
