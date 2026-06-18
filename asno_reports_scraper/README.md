# ASNO Reports Scraper

Scraper/RPA robusto para el módulo **Informes** de ASNO/Wappsi.

## Comandos

Desde `asno_reports_scraper/`:

```powershell
python -m app.main discover
python -m app.main audit-reports
python -m app.main inspect --report "ventas"
python -m app.main extract --report "ventas" --from 2022-01-01 --to 2026-06-16 --chunk monthly
python -m app.main extract-all --from 2022-01-01 --to 2026-06-16 --chunk monthly
```

`audit-reports` es el paso seguro previo a extracción masiva: inicia sesión, entra al
módulo Informes, abre cada subpágina auditable, guarda HTML/screenshot, detecta
filtros/fechas/botones/exportaciones/tablas/paginación y recomienda estrategia por
informe sin consultar rangos históricos largos.

Extractor real inicial validado para ventas:

```powershell
python -m app.main extract --report sales --from 2026-06-01 --to 2026-06-17
python -m app.main extract --report sales --from 2026-06-01 --to 2026-06-17 --learn
python -m app.main extract --report sales --from 2022-01-01 --to 2026-06-17 --chunk monthly
```

Regla importante: `sales` siempre debe ejecutarse por chunks mensuales cuando el
rango sea histórico. No usar un rango completo de varios años en una sola consulta.

Modo aprendizaje manual:

```powershell
python -m app.main list-recipes
python -m app.main replay-recipe --report sales --from 2026-06-01 --to 2026-06-17
python -m app.main replay-recipe --report sales --from 2026-06-01 --to 2026-06-17 --learn
python -m app.main delete-recipe --report sales
```

Con `--learn`, si el scraper no encuentra un selector crítico, deja el navegador
abierto, registra eventos manuales, espera ENTER en consola y guarda una receta en
`configs/learned_recipes/{report}.yaml`.

## Salidas

- `data/raw/reports_index.json`
- `data/audit/reports_audit.json`
- `ASNO_REPORTS_AUDIT_FOR_CHATGPT.md`
- `docs/audits/asno_reports_audit.md`
- `data/raw/*_structure.json`
- `data/raw/*_table.json`
- `data/raw/*_table.csv`
- `data/processed/records_partial.jsonl`
- `data/processed/*_summary.json`
- `data/raw/sales/YYYY-MM/raw.html`
- `data/processed/sales/YYYY-MM/sales.json`
- `data/processed/sales/YYYY-MM/sales.xlsx`
- `data/logs/sales_YYYY-MM.log`
- `data/learning/{report}/events.jsonl`
- `data/learning/{report}/dom_before.html`
- `data/learning/{report}/dom_after.html`
- `configs/learned_recipes/{report}.yaml`
- `data/processed/run_summary.json`
- `data/downloads/`
- `data/screenshots/`
- `data/html/`
- `data/logs/asno_reports.log`

## Diseño

- Login con Playwright y variables de entorno.
- Login Wappsi probado:
  1. abre `ASNO_URL`
  2. guarda evidencia antes
  3. llena usuario/password con selectores flexibles
  4. habilita botón si está disabled
  5. click login
  6. si aparece sesión activa, click en `a[href*='log_out_session']`
  7. vuelve a intentar login una segunda vez
  8. guarda `login_report.json`, `login_error.json` y `session_state.json`
- Descubrimiento automático del sidebar/módulo Informes.
- Inspección de filtros, fechas, botones de exportación, tablas y modales.
- Extracción por chunks mensuales por defecto.
- Si existe Excel/CSV, descarga archivo original.
- Si no existe exportación, extrae tabla HTML.
- Si un informe falla, guarda evidencia y continúa.
- JSONL append-only para no perder progreso.

## Configuración

Crear `.env` o usar `credentials.txt` del workspace padre:

```env
ASNO_URL=https://wappsi336.com/holamigo/login
ASNO_REPORTS_URL=https://wappsi336.com/holamigo/admin/reports
ASNO_USER=...
ASNO_PASSWORD=...
HEADLESS=false
```
