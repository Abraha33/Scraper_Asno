from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .config import ROOT_DIR, Settings
from .pattern_engine import extractor_for_pattern, normalize_pattern
from .storage import now_iso, read_json, write_json


PRIORITY_1 = ("ventas", "compras", "pagos", "gastos", "inventario", "traslados", "cartera", "cuentas por pagar", "caja")
PRIORITY_2 = ("clientes", "proveedores", "productos", "listas de precios", "bodegas", "usuarios", "actividad")
PRIORITY_3 = ("configuración", "reportes", "dashboard", "root")


MODULE_ALIASES = {
    "sales": "sales",
    "ventas": "sales",
    "compras": "purchases",
    "purchases": "purchases",
    "traslados": "transfers",
    "inventario": "inventory",
    "clientes": "customers",
    "proveedores": "suppliers",
    "pagos": "payments",
    "caja": "cash",
    "usuarios": "users",
    "configuración": "settings",
    "reportes": "reports",
    "cartera": "portfolio",
}


def _priority_for_module(module: str) -> int:
    text = module.lower()
    if any(token in text for token in PRIORITY_1):
        return 1
    if any(token in text for token in PRIORITY_2):
        return 2
    return 3


def _package_module_name(module: str) -> str:
    return MODULE_ALIASES.get(module, module.replace(" ", "_"))


def _strategy_for_page(page: dict[str, Any]) -> str:
    pattern = normalize_pattern(page.get("pattern"))
    if pattern == "filter_paginated_table":
        return "monthly_chunks_if_date_filter_else_paginated_full_readonly"
    if pattern == "filter_table":
        return "quarterly_or_full_readonly"
    if pattern in {"transaction_form_readonly", "settings_page"}:
        return "audit_only_readonly"
    if pattern == "document_report":
        return "document_snapshot_or_export_when_safe"
    return extractor_for_pattern(pattern)


def build_data_package_design() -> dict[str, Any]:
    modules = [
        "sales",
        "purchases",
        "transfers",
        "inventory",
        "customers",
        "suppliers",
        "payments",
        "expenses",
        "users",
    ]
    return {
        "root": "data/export/asno_data_package",
        "manifest": {
            "path": "manifest.json",
            "fields": [
                "system_name",
                "extraction_date",
                "historical_range",
                "modules_extracted",
                "files_count",
                "records_count",
                "errors",
                "extractor_version",
            ],
        },
        "index": {
            "path": "index.json",
            "fields": ["modules", "files", "relationships", "schemas", "counts_summary"],
        },
        "modules": {
            module: {
                "index": f"modules/{module}/index.json",
                "metadata": f"modules/{module}/metadata.json",
                "chunks": f"modules/{module}/chunks/",
                "documents": f"modules/{module}/documents/",
                "raw": f"modules/{module}/raw/",
            }
            for module in modules
        },
        "relationships": [
            "relationships/customers_sales.json",
            "relationships/products_sales.json",
            "relationships/suppliers_purchases.json",
            "relationships/inventory_movements.json",
        ],
        "support_dirs": ["logs", "errors", "schemas"],
        "chunk_schema": {
            "module": "...",
            "source_url": "...",
            "date_from": "...",
            "date_to": "...",
            "extracted_at": "...",
            "records_count": 0,
            "records": [],
        },
    }


def generate_extraction_plan(settings: Settings, *, plan_only: bool = True) -> dict[str, Any]:
    system = read_json(settings.audit_dir / "system_map.json", {})
    pages = system.get("pages", [])
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in pages:
        grouped[str(page.get("module") or "desconocido")].append(page)
    modules_plan: list[dict[str, Any]] = []
    for module, module_pages in grouped.items():
        priority = _priority_for_module(module)
        safe_pages = [page for page in module_pages if not page.get("dangerous_actions_detected")]
        risky_pages = [page for page in module_pages if page.get("dangerous_actions_detected")]
        patterns = sorted({normalize_pattern(page.get("pattern")) for page in module_pages})
        modules_plan.append(
            {
                "module": module,
                "package_module": _package_module_name(module),
                "priority": priority,
                "pages_count": len(module_pages),
                "safe_pages_count": len(safe_pages),
                "risky_pages_count": len(risky_pages),
                "patterns": patterns,
                "recommended_extractors": sorted({extractor_for_pattern(pattern) for pattern in patterns}),
                "strategy": "read_only_generic_extractors_first_then_assisted_exceptions",
                "pages": [
                    {
                        "name": page.get("name"),
                        "url": page.get("url"),
                        "pattern": normalize_pattern(page.get("pattern")),
                        "extractor": extractor_for_pattern(page.get("pattern")),
                        "strategy": _strategy_for_page(page),
                        "read_only_safe": page.get("read_only_safe"),
                        "needs_assisted_review": page.get("needs_assisted_review"),
                    }
                    for page in module_pages
                ],
            }
        )
    modules_plan.sort(key=lambda item: (item["priority"], item["module"]))
    plan = {
        "created_at": now_iso(),
        "plan_only": plan_only,
        "source_audit": str(settings.audit_dir / "system_map.json"),
        "historical_range_default": {"from": "2001-01-01", "to": "2026-12-31"},
        "priorities": {
            "priority_1": list(PRIORITY_1),
            "priority_2": list(PRIORITY_2),
            "priority_3": list(PRIORITY_3),
        },
        "modules": modules_plan,
        "data_package_design": build_data_package_design(),
        "next_step": "implement generic_filter_paginated_table_extractor against one safe priority-1 module",
    }
    output_json = settings.data_dir / "plans" / "extraction_plan.json"
    output_markdown = ROOT_DIR / "docs" / "plans" / "asno_extraction_plan.md"
    plan["paths"] = {
        "json": str(output_json),
        "markdown": str(output_markdown),
    }
    write_json(output_json, plan)
    generate_extraction_plan_markdown(plan, output_markdown)
    return plan


def generate_extraction_plan_markdown(plan: dict[str, Any], path: Path) -> None:
    lines = [
        "# Plan de extracción ASNO Mirror",
        "",
        "## Resumen",
        "",
        f"- Creado: `{plan['created_at']}`",
        f"- Modo: `plan_only={plan['plan_only']}`",
        f"- Auditoría fuente: `{plan['source_audit']}`",
        f"- Rango histórico por defecto: `{plan['historical_range_default']['from']}` → `{plan['historical_range_default']['to']}`",
        "",
        "## Prioridades",
        "",
    ]
    for priority, items in plan["priorities"].items():
        lines.append(f"### {priority}")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(["## Módulos", "", "| Prioridad | Módulo | Páginas | Seguras | Riesgo | Patrones |", "|---:|---|---:|---:|---:|---|"])
    for module in plan["modules"]:
        lines.append(
            f"| {module['priority']} | `{module['module']}` | {module['pages_count']} | {module['safe_pages_count']} | {module['risky_pages_count']} | {', '.join(module['patterns'])} |"
        )
    lines.extend(["", "## Diseño de paquete portable para IA", ""])
    package = plan["data_package_design"]
    lines.append(f"- Root: `{package['root']}`")
    lines.append(f"- Manifest: `{package['manifest']['path']}`")
    lines.append(f"- Index: `{package['index']['path']}`")
    lines.append("")
    lines.append("### Módulos del paquete")
    for module, paths in package["modules"].items():
        lines.append(f"- `{module}`: chunks `{paths['chunks']}`, raw `{paths['raw']}`, metadata `{paths['metadata']}`")
    lines.extend(["", "### Relaciones previstas"])
    for relation in package["relationships"]:
        lines.append(f"- `{relation}`")
    lines.extend(["", "## Próximo paso", "", plan["next_step"]])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
