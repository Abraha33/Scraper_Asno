from __future__ import annotations

import asyncio
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from playwright.async_api import Page

from .config import ROOT_DIR, Settings
from .storage import now_iso, safe_name


SENSITIVE_RE = re.compile(r"(password|passwd|pass|secret|token|key|credential|login)", re.I)
RECIPE_DIR = ROOT_DIR / "configs" / "learned_recipes"
SALES_TABLE_RE = re.compile(r"Fecha|N[uú]mero|Numero|Total|Subtotal|Pagado|Saldo", re.I)
CALENDAR_RE = re.compile(r"\b(Lu|Ma|Mi|Ju|Vi|S[aá]|Do|Hoy)\b", re.I)


def recipe_path(report_slug: str) -> Path:
    return RECIPE_DIR / f"{safe_name(report_slug)}.yaml"


def learning_report_dir(settings: Settings, report_slug: str) -> Path:
    return settings.learning_dir / safe_name(report_slug)


def mask_sensitive_values(value: Any, field_hint: str = "") -> Any:
    if value is None:
        return None
    text = str(value)
    if SENSITIVE_RE.search(field_hint) or SENSITIVE_RE.search(text):
        return "[REDACTED]"
    if len(text) > 250:
        return text[:250] + "...[TRUNCATED]"
    return text


def _looks_like_calendar(text: Any) -> bool:
    value = str(text or "")
    return bool(CALENDAR_RE.search(value)) and not bool(SALES_TABLE_RE.search(value))


def _looks_like_sales_table(text: Any) -> bool:
    value = str(text or "")
    return bool(SALES_TABLE_RE.search(value)) and not _looks_like_calendar(value)


def _is_noise_event(event: dict[str, Any]) -> bool:
    selector = str(event.get("selector") or "")
    text = str(event.get("text") or event.get("label") or "")
    url = str(event.get("url") or "")
    tag = str(event.get("tag") or "")
    if event.get("type") == "click" and tag in {"div", "span", "label"} and not event.get("id") and not event.get("name"):
        return True
    if "ul.nav" in selector or "/nav[" in str(event.get("xpath") or ""):
        return True
    if "Importar Productos" in text:
        return True
    if event.get("type") == "dom_table_visible" and not _looks_like_sales_table(text):
        return True
    if event.get("type") == "dom_export_visible":
        combined = f"{text} {url} {selector}".lower()
        if "import" in combined or "importar" in combined:
            return True
        if not re.search(r"\b(pdf|excel|xls|xlsx|csv)\b|/pdf|/xls|/xlsx|/csv", combined):
            return True
    return False


def _date_template_for_field(event: dict[str, Any], value: Any) -> str | None:
    field_hint = " ".join(str(event.get(key) or "").lower() for key in ("name", "id", "selector", "label"))
    value_text = str(value or "")
    has_time = bool(re.search(r"\d{1,2}:\d{2}", value_text))
    if any(token in field_hint for token in ("start_date", "fecha de inicio", "date_from", "from")):
        return "{date_from_ddmmyyyy_hhmmss}" if has_time else "{date_from_ddmmyyyy}"
    if any(token in field_hint for token in ("end_date", "fecha final", "date_to", "to")):
        return "{date_to_ddmmyyyy_hhmmss}" if has_time else "{date_to_ddmmyyyy}"
    return None


def _template_dates(value: str, start: date | None, end: date | None) -> str:
    if not value:
        return value
    replacements: dict[str, str] = {}
    if start:
        replacements[start.isoformat()] = "{date_from_yyyy_mm_dd}"
        replacements[start.strftime("%d/%m/%Y")] = "{date_from_ddmmyyyy}"
        replacements[f"{start.strftime('%d/%m/%Y')} 00:00:00"] = "{date_from_ddmmyyyy_hhmmss}"
    if end:
        replacements[end.isoformat()] = "{date_to_yyyy_mm_dd}"
        replacements[end.strftime("%d/%m/%Y")] = "{date_to_ddmmyyyy}"
        replacements[f"{end.strftime('%d/%m/%Y')} 23:59:59"] = "{date_to_ddmmyyyy_hhmmss}"
    result = value
    for raw, template in replacements.items():
        result = result.replace(raw, template)
    return result


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    if not text:
        return '""'
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _write_simple_yaml(path: Path, data: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append(f"report: {_yaml_scalar(data.get('report'))}")
    lines.append(f"report_name: {_yaml_scalar(data.get('report_name'))}")
    lines.append(f"learned_at: {_yaml_scalar(data.get('learned_at'))}")
    lines.append("steps:")
    for step in data.get("steps", []):
        lines.append(f"  - action: {_yaml_scalar(step.get('action'))}")
        for key in ("selector", "label", "value", "value_template", "target", "strategy"):
            if key in step and step.get(key) is not None:
                lines.append(f"    {key}: {_yaml_scalar(step.get(key))}")
        candidates = step.get("candidates") or {}
        lines.append("    candidates:")
        for key in ("css", "text", "aria_label", "name", "id", "xpath", "role"):
            value = candidates.get(key)
            if value:
                lines.append(f"      {key}: {_yaml_scalar(value)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def _read_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"steps": []}
    current_step: dict[str, Any] | None = None
    in_candidates = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            if key != "steps":
                data[key] = _parse_scalar(value)
            continue
        if indent == 2 and line.startswith("- "):
            current_step = {"candidates": {}}
            data["steps"].append(current_step)
            in_candidates = False
            rest = line[2:]
            if ":" in rest:
                key, value = rest.split(":", 1)
                current_step[key.strip()] = _parse_scalar(value)
            continue
        if current_step is None:
            continue
        if indent == 4 and line == "candidates:":
            in_candidates = True
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            if in_candidates and indent >= 6:
                current_step.setdefault("candidates", {})[key.strip()] = _parse_scalar(value)
            elif indent == 4:
                in_candidates = False
                current_step[key.strip()] = _parse_scalar(value)
    return data


async def build_selector_candidates(page: Page, event: dict[str, Any] | None = None) -> dict[str, Any]:
    if event:
        return {
            "css": event.get("selector"),
            "text": event.get("text"),
            "aria_label": event.get("aria_label"),
            "name": event.get("name"),
            "id": event.get("id"),
            "xpath": event.get("xpath"),
            "role": event.get("role"),
        }
    return {}


async def record_user_events(page: Page, events_path: Path) -> None:
    events_path.parent.mkdir(parents=True, exist_ok=True)
    def append_event(payload: dict[str, Any]) -> None:
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({**payload, "recorded_at": now_iso()}, ensure_ascii=False) + "\n")

    page.on(
        "download",
        lambda download: append_event(
            {
                "type": "download_started",
                "url": page.url,
                "suggested_filename": mask_sensitive_values(download.suggested_filename),
            }
        ),
    )
    try:
        await page.expose_binding(
            "__asnoRecordEvent",
            lambda _source, payload: append_event(payload),
        )
    except Exception:
        pass
    await page.evaluate(
        """() => {
            if (window.__ASNO_LEARNING_INSTALLED__) return;
            window.__ASNO_LEARNING_INSTALLED__ = true;
            const cssPath = (el) => {
                if (!el || !el.tagName) return null;
                if (el.id) return `#${CSS.escape(el.id)}`;
                if (el.name) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.name)}"]`;
                const parts = [];
                let cur = el;
                while (cur && cur.nodeType === 1 && parts.length < 5) {
                    let part = cur.tagName.toLowerCase();
                    if (cur.className && typeof cur.className === 'string') {
                        const cls = cur.className.split(/\\s+/).filter(Boolean)[0];
                        if (cls) part += `.${CSS.escape(cls)}`;
                    }
                    const parent = cur.parentElement;
                    if (parent) {
                        const same = Array.from(parent.children).filter(x => x.tagName === cur.tagName);
                        if (same.length > 1) part += `:nth-of-type(${same.indexOf(cur) + 1})`;
                    }
                    parts.unshift(part);
                    cur = parent;
                }
                return parts.join(' > ');
            };
            const xpath = (el) => {
                if (!el || !el.tagName) return null;
                if (el.id) return `//*[@id="${el.id}"]`;
                const parts = [];
                let cur = el;
                while (cur && cur.nodeType === 1) {
                    let ix = 1;
                    let sib = cur.previousElementSibling;
                    while (sib) {
                        if (sib.tagName === cur.tagName) ix++;
                        sib = sib.previousElementSibling;
                    }
                    parts.unshift(`${cur.tagName.toLowerCase()}[${ix}]`);
                    cur = cur.parentElement;
                }
                return '/' + parts.join('/');
            };
            const labelFor = (el) => {
                if (el.id) {
                    const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                    if (label) return (label.innerText || '').trim().replace(/\\s+/g, ' ');
                }
                const label = el.closest('label');
                return label ? (label.innerText || '').trim().replace(/\\s+/g, ' ') : '';
            };
            const payload = (type, el) => ({
                type,
                url: location.href,
                tag: el && el.tagName ? el.tagName.toLowerCase() : null,
                selector: cssPath(el),
                text: (el && (el.innerText || el.textContent || el.value) || '').toString().trim().replace(/\\s+/g, ' ').slice(0, 250),
                value: el && 'value' in el ? String(el.value || '') : null,
                checked: el && 'checked' in el ? !!el.checked : null,
                id: el ? el.id || null : null,
                name: el ? el.getAttribute('name') : null,
                aria_label: el ? el.getAttribute('aria-label') : null,
                role: el ? el.getAttribute('role') : null,
                label: el ? labelFor(el) : null,
                xpath: xpath(el),
            });
            document.addEventListener('click', (ev) => window.__asnoRecordEvent(payload('click', ev.target)), true);
            document.addEventListener('change', (ev) => window.__asnoRecordEvent(payload('change', ev.target)), true);
            document.addEventListener('input', (ev) => {
                const el = ev.target;
                if (el && ['INPUT', 'TEXTAREA'].includes(el.tagName)) window.__asnoRecordEvent(payload('input', el));
            }, true);
            const observer = new MutationObserver(() => {
                const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
                const isCalendar = (table) => !!table.closest('.datetimepicker, .datepicker, #ui-datepicker-div') || /\\b(Lu|Ma|Mi|Ju|Vi|Sá|Do|Hoy)\\b/i.test(table.innerText || '');
                const salesLike = (table) => /Fecha|Número|Numero|Total|Subtotal|Pagado|Saldo/i.test(table.innerText || '');
                const table = Array.from(document.querySelectorAll('table')).find(t => visible(t) && !isCalendar(t) && salesLike(t));
                if (table) window.__asnoRecordEvent({ type: 'dom_table_visible', url: location.href, selector: table.id ? `#${CSS.escape(table.id)}` : 'table', text: (table.innerText || '').slice(0, 250) });
                const link = Array.from(document.querySelectorAll('a,button')).find(el => visible(el) && /pdf|excel|xls|xlsx|csv/i.test(`${el.innerText || ''} ${el.href || ''}`) && !/import|importar/i.test(`${el.innerText || ''} ${el.href || ''}`));
                if (link) window.__asnoRecordEvent(payload('dom_export_visible', link));
            });
            observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true });
        }"""
    )


async def wait_for_user_confirmation(confirm_file: Path | None = None) -> None:
    try:
        await asyncio.to_thread(input, "Cuando termines la acción manual, volvé a esta terminal y presioná ENTER...")
        return
    except EOFError:
        if not confirm_file:
            raise
    assert confirm_file is not None
    print("")
    print("La terminal no acepta ENTER interactivo en este entorno.")
    print(f"Fallback activo: cuando termines, creá este archivo para continuar: {confirm_file}")
    while not confirm_file.exists():
        await asyncio.sleep(1)


async def wait_for_learning_signal(page: Page, confirm_file: Path | None = None, timeout_seconds: int = 900) -> str:
    async def has_success_signal() -> str | None:
        try:
            return await page.evaluate(
                """() => {
                    const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
                    const isCalendar = (table) => !!table.closest('.datetimepicker, .datepicker, #ui-datepicker-div');
                    const tableTextLooksUseful = (table) => /Fecha|Número|Numero|Total|Subtotal|Pagado|Saldo/i.test(table.innerText || '');
                    const table = Array.from(document.querySelectorAll('table')).find((item) => visible(item) && !isCalendar(item) && tableTextLooksUseful(item) && item.querySelectorAll('tbody tr td, tr td').length >= 5);
                    if (table) return 'table_visible';
                    const exportEl = Array.from(document.querySelectorAll('a,button')).find((el) => visible(el) && /pdf|excel|xls|xlsx|csv/i.test(`${el.innerText || ''} ${el.href || ''}`));
                    if (exportEl) return 'export_visible';
                    return null;
                }"""
            )
        except Exception:
            return None

    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        if confirm_file and confirm_file.exists():
            return "confirm_file"
        signal = await has_success_signal()
        if signal:
            return signal
        await asyncio.sleep(1)
    raise TimeoutError(f"Learning mode timed out after {timeout_seconds}s waiting for table/export/manual confirmation")


async def enter_learning_mode(
    page: Page,
    settings: Settings,
    report_slug: str,
    report_name: str,
    reason: str,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    base = learning_report_dir(settings, report_slug)
    screenshots_dir = base / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    confirm_file = base / "CONTINUE"
    if confirm_file.exists():
        confirm_file.unlink()
    events_path = base / "events.jsonl"
    (base / "dom_before.html").write_text(await page.content(), encoding="utf-8")
    await page.screenshot(path=screenshots_dir / "before_manual.png", full_page=True)
    await record_user_events(page, events_path)
    print("")
    print("MANUAL: necesito tu ayuda en el navegador, pero sigo observando.")
    print(f"Motivo: {reason}")
    print("Hac? la acci?n manual necesaria. Apenas detecte tabla, exportaci?n o descarga, retomo solo.")
    print(f"Si quer?s forzar continuaci?n manualmente, cre? este archivo: {confirm_file}")
    signal = await wait_for_learning_signal(page, confirm_file)
    print(f"Aprendizaje retomado autom?ticamente por se?al: {signal}")
    (base / "dom_after.html").write_text(await page.content(), encoding="utf-8")
    await page.screenshot(path=screenshots_dir / "after_manual.png", full_page=True)
    recipe = await generate_recipe_from_events(report_slug, report_name, events_path, start, end)
    save_learned_recipe(report_slug, recipe)
    return recipe


async def generate_recipe_from_events(
    report_slug: str,
    report_name: str,
    events_path: Path,
    start: date | None = None,
    end: date | None = None,
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    steps: list[dict[str, Any]] = []
    last_by_selector: dict[tuple[str, str], int] = {}
    for event in events:
        etype = event.get("type")
        if etype not in {"click", "change", "input", "dom_table_visible", "dom_export_visible"}:
            continue
        if _is_noise_event(event):
            continue
        selector = event.get("selector")
        if not selector:
            continue
        action = "wait_for" if etype == "dom_table_visible" else "click"
        if etype in {"input", "change"} and event.get("tag") in {"input", "textarea"}:
            action = "fill"
        elif etype == "change" and event.get("tag") == "select":
            action = "select"
        elif etype == "dom_export_visible":
            action = "wait_for"
        value = mask_sensitive_values(event.get("value"), f"{event.get('name', '')} {event.get('id', '')}")
        if isinstance(value, str):
            value = _template_dates(value, start, end)
        field_template = _date_template_for_field(event, value)
        if field_template:
            value = field_template
        step: dict[str, Any] = {
            "action": action,
            "selector": selector,
            "label": event.get("label") or event.get("text"),
            "candidates": await build_selector_candidates(None, event),
        }
        if action in {"fill", "select"}:
            if isinstance(value, str) and "{" in value and "}" in value:
                step["value_template"] = value
            else:
                step["value"] = value
        if action == "wait_for":
            step["target"] = "table" if etype == "dom_table_visible" else "export"
        key = (action, selector)
        if key in last_by_selector and action in {"fill", "select", "wait_for", "click"}:
            steps[last_by_selector[key]] = step
        else:
            last_by_selector[key] = len(steps)
            steps.append(step)
    if not any(step.get("action") == "wait_for" and step.get("target") == "table" for step in steps):
        steps.append({"action": "wait_for", "target": "table", "selector": "table", "strategy": "visible_table", "candidates": {"css": "table"}})
    if not any(step.get("action") == "paginate" for step in steps):
        steps.append({"action": "paginate", "strategy": "datatable_next", "selector": "a.paginate_button.next:not(.disabled)", "candidates": {"css": "a.paginate_button.next:not(.disabled)", "text": "Siguiente"}})
    return {"report": report_slug, "report_name": report_name, "learned_at": now_iso(), "steps": steps}


def save_learned_recipe(report_slug: str, recipe: dict[str, Any]) -> Path:
    path = recipe_path(report_slug)
    _write_simple_yaml(path, recipe)
    return path


def load_learned_recipe(report_slug: str) -> dict[str, Any] | None:
    path = recipe_path(report_slug)
    if not path.exists():
        return None
    return _read_simple_yaml(path)


def list_learned_recipes() -> list[Path]:
    RECIPE_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(RECIPE_DIR.glob("*.yaml"))


def delete_learned_recipe(report_slug: str) -> bool:
    path = recipe_path(report_slug)
    if not path.exists():
        return False
    path.unlink()
    return True


def _render_template(value: str | None, start: date, end: date) -> str | None:
    if value is None:
        return None
    return (
        value.replace("{date_from_yyyy_mm_dd}", start.isoformat())
        .replace("{date_to_yyyy_mm_dd}", end.isoformat())
        .replace("{date_from_ddmmyyyy}", start.strftime("%d/%m/%Y"))
        .replace("{date_to_ddmmyyyy}", end.strftime("%d/%m/%Y"))
        .replace("{date_from_ddmmyyyy_hhmmss}", f"{start.strftime('%d/%m/%Y')} 00:00:00")
        .replace("{date_to_ddmmyyyy_hhmmss}", f"{end.strftime('%d/%m/%Y')} 23:59:59")
    )


async def _locator_from_candidates(page: Page, step: dict[str, Any]):
    candidates = step.get("candidates") or {}
    selectors = [step.get("selector"), candidates.get("css")]
    for selector in [item for item in selectors if item]:
        locator = page.locator(selector).first
        try:
            if await locator.count():
                return locator
        except Exception:
            continue
    if candidates.get("id"):
        locator = page.locator(f"#{candidates['id']}").first
        if await locator.count():
            return locator
    if candidates.get("name"):
        locator = page.locator(f"[name='{candidates['name']}']").first
        if await locator.count():
            return locator
    if candidates.get("text"):
        locator = page.get_by_text(candidates["text"], exact=False).first
        if await locator.count():
            return locator
    if candidates.get("xpath"):
        locator = page.locator(f"xpath={candidates['xpath']}").first
        if await locator.count():
            return locator
    raise RuntimeError(f"No selector candidate worked for step: {step}")


async def validate_recipe_step(page: Page, step: dict[str, Any]) -> bool:
    try:
        if step.get("action") in {"click", "fill", "select"}:
            await _locator_from_candidates(page, step)
        return True
    except Exception:
        return False


async def replay_recipe(page: Page, recipe: dict[str, Any], start: date, end: date) -> dict[str, Any]:
    replayed: list[dict[str, Any]] = []
    for step in recipe.get("steps", []):
        action = step.get("action")
        if action == "wait_for":
            target = step.get("target")
            if target == "table":
                await page.locator(step.get("selector") or "table").first.wait_for(state="visible", timeout=45_000)
            replayed.append({"step": step, "status": "success"})
            continue
        if action == "paginate":
            replayed.append({"step": step, "status": "skipped_runtime_pagination"})
            continue
        locator = await _locator_from_candidates(page, step)
        if action == "click":
            if await locator.is_visible(timeout=2_000):
                await locator.click()
            else:
                await locator.evaluate("(el) => el.click()")
        elif action == "fill":
            value = _render_template(step.get("value_template") or step.get("value") or "", start, end) or ""
            await locator.evaluate(
                """(el, value) => {
                    el.removeAttribute('readonly');
                    el.removeAttribute('disabled');
                    el.value = value;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }""",
                value,
            )
        elif action == "select":
            value = _render_template(step.get("value_template") or step.get("value") or "", start, end) or ""
            await locator.select_option(label=value)
        replayed.append({"step": step, "status": "success"})
    return {"status": "success", "steps": len(replayed), "details": replayed}
