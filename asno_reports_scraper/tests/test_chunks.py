from datetime import date

from app.report_extractor import month_chunks


def test_month_chunks_splits_range_by_month():
    chunks = month_chunks(date(2022, 1, 15), date(2022, 3, 2))
    assert chunks == [
        (date(2022, 1, 15), date(2022, 1, 31)),
        (date(2022, 2, 1), date(2022, 2, 28)),
        (date(2022, 3, 1), date(2022, 3, 2)),
    ]

