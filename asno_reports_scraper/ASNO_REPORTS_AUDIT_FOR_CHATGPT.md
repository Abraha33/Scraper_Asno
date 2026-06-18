# Auditoría módulo de informes ASNO/Wappsi

## 1. Resumen general

- URL auditada: `https://wappsi336.com/holamigo/admin/reports`
- Fecha de auditoría: `2026-06-17T16:01:53`
- Total informes detectados: **17**
- Informes abiertos correctamente: **0**
- Informes con error: **1**
- Informes tipo PDF: **0**
- Informes tipo tabla: **0**
- Informes con paginación: **0**
- Informes con Excel: **0**
- Informes desconocidos: **1**

## 2. Mapa general de informes detectados

| # | Informe | URL | Categoría | Tipo detectado | Tiene fechas | Tiene rango fechas | Exporta PDF | Exporta Excel | Tiene tabla | Tiene paginación | Riesgo | Estrategia recomendada |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Productos | https://wappsi336.com/holamigo/# | inventario | unknown | no | no | no | no | no | no | high | inspect_manually |

## 3. Detalle por informe

### Productos

URL: `https://wappsi336.com/holamigo/#`
Categoría inferida: `inventario`
Tipo detectado: `unknown`
Riesgo: `high`
Estrategia recomendada: `inspect_manually`

Filtros detectados:
- No se detectaron filtros visibles.

Fecha:
- Tiene filtro de fecha: no
- Tiene opción rango de fechas: no
- Selector fecha inicial: `-`
- Selector fecha final: `-`
- Formato de fecha detectado: `unknown`

Botones detectados:
- Consultar: no
- Generar: no
- Guardar: no
- PDF: no
- Excel: no
- Imprimir: no

Resultado:
- Muestra tabla: no
- Tiene paginación: no
- Genera PDF: no
- Descarga Excel: no

Observaciones:
- Error/advertencia: Ítem no auditable: no apunta a /admin/reports/.
- no auditado

## 4. Informes prioritarios para análisis financiero

| Informe objetivo | Encontrado | Nombre detectado | Tipo | Estrategia recomendada | Prioridad |
|---|---|---|---|---|---|
| Informe de Ventas | no | - | - | - | baja |
| Informe de Compras | no | - | - | - | baja |
| Informe Movimiento de Productos | sí | Productos | unknown | inspect_manually | alta |
| Cantidades en Bodega | no | - | - | - | baja |
| Informe Flujo de Caja Detallado | no | - | - | - | baja |
| Rentabilidad por Documento | no | - | - | - | baja |
| Rentabilidad por Cliente | no | - | - | - | baja |
| Rentabilidad por Producto | no | - | - | - | baja |
| Informe de Pagos | no | - | - | - | baja |
| Informe de Cliente | no | - | - | - | baja |
| Informe de proveedor | no | - | - | - | baja |

## 5. Reglas recomendadas de extracción

### Informes PDF/documento

Estos informes deben extraerse una sola vez con rango completo `2022-01-01` hasta `2026-06-17` y luego convertir el PDF a JSON:
- No se detectaron informes puramente PDF.

### Informes tabulares

Estos informes no deben consultarse con rango completo si pueden cargar muchos registros. Recomendación: mensual para riesgo alto/paginación; trimestral para tablas livianas:

### Informes con Excel

Cuando Excel exista, conviene priorizar descarga directa y normalización posterior antes que scraping celda por celda:

### Informes desconocidos

Estos requieren revisión manual o una regla específica adicional antes de automatizar extracción:
- Productos: `Ítem no auditable: no apunta a /admin/reports/.`

## 6. Riesgos técnicos encontrados

- Riesgo de carga: varios reportes tienen muchos filtros y tablas/paginación; no conviene consultar rangos grandes de una sola vez.
- Riesgo de paginación: los informes paginados requieren recorrer páginas o descargar Excel si está disponible.
- Riesgo de rango grande: ventas, compras, inventario, movimientos y cartera pueden pegar la web si se consulta todo el histórico junto.
- Filtros difíciles: algunos reportes tienen más de 30 controles visibles; hay que mapear selectores estables antes de extraer.
- Botones ocultos/dinámicos: algunos botones aparecen como links/íconos o se habilitan luego de elegir filtros.
- Reportes sin exportación clara: los `unknown` no deben automatizarse hasta inspección específica.

## 7. Próximo paso recomendado

Primero conviene implementar el extractor de un informe tabular con fecha y paginación, porque valida el caso más común y riesgoso.

```json
{
  "total_reports": 17,
  "pdf_reports": [],
  "table_reports": [],
  "paginated_reports": [],
  "excel_reports": [],
  "unknown_reports": [
    "Productos"
  ],
  "priority_reports": [
    {
      "name": "Productos",
      "type": "unknown",
      "strategy": "inspect_manually",
      "priority": "alta"
    }
  ],
  "recommended_next_report": ""
}
```
