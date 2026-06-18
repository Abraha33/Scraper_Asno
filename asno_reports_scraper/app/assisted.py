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
from .storage import now_iso, safe_name, write_json


SENSITIVE_HTML_RE = re.compile(
    r'(?i)("?(?:password|secret|token|key)"?\s*[:=]\s*["\']?)([^"\'<>,} ]+)',
)


class AssistedAbort(RuntimeError):
    pass


@dataclass(frozen=True)
class AssistedResult:
    decision: str
    event_path: Path
    detected_after_user_action: dict[str, Any]


def _redact_html(html: str) -> str:
    return SENSITIVE_HTML_RE.sub(r"\1[REDACTED]", html)


def _timestamp_for_path() -> str:
    return now_iso().replace(":", "_")


def _assisted_run_dir(settings: Settings, report_slug: str) -> Path:
    return settings.assisted_dir / safe_name(report_slug) / _timestamp_for_path()


async def _save_html_and_screenshot(page: Page, directory: Path, prefix: str) -> dict[str, str]:
    directory.mkdir(parents=True, exist_ok=True)
    html_path = directory / f"{prefix}.html"
    screenshot_path = directory / f"{prefix}.png"
    html_path.write_text(_redact_html(await page.content()), encoding="utf-8")
    try:
        await page.screenshot(path=screenshot_path, full_page=True, timeout=20_000)
    except Exception:
        pass
    return {"html": str(html_path), "screenshot": str(screenshot_path)}


async def save_before_state(page: Page, directory: Path) -> dict[str, str]:
    return await _save_html_and_screenshot(page, directory, "before")


async def save_after_state(page: Page, directory: Path) -> dict[str, str]:
    return await _save_html_and_screenshot(page, directory, "after")


async def wait_for_user_decision(decision_file: Path) -> str:
    default_decision = os.getenv("ASNO_ASSISTED_DEFAULT_DECISION", "").strip().lower()
    if default_decision in {"enter", "retry", "skip", "abort"}:
        return default_decision
    prompt = "Decisión asistida [ENTER=continuar | retry | skip | abort]: "
    try:
        raw = await asyncio.to_thread(input, prompt)
        decision = (raw or "enter").strip().lower()
    except EOFError:
        print("")
        print("La terminal no acepta input interactivo en este entorno.")
        print(f"Escribí una decisión en este archivo para continuar: {decision_file}")
        decision_file.parent.mkdir(parents=True, exist_ok=True)
        while not decision_file.exists():
            await asyncio.sleep(1)
        decision = (decision_file.read_text(encoding="utf-8").strip() or "enter").lower()
    if decision not in {"enter", "retry", "skip", "abort"}:
        decision = "enter"
    return decision


async def assisted_pause(
    page: Page,
    settings: Settings,
    report_slug: str,
    report_name: str,
    reason: str,
) -> AssistedResult:
    directory = _assisted_run_dir(settings, report_slug)
    url_before = page.url
    before = await save_before_state(page, directory)
    decision_file = directory / "DECISION.txt"

    print("")
    print("PAUSA ASISTIDA")
    print(f"Reporte: {report_name}")
    print(f"URL: {url_before}")
    print(f"Motivo: {reason}")
    print("No pude resolver esta parte automáticamente.")
    print("Abraham, realiza la acción manualmente en el navegador abierto.")
    print("Cuando termines, vuelve a la terminal y escribe:")
    print("ENTER = continuar")
    print("retry = volver a intentar")
    print("skip = saltar este informe")
    print("abort = detener ejecución")

    decision = await wait_for_user_decision(decision_file)
    after = await save_after_state(page, directory)
    detected = await detect_state_after_manual_action(page, url_before)
    event = {
        "report_slug": report_slug,
        "report_name": report_name,
        "reason": reason,
        "url_before": url_before,
        "url_after": page.url,
        "user_decision": decision,
        "detected_after_user_action": detected,
        "before_screenshot": before.get("screenshot"),
        "after_screenshot": after.get("screenshot"),
        "before_html": before.get("html"),
        "after_html": after.get("html"),
        "created_at": now_iso(),
    }
    event_path = directory / "assisted_event.json"
    write_json(event_path, event)
    if decision == "abort":
        raise AssistedAbort(f"Assisted abort requested for {report_slug}: {reason}")
    return AssistedResult(decision, event_path, detected)


async def safe_pause_on_unknown(
    page: Page,
    settings: Settings,
    report_slug: str,
    report_name: str,
    reason: str = "Reporte clasificado como unknown",
) -> AssistedResult:
    return await assisted_pause(page, settings, report_slug, report_name, reason)


async def safe_pause_on_timeout(
    page: Page,
    settings: Settings,
    report_slug: str,
    report_name: str,
    reason: str,
) -> AssistedResult:
    return await assisted_pause(page, settings, report_slug, report_name, reason)


def continue_or_skip(result: AssistedResult) -> str:
    return result.decision
