# Validación generic_filter_paginated_table_extractor

Fecha: 2026-06-17

## Resumen

Se implementó `extract-generic` como extractor real para páginas clasificadas como `filter_paginated_table` / `paginated_table`.

El extractor:

- Lee `configs/patterns.yaml`.
- Lee `data/plans/extraction_plan.json`.
- Resuelve páginas del módulo solicitado.
- Aplica chunks mensuales.
- Aplica filtros de fecha si existen y son detectables.
- Recorre paginación completa por defecto.
- Solo limita páginas si se pasa explícitamente `--limit-pages`.
- Guarda `raw.html`, `json`, `xlsx` y `log`.
- Registra conteos de páginas/filas.
- Respeta modo READ-ONLY.
- Registra acciones peligrosas y no las ejecuta.
- Usa `--assisted` como recuperación si falla.

## Regla crítica validada

`extract-generic` ya no usa `10` páginas por defecto.

- Default: `--limit-pages` queda en `None`.
- La extracción camina hasta que la paginación termina o se detecta atasco real.
- `10` páginas solo ocurre con:

```powershell
--limit-pages 10
```

## Comando 1: sales

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-generic --module sales --from 2026-06-01 --to 2026-06-17 --debug-counts
```

Resultado:

```text
GENERIC_MODULE: sales
STATUS: success
TARGETS: 1
CHUNKS: 1
LIMIT_PAGES: None
ROWS: 2
FAILED_CHUNKS: 0
PAGES_WALKED: 1
ROWS_BEFORE_DEDUPE: 2
ROWS_AFTER_DEDUPE: 2
UNIQUE_IDS: 2
```

Página extraída:

```text
Lista Órdenes de Pedido
```

Conteos:

```text
pages_detected=1
pages_walked=1
termination=next_button_disabled
visible_rows=2
extracted=2
unique=2
```

Archivos:

```text
data/raw/generic/sales/Lista_rdenes_de_Pedido_2026-06/raw.html
data/processed/generic/sales/Lista_rdenes_de_Pedido_2026-06/sales.json
data/processed/generic/sales/Lista_rdenes_de_Pedido_2026-06/sales.xlsx
data/logs/generic_sales_Lista_rdenes_de_Pedido_2026-06.log
```

## Comando 2: transfers

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-generic --module transfers --from 2026-06-01 --to 2026-06-17 --debug-counts
```

Resultado:

```text
GENERIC_MODULE: transfers
STATUS: success
TARGETS: 2
CHUNKS: 1
LIMIT_PAGES: None
ROWS: 115
FAILED_CHUNKS: 0
PAGES_WALKED: 3
ROWS_BEFORE_DEDUPE: 115
ROWS_AFTER_DEDUPE: 115
UNIQUE_IDS: 115
```

Páginas extraídas:

### Lista de traslados

```text
status=success
rows=114
pages_detected=9
pages_walked=2
termination=next_button_disabled
visible_rows=114
extracted=114
unique=114
```

Archivos:

```text
data/raw/generic/transfers/Lista_de_traslados_2026-06/raw.html
data/processed/generic/transfers/Lista_de_traslados_2026-06/transfers.json
data/processed/generic/transfers/Lista_de_traslados_2026-06/transfers.xlsx
data/logs/generic_transfers_Lista_de_traslados_2026-06.log
```

### Ordenes de traslado

```text
status=success
rows=1
pages_detected=None
pages_walked=1
termination=next_button_disabled
visible_rows=1
extracted=1
unique=1
```

Archivos:

```text
data/raw/generic/transfers/Ordenes_de_traslado_2026-06/raw.html
data/processed/generic/transfers/Ordenes_de_traslado_2026-06/transfers.json
data/processed/generic/transfers/Ordenes_de_traslado_2026-06/transfers.xlsx
data/logs/generic_transfers_Ordenes_de_traslado_2026-06.log
```

## Corrección aplicada durante validación

Se detectó que `transfers` tiene dos páginas `filter_paginated_table`.

Antes:

- Ambas páginas podían escribir sobre el mismo chunk `2026-06`.

Después:

- El chunk incluye el slug de la página:

```text
Lista_de_traslados_2026-06
Ordenes_de_traslado_2026-06
```

Esto evita pérdida de datos entre páginas del mismo módulo.

## Estado

Validación aprobada para:

- `sales`
- `transfers`

Próximo paso recomendado:

Probar módulos prioritarios con más volumen, de a uno:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-generic --module customers --from 2026-06-01 --to 2026-06-17 --debug-counts
```

Si una página se atasca:

```powershell
--assisted
```
