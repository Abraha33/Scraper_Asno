from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from .config import Settings


def safe_name(value: str, max_len: int = 120) -> str:
    import re

    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return (normalized or "item")[:max_len]


def stable_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()


async def save_evidence(page: Page, settings: Settings, label: str) -> dict[str, str]:
    settings.html_dir.mkdir(parents=True, exist_ok=True)
    settings.screenshots_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_name(f"{now_iso()}_{label}")
    html_path = settings.html_dir / f"{stem}.html"
    screenshot_path = settings.screenshots_dir / f"{stem}.png"
    html = await page.content()
    html = re.sub(
        r'(?i)("?(?:password|secret|token|key)"?\s*[:=]\s*["\']?)([^"\'<>,} ]+)',
        r"\1[REDACTED]",
        html,
    )
    html_path.write_text(html, encoding="utf-8")
    try:
        await page.screenshot(path=screenshot_path, full_page=True, timeout=20_000)
    except Exception as exc:
        logging.warning("Could not save screenshot for %s: %s", label, exc)
    return {"html": str(html_path), "screenshot": str(screenshot_path)}


def avoid_duplicates(rows: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    clean: list[dict[str, Any]] = []
    for row in rows:
        key = stable_id(*(str(row.get(field, "")) for field in key_fields))
        if key in seen:
            continue
        seen.add(key)
        clean.append(row)
    return clean
