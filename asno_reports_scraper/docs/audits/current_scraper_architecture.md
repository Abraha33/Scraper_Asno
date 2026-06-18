# Auditoría técnica de arquitectura actual — ASNO Reports Scraper

Fecha: 2026-06-17

## 1. Estructura actual del proyecto

El scraper vive principalmente en `asno_reports_scraper/`.

- `app/`: código Python del scraper.
- `configs/`: configuración de reportes y recetas aprendidas.
- `data/raw/`: HTML/raw outputs.
- `data/processed/`: JSON/XLSX procesados.
- `data/logs/`: logs de ejecución.
- `data/html/` y `data/screenshots/`: evidencia de diagnóstico/error.
- `data/learning/`: evidencia del modo aprendizaje manual.
- `docs/audits/`: informes técnicos.
- `tests/`: pruebas unitarias/smoke.

## 2. Archivos principales

- `app/main.py`: CLI principal. Enruta `discover`, `audit-reports`, `inspect`, `extract`, `extract-all`, recetas y replay.
- `app/config.py`: carga `.env`/`credentials.txt`, rutas de datos y flags como `HEADLESS`.
- `app/browser.py`: crea contexto Playwright.
- `app/login.py`: login robusto con manejo de sesión activa.
- `app/reports_index.py`: descubre enlaces del módulo Informes.
- `app/reports_audit.py`: audita pantallas de informes y clasifica tipo/estrategia.
- `app/dom_utils.py`: detectores de filtros, fechas, botones, exportaciones, tablas y paginación.
- `app/sales_extractor.py`: extractor real específico para `sales`.
- `app/human_learning.py`: modo aprendizaje manual/recetas.
- `configs/reports.yaml`: configuración de reportes, incluido `sales`.

## 3. Cómo funciona el login

El login usa `app/login.py`:

1. Abre `ASNO_URL`.
2. Guarda evidencia antes del intento.
3. Busca usuario/password con selectores flexibles.
4. Llena credenciales desde variables de entorno/config.
5. Busca botón de login por varios selectores.
6. Hace click.
7. Si aparece sesión activa (`a[href*='log_out_session']`), cierra esa sesión y reintenta.
8. Si entra correctamente, guarda `session_state.json` y `login_report.json`.
9. Si falla, guarda `login_error.json`.

No guarda credenciales en código.

## 4. Cómo funciona el extractor de ventas

`app/sales_extractor.py` implementa el primer extractor real:

- Reporte: `sales / Informe de Ventas`.
- URL: `/admin/reports/sales`.
- Lee configuración desde `configs/reports.yaml`.
- Aplica rango de fechas usando:
  - `#start_date_dh`
  - `#end_date_dh`
- Fuerza `Rango de fechas` vía Select2/JS cuando aplica.
- Ejecuta botón real `#submit_filter`.
- Espera tabla de ventas real, excluyendo datepickers/calendarios.
- Recorre paginación DataTables.
- Deduplica filas con `_row_id`.
- Guarda HTML, JSON, XLSX y log.

Importante: hubo una corrida visual corregida con 970 filas para `2026-06-01` a `2026-06-17`. Una corrida previa de 11.567/20.000 filas probablemente correspondía a un rango más amplio o a filtro no aplicado; no debe usarse como evidencia final del rango parcial.

## 5. Cómo maneja fechas

El extractor `sales` usa formato `%d/%m/%Y`.

Para histórico largo, la regla técnica es chunking mensual. El rango global documentado es:

- Inicio: `2001-01-01 00:00:00`
- Fin: `2026-12-31 23:59:59`

No debe consultarse completo en una sola petición.

## 6. Cómo maneja paginación

Hay dos niveles:

- `app/pagination.py`: espera loaders y contiene paginación genérica básica.
- `app/sales_extractor.py`: paginación específica DataTables con `a.paginate_button.next:not(.disabled)`.

El extractor espera cambio de estado de paginación y tabla antes de continuar.

## 7. Cómo guarda raw/html/json/xlsx/logs

Para `sales`:

- Raw HTML:
  - `data/raw/sales/YYYY-MM/raw.html`
- JSON procesado:
  - `data/processed/sales/YYYY-MM/sales.json`
- Excel procesado:
  - `data/processed/sales/YYYY-MM/sales.xlsx`
- Log:
  - `data/logs/sales_YYYY-MM.log`

Errores generales guardan evidencia con `save_evidence()` en:

- `data/html/`
- `data/screenshots/`

## 8. Partes reutilizables para otros informes

Reutilizable:

- Login.
- Browser/context Playwright.
- Descubrimiento de informes.
- Detección DOM (`dom_utils.py`).
- Auditoría base (`reports_audit.py`).
- Storage (`storage.py`).
- Paginación básica.
- Loader de configuración de reportes.
- Modo aprendizaje/manual existente.

## 9. Partes hardcodeadas para sales

Hardcodeado o muy específico:

- `sales_extractor.py`.
- Headers esperados de tabla de ventas.
- Selector de submit `#submit_filter`.
- Selectores de fecha de ventas.
- Reglas de exclusión de datepicker en tabla.
- Ruta de salida `sales/YYYY-MM`.

## 10. Dónde conviene integrar modo asistido

Integración recomendada:

- `app/assisted.py`: pausa asistida, evidencia before/after y decisión del usuario.
- `app/state_detector.py`: detector de estado reutilizable después de intervención manual.
- `app/reports_audit.py`: pausar cuando un reporte queda `unknown`, falla, no detecta tabla/exportación/paginación o hay timeout.
- `app/sales_extractor.py`: pausar en fallos críticos si `--assisted` está activo.
- `app/main.py`: flags `--assisted` y `--limit-reports`.

## 11. Riesgos de modificar el extractor que ya funciona

- Romper `sales` al mezclar lógica asistida dentro del flujo principal.
- Aceptar recetas contaminadas por sidebar/datepickers.
- Confundir tabla de calendario con tabla de reporte.
- Guardar HTML con secretos si no se redacted correctamente.
- Consultar rangos demasiado grandes.
- Cerrar navegador/sesión cuando Abraham necesita intervenir.

## 12. Plan de implementación seguro

1. No tocar el core de extracción de `sales` salvo agregar flags opcionales.
2. Crear `state_detector.py` separado.
3. Crear `assisted.py` separado.
4. Integrar `audit-reports --assisted`.
5. Integrar `extract --assisted` solo como fallback en fallos críticos.
6. Agregar `--limit-reports` para pruebas cortas.
7. Validar sintaxis.
8. Probar `audit-reports --assisted --limit-reports 3`.
9. Confirmar que `extract --report sales ...` sigue funcionando sin `--assisted`.

