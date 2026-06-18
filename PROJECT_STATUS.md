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
| **Ventas 970 vs 11567** | Discrepancia en conteos de ventas entre diferentes métodos de extracción. Requiere investigación en Sprint 1. |
| **Target sales ambiguo** | El target `sales_report` puede referirse a diferentes URLs/módulos. Requiere registro explícito. |
| **data/ no debe subirse** | El directorio `data/` contiene datos extraídos. Está en `.gitignore`. |
| **credentials.txt no debe subirse** | Contiene credenciales reales de ASNO. Está en `.gitignore` y no está trackeado. |
| **extract-all peligroso** | `extract-all` sin plan ni checkpoints puede sobrecargar el sistema y generar datos inconsistentes. |
| **Acciones read-only** | Todo el scraper debe mantenerse en modo READ-ONLY. No modificar datos en ASNO. |
| **Extracciones históricas largas** | Ejecutar extracciones de meses/años sin chunking puede fallar por timeout o saturación. |

## Próximo sprint recomendado

**Sprint 1 - Core Stabilization**

Objetivos:
- Auditar arquitectura actual
- Confirmar ventas histórico y resolver discrepancia 970 vs 11567
- Revisar diferencias de conteos entre extractores
- Separar flujos normal / assisted / learning
- Endurecer manejo de errores y reintentos
