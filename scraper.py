from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import BrowserContext, Page, Request, Response, async_playwright


DEFAULT_START_DATE = "01/01/2021 00:00:00"
DEFAULT_END_DATE = "31/12/2026 00:00:00"
DEFAULT_OUTPUT_DIR = Path("outputs") / "informes"
DEFAULT_STATE_DIR = Path("state")
DEFAULT_LOG_DIR = Path("logs")

DATE_INPUT_HINTS = (
    "fecha",
    "desde",
    "hasta",
    "inicio",
    "fin",
    "fch",
    "date",
)

USERNAME_HINTS = (
    "usuario",
    "user",
    "username",
    "login",
    "email",
    "correo",
)

PASSWORD_HINTS = (
    "password",
    "pass",
    "clave",
    "contraseña",
    "contrasena",
)

SEARCH_BUTTON_HINTS = (
    "buscar",
    "consultar",
    "filtrar",
    "generar",
    "aceptar",
    "ver",
)

EXPORT_HINTS = (
    "excel",
    "csv",
    "pdf",
    "export",
    "descargar",
    "imprimir",
)


@dataclass
class ScrapeConfig:
    base_url: str
    reports_url: str | None
    username: str
    password: str
    start_date: str = DEFAULT_START_DATE
    end_date: str = DEFAULT_END_DATE
    output_dir: Path = DEFAULT_OUTPUT_DIR
    state_dir: Path = DEFAULT_STATE_DIR
    log_dir: Path = DEFAULT_LOG_DIR
    headless: bool = False
    max_pages: int = 500
    batch_size: int | None = None
    resume: bool = False
    restart_browser_every: int = 50
    production: bool = False
    diagnose_only: bool = False
    diagnose_report_limit: int = 0
    force_logout_paths: bool = False
    skip_initial_logout: bool = False
    manual_login: bool = False
    manual_login_timeout_sec: int = 180
    slow_mo_ms: int = 75
    timeout_ms: int = 45_000


@dataclass
class PageArtifact:
    url: str
    title: str
    html_file: str
    screenshot_file: str
    table_files: list[str]
    links_found: int
    network_files: list[str]


@dataclass
class ProgressState:
    total_expected: int
    completed_urls: list[str]
    failed_urls: list[str]
    current_url: str | None
    last_success_url: str | None
    started_at: str
    updated_at: str
    production_settings: dict[str, Any]
    batch_size: int | None
    restart_browser_every: int


def load_env_txt(path: Path) -> dict[str, str]:
    """Read credentials/env files written as key:"value" without printing secrets."""
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def first_env(*names: str, fallback: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return fallback


def build_config(args: argparse.Namespace) -> ScrapeConfig:
    load_dotenv()

    env_file = Path(args.env_txt)
    if not env_file.exists() and args.env_txt == "credentials":
        for candidate in (Path("credentials.txt"), Path("env.txt")):
            if candidate.exists():
                env_file = candidate
                break
    env_txt_values = load_env_txt(env_file)
    for key, value in env_txt_values.items():
        os.environ.setdefault(key, value)

    base_url = args.base_url or first_env(
        "INFORMES_BASE_URL",
        "BASE_URL",
        "URL_BASE",
        "LOGIN_URL",
        "url_base",
        "url",
    )
    username = args.username or first_env(
        "url_user",
        "INFORMES_USERNAME",
        "USERNAME",
        "USER",
    )
    password = args.password or first_env(
        "url_password",
        "INFORMES_PASSWORD",
        "PASSWORD",
        "PASS",
    )
    reports_url = args.reports_url or first_env(
        "INFORMES_REPORTS_URL",
        "REPORTS_URL",
        "url_reports",
    )

    missing = [
        name
        for name, value in (
            ("base_url", base_url),
            ("username", username),
            ("password", password),
        )
        if not value
    ]
    if missing:
        raise SystemExit(
            "Faltan datos de configuración: "
            + ", ".join(missing)
            + ". Agregalos en .env/env.txt o pasalos por CLI. "
            + "Ejemplo: python scraper.py --base-url https://..."
        )

    return ScrapeConfig(
        base_url=base_url,
        reports_url=reports_url,
        username=username,
        password=password,
        start_date=args.start_date,
        end_date=args.end_date,
        output_dir=Path(args.output_dir),
        state_dir=Path(args.state_dir),
        log_dir=Path(args.log_dir),
        headless=args.headless,
        max_pages=args.max_pages,
        batch_size=args.batch_size,
        resume=args.resume,
        restart_browser_every=args.restart_browser_every,
        production=args.production,
        diagnose_only=args.diagnose_only,
        diagnose_report_limit=args.diagnose_report_limit,
        force_logout_paths=args.force_logout_paths,
        skip_initial_logout=args.skip_initial_logout,
        manual_login=args.manual_login,
        manual_login_timeout_sec=args.manual_login_timeout_sec,
        slow_mo_ms=args.slow_mo_ms,
        timeout_ms=args.timeout_ms,
    )


def setup_logging(config: ScrapeConfig) -> Path:
    config.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = config.log_dir / "informes_extract.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    return log_path


def safe_name(value: str, max_len: int = 90) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return normalized[:max_len] or "artifact"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def partial_path(config: ScrapeConfig) -> Path:
    return config.output_dir / "pages_partial.jsonl"


def progress_path(config: ScrapeConfig) -> Path:
    return config.state_dir / "informes_progress.json"


def errors_path(config: ScrapeConfig) -> Path:
    return config.output_dir / "errors.json"


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()


def read_partial_completed_urls(path: Path) -> set[str]:
    completed: set[str] = set()
    if not path.exists():
        return completed
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = row.get("url")
        if url:
            completed.add(url)
    return completed


def load_progress(config: ScrapeConfig) -> ProgressState | None:
    path = progress_path(config)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return ProgressState(
        total_expected=int(raw.get("total_expected", 0)),
        completed_urls=list(raw.get("completed_urls", [])),
        failed_urls=list(raw.get("failed_urls", [])),
        current_url=raw.get("current_url"),
        last_success_url=raw.get("last_success_url"),
        started_at=raw.get("started_at") or now_iso(),
        updated_at=raw.get("updated_at") or now_iso(),
        production_settings=dict(raw.get("production_settings", {})),
        batch_size=raw.get("batch_size"),
        restart_browser_every=int(raw.get("restart_browser_every", config.restart_browser_every)),
    )


def save_progress(config: ScrapeConfig, state: ProgressState) -> None:
    state.updated_at = now_iso()
    path = progress_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False), encoding="utf-8")


def load_errors(config: ScrapeConfig) -> list[dict[str, Any]]:
    path = errors_path(config)
    if not path.exists():
        return []
    try:
        return list(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return []


def save_errors(config: ScrapeConfig, errors: list[dict[str, Any]]) -> None:
    path = errors_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8")


def same_origin(url_a: str, url_b: str) -> bool:
    parsed_a = urlparse(url_a)
    parsed_b = urlparse(url_b)
    return parsed_a.netloc == parsed_b.netloc


def admin_url(config: ScrapeConfig, path: str = "") -> str:
    parsed = urlparse(config.base_url)
    prefix = parsed.path.split("/admin", 1)[0].rstrip("/")
    clean_path = path.lstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{prefix}/admin/{clean_path}".rstrip("/")


def looks_like_informes_url(url: str) -> bool:
    low = url.lower()
    return any(
        token in low
        for token in (
            "informe",
            "reporte",
            "tramite",
            "comercial",
            "consulta",
            "gestion",
            "solicitud",
        )
    )


async def dismiss_popups(page: Page) -> None:
    candidates = (
        "button:has-text('Aceptar')",
        "button:has-text('OK')",
        "button:has-text('Ok')",
        "button:has-text('Cerrar')",
        "button:has-text('Entendido')",
        "button:has-text('Continuar')",
        "a:has-text('Cerrar')",
        ".modal button.close",
        ".swal2-confirm",
        "[aria-label='Close']",
        "[aria-label='Cerrar']",
    )
    for selector in candidates:
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=750):
                await locator.click(timeout=1_500)
                await page.wait_for_timeout(500)
        except Exception:
            continue


async def fill_first_matching(page: Page, hints: tuple[str, ...], value: str) -> bool:
    selectors: list[str] = []
    for hint in hints:
        selectors.extend(
            [
                f"input[name*='{hint}' i]",
                f"input[id*='{hint}' i]",
                f"input[placeholder*='{hint}' i]",
                f"input[aria-label*='{hint}' i]",
            ]
        )

    if any(h in PASSWORD_HINTS for h in hints):
        selectors.insert(0, "input[type='password']")
    else:
        selectors.extend(("input[type='text']", "input:not([type])"))

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=1_000):
                await locator.fill(value, timeout=3_000)
                return True
        except Exception:
            continue
    return False


async def human_type(locator: Any, value: str) -> None:
    await locator.click(timeout=5_000)
    await locator.press("Control+A")
    await locator.press("Backspace")
    await locator.type(value, delay=80)


async def click_first_matching(page: Page, hints: tuple[str, ...]) -> bool:
    selectors: list[str] = []
    for hint in hints:
        selectors.extend(
            [
                f"button:has-text('{hint}')",
                f"a:has-text('{hint}')",
                f"input[type='submit'][value*='{hint}' i]",
                f"input[type='button'][value*='{hint}' i]",
            ]
        )

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=1_000):
                await locator.click(timeout=5_000)
                return True
        except Exception:
            continue
    return False


async def logout_if_possible(page: Page) -> None:
    logout_selectors = (
        "a:has-text('Cerrar sesión')",
        "a:has-text('Cerrar Sesión')",
        "button:has-text('Cerrar sesión')",
        "button:has-text('Cerrar Sesión')",
        "text=Cerrar Sesión",
        "text=Cerrar sesión",
        "a:has-text('Salir')",
        "button:has-text('Salir')",
        "a[href*='logout' i]",
        "a[href*='salir' i]",
    )
    for selector in logout_selectors:
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=1_000):
                await locator.click(timeout=5_000)
                await page.wait_for_load_state("networkidle", timeout=15_000)
                return
        except Exception:
            continue


async def close_existing_session_from_lobby(page: Page, config: ScrapeConfig) -> None:
    """Use the real ASNO/Wappsi lobby/sidebar flow shown in the video."""
    for target in (admin_url(config, "calendar"), admin_url(config)):
        try:
            await page.goto(target, wait_until="domcontentloaded", timeout=15_000)
            await page.wait_for_load_state("networkidle", timeout=15_000)
            await dismiss_popups(page)
            if "login" in page.url.lower():
                continue
            logging.info("Existing session detected at %s; trying sidebar logout", page.url)
            await logout_if_possible(page)
            await page.wait_for_load_state("networkidle", timeout=15_000)
            return
        except Exception:
            continue


async def force_logout_paths(page: Page, config: ScrapeConfig) -> None:
    parsed = urlparse(config.base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    base_path = parsed.path.split("/admin", 1)[0]
    candidates = [
        urljoin(origin, f"{base_path}/admin/logout"),
        urljoin(origin, f"{base_path}/admin/auth/logout"),
        urljoin(origin, f"{base_path}/logout"),
        urljoin(origin, f"{base_path}/auth/logout"),
    ]
    for url in candidates:
        try:
            logging.info("Trying logout URL: %s", url)
            await page.goto(url, wait_until="domcontentloaded", timeout=12_000)
            await page.wait_for_load_state("networkidle", timeout=12_000)
            await dismiss_popups(page)
        except Exception:
            continue


async def wait_for_manual_login(page: Page, config: ScrapeConfig) -> None:
    print("LOGIN MANUAL: se abrió el navegador visible.")
    print("LOGIN MANUAL: iniciá sesión en la ventana. El scraper espera hasta que salgas de /auth/login.")
    deadline = asyncio.get_event_loop().time() + config.manual_login_timeout_sec
    last_url = ""
    stable_since: float | None = None
    while asyncio.get_event_loop().time() < deadline:
        current_url = page.url
        if current_url != last_url:
            logging.info("Manual login current URL: %s", current_url)
            last_url = current_url
        is_login = "login" in current_url.lower()
        if not is_login:
            if stable_since is None:
                stable_since = asyncio.get_event_loop().time()
            if asyncio.get_event_loop().time() - stable_since >= 8:
                await page.wait_for_load_state("networkidle", timeout=15_000)
                await dismiss_popups(page)
                if "login" not in page.url.lower():
                    logging.info("Manual login accepted and stable at URL: %s", page.url)
                    return
                stable_since = None
        else:
            stable_since = None
        await page.wait_for_timeout(1_000)
    diagnostics_dir = config.output_dir / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "manual_login_timeout.html").write_text(await page.content(), encoding="utf-8")
    await page.screenshot(path=diagnostics_dir / "manual_login_timeout.png", full_page=True)
    raise RuntimeError(
        "No se completó el login manual dentro del tiempo configurado. "
        f"Diagnóstico guardado en: {diagnostics_dir.resolve()}"
    )


async def login(page: Page, config: ScrapeConfig) -> None:
    if not config.skip_initial_logout:
        await close_existing_session_from_lobby(page, config)
    await page.goto(config.base_url, wait_until="domcontentloaded", timeout=config.timeout_ms)
    await dismiss_popups(page)
    if config.manual_login:
        await wait_for_manual_login(page, config)
        return

    if not config.skip_initial_logout:
        await logout_if_possible(page)
        if config.force_logout_paths:
            await force_logout_paths(page, config)
    await page.goto(config.base_url, wait_until="domcontentloaded", timeout=config.timeout_ms)
    await dismiss_popups(page)

    user_filled = False
    password_filled = False

    if await page.locator("input[name='identity']").count():
        await human_type(page.locator("input[name='identity']").first, config.username)
        user_filled = True
    if await page.locator("input[name='password']").count():
        await human_type(page.locator("input[name='password']").first, config.password)
        password_filled = True
    if not user_filled:
        user_filled = await fill_first_matching(page, USERNAME_HINTS, config.username)
    if not password_filled:
        password_filled = await fill_first_matching(page, PASSWORD_HINTS, config.password)

    if not user_filled or not password_filled:
        raise RuntimeError(
            "No pude ubicar campos de usuario/contraseña. "
            "Hay que ajustar selectores de login con el HTML real."
        )

    diagnostics_dir = config.output_dir / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "login_before_submit.html").write_text(await page.content(), encoding="utf-8")
    await page.screenshot(path=diagnostics_dir / "login_before_submit.png", full_page=True)
    try:
        actual_username = await page.locator("input[name='identity']").first.input_value(timeout=3_000)
        if actual_username != config.username:
            raise RuntimeError(
                f"El campo Nombre quedó con {actual_username!r}, pero credentials indica {config.username!r}. "
                "Corto antes de enviar para evitar intentos fallidos."
            )
    except RuntimeError:
        raise
    except Exception:
        logging.warning("No pude verificar el valor final del campo Nombre antes del submit.")

    await page.evaluate(
        """() => {
            for (const input of document.querySelectorAll('input')) {
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
            }
        }"""
    )

    try:
        button = page.locator("#btnLogin, button[type='submit']").first
        await button.wait_for(state="visible", timeout=10_000)
        try:
            await page.wait_for_function(
                """() => {
                    const button = document.querySelector('#btnLogin, button[type="submit"]');
                    return button && !button.disabled && !button.hasAttribute('disabled');
                }""",
                timeout=8_000,
            )
        except Exception:
            logging.warning("Login button did not visibly enable; trying normal click anyway.")
        async with page.expect_navigation(wait_until="networkidle", timeout=config.timeout_ms):
            await button.click(timeout=10_000)
    except Exception:
        await page.locator("form[action*='auth/login']").first.evaluate(
            """form => {
                const button = form.querySelector('button[type="submit"]');
                if (button) {
                    button.removeAttribute('disabled');
                    button.disabled = false;
                }
                if (form.requestSubmit) {
                    form.requestSubmit(button || undefined);
                } else {
                    form.submit();
                }
            }"""
        )
        await page.wait_for_load_state("networkidle", timeout=config.timeout_ms)

    await page.wait_for_load_state("networkidle", timeout=config.timeout_ms)
    await dismiss_popups(page)
    await page.wait_for_timeout(3_000)
    (diagnostics_dir / "login_after_submit.html").write_text(await page.content(), encoding="utf-8")
    await page.screenshot(path=diagnostics_dir / "login_after_submit.png", full_page=True)

    if "login" in page.url.lower():
        if config.manual_login:
            await wait_for_manual_login(page, config)
            return
        login_failed_html = await page.content()
        (diagnostics_dir / "login_failed.html").write_text(login_failed_html, encoding="utf-8")
        await page.screenshot(path=diagnostics_dir / "login_failed.png", full_page=True)
        login_failed_text = BeautifulSoup(login_failed_html, "html.parser").get_text(" ", strip=True)
        if "bloqueado" in login_failed_text.lower() or "demasiados intentos" in login_failed_text.lower():
            raise RuntimeError(
                "ASNO/Wappsi bloqueó temporalmente el usuario por demasiados intentos fallidos. "
                "No reintento para evitar extender el bloqueo. Esperá el tiempo indicado por el sistema "
                f"y verificá credenciales. Diagnóstico guardado en: {diagnostics_dir.resolve()}"
            )
        raise RuntimeError(
            "El sistema siguió en login después de enviar credenciales. "
            "Puede ser credencial inválida, bloqueo de sesión, captcha o validación adicional."
            f" Diagnóstico guardado en: {diagnostics_dir.resolve()}"
        )


async def discover_links(page: Page, base_url: str) -> set[str]:
    hrefs = await page.eval_on_selector_all(
        "a[href]",
        """links => links.map(a => ({
            href: a.href,
            text: (a.innerText || a.textContent || '').trim()
        }))""",
    )

    urls: set[str] = set()
    for item in hrefs:
        href = item.get("href", "")
        text = item.get("text", "")
        absolute = urljoin(page.url, href)
        if not absolute.startswith(("http://", "https://")):
            continue
        if not same_origin(base_url, absolute):
            continue
        if looks_like_informes_url(absolute) or looks_like_informes_url(text):
            urls.add(absolute)

    return urls


async def find_informes_entrypoints(page: Page, config: ScrapeConfig) -> set[str]:
    found = await discover_links(page, config.base_url)

    for text in ("Informes", "Reportes", "Trámites", "Tramites", "Comerciales", "Consultas"):
        try:
            locator = page.get_by_text(text, exact=False).first
            if await locator.count() and await locator.is_visible(timeout=1_000):
                await locator.click(timeout=5_000)
                await page.wait_for_load_state("networkidle", timeout=15_000)
                await dismiss_popups(page)
                found.add(page.url)
                found.update(await discover_links(page, config.base_url))
        except Exception:
            continue

    return found


async def open_reports_sidebar(page: Page) -> None:
    """Open the left sidebar Informes section as shown in the ASNO video."""
    candidates = (
        "a:has-text('Informes')",
        "li:has-text('Informes') > a",
        "text=Informes",
    )
    for selector in candidates:
        try:
            locator = page.locator(selector).first
            if await locator.count() and await locator.is_visible(timeout=2_000):
                await locator.click(timeout=5_000)
                await page.wait_for_timeout(750)
                await dismiss_popups(page)
                return
        except Exception:
            continue


async def discover_sidebar_reports(page: Page, config: ScrapeConfig) -> list[dict[str, Any]]:
    await open_reports_sidebar(page)
    items = await page.evaluate(
        """() => {
            const norm = s => (s || '').trim().replace(/\\s+/g, ' ');
            const visible = el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
            };
            const links = Array.from(document.querySelectorAll('a,button,[role=button]'));
            return links
                .map((el, index) => ({
                    index,
                    text: norm(el.innerText || el.textContent || el.value),
                    href: el.href || el.getAttribute('href') || null,
                    onclick: el.getAttribute('onclick'),
                    id: el.getAttribute('id'),
                    class: el.getAttribute('class'),
                    visible: visible(el)
                }))
                .filter(item => item.visible && item.text)
                .filter(item => /informe|cantidad|producto|ventas|compras|inventario|cierre|flujo|alerta|comprobante|diario|bodega|categor/i.test(item.text));
        }"""
    )
    reports: list[dict[str, Any]] = []
    for item in items:
        text = item.get("text") or ""
        if text.lower() == "informes":
            continue
        href = item.get("href")
        if href and href.startswith("http") and not same_origin(config.base_url, href):
            continue
        reports.append(item)
    return reports


async def close_visible_modal(page: Page) -> None:
    selectors = (
        ".modal.in button.close",
        ".modal.show button.close",
        ".modal button.close",
        "button:has-text('×')",
        "button:has-text('Cerrar')",
    )
    for selector in selectors:
        try:
            locator = page.locator(selector).last
            if await locator.count() and await locator.is_visible(timeout=1_000):
                await locator.click(timeout=3_000)
                await page.wait_for_timeout(500)
                return
        except Exception:
            continue
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
    except Exception:
        pass


async def inspect_sidebar_report_modal(page: Page, report_name: str, config: ScrapeConfig, index: int) -> None:
    await open_reports_sidebar(page)
    try:
        locator = page.get_by_text(report_name, exact=True).first
        if not await locator.count():
            locator = page.get_by_text(report_name, exact=False).first
        if not await locator.count() or not await locator.is_visible(timeout=2_000):
            return
        await locator.click(timeout=5_000)
        await page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        await page.wait_for_timeout(2_000)

    await dismiss_popups(page)
    await apply_date_range(page, config)
    await save_diagnostics(page, config, f"sidebar_report_{index:02d}_{report_name}")
    await close_visible_modal(page)


async def apply_date_range(page: Page, config: ScrapeConfig) -> None:
    inputs = await page.locator("input").element_handles()
    date_like: list[Any] = []

    for handle in inputs:
        attrs = await handle.evaluate(
            """el => ({
                type: el.getAttribute('type') || '',
                name: el.getAttribute('name') || '',
                id: el.getAttribute('id') || '',
                placeholder: el.getAttribute('placeholder') || '',
                aria: el.getAttribute('aria-label') || '',
                value: el.value || ''
            })"""
        )
        blob = " ".join(str(v).lower() for v in attrs.values())
        if attrs["type"].lower() in ("date", "datetime-local") or any(h in blob for h in DATE_INPUT_HINTS):
            date_like.append(handle)

    if len(date_like) >= 2:
        await date_like[0].fill(config.start_date)
        await date_like[1].fill(config.end_date)
    elif len(date_like) == 1:
        await date_like[0].fill(config.start_date)

    await click_first_matching(page, SEARCH_BUTTON_HINTS)
    await page.wait_for_load_state("networkidle", timeout=20_000)
    await dismiss_popups(page)


async def trigger_exports(page: Page, output_dir: Path) -> list[str]:
    downloaded: list[str] = []
    for hint in EXPORT_HINTS:
        locators = [
            page.locator(f"a:has-text('{hint}')"),
            page.locator(f"button:has-text('{hint}')"),
            page.locator(f"input[value*='{hint}' i]"),
            page.locator(f"a[href*='{hint}' i]"),
        ]
        for locator in locators:
            count = await locator.count()
            for idx in range(min(count, 5)):
                target = locator.nth(idx)
                try:
                    if not await target.is_visible(timeout=500):
                        continue
                    async with page.expect_download(timeout=8_000) as download_info:
                        await target.click(timeout=3_000)
                    download = await download_info.value
                    suggested = safe_name(download.suggested_filename)
                    destination = output_dir / "downloads" / suggested
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    await download.save_as(destination)
                    downloaded.append(str(destination))
                except Exception:
                    continue
    return downloaded


async def extract_tables(page: Page, output_dir: Path, stem: str) -> list[str]:
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    table_files: list[str] = []

    for table_idx, table in enumerate(soup.select("table"), start=1):
        rows: list[list[str]] = []
        for tr in table.select("tr"):
            cells = [
                cell.get_text(" ", strip=True)
                for cell in tr.select("th,td")
            ]
            if cells:
                rows.append(cells)

        if not rows:
            continue

        path = output_dir / "tables" / f"{stem}_table_{table_idx:02d}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        table_files.append(str(path))

    return table_files


async def extract_component_map(page: Page) -> dict[str, Any]:
    return await page.evaluate(
        """() => {
            const text = el => (el.innerText || el.textContent || el.value || '').trim().replace(/\\s+/g, ' ');
            const attrs = (el, names) => Object.fromEntries(names.map(name => [name, el.getAttribute(name)]));
            const visible = el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style && style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
            };
            return {
                url: location.href,
                title: document.title,
                links: Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    text: text(a),
                    href: a.href,
                    visible: visible(a),
                    attrs: attrs(a, ['id', 'class', 'target', 'onclick', 'data-url', 'data-href'])
                })),
                buttons: Array.from(document.querySelectorAll('button,input[type=button],input[type=submit],a.btn')).map(b => ({
                    text: text(b),
                    type: b.getAttribute('type'),
                    disabled: !!b.disabled || b.getAttribute('disabled') !== null,
                    visible: visible(b),
                    attrs: attrs(b, ['id', 'class', 'name', 'value', 'onclick', 'data-url', 'data-href'])
                })),
                inputs: Array.from(document.querySelectorAll('input,select,textarea')).map(i => ({
                    tag: i.tagName.toLowerCase(),
                    type: i.getAttribute('type'),
                    name: i.getAttribute('name'),
                    id: i.getAttribute('id'),
                    placeholder: i.getAttribute('placeholder'),
                    value: i.tagName.toLowerCase() === 'select' ? '' : i.value,
                    visible: visible(i),
                    attrs: attrs(i, ['class', 'data-url', 'data-href', 'data-provide'])
                })),
                forms: Array.from(document.querySelectorAll('form')).map(f => ({
                    action: f.action,
                    method: f.method,
                    attrs: attrs(f, ['id', 'class', 'name'])
                })),
                tables: Array.from(document.querySelectorAll('table')).map((t, index) => ({
                    index,
                    id: t.getAttribute('id'),
                    class: t.getAttribute('class'),
                    visible: visible(t),
                    row_count: t.querySelectorAll('tr').length,
                    header_text: Array.from(t.querySelectorAll('th')).map(text).slice(0, 30)
                })),
                iframes: Array.from(document.querySelectorAll('iframe')).map(i => ({
                    src: i.src,
                    name: i.name,
                    id: i.id,
                    visible: visible(i)
                })),
                hidden_urls: Array.from(document.querySelectorAll('[onclick],[data-url],[data-href],[href]'))
                    .map(el => [el.getAttribute('onclick'), el.getAttribute('data-url'), el.getAttribute('data-href'), el.getAttribute('href')])
                    .flat()
                    .filter(Boolean)
                    .filter(v => /admin|report|informe|ajax|api|consulta|tramite|trans/i.test(v))
                    .slice(0, 500)
            };
        }"""
    )


async def save_diagnostics(page: Page, config: ScrapeConfig, label: str) -> dict[str, Any]:
    diagnostics_dir = config.output_dir / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_name(label)
    component_map = await extract_component_map(page)
    (diagnostics_dir / f"{stem}_component_map.json").write_text(
        json.dumps(component_map, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (diagnostics_dir / f"{stem}.html").write_text(await page.content(), encoding="utf-8")
    await page.screenshot(path=diagnostics_dir / f"{stem}.png", full_page=True)
    return component_map


def should_capture_response(response: Response) -> bool:
    content_type = response.headers.get("content-type", "").lower()
    url = response.url.lower()
    return (
        "application/json" in content_type
        or "text/csv" in content_type
        or "application/pdf" in content_type
        or url.endswith((".json", ".csv", ".pdf", ".xlsx", ".xls"))
    )


async def capture_response(response: Response, output_dir: Path, index: int) -> str | None:
    if not should_capture_response(response):
        return None
    try:
        body = await response.body()
    except Exception:
        return None

    parsed = urlparse(response.url)
    suffix = Path(parsed.path).suffix or ".bin"
    name = safe_name(f"{index:04d}_{parsed.netloc}_{parsed.path}") + suffix
    path = output_dir / "network" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return str(path)


async def save_page_artifacts(
    page: Page,
    output_dir: Path,
    network_files: list[str],
    seq: int,
) -> PageArtifact:
    title = await page.title()
    stem = safe_name(f"{seq:04d}_{title}_{urlparse(page.url).path}")

    html_path = output_dir / "html" / f"{stem}.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(await page.content(), encoding="utf-8")

    screenshot_path = output_dir / "screenshots" / f"{stem}.png"
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=screenshot_path, full_page=True)

    table_files = await extract_tables(page, output_dir, stem)
    links = await discover_links(page, page.url)

    return PageArtifact(
        url=page.url,
        title=title,
        html_file=str(html_path),
        screenshot_file=str(screenshot_path),
        table_files=table_files,
        links_found=len(links),
        network_files=network_files.copy(),
    )


async def scrape(config: ScrapeConfig) -> list[PageArtifact]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.state_dir.mkdir(parents=True, exist_ok=True)
    log_path = setup_logging(config)

    artifacts: list[PageArtifact] = []
    visited: set[str] = set()
    queue: list[str] = []
    network_files: list[str] = []
    response_counter = 0
    batch_processed = 0
    completed_from_partial = read_partial_completed_urls(partial_path(config)) if config.resume else set()
    loaded_progress = load_progress(config) if config.resume else None
    errors = load_errors(config)
    state = loaded_progress or ProgressState(
        total_expected=0,
        completed_urls=sorted(completed_from_partial),
        failed_urls=[],
        current_url=None,
        last_success_url=None,
        started_at=now_iso(),
        updated_at=now_iso(),
        production_settings={
            "production": config.production,
            "headless": config.headless,
            "start_date": config.start_date,
            "end_date": config.end_date,
            "max_pages": config.max_pages,
        },
        batch_size=config.batch_size,
        restart_browser_every=config.restart_browser_every,
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.headless, slow_mo=config.slow_mo_ms)
        context: BrowserContext = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        page.set_default_timeout(config.timeout_ms)

        async def on_response(response: Response) -> None:
            nonlocal response_counter
            response_counter += 1
            captured = await capture_response(response, config.output_dir, response_counter)
            if captured:
                network_files.append(captured)

        page.on("response", lambda response: asyncio.create_task(on_response(response)))

        await login(page, config)
        try:
            await page.goto(admin_url(config, "calendar"), wait_until="domcontentloaded", timeout=config.timeout_ms)
            await page.wait_for_load_state("networkidle", timeout=config.timeout_ms)
            await dismiss_popups(page)
        except Exception:
            pass
        post_login_map = await save_diagnostics(page, config, "post_login")
        sidebar_reports = await discover_sidebar_reports(page, config)
        sidebar_reports_path = config.output_dir / "diagnostics" / "sidebar_reports_index.json"
        sidebar_reports_path.parent.mkdir(parents=True, exist_ok=True)
        sidebar_reports_path.write_text(
            json.dumps(sidebar_reports, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if config.reports_url:
            await page.goto(config.reports_url, wait_until="domcontentloaded", timeout=config.timeout_ms)
            await page.wait_for_load_state("networkidle", timeout=config.timeout_ms)
            await dismiss_popups(page)
            if "login" in page.url.lower():
                logging.warning("Reports URL redirected to login; trying to discover Informes from post-login menu.")
                candidate_links = [
                    item["href"]
                    for item in list(post_login_map.get("links", [])) + sidebar_reports
                    if item.get("href")
                    and same_origin(config.base_url, item["href"])
                    and looks_like_informes_url((item.get("text") or "") + " " + item["href"])
                ]
                if candidate_links:
                    await page.goto(candidate_links[0], wait_until="domcontentloaded", timeout=config.timeout_ms)
                    await page.wait_for_load_state("networkidle", timeout=config.timeout_ms)
                    await dismiss_popups(page)
            await apply_date_range(page, config)

        if config.diagnose_only:
            component_map = await save_diagnostics(page, config, "reports")
            all_links_for_candidates = list(post_login_map.get("links", [])) + list(component_map.get("links", []))
            report_links = [
                item["href"]
                for item in all_links_for_candidates
                if item.get("href")
                and same_origin(config.base_url, item["href"])
                and looks_like_informes_url((item.get("text") or "") + " " + item["href"])
            ]
            unique_report_links = list(dict.fromkeys(report_links).keys())
            if config.diagnose_report_limit > 0:
                unique_report_links = unique_report_links[: config.diagnose_report_limit]

            for index, link in enumerate(unique_report_links, start=1):
                try:
                    await page.goto(link, wait_until="domcontentloaded", timeout=config.timeout_ms)
                    await page.wait_for_load_state("networkidle", timeout=20_000)
                    await dismiss_popups(page)
                    await apply_date_range(page, config)
                    await save_diagnostics(page, config, f"reports_link_{index:02d}")
                except Exception as exc:
                    errors.append({"url": link, "error": repr(exc), "created_at": now_iso()})
                    save_errors(config, errors)

            modal_reports = []
            for item in sidebar_reports:
                name = item.get("text")
                if name and name not in modal_reports:
                    modal_reports.append(name)
            if config.diagnose_report_limit > 0:
                modal_reports = modal_reports[: config.diagnose_report_limit]

            for index, name in enumerate(modal_reports, start=1):
                try:
                    await page.goto(admin_url(config, "calendar"), wait_until="domcontentloaded", timeout=config.timeout_ms)
                    await page.wait_for_load_state("networkidle", timeout=20_000)
                    await dismiss_popups(page)
                    await inspect_sidebar_report_modal(page, name, config, index)
                except Exception as exc:
                    errors.append({"report": name, "error": repr(exc), "created_at": now_iso()})
                    save_errors(config, errors)

            diagnostic_summary = {
                "created_at": now_iso(),
                "base_url": config.base_url,
                "reports_url": config.reports_url,
                "start_date": config.start_date,
                "end_date": config.end_date,
                "links_found": len(component_map.get("links", [])),
                "buttons_found": len(component_map.get("buttons", [])),
                "inputs_found": len(component_map.get("inputs", [])),
                "forms_found": len(component_map.get("forms", [])),
                "tables_found": len(component_map.get("tables", [])),
                "candidate_report_links": report_links[:50],
                "sidebar_reports_count": len(sidebar_reports),
                "sidebar_reports": sidebar_reports[:100],
            }
            diagnostics_dir = config.output_dir / "diagnostics"
            diagnostics_dir.mkdir(parents=True, exist_ok=True)
            (diagnostics_dir / "diagnostic_summary.json").write_text(
                json.dumps(diagnostic_summary, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"DIAGNOSTIC_PATH: {diagnostics_dir.resolve()}")
            print(f"LINKS_FOUND: {diagnostic_summary['links_found']}")
            print(f"BUTTONS_FOUND: {diagnostic_summary['buttons_found']}")
            print(f"INPUTS_FOUND: {diagnostic_summary['inputs_found']}")
            print(f"TABLES_FOUND: {diagnostic_summary['tables_found']}")
            await context.close()
            await browser.close()
            return artifacts

        entrypoints = await find_informes_entrypoints(page, config)
        if config.reports_url:
            entrypoints.add(config.reports_url)
        queue.extend(sorted(entrypoints))

        if not queue:
            queue.append(page.url)

        queue = [url for url in queue if url not in completed_from_partial]
        state.total_expected = max(state.total_expected, len(queue) + len(set(state.completed_urls)))
        save_progress(config, state)

        while queue and len(visited) < config.max_pages:
            if config.batch_size is not None and batch_processed >= config.batch_size:
                logging.info("Batch limit reached: %s", config.batch_size)
                break

            url = queue.pop(0)
            if url in visited:
                continue
            if url in completed_from_partial or url in set(state.completed_urls):
                continue
            visited.add(url)
            state.current_url = url
            save_progress(config, state)

            try:
                if (
                    config.restart_browser_every
                    and batch_processed
                    and batch_processed % config.restart_browser_every == 0
                ):
                    logging.info("Restarting browser/session after %s processed pages", batch_processed)
                    await context.close()
                    context = await browser.new_context(accept_downloads=True)
                    page = await context.new_page()
                    page.set_default_timeout(config.timeout_ms)
                    page.on("response", lambda response: asyncio.create_task(on_response(response)))
                    await login(page, config)

                await page.goto(url, wait_until="domcontentloaded", timeout=config.timeout_ms)
                if "auth/login" in page.url.lower():
                    logging.info("Session expired while opening %s; logging in again", url)
                    await login(page, config)
                    await page.goto(url, wait_until="domcontentloaded", timeout=config.timeout_ms)

                await dismiss_popups(page)
                await apply_date_range(page, config)
                downloads = await trigger_exports(page, config.output_dir)
                network_files.extend(downloads)

                artifact = await save_page_artifacts(page, config.output_dir, network_files, len(artifacts) + 1)
                artifacts.append(artifact)
                append_jsonl(partial_path(config), asdict(artifact))
                batch_processed += 1

                if artifact.url not in state.completed_urls:
                    state.completed_urls.append(artifact.url)
                state.last_success_url = artifact.url
                state.current_url = None
                save_progress(config, state)

                discovered = await discover_links(page, config.base_url)
                for found_url in sorted(discovered):
                    known = set(state.completed_urls) | set(state.failed_urls) | set(queue) | visited
                    if found_url not in known and len(visited) + len(queue) < config.max_pages:
                        queue.append(found_url)
                        state.total_expected = max(state.total_expected, len(queue) + len(set(state.completed_urls)))
                        save_progress(config, state)
            except Exception as exc:
                logging.exception("Failed scraping URL %s", url)
                if url not in state.failed_urls:
                    state.failed_urls.append(url)
                state.current_url = None
                errors.append(
                    {
                        "url": url,
                        "error": repr(exc),
                        "created_at": now_iso(),
                    }
                )
                save_errors(config, errors)
                save_progress(config, state)
                continue

        manifest = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "base_url_origin": urlparse(config.base_url).netloc,
            "start_date": config.start_date,
            "end_date": config.end_date,
            "visited_count": len(visited),
            "artifacts_count": len(artifacts),
            "artifacts": [asdict(item) for item in artifacts],
        }
        manifest_path = config.output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        await context.close()
        await browser.close()

    remaining = max(state.total_expected - len(set(state.completed_urls)) - len(set(state.failed_urls)), 0)
    next_url = queue[0] if queue else None
    print(f"TOTAL_EXPECTED: {state.total_expected}")
    print(f"BATCH_SIZE: {config.batch_size}")
    print(f"BATCH_PROCESSED: {batch_processed}")
    print(f"TOTAL_COMPLETED_SO_FAR: {len(set(state.completed_urls))}")
    print(f"TOTAL_REMAINING: {remaining}")
    print(f"TOTAL_FAILED_SO_FAR: {len(set(state.failed_urls))}")
    print(f"LAST_SUCCESS_URL: {state.last_success_url}")
    print(f"NEXT_URL: {next_url}")
    print(f"PARTIAL_PATH: {partial_path(config).resolve()}")
    print(f"PROGRESS_PATH: {progress_path(config).resolve()}")
    print(f"ERRORS_PATH: {errors_path(config).resolve()}")
    print(f"LOG_PATH: {log_path.resolve()}")
    print("CAN_RESUME: True")

    return artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper browser-first para Informes / trámites comerciales."
    )
    parser.add_argument("--base-url", help="URL de login o URL inicial del sistema.")
    parser.add_argument("--reports-url", help="URL directa del módulo de reportes/informes.")
    parser.add_argument("--username", help="Usuario. Si se omite, lee env/url_user.")
    parser.add_argument("--password", help="Contraseña. Si se omite, lee env/url_password.")
    parser.add_argument("--env-txt", default="credentials", help="Archivo credentials/env.txt con formato key:\"value\".")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR))
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--restart-browser-every", type=int, default=50)
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--diagnose-only", action="store_true", help="Mapea Informes/Reportes sin hacer extracción completa.")
    parser.add_argument("--diagnose-report-limit", type=int, default=0, help="Cantidad de informes del sidebar a inspeccionar. 0 = todos.")
    parser.add_argument("--force-logout-paths", action="store_true", help="Además del logout visual, intenta rutas /logout antes del login.")
    parser.add_argument("--skip-initial-logout", action="store_true", help="No intenta cerrar sesión antes del login; útil para contexto Playwright limpio.")
    parser.add_argument("--manual-login", action="store_true", help="Abre navegador visible y espera a que el usuario inicie sesión.")
    parser.add_argument("--manual-login-timeout-sec", type=int, default=180)
    parser.add_argument("--timeout-ms", type=int, default=45_000)
    parser.add_argument("--slow-mo-ms", type=int, default=75)
    parser.add_argument("--headless", action="store_true")
    return parser.parse_args()


async def main() -> None:
    config = build_config(parse_args())
    artifacts = await scrape(config)
    print(f"Extracción terminada. Páginas capturadas: {len(artifacts)}")
    print(f"Salida: {config.output_dir.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
