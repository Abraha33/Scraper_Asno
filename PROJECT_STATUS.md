# PROJECT STATUS - ASNO Mirror

## Estado actual

### Qué existe actualmente

- **Credenciales**: Archivo `credentials.txt` local (ignorado por git) con URL, usuario y contraseña de ASNO/Wappsi.
- **Scraper raíz**: `scraper.py` — script monolítico original con Playwright para navegación, login, extracción de tablas y diagnóstico.
- **Módulo app**: `asno_reports_scraper/app/` — arquitectura modular con 25+ módulos:
  - `main.py` — entry point con CLI por subcomandos
  - `browser.py` — gestión de navegador Playwright
  - `login.py` — autenticación en ASNO/Wappsi
  - `config.py` — configuración y settings
  - `storage.py` — persistencia JSON
  - `report_detector.py`, `reports_index.py` — detección de reportes
  - `report_extractor.py`, `sales_extractor.py` — extractores específicos
  - `generic_runner.py` — ejecutor genérico por targets
  - `pattern_builder.py`, `pattern_engine.py` — construcción de patrones
  - `site_patterns_audit.py`, `reports_audit.py` — auditorías
  - `human_learning.py`, `teach_mode.py`, `assisted.py`, `state_detector.py` — aprendizaje y asistencia
  - `extraction_targets.py`, `extraction_planner.py` — planificación
  - `normalizer.py`, `pagination.py`, `dom_utils.py`, `downloads.py` — utilidades
  - `report_configs.py`, `chatgpt_audit_report.py` — config y reportes
- **Configs**: `configs/reports.yaml`, `configs/patterns.yaml`, `configs/extraction_targets.yaml`, `configs/extraction_targets.generated.yaml`
- **Tests**: `tests/test_chunks.py`, `test_storage.py`, `test_report_configs.py`, `test_sales_extractor.py`, `test_human_learning.py`
- **Documentación**: `docs/audits/`, `docs/plans/`, `docs/decisions/`, `docs/usage/`, `docs/architecture/`
- **Requerimientos**: `requirements.txt` con playwright, pandas, openpyxl, pydantic, python-dotenv, pytest, beautifulsoup4

### Qué comandos funcionan

Desde `asno_reports_scraper/`:

| Comando | Descripción |
|---------|-------------|
| `build-patterns` | Construye patrones aprendidos desde sesiones teach |
| `audit-reports` | Audita reportes del sidebar (read-only) |
| `audit-site-patterns` | Audita patrones del sitio |
| `audit-system` | Auditoría completa del sistema |
| `extract-system --plan-only` | Genera plan de extracción sin ejecutar |
| `list-targets` | Lista targets de extracción registrados |
| `list-recipes` | Lista recetas aprendidas |
| `extract-generic --target sales_report --from YYYY-MM-DD --to YYYY-MM-DD` | Extrae datos genéricos por target |
| `extract-pattern` | Extrae por patrón específico |
| `teach` | Modo enseñanza para nuevos módulos |
| `discover` | Descubre reportes disponibles |
| `inspect` | Inspecciona un reporte específico |
| `extract sales` | Extrae reporte de ventas |
| `extract-all` | Extracción completa (peligrosa, evitar sin plan) |
| `replay-recipe` | Replay de receta aprendida |

### Qué módulos existen

```
asno_reports_scraper/app/
├── __init__.py
├── assisted.py
├── browser.py
├── chatgpt_audit_report.py
├── config.py
├── dom_utils.py
├── downloads.py
├── extraction_planner.py
├── extraction_targets.py
├── generic_runner.py
├── human_learning.py
├── login.py
├── main.py
├── normalizer.py
├── pagination.py
├── pattern_builder.py
├── pattern_engine.py
├── report_configs.py
├── report_detector.py
├── report_extractor.py
├── reports_audit.py
├── reports_index.py
├── sales_extractor.py
├── site_patterns_audit.py
├── state_detector.py
├── storage.py
├── teach_mode.py
└── generic_extractors/
    ├── __init__.py
    ├── common.py
    └── filter_paginated_table.py
```

### Qué extractores existen

| Extractor | Tipo | Estado |
|-----------|------|--------|
| `sales_extractor.py` | Específico (Ventas) | Funcional |
| `report_extractor.py` | Genérico por reporte | Funcional |
| `generic_runner.py` | Genérico por target (vía extraction_targets.yaml) | Funcional |
| `pattern_engine.py` | Por patrón (filter_paginated_table, paginated_table) | Funcional |
| `teach_mode.py` | Enseñanza guiada | Experimental |
| `human_learning.py` | Aprendizaje automático | Experimental |

## Comandos funcionales conocidos

```powershell
# Construir patrones desde sesiones teach
python -m app.main --env-file "..\credentials.txt" build-patterns

# Auditoría del sistema con patrones y asistencia
python -m app.main --env-file "..\credentials.txt" audit-system --patterns --assisted

# Plan de extracción (solo plan, sin ejecutar)
python -m app.main --env-file "..\credentials.txt" extract-system --plan-only

# Listar targets registrados
python -m app.main --env-file "..\credentials.txt" list-targets

# Extracción genérica por target (ventas)
python -m app.main --env-file "..\credentials.txt" extract-generic --target sales_report --from 2026-06-01 --to 2026-06-17 --debug-counts

# Extracción de ventas
python -m app.main --env-file "..\credentials.txt" extract --report sales --from 2026-06-01 --to 2026-06-17

# Modo enseñanza
python -m app.main --env-file "..\credentials.txt" teach --module sales_report

# Descubrir reportes
python -m app.main --env-file "..\credentials.txt" discover
```

## Riesgos conocidos

| Riesgo | Descripción |
|--------|-------------|
| **Paginación no confiable** | La info text de DataTables no se actualiza consistentemente entre páginas, causando sobre/sub conteo (~100 rows extra por mes). Ver `docs/audits/sprint_1_core_stabilization.md`. |
| **Dedup inefectivo** | `_source_page` incluido en el fingerprint — filas duplicadas entre páginas NO se deduplican. |
| **Modo learning ruidoso** | Captura clicks de navegación del sidebar como pasos de receta (ej: "Importar Productos" en lugar del reporte). |
| **Asistencia sin valor en happy path** | Modo assisted (Enter) produce resultados idénticos a normal para ventas. |
| **data/ no debe subirse** | El directorio `data/` contiene datos extraídos. Está en `.gitignore`. |
| **credentials.txt no debe subirse** | Contiene credenciales reales de ASNO. Está en `.gitignore` y no está trackeado. |
| **extract-all peligroso** | `extract-all` sin plan ni checkpoints puede sobrecargar el sistema y generar datos inconsistentes. |
| **Acciones read-only** | Todo el scraper debe mantenerse en modo READ-ONLY. No modificar datos en ASNO. |
| **Extracciones históricas largas** | Ejecutar extracciones de meses/años sin chunking puede fallar por timeout o saturación. |

## Sprint 1 — Core Stabilization (completado: 2026-06-17)

### Hallazgos clave

| # | Issue | Severidad | Archivo | Línea |
|---|-------|-----------|---------|-------|
| 1 | Paginación: timeout silencioso en `wait_for_function` | **Alta** | `sales_extractor.py` | 323 |
| 2 | Paginación: sin reintento cuando info text no cambia | **Alta** | `sales_extractor.py` | 327-328 |
| 3 | Dedup: `_source_page` en fingerprint desactiva dedup cross-page | **Media** | `sales_extractor.py` | 383 |
| 4 | Modo learning: captura navegación sidebar como pasos | **Media** | `human_learning.py` | (observer) |
| 5 | Asistencia en happy path sin valor agregado | **Baja** | `sales_extractor.py` | 579-595 |
| 6 | `debug_pagination` empeora el problema de info text stale | **Baja** | `sales_extractor.py` | 347 |

### Discrepancia 970 vs 11567 resuelta
- Ambos comandos llaman la misma función `extract_sales_report()` con diferentes rangos de fecha
- La discrepancia es esperada por rangos diferentes, NO por bug de code-path
- **Sin embargo**: ningún conteo es confiable debido al bug de paginación (sobre/sub conteo)

### Totales actuales de data/logs/

| Chunk | DataTable "entries" | Filas colectadas | Diferencia |
|-------|---------------------|------------------|------------|
| 2026-01 | 1 604 | 1 704 | +100 |
| 2026-02 | 1 766 | 1 866 | +100 |
| 2026-03 | 1 933 | 2 033 | +100 |
| 2026-04 | 1 808 | 1 908 | +100 |
| 2026-05 | 2 038 | 2 138 | +100 |
| 2026-06 | 870 | 900 | +30 |
| **Suma** | **10 019** | **10 549** | **+530** |

### Documentación generada
- `docs/audits/sprint_1_core_stabilization.md` — Auditoría completa con análisis técnico
- `docs/audits/sprint_2_pagination_dedup_fix.md` — Fix de paginación y deduplicación

## Sprint 2 — Pagination & Dedup Fix (completado: 2026-06-17)

### Cambios realizados

| Archivo | Cambio |
|---------|--------|
| `app/pagination.py` | Nueva función `advance_page_detailed()` con detección de cambio de tbody + retry loop. Utilidad reusable. |
| `app/sales_extractor.py` | `next_page_detail()` ahora delega en `advance_page_detailed()`. `_dedupe_rows()` excluye campos `_` del fingerprint. `collect_all_sales_pages()` detecta páginas repetidas. Debug counts extendido. |
| `app/main.py` | Muestra `DEBUG_DATATABLES_ENTRIES`, `DEBUG_PAGES_REPEATED`, `DEBUG_RETRIES_TOTAL` |
| `tests/test_sales_extractor.py` | 7 nuevos tests de dedup (12 tests total, todos pasan) |

### Problemas resueltos

| # | Issue | Solución |
|---|-------|----------|
| 1 | Paginación: timeout silencioso en `wait_for_function` | Reemplazado por `advance_page_detailed()` con señal primaria de cambio de tbody + retry loop |
| 2 | Paginación: retornaba True aún sin cambio de página | Ahora retorna False cuando la página no avanzó realmente |
| 3 | Dedup: `_source_page` en fingerprint | Fingerprint ahora excluye TODOS los campos con prefijo `_` |
| 4 | Debug-counts incompletos | Agregados: `datatables_entries`, `pages_repeated`, `retries_total`, `pages_detected_from_info` |

### Estado de validación

- `py_compile`: pasa en los 4 archivos modificados
- `pytest`: 12/12 tests pasan
- Validación live: pendiente (requiere ejecución con ASNO real)

### Comandos de validación pendientes

```powershell
python -m app.main --env-file "..\credentials.txt" extract --report sales --from 2026-06-01 --to 2026-06-17 --debug-counts
python -m app.main --env-file "..\credentials.txt" extract-generic --target sales_report --from 2026-06-01 --to 2026-06-17 --debug-counts
```

### Acciones para Sprint 3 (recomendadas)
- Validación live de paginación corregida
- Re-colectar todos los chunks mensuales con paginación corregida para cifras precisas
- Aplicar mismo fix a `common.py:go_next_page()` (mismo patrón info-text-only)
- Modo learning: filtrar steps de navegación irrelevantes
- Remover assisted pause del happy path de ventas
- Test end-to-end con mock DataTable
# Project Status — ASNO Mirror

Repositorio inicializado para trabajo por sprints.

## Principios

- READ-ONLY por defecto.
- Target explícito antes que heurística ambigua.
- Evidencia en logs, HTML y screenshots cuando haya fallos.

## Comandos conocidos

- `build-patterns`
- `audit-system --patterns --assisted`
- `extract-system --plan-only`
- `list-targets`
- `extract-generic --target <target_id>`
