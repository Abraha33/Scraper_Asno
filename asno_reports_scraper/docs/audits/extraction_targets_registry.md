# Auditoría registry de extraction targets

Fecha: 2026-06-17

## Por qué se separó `module` vs `target`

El comando anterior:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-generic --module sales --from 2026-06-01 --to 2026-06-17 --debug-counts
```

resolvía automáticamente una página del módulo `sales`.

Eso produjo una extracción válida técnicamente, pero semánticamente incorrecta para el objetivo:

```text
Lista Órdenes de Pedido
ROWS: 2
```

El problema es que `module=sales` es una familia de páginas, no una página exacta.

Ejemplos:

- `sales_report` → `/admin/reports/sales`
- `sales_orders` → `/admin/sales/orders`

Por eso se creó un registry explícito de targets.

## Archivos creados

```text
configs/extraction_targets.yaml
configs/extraction_targets.generated.yaml
```

Regla:

- `configs/extraction_targets.generated.yaml` se puede regenerar automáticamente.
- `configs/extraction_targets.yaml` es la fuente manual oficial y no debe sobrescribirse si ya existe.

## Comando agregado

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" list-targets
```

Muestra:

- `target_id`
- `name`
- `module`
- `url`
- `pattern`
- `priority`
- `safe_read_only`
- `status`

## Targets clave creados

```yaml
sales_report:
  name: "Informe de Ventas"
  module: "sales"
  url: "/admin/reports/sales"
  pattern: "filter_paginated_table"
  priority: "high"

sales_orders:
  name: "Órdenes de venta"
  module: "sales"
  url: "/admin/sales/orders"
  pattern: "filter_paginated_table"
  priority: "medium"

transfers_list:
  name: "Lista de traslados"
  module: "transfers"
  url: "/admin/transfers"
  pattern: "filter_paginated_table"
  priority: "high"

transfers_orders:
  name: "Órdenes de traslado"
  module: "transfers"
  url: "/admin/transfers/orders"
  pattern: "filter_paginated_table"
  priority: "high"
```

## Targets ambiguos

### `module=sales`

Ahora falla de forma segura:

```text
El module=sales es ambiguo. No voy a elegir un target silenciosamente.
Usá --target con uno de estos targets:
  - sales_report: Informe de Ventas (https://wappsi336.com/holamigo/admin/reports/sales)
  - sales_orders: Lista Órdenes de Pedido (https://wappsi336.com/holamigo/admin/sales/orders)
```

Esto evita volver a confundir informe de ventas con órdenes de venta.

### `module=transfers`

También tiene múltiples targets:

- `transfers_list`
- `transfers_orders`

Se deben ejecutar explícitamente por target.

## Prueba `sales_report`

Comando:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-generic --target sales_report --from 2026-06-01 --to 2026-06-17 --debug-counts
```

Resultado:

```text
GENERIC_MODULE: sales
TARGET_ID: sales_report
STATUS: success
TARGETS: 1
CHUNKS: 1
LIMIT_PAGES: None
ROWS: 900
FAILED_CHUNKS: 0
PAGES_WALKED: 9
ROWS_BEFORE_DEDUPE: 900
ROWS_AFTER_DEDUPE: 900
UNIQUE_IDS: 900
```

Nota técnica:

`sales_report` delega en el extractor histórico de ventas ya probado, porque `/admin/reports/sales` requiere el flujo específico del informe. Esto evita que el extractor genérico haga click ciego en botones como `Guardar`, que están prohibidos por la política READ-ONLY genérica.

Archivos:

```text
data/raw/sales/2026-06/raw.html
data/processed/sales/2026-06/sales.json
data/processed/sales/2026-06/sales.xlsx
data/logs/sales_2026-06.log
```

## Prueba `transfers_list`

Comando:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-generic --target transfers_list --from 2026-06-01 --to 2026-06-17 --debug-counts
```

Resultado:

```text
TARGET_ID: transfers_list
STATUS: success
ROWS: 114
FAILED_CHUNKS: 0
PAGES_WALKED: 2
ROWS_BEFORE_DEDUPE: 114
ROWS_AFTER_DEDUPE: 114
UNIQUE_IDS: 114
```

Archivos:

```text
data/raw/generic/transfers/transfers_list_2026-06/raw.html
data/processed/generic/transfers/transfers_list_2026-06/transfers.json
data/processed/generic/transfers/transfers_list_2026-06/transfers.xlsx
data/logs/generic_transfers_transfers_list_2026-06.log
```

## Prueba `transfers_orders`

Comando:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-generic --target transfers_orders --from 2026-06-01 --to 2026-06-17 --debug-counts
```

Resultado:

```text
TARGET_ID: transfers_orders
STATUS: success
ROWS: 1
FAILED_CHUNKS: 0
PAGES_WALKED: 1
ROWS_BEFORE_DEDUPE: 1
ROWS_AFTER_DEDUPE: 1
UNIQUE_IDS: 1
```

Archivos:

```text
data/raw/generic/transfers/transfers_orders_2026-06/raw.html
data/processed/generic/transfers/transfers_orders_2026-06/transfers.json
data/processed/generic/transfers/transfers_orders_2026-06/transfers.xlsx
data/logs/generic_transfers_transfers_orders_2026-06.log
```

## Cambios en `extract-generic`

Nuevo uso recomendado:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-generic --target sales_report --from 2026-06-01 --to 2026-06-17 --debug-counts
```

Uso por módulo:

- Si el módulo tiene un solo target, puede ejecutarse.
- Si el módulo tiene múltiples targets, falla y lista targets disponibles.
- Ya no elige targets ambiguos silenciosamente.

## Validación de target

Antes de extraer, el extractor registra:

- `target_id`
- URL esperada
- URL actual
- título/H1 detectado
- patrón esperado
- patrón detectado
- conteos

En targets genéricos, el log incluye estos datos.

## Riesgos pendientes

- Algunos reportes usan botones con texto `Guardar` para consultar/generar. El extractor genérico no debe tratarlos como seguros sin una receta/target específico.
- `sales_report` usa extractor especializado por seguridad y por exactitud.
- Falta definir targets explícitos prioritarios para compras, gastos, cartera y pagos.
- Algunos `safe_read_only=False` pueden ser extractables, pero requieren revisión antes de automatizar.
