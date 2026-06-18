# Auditoría de patrones aprendidos ASNO

## Resumen

- Generado: `2026-06-17T16:46:31`
- Sesiones teach: **5**
- Eventos assisted: **10**
- Recetas aprendidas: **1**
- Páginas del sistema mapeadas: **175**
- Páginas con acciones peligrosas: **106**

## 1. Patrones enseñados por Abraham

- `Informe_de_traslados` — Informe de traslados — eventos: 0 — DOM snapshots: 1 — `G:\My Drive\ScrapperInform\asno_reports_scraper\data\teach\Informe_de_traslados\2026-06-17T14_01_46`
- `transfers` — Informe de traslados — eventos: 0 — DOM snapshots: 1 — `G:\My Drive\ScrapperInform\asno_reports_scraper\data\teach\transfers\2026-06-17T14_03_01`
- `transfers` — Informe de traslados — eventos: 0 — DOM snapshots: 1 — `G:\My Drive\ScrapperInform\asno_reports_scraper\data\teach\transfers\2026-06-17T14_23_51`
- `transfers` — Informe de traslados — eventos: 0 — DOM snapshots: 1 — `G:\My Drive\ScrapperInform\asno_reports_scraper\data\teach\transfers\2026-06-17T14_49_01`
- `transfers` — Informe de traslados — eventos: 7 — DOM snapshots: 3 — `G:\My Drive\ScrapperInform\asno_reports_scraper\data\teach\transfers\2026-06-17T14_54_14`

## 2. Páginas/módulos con patrones similares

| Patrón | Páginas | Extractor recomendado | Módulos principales |
|---|---:|---|---|
| `filter_paginated_table` | 70 | `generic_filter_paginated_table_extractor` | reports (22), system_settings (21), production_order (4), products (4), purchases (3) |
| `filter_table` | 27 | `generic_filter_table_extractor` | products (8), purchases (4), reports (3), pos (2), quotes (2) |
| `transaction_form` | 23 | `manual_review_transaction_form` | reports (12), financing (2), products (2), affiliates (1), billers (1) |
| `detail_page` | 22 | `generic_detail_page_reader` | sales (6), pos (5), reports (5), warranty (2), budget (1) |
| `document_report` | 11 | `generic_document_report_detector` | reports (4), dashboard (3), system_settings (2), auth (1), pos (1) |
| `list_table` | 10 | `generic_table_extractor` | pos (2), sales (2), calendar (1), customers (1), dashboard (1) |
| `settings_page` | 7 | `manual_review_settings_reader` | system_settings (2), marketing (1), pos (1), products (1), reports (1) |
| `paginated_table` | 4 | `generic_paginated_table_extractor` | reports (4) |
| `unknown` | 1 | `inspect_manually` | pos (1) |

## 3. Selectores repetidos

- `nav.navbar-default > div.sidebar-collapse:nth-of-type(2) > ul.nav > li.mm_products:nth-of-type(7) > a`: 1
- `ul.nav > li.mm_products:nth-of-type(7) > ul.nav > li.mm_transfers:nth-of-type(17) > a`: 1
- `ul.nav > li.mm_transfers:nth-of-type(17) > ul.nav > li:nth-of-type(1) > a`: 1

## 4. Filtros repetidos

- No se detectó evidencia suficiente.

## 5. Tipos/campos de fecha repetidos

- No se detectó evidencia suficiente.

## 6. Tablas repetidas

- `div.col-lg-12 > div.fc:nth-of-type(1) > div.fc-view-container:nth-of-type(2) > div.fc-view > table`: 5
- `thead.fc-head > tr > td.fc-head-container > div.fc-row > table`: 5
- `div.fc-day-grid-container > div.fc-day-grid > div.fc-row:nth-of-type(1) > div.fc-bg:nth-of-type(1) > table`: 5
- `div.fc-day-grid-container > div.fc-day-grid > div.fc-row:nth-of-type(1) > div.fc-content-skeleton:nth-of-type(2) > table`: 5
- `div.fc-day-grid-container > div.fc-day-grid > div.fc-row:nth-of-type(2) > div.fc-bg:nth-of-type(1) > table`: 5

## 7. Paginaciones repetidas

- No se detectó evidencia suficiente.

## 8. Botones PDF/Excel/Imprimir/Guardar repetidos

- `Guardar`: 2
- `Importar Productos`: 2
- `Imprimir Etiquetas`: 2
- `Productos`: 1
- `Traslados`: 1
- `Lista de traslados`: 1
- `Agregar traslado por archivo CSV`: 1

## 9. Modales/popups repetidos

- No se detectó evidencia suficiente.

## 10. Acciones peligrosas a evitar

- `crear`
- `editar`
- `guardar`
- `actualizar`
- `eliminar`
- `borrar`
- `anular`
- `confirmar`
- `pagar`
- `cerrar caja`
- `facturar`
- `enviar`
- `importar`
- `sincronizar`
- `procesar`
- `aprobar`

## 11. Extractores genéricos que se pueden crear ya

- `filter_paginated_table`
- `filter_table`
- `export_excel`
- `export_pdf`
- `detail_modal`
- `detail_page`
- `crud_list_readonly`
- `transaction_form_readonly`
- `readonly_table`

## Decisión técnica

El primer extractor reutilizable debe ser `generic_filter_paginated_table_extractor`, porque el sistema ya mostró que ese patrón domina los listados y reportes tabulares.
