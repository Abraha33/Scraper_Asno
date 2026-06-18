from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from playwright.async_api import Page

from .config import Settings
from .storage import now_iso, save_evidence, write_json


def _admin_url(settings: Settings, path: str = "") -> str:
    parsed = urlparse(settings.asno_url)
    prefix = parsed.path.split("/admin", 1)[0].rstrip("/")
    clean = path.lstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{prefix}/admin/{clean}".rstrip("/")


async def _human_type(page: Page, selector: str, value: str) -> None:
    locator = page.locator(selector).first
    await locator.wait_for(state="visible")
    await locator.click()
    await locator.press("Control+A")
    await locator.press("Backspace")
    await locator.type(value, delay=80)


async def _first_visible(page: Page, selectors: tuple[str, ...]):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible(timeout=1_500):
                return locator
        except Exception:
            continue
    return None


@dataclass
class LoginResult:
    status: str
    url: str
    message: str = ""
    attempt: int = 1
    evidence: dict[str, str] | None = None


async def _click_logout_if_visible(page: Page) -> bool:
    for selector in (
        "a:has-text('Cerrar Sesión')",
        "a:has-text('Cerrar sesión')",
        "button:has-text('Cerrar Sesión')",
        "button:has-text('Cerrar sesión')",
        "text=Cerrar Sesión",
    ):
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=1_000):
                await locator.click()
                await page.wait_for_load_state("networkidle")
                return True
        except Exception:
            continue
    return False


async def close_existing_session(page: Page, settings: Settings) -> None:
    try:
        await page.goto(_admin_url(settings, "calendar"), wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
        if "login" not in page.url.lower():
            await _click_logout_if_visible(page)
    except Exception as exc:
        logging.info("No existing session to close or lobby inaccessible: %s", exc)


async def _submit_login_once(page: Page, settings: Settings, attempt: int) -> LoginResult:
    login_candidates = []
    for candidate in (settings.asno_url, _admin_url(settings, "auth/login"), _admin_url(settings, "login")):
        if candidate not in login_candidates:
            login_candidates.append(candidate)
    before = None
    username = None
    password = None
    for login_url in login_candidates:
        await page.goto(login_url, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        before = await save_evidence(page, settings, f"before_login_attempt_{attempt}")
        username = await _first_visible(
            page,
            (
                "#input_name_login",
                "input[name='identity']",
                "input[name='user']",
                "input[name='username']",
                "input[name='name']",
                "input[type='text']",
                "input[type='email']",
            ),
        )
        password = await _first_visible(
            page,
            (
                "#input_pass_login",
                "input[name='password']",
                "input[name='pass']",
                "input[type='password']",
            ),
        )
        if username and password:
            break
    if not username or not password:
        evidence = await save_evidence(page, settings, f"login_missing_fields_attempt_{attempt}")
        return LoginResult("failure", page.url, "missing username/password fields", attempt, evidence)

    await username.fill(settings.user)
    await password.fill(settings.password)

    actual_user = await username.input_value()
    if actual_user != settings.user:
        evidence = await save_evidence(page, settings, f"login_wrong_user_attempt_{attempt}")
        return LoginResult("failure", page.url, f"field mismatch: expected {settings.user!r}, got {actual_user!r}", attempt, evidence)

    button = await _first_visible(
        page,
        (
            "#btnLogin",
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Ingresar')",
            "button:has-text('Acceder')",
            "button:has-text('Login')",
            "button:has-text('Iniciar sesión')",
        ),
    )
    if not button:
        evidence = await save_evidence(page, settings, f"login_missing_button_attempt_{attempt}")
        return LoginResult("failure", page.url, "missing login button", attempt, evidence)

    try:
        await button.evaluate("element => element.removeAttribute('disabled')")
    except Exception:
        pass

    try:
        await button.click()
    except Exception:
        await button.click(force=True)

    await page.wait_for_timeout(10_000)
    try:
        await page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        pass

    evidence = await save_evidence(page, settings, f"after_login_attempt_{attempt}")
    text = BeautifulSoup(await page.content(), "html.parser").get_text(" ", strip=True)
    lowered = text.lower()
    login_url = "login" in page.url.lower()

    has_active_session_link = await page.locator("a[href*='log_out_session']").count() > 0
    if has_active_session_link or any(token in lowered for token in ("sesión activa", "sesion activa")):
        return LoginResult("active_session", page.url, "active session detected", attempt, evidence)

    if "bloqueado" in lowered or "demasiados intentos" in lowered:
        return LoginResult("locked", page.url, "user locked by too many failed attempts", attempt, evidence)

    if login_url or "ingreso a wappsi" in lowered or "error de acceso" in lowered:
        return LoginResult("failure", page.url, "remained on login page or access error", attempt, evidence)

    state_path = settings.processed_dir / "session_state.json"
    await page.context.storage_state(path=state_path)
    result = LoginResult("success", page.url, "login successful", attempt, evidence)
    write_json(settings.processed_dir / "login_report.json", {**asdict(result), "session_state": str(state_path), "created_at": now_iso()})
    return result


async def _close_active_session_warning(page: Page, settings: Settings) -> bool:
    locator = page.locator("a[href*='log_out_session']").first
    try:
        if await locator.count() and await locator.is_visible(timeout=3_000):
            await locator.click()
            await page.wait_for_timeout(3_000)
            await save_evidence(page, settings, "closed_active_session")
            return True
    except Exception:
        logging.exception("Could not close active session warning.")
    return False


async def login(page: Page, settings: Settings, *, close_session_first: bool = False) -> LoginResult:
    # Important: do not proactively logout by default. Wappsi may show a session-active
    # warning after a normal login attempt; only then click log_out_session and retry.
    if close_session_first:
        await close_existing_session(page, settings)

    last = LoginResult("failure", page.url, "not attempted")
    for attempt in range(1, 4):
        last = await _submit_login_once(page, settings, attempt=attempt)
        write_json(settings.processed_dir / "login_report.json", {**asdict(last), "created_at": now_iso()})
        if last.status == "success":
            return last
        if last.status == "active_session":
            closed = await _close_active_session_warning(page, settings)
            if closed:
                continue
        break

    write_json(settings.processed_dir / "login_error.json", {**asdict(last), "created_at": now_iso()})
    raise RuntimeError(f"Login failed: {last.status} - {last.message}")


async def go_to_reports_module(page: Page, settings: Settings) -> None:
    if not settings.reports_url:
        raise RuntimeError("ASNO_REPORTS_URL is required for reports module commands")
    await page.goto(settings.reports_url, wait_until="domcontentloaded")
    await page.wait_for_load_state("networkidle")
    if "login" in page.url.lower():
        await page.goto(_admin_url(settings, "calendar"), wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
    for selector in ("a:has-text('Informes')", "li:has-text('Informes') > a", "text=Informes"):
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=2_000):
                await locator.click()
                await page.wait_for_load_state("networkidle")
                return
        except Exception:
            continue
