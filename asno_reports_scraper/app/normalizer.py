from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def table_rows_from_html(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    for table in soup.select("table"):
        headers = [normalize_text(th.get_text(" ")) for th in table.select("th")]
        for tr in table.select("tr"):
            cells = [normalize_text(td.get_text(" ")) for td in tr.select("td")]
            if not cells:
                continue
            if headers and len(headers) == len(cells):
                rows.append(dict(zip(headers, cells)))
            else:
                rows.append({f"col_{idx + 1}": cell for idx, cell in enumerate(cells)})
    return rows

