from __future__ import annotations

from datetime import date

from app.report_configs import load_report_config
from app.sales_extractor import absolute_report_url, chunk_key, format_report_date


class DummySettings:
    asno_url = "https://wappsi336.com/holamigo/login"


def test_sales_date_format_is_dd_mm_yyyy() -> None:
    config = load_report_config("sales")

    assert format_report_date(date(2026, 6, 17), config) == "17/06/2026"


def test_sales_output_chunk_key() -> None:
    assert chunk_key(date(2026, 6, 1)) == "2026-06"


def test_sales_absolute_report_url() -> None:
    config = load_report_config("sales")

    assert absolute_report_url(DummySettings(), config) == "https://wappsi336.com/holamigo/admin/reports/sales"
