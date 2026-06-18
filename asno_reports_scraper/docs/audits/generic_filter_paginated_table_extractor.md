# Generic filter paginated table extractor

## Objetivo

Extractor genérico READ-ONLY para páginas ASNO/Wappsi clasificadas como:

- `filter_paginated_table`
- `paginated_table`

Sirve para listados con filtros, tabla visible y paginación tipo DataTables/Pagination.

## Comando

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-pattern --pattern filter_paginated_table --module users --max-pages 1
```

También se puede apuntar a una URL explícita:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-pattern --pattern filter_paginated_table --module customers --url "https://wappsi336.com/holamigo/admin/customers" --max-pages 5
```

Con fechas, si la página tiene campos detectables:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-pattern --pattern filter_paginated_table --module reports --url "https://wappsi336.com/holamigo/admin/reports/sales" --from 2026-06-01 --to 2026-06-17 --max-pages 20
```

## Reglas de seguridad

- No ejecuta acciones peligrosas.
- Registra botones peligrosos visibles.
- Solo puede hacer click en:
  - botón seguro de filtro/búsqueda/consulta/generar si no contiene texto peligroso
  - botón de paginación siguiente
- Nunca hace click en:
  - crear
  - editar
  - guardar
  - actualizar
  - eliminar
  - borrar
  - anular
  - confirmar
  - pagar
  - cerrar caja
  - facturar
  - enviar
  - importar
  - sincronizar
  - procesar
  - aprobar

## Salida

Guarda datos en el paquete portable para IA:

```text
data/export/asno_data_package/
  manifest.json
  index.json
  modules/<module>/
    chunks/<chunk>.json
    raw/<chunk>.html
    metadata.json
    index.json
```

También guarda debug en:

```text
data/debug/generic_filter_paginated_table/
data/debug/generic_extract_pattern_summary.json
```

## Prueba verificada

Comando:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-pattern --pattern filter_paginated_table --module users --max-pages 1
```

Resultado:

- Estado: `success`
- Página: `Lista Usuarios`
- Filas: `9`
- Páginas recorridas: `1`
- Finalización: `next_button_disabled`

## Próximo paso

Probar contra una página prioritaria con más volumen pero bajo límite:

```powershell
python -m app.main --env-file "G:\My Drive\ScrapperInform\credentials.txt" extract-pattern --pattern filter_paginated_table --module customers --max-pages 2
```

Si funciona, extender a módulos prioridad 1 del plan.
