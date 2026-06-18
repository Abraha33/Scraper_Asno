from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_key_value_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, raw_value = line.split("=", 1)
        elif ":" in line:
            key, raw_value = line.split(":", 1)
        else:
            continue
        key = key.strip()
        if not ENV_KEY_RE.match(key):
            continue
        values[key] = raw_value.strip().strip('"').strip("'")
    return values


def _first(*names: str, fallback: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return fallback


@dataclass(frozen=True)
class Settings:
    asno_url: str
    reports_url: str | None
    user: str
    password: str
    headless: bool = False
    slow_mo_ms: int = 250
    timeout_ms: int = 60_000
    data_dir: Path = DATA_DIR
    raw_dir: Path = DATA_DIR / "raw"
    audit_dir: Path = DATA_DIR / "audit"
    learning_dir: Path = DATA_DIR / "learning"
    assisted_dir: Path = DATA_DIR / "assisted"
    teach_dir: Path = DATA_DIR / "teach"
    debug_dir: Path = DATA_DIR / "debug"
    processed_dir: Path = DATA_DIR / "processed"
    downloads_dir: Path = DATA_DIR / "downloads"
    screenshots_dir: Path = DATA_DIR / "screenshots"
    html_dir: Path = DATA_DIR / "html"
    logs_dir: Path = DATA_DIR / "logs"

    @classmethod
    def load(cls, env_file: str | Path | None = None, *, require_reports_url: bool = True) -> "Settings":
        load_dotenv()
        if env_file:
            for key, value in _parse_key_value_file(Path(env_file)).items():
                os.environ.setdefault(key, value)
        else:
            for candidate in ("credentials.txt", "credentials", "env.txt"):
                path = Path.cwd().parent / candidate if Path.cwd().name == "asno_reports_scraper" else Path.cwd() / candidate
                if path.exists():
                    for key, value in _parse_key_value_file(path).items():
                        os.environ.setdefault(key, value)
                    break

        asno_url = _first("ASNO_URL", "INFORMES_BASE_URL", "url", "url_base")
        reports_url = _first("ASNO_REPORTS_URL", "INFORMES_REPORTS_URL", "REPORTS_URL", "url_reports")
        user = _first("ASNO_USER", "url_user", "INFORMES_USERNAME")
        password = _first("ASNO_PASSWORD", "url_password", "INFORMES_PASSWORD")

        required = [
            ("ASNO_URL", asno_url),
            ("ASNO_USER", user),
            ("ASNO_PASSWORD", password),
        ]
        if require_reports_url:
            required.append(("ASNO_REPORTS_URL", reports_url))
        missing = [name for name, value in required if not value]
        if missing:
            raise SystemExit(f"Missing configuration: {', '.join(missing)}")

        headless = (_first("HEADLESS", fallback="false") or "false").lower() in {"1", "true", "yes"}
        return cls(
            asno_url=asno_url,
            reports_url=reports_url,
            user=user,
            password=password,
            headless=headless,
        )

    def ensure_dirs(self) -> None:
        for path in (
            self.raw_dir,
            self.audit_dir,
            self.learning_dir,
            self.assisted_dir,
            self.teach_dir,
            self.debug_dir,
            self.processed_dir,
            self.downloads_dir,
            self.screenshots_dir,
            self.html_dir,
            self.logs_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
