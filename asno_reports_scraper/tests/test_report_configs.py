from __future__ import annotations

from app.report_configs import load_report_config


def test_load_sales_report_config() -> None:
    config = load_report_config("sales")

    assert config.report_id == "sales"
    assert config.name == "Informe de Ventas"
    assert config.url_path == "/admin/reports/sales"
    assert config.date_from_selector == "#start_date_dh"
    assert config.date_to_selector == "#end_date_dh"
    assert config.date_format == "%d/%m/%Y"
    assert config.strategy == "table_monthly_chunks"
    assert config.submit_selector == "#submit_filter"
