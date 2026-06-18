# Plan de extracción ASNO Mirror

## Resumen

- Creado: `2026-06-17T16:46:33`
- Modo: `plan_only=True`
- Auditoría fuente: `G:\My Drive\ScrapperInform\asno_reports_scraper\data\audit\system_map.json`
- Rango histórico por defecto: `2001-01-01` → `2026-12-31`

## Prioridades

### priority_1
- ventas
- compras
- pagos
- gastos
- inventario
- traslados
- cartera
- cuentas por pagar
- caja

### priority_2
- clientes
- proveedores
- productos
- listas de precios
- bodegas
- usuarios
- actividad

### priority_3
- configuración
- reportes
- dashboard
- root

## Módulos

| Prioridad | Módulo | Páginas | Seguras | Riesgo | Patrones |
|---:|---|---:|---:|---:|---|
| 3 | `affiliates` | 2 | 2 | 0 | filter_paginated_table, transaction_form_readonly |
| 3 | `auth` | 1 | 1 | 0 | document_report |
| 3 | `billers` | 2 | 2 | 0 | filter_paginated_table, transaction_form_readonly |
| 3 | `budget` | 1 | 1 | 0 | detail_page |
| 3 | `calendar` | 1 | 1 | 0 | list_table |
| 3 | `customers` | 3 | 3 | 0 | detail_page, filter_paginated_table, list_table |
| 3 | `dashboard` | 4 | 2 | 2 | document_report, list_table |
| 3 | `debit_notes` | 1 | 0 | 1 | filter_table |
| 3 | `financing` | 2 | 0 | 2 | transaction_form_readonly |
| 3 | `marketing` | 2 | 2 | 0 | filter_paginated_table, settings_page |
| 3 | `notifications` | 1 | 1 | 0 | filter_paginated_table |
| 3 | `pos` | 14 | 9 | 5 | detail_page, document_report, filter_paginated_table, filter_table, list_table, settings_page, transaction_form_readonly, unknown |
| 3 | `production_order` | 5 | 1 | 4 | filter_paginated_table, filter_table |
| 3 | `products` | 16 | 2 | 14 | detail_page, filter_paginated_table, filter_table, settings_page, transaction_form_readonly |
| 3 | `purchases` | 7 | 4 | 3 | filter_paginated_table, filter_table |
| 3 | `quotes` | 3 | 2 | 1 | filter_paginated_table, filter_table |
| 3 | `reports` | 51 | 12 | 39 | detail_page, document_report, filter_paginated_table, filter_table, paginated_table, settings_page, transaction_form_readonly |
| 3 | `returns` | 2 | 0 | 2 | filter_table |
| 3 | `root` | 1 | 1 | 0 | list_table |
| 3 | `sales` | 10 | 7 | 3 | detail_page, filter_paginated_table, filter_table, list_table |
| 3 | `sales_reports` | 1 | 1 | 0 | detail_page |
| 3 | `seller` | 2 | 2 | 0 | filter_paginated_table, transaction_form_readonly |
| 3 | `suppliers` | 3 | 3 | 0 | filter_paginated_table, list_table |
| 3 | `system_settings` | 27 | 4 | 23 | document_report, filter_paginated_table, list_table, settings_page, transaction_form_readonly |
| 3 | `transfers` | 5 | 0 | 5 | filter_paginated_table, filter_table, transaction_form_readonly |
| 3 | `users` | 3 | 1 | 2 | filter_paginated_table, settings_page, transaction_form_readonly |
| 3 | `wappsi_invoicing` | 3 | 3 | 0 | filter_paginated_table, filter_table |
| 3 | `warranty` | 2 | 2 | 0 | detail_page |

## Diseño de paquete portable para IA

- Root: `data/export/asno_data_package`
- Manifest: `manifest.json`
- Index: `index.json`

### Módulos del paquete
- `sales`: chunks `modules/sales/chunks/`, raw `modules/sales/raw/`, metadata `modules/sales/metadata.json`
- `purchases`: chunks `modules/purchases/chunks/`, raw `modules/purchases/raw/`, metadata `modules/purchases/metadata.json`
- `transfers`: chunks `modules/transfers/chunks/`, raw `modules/transfers/raw/`, metadata `modules/transfers/metadata.json`
- `inventory`: chunks `modules/inventory/chunks/`, raw `modules/inventory/raw/`, metadata `modules/inventory/metadata.json`
- `customers`: chunks `modules/customers/chunks/`, raw `modules/customers/raw/`, metadata `modules/customers/metadata.json`
- `suppliers`: chunks `modules/suppliers/chunks/`, raw `modules/suppliers/raw/`, metadata `modules/suppliers/metadata.json`
- `payments`: chunks `modules/payments/chunks/`, raw `modules/payments/raw/`, metadata `modules/payments/metadata.json`
- `expenses`: chunks `modules/expenses/chunks/`, raw `modules/expenses/raw/`, metadata `modules/expenses/metadata.json`
- `users`: chunks `modules/users/chunks/`, raw `modules/users/raw/`, metadata `modules/users/metadata.json`

### Relaciones previstas
- `relationships/customers_sales.json`
- `relationships/products_sales.json`
- `relationships/suppliers_purchases.json`
- `relationships/inventory_movements.json`

## Próximo paso

implement generic_filter_paginated_table_extractor against one safe priority-1 module
