# Auditoría regresión sales vs assisted

Fecha: 2026-06-17

## Resumen ejecutivo

Se investigó la supuesta regresión donde `extract --report sales --from 2026-06-01 --to 2026-06-17 --assisted` devolvía 970 filas en lugar del resultado histórico reportado de 11.567 filas / 116 páginas.

Conclusión verificada: **no se encontró una diferencia entre modo normal y modo assisted en el camino feliz**. En la versión actual, ambos modos aplican los mismos filtros, recorren las mismas páginas y producen los mismos conteos para el rango `2026-06-01` a `2026-06-17`.

El número 11.567 no fue reproducible para ese rango de junio parcial. La evidencia apunta a que ese número corresponde a un rango mayor o a filtros distintos. Como referencia, el rango `2026-01-01` a `2026-06-17`, ejecutado por chunks mensuales, produjo 10.619 filas y 110 páginas recorridas.

## Cambios aplicados

Se agregó instrumentación de debug para ventas:

- `--debug-pagination`
- `--debug-filters`
- `--debug-counts`

Archivos modificados:

- `app/config.py`
- `app/sales_extractor.py`
- `app/main.py`

Nueva salida de debug:

- `data/debug/sales_compare/*.json`

Además, el log mensual ahora incluye sección `[debug]` con:

- URL del reporte
- fechas aplicadas
- selector de rango
- opción seleccionada en “Filtrar por”
- page size
- páginas recorridas
- filas por página
- filas antes de deduplicar
- filas después de deduplicar
- IDs únicos
- motivo de finalización de paginación

## Comandos usados

### Comando A: normal

```powershell
python -m app.main --env-file ..\credentials.txt extract --report sales --from 2026-06-01 --to 2026-06-17 --debug-counts --debug-filters --debug-pagination
```

Resultado:

- filas antes de deduplicar: 970
- filas después de deduplicar: 970
- IDs únicos: 970
- páginas recorridas: 10
- motivo de finalización: `next_button_disabled`
- filas por página: `[100,100,100,100,100,100,100,100,100,70]`

Debug JSON:

```text
data/debug/sales_compare/sales_2026-06-01_2026-06-17_normal_2026-06-17T13_49_14.json
```

### Comando B: assisted

```powershell
python -m app.main --env-file ..\credentials.txt extract --report sales --from 2026-06-01 --to 2026-06-17 --assisted --debug-counts --debug-filters --debug-pagination
```

Resultado:

- filas antes de deduplicar: 970
- filas después de deduplicar: 970
- IDs únicos: 970
- páginas recorridas: 10
- motivo de finalización: `next_button_disabled`
- filas por página: `[100,100,100,100,100,100,100,100,100,70]`

Debug JSON:

```text
data/debug/sales_compare/sales_2026-06-01_2026-06-17_assisted_2026-06-17T13_54_21.json
```

## Comparación de filtros

### Normal

Antes del submit:

- URL: `https://wappsi336.com/holamigo/admin/reports/sales`
- fecha inicial: `01/06/2026`
- fecha final: `17/06/2026`
- selector rango: `#date_records_filter_dh`
- valor rango: `5`
- texto rango: `Rango de fechas`
- page size después de cargar tabla: `100`

### Assisted

Antes del submit:

- URL: `https://wappsi336.com/holamigo/admin/reports/sales`
- fecha inicial: `01/06/2026`
- fecha final: `17/06/2026`
- selector rango: `#date_records_filter_dh`
- valor rango: `5`
- texto rango: `Rango de fechas`
- page size después de cargar tabla: `100`

## Diferencia exacta entre normal y assisted

No se detectó diferencia funcional para el rango probado.

| Métrica | Normal | Assisted |
|---|---:|---:|
| Filas antes dedupe | 970 | 970 |
| Filas después dedupe | 970 | 970 |
| IDs únicos | 970 | 970 |
| Páginas recorridas | 10 | 10 |
| Motivo final | next_button_disabled | next_button_disabled |
| Page size | 100 | 100 |
| Rango fechas seleccionado | sí | sí |

## Hallazgos técnicos

### 1. `--assisted` no altera el camino feliz

La integración assisted solo entra en el bloque de excepción. Si el extractor normal logra abrir el reporte, aplicar fechas, consultar y paginar, no se invoca `assisted_pause()`.

Por eso ambos comandos produjeron la misma salida.

### 2. El resultado histórico de 11.567 no corresponde al rango verificado

Para `2026-06-01` a `2026-06-17`, ASNO devolvió 10 páginas y 970 filas.

Se probó además `2026-01-01` a `2026-06-17` con chunks mensuales:

```powershell
python -m app.main --env-file ..\credentials.txt extract --report sales --from 2026-01-01 --to 2026-06-17 --debug-counts --debug-filters --debug-pagination
```

Resultado:

- chunks: 6
- filas totales: 10.619
- páginas totales recorridas: 110

Desglose:

| Chunk | Filas | Páginas |
|---|---:|---:|
| 2026-01 | 1.704 | 18 |
| 2026-02 | 1.866 | 19 |
| 2026-03 | 2.033 | 21 |
| 2026-04 | 1.908 | 20 |
| 2026-05 | 2.138 | 22 |
| 2026-06-01..2026-06-17 | 970 | 10 |

Esto es cercano a 11.567 / 116 páginas, pero no igual. La causa más probable es que el dato histórico fue tomado con rango mayor, fechas distintas o filtros distintos.

### 3. Después del submit, ASNO resetea visualmente campos de fecha

En ambos modos, después de consultar, los inputs visibles `#start_date_dh` y `#end_date_dh` aparecen como:

```text
31/12/1899 00:00
```

Esto ocurre después del submit y ocurre igual en normal y assisted. No explica diferencia entre modos, pero queda como riesgo técnico: la evidencia confiable para filtros es `filters_after_apply`, capturada antes del click de consultar.

### 4. `audit-reports --assisted` sigue funcionando

Se validó:

```powershell
python -m app.main --env-file ..\credentials.txt audit-reports --assisted --limit-reports 1
```

Resultado: disparó pausa asistida sobre ítem padre/no auditable y guardó evidencia.

## Fix aplicado

No se cambió la lógica de extracción feliz de ventas porque no se encontró diferencia entre normal y assisted.

Sí se aplicó un fix de observabilidad/regresión:

1. Se agregaron flags debug.
2. Se agregó captura exacta de filtros antes/después del submit.
3. Se agregó trazabilidad de paginación página por página.
4. Se agregó conteo antes/después de deduplicación.
5. Se agregó escritura de evidencia en `data/debug/sales_compare/`.
6. Se agregó sección debug al log del chunk mensual.

Este fix permite detectar inmediatamente si en una ejecución futura se pierden páginas, cambia el page size, no se selecciona “Rango de fechas” o se aplican fechas incorrectas.

## Estado final

- `sales` normal: OK, 970 filas para `2026-06-01..2026-06-17`.
- `sales --assisted`: OK, 970 filas para el mismo rango.
- Paginación: OK, 10 páginas recorridas, finaliza por botón next deshabilitado.
- Deduplicación: OK, 970 filas antes y después.
- `audit-reports --assisted`: OK, pausa asistida sigue funcionando.

## Recomendación siguiente

Agregar una mejora separada para que `audit-reports --limit-reports` escriba archivos sample separados y no pise `ASNO_REPORTS_AUDIT_FOR_CHATGPT.md`.

También conviene crear un comando dedicado de comparación:

```powershell
python -m app.main compare-sales --from 2026-06-01 --to 2026-06-17
```

Ese comando podría ejecutar normal y assisted en una carpeta aislada y fallar si hay diferencia de filtros, páginas o IDs únicos.

