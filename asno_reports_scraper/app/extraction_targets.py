from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from .config import ROOT_DIR, Settings
from .pattern_engine import normalize_pattern
from .storage import read_json, safe_name


TARGETS_PATH = ROOT_DIR / "configs" / "extraction_targets.yaml"
GENERATED_TARGETS_PATH = ROOT_DIR / "configs" / "extraction_targets.generated.yaml"


@dataclass(frozen=True)
class ExtractionTarget:
    target_id: str
    name: str
    module: str
    url: str
    pattern: str
    date_filter: bool = False
    expected_outputs: tuple[str, ...] = ("table",)
    priority: str = "medium"
    safe_read_only: bool = True
    status: str = "active"


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _write_targets_yaml(path: Path, targets: dict[str, ExtractionTarget]) -> None:
    lines = ["targets:"]
    for target_id, target in sorted(targets.items()):
        lines.extend(
            [
                f"  {target_id}:",
                f"    name: {_yaml_scalar(target.name)}",
                f"    module: {_yaml_scalar(target.module)}",
                f"    url: {_yaml_scalar(target.url)}",
                f"    pattern: {_yaml_scalar(target.pattern)}",
                f"    date_filter: {_yaml_scalar(target.date_filter)}",
                "    expected_outputs:",
            ]
        )
        for output in target.expected_outputs:
            lines.append(f"      - {_yaml_scalar(output)}")
        lines.extend(
            [
                f"    priority: {_yaml_scalar(target.priority)}",
                f"    safe_read_only: {_yaml_scalar(target.safe_read_only)}",
                f"    status: {_yaml_scalar(target.status)}",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().strip('"').strip("'").lower() in {"true", "1", "yes", "sí", "si"}


def _parse_scalar(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().strip('"').strip("'")


def _read_targets_yaml(path: Path) -> dict[str, ExtractionTarget]:
    """Small parser for the controlled extraction_targets.yaml shape."""
    if not path.exists():
        return {}
    targets: dict[str, dict[str, Any]] = {}
    current_id: str | None = None
    current_list_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#") or raw_line.strip() == "targets:":
            continue
        if raw_line.startswith("  ") and not raw_line.startswith("    ") and raw_line.strip().endswith(":"):
            current_id = raw_line.strip().rstrip(":")
            targets[current_id] = {}
            current_list_key = None
            continue
        if current_id is None:
            continue
        if raw_line.startswith("    ") and not raw_line.startswith("      "):
            key, _, value = raw_line.strip().partition(":")
            if not value:
                current_list_key = key
                targets[current_id][key] = []
            else:
                current_list_key = None
                targets[current_id][key] = _parse_scalar(value)
            continue
        if raw_line.startswith("      -") and current_list_key:
            targets[current_id].setdefault(current_list_key, []).append(_parse_scalar(raw_line.strip()[1:].strip()))
    parsed: dict[str, ExtractionTarget] = {}
    for target_id, data in targets.items():
        parsed[target_id] = ExtractionTarget(
            target_id=target_id,
            name=str(data.get("name") or target_id),
            module=str(data.get("module") or "unknown"),
            url=str(data.get("url") or ""),
            pattern=normalize_pattern(str(data.get("pattern") or "unknown")),
            date_filter=_parse_bool(str(data.get("date_filter")) if "date_filter" in data else None),
            expected_outputs=tuple(data.get("expected_outputs") or ["table"]),
            priority=str(data.get("priority") or "medium"),
            safe_read_only=_parse_bool(str(data.get("safe_read_only")) if "safe_read_only" in data else None, default=True),
            status=str(data.get("status") or "active"),
        )
    return parsed


def _target_id_for_page(page: dict[str, Any]) -> str:
    module = str(page.get("module") or "unknown")
    name = str(page.get("name") or "")
    url = str(page.get("url") or "")
    path = urlparse(url).path.strip("/").split("/")
    last = path[-1] if path else name
    if url.endswith("/admin/reports/sales") or name.lower() == "informe de ventas":
        return "sales_report"
    if url.endswith("/admin/sales/orders"):
        return "sales_orders"
    if url.rstrip("/").endswith("/admin/transfers"):
        return "transfers_list"
    if url.rstrip("/").endswith("/admin/transfers/orders"):
        return "transfers_orders"
    base = safe_name(f"{module}_{last or name}".lower())
    return base


def _module_for_page(page: dict[str, Any]) -> str:
    url = str(page.get("url") or "")
    if "/admin/reports/sales" in url:
        return "sales"
    if "/admin/reports/transfers" in url:
        return "transfers"
    return str(page.get("module") or "unknown")


def generate_extraction_targets(settings: Settings) -> dict[str, ExtractionTarget]:
    pages = read_json(settings.audit_dir / "system_map.json", {}).get("pages", [])
    plan = read_json(settings.data_dir / "plans" / "extraction_plan.json", {})
    targets: dict[str, ExtractionTarget] = {}
    for page in pages:
        pattern = normalize_pattern(str(page.get("pattern") or ""))
        if pattern not in {"filter_paginated_table", "paginated_table"}:
            continue
        target_id = _target_id_for_page(page)
        if target_id in targets:
            continue
        name = str(page.get("name") or target_id)
        url = str(page.get("url") or "")
        module = _module_for_page(page)
        targets[target_id] = ExtractionTarget(
            target_id=target_id,
            name=name,
            module=module,
            url=url,
            pattern=pattern,
            date_filter=bool(page.get("has_date_filter")) or "/reports/" in url,
            expected_outputs=("table",),
            priority="high" if target_id in {"sales_report", "transfers_list", "transfers_orders"} else "medium",
            safe_read_only=bool(page.get("read_only_safe", True)) or target_id in {"sales_report", "transfers_list", "transfers_orders"},
            status="active",
        )

    # Ensure business-critical targets exist even if a stale audit misses them.
    defaults = {
        "sales_report": ExtractionTarget(
            target_id="sales_report",
            name="Informe de Ventas",
            module="sales",
            url="/admin/reports/sales",
            pattern="filter_paginated_table",
            date_filter=True,
            priority="high",
            safe_read_only=True,
        ),
        "sales_orders": ExtractionTarget(
            target_id="sales_orders",
            name="Órdenes de venta",
            module="sales",
            url="/admin/sales/orders",
            pattern="filter_paginated_table",
            date_filter=True,
            priority="medium",
            safe_read_only=True,
        ),
        "transfers_list": ExtractionTarget(
            target_id="transfers_list",
            name="Lista de traslados",
            module="transfers",
            url="/admin/transfers",
            pattern="filter_paginated_table",
            date_filter=True,
            priority="high",
            safe_read_only=True,
        ),
        "transfers_orders": ExtractionTarget(
            target_id="transfers_orders",
            name="Órdenes de traslado",
            module="transfers",
            url="/admin/transfers/orders",
            pattern="filter_paginated_table",
            date_filter=True,
            priority="high",
            safe_read_only=True,
        ),
    }
    for target_id, target in defaults.items():
        targets.setdefault(target_id, target)
    _write_targets_yaml(GENERATED_TARGETS_PATH, targets)
    if not TARGETS_PATH.exists():
        _write_targets_yaml(TARGETS_PATH, targets)
    return targets


def load_extraction_targets(settings: Settings, *, ensure_generated: bool = True) -> dict[str, ExtractionTarget]:
    if ensure_generated:
        generate_extraction_targets(settings)
    targets = _read_targets_yaml(TARGETS_PATH)
    if not targets:
        targets = _read_targets_yaml(GENERATED_TARGETS_PATH)
    return targets


def absolute_target_url(settings: Settings, target: ExtractionTarget) -> str:
    if target.url.startswith("http://") or target.url.startswith("https://"):
        return target.url
    parsed = urlparse(settings.asno_url)
    path = parsed.path
    if "/admin" in path:
        path = path.split("/admin", 1)[0]
    base = f"{parsed.scheme}://{parsed.netloc}{path.rstrip('/')}/"
    return urljoin(base, target.url.lstrip("/"))


def targets_by_module(targets: dict[str, ExtractionTarget], module: str) -> list[ExtractionTarget]:
    return sorted(
        [target for target in targets.values() if target.module.lower() == module.lower() and target.status == "active"],
        key=lambda item: ({"high": 0, "medium": 1, "low": 2}.get(item.priority, 9), item.target_id),
    )


def list_targets_rows(settings: Settings) -> list[dict[str, Any]]:
    targets = load_extraction_targets(settings)
    return [
        {
            "target_id": target.target_id,
            "name": target.name,
            "module": target.module,
            "url": absolute_target_url(settings, target),
            "pattern": target.pattern,
            "priority": target.priority,
            "safe_read_only": target.safe_read_only,
            "status": target.status,
        }
        for target in sorted(targets.values(), key=lambda item: (item.module, item.target_id))
    ]


def title_tokens(value: str) -> set[str]:
    stop = {"de", "del", "la", "el", "los", "las", "y", "por", "para", "lista", "informe"}
    return {token for token in re.findall(r"[a-záéíóúñü0-9]+", value.lower()) if len(token) > 2 and token not in stop}
