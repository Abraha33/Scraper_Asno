# Backlog — ASNO Mirror

## Core

- [ ] Auditar arquitectura actual y dependencias entre módulos
- [ ] Estandarizar manejo de errores en todos los extractores
- [ ] Implementar logging estructurado con niveles consistentes
- [ ] Agregar timeouts configurables por operación
- [ ] Separar configuración por entorno (dev/staging/prod)
- [ ] Agregar pruebas unitarias para módulos core

## Targets

- [ ] Validar que `credentials.txt` y `data/` no estén trackeados (✓ Sprint 0)
- [ ] Mantener `extract-generic --target sales_report` como target explícito
- [ ] Validar targets de transfers
- [ ] Agregar targets para compras, pagos, gastos, inventario y cartera
- [ ] Implementar registro explícito module vs target para evitar ambigüedad
- [ ] Validar URLs de targets contra el registry

## Reports

- [ ] Confirmar ventas histórico completo (discrepancia 970 vs 11567)
- [ ] Extracción de compras (fechas, montos, estados)
- [ ] Extracción de pagos (calendario, montos, métodos)
- [ ] Extracción de gastos (categorías, montos, períodos)
- [ ] Extracción de inventario (productos, stocks, movimientos)
- [ ] Extracción de cartera (clientes, saldos, vencimientos)
- [ ] Validación cruzada de montos entre reportes

## PDF/Excel

- [ ] Implementar extractor de reportes PDF
- [ ] Implementar extractor de reportes Excel multi-hoja
- [ ] Normalizar datos extraídos de PDF/Excel a JSON
- [ ] Manejar tablas anidadas y formatos irregulares
- [ ] Validar integridad de datos post-extracción

## Database

- [ ] Diseñar esquema SQLite para ASNO Mirror
- [ ] Implementar capa de persistencia local
- [ ] Migrar datos extraídos a la DB local
- [ ] Crear consultas y vistas de reporte
- [ ] Implementar backup y restauración de la DB

## Normalization

- [ ] Normalizar fechas a ISO 8601 en todos los módulos
- [ ] Normalizar montos a decimal con 2 dígitos
- [ ] Normalizar cantidades y unidades de medida
- [ ] Implementar IDs estables y deduplicación cruzada
- [ ] Validar consistencia de datos post-normalización

## Dashboard

- [ ] Investigar opciones de dashboard local (Streamlit / Gradio)
- [ ] Implementar visualización de reportes
- [ ] Monitoreo de extracciones en tiempo real
- [ ] Alertas de errores y discrepancias
- [ ] Exportación de reportes a PDF/HTML

## Docs

- [ ] Escribir guía de instalación y configuración
- [ ] Documentar todos los comandos CLI
- [ ] Crear guía de contribución (CONTRIBUTING.md)
- [ ] Documentar flujo de trabajo por sprints
- [ ] Diagrama de arquitectura del sistema
