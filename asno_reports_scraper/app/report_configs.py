from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ROOT_DIR


@dataclass(frozen=True)
class ReportConfig:
    report_id: str
    name: str
    url_path: str
    type: str
    strategy: str
    risk: str
    date_format: str
    date_from_selector: str
    date_to_selector: str
    range_selector: str | None
    range_value_contains: str | None
    submit_selector: str | None
    table_selector: str
    pagination_next_selector: str
    output_id: str


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


def _load_reports_section(path: Path) -> dict[str, dict[str, Any]]:
    reports: dict[str, dict[str, Any]] = {}
    in_reports = False
    current_report: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            in_reports = line == "reports:"
            current_report = None
            continue
        if not in_reports:
            continue
        if indent == 2 and line.endswith(":"):
            current_report = line[:-1].strip()
            reports[current_report] = {}
            continue
        if indent >= 4 and current_report and ":" in line:
            key, value = line.split(":", 1)
            reports[current_report][key.strip()] = _parse_scalar(value)
    return reports


def load_report_config(report_id: str, path: Path | None = None) -> ReportConfig:
    config_path = path or ROOT_DIR / "configs" / "reports.yaml"
    reports = _load_reports_section(config_path)
    if report_id not in reports:
        available = ", ".join(sorted(reports)) or "none"
        raise KeyError(f"Report config not found: {report_id}. Available: {available}")
    item = reports[report_id]
    return ReportConfig(
        report_id=report_id,
        name=str(item["name"]),
        url_path=str(item["url_path"]),
        type=str(item["type"]),
        strategy=str(item["strategy"]),
        risk=str(item["risk"]),
        date_format=str(item["date_format"]),
        date_from_selector=str(item["date_from_selector"]),
        date_to_selector=str(item["date_to_selector"]),
        range_selector=str(item.get("range_selector") or "") or None,
        range_value_contains=str(item.get("range_value_contains") or "") or None,
        submit_selector=str(item.get("submit_selector") or "") or None,
        table_selector=str(item.get("table_selector") or "table:visible"),
        pagination_next_selector=str(item.get("pagination_next_selector") or "a.paginate_button.next:not(.disabled)"),
        output_id=str(item.get("output_id") or report_id),
    )
