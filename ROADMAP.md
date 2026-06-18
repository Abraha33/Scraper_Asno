# Roadmap — ASNO Mirror

## Sprint 0 - Repo Setup & Safety
- Seguridad de repo (.gitignore, credentials)
- Documentación base (README, PROJECT_STATUS, ROADMAP, BACKLOG)
- Validación de compilación (py_compile)
- Verificar que credentials.txt y data/ no estén trackeados

## Sprint 1 - Core Stabilization
- Auditar arquitectura actual de módulos
- Confirmar ventas histórico y resolver discrepancia 970 vs 11567
- Revisar diferencias de conteos entre extractores
- Separar flujos normal / assisted / learning
- Endurecer manejo de errores y reintentos

## Sprint 2 - Extraction Targets Registry
- Mantener registry explícito `module` vs `target`
- Validar targets críticos (ventas, compras, pagos, gastos)
- Evitar selección ambigua de targets
- Agregar validación de URLs contra registry

## Sprint 3 - Generic Table Extractor
- Endurecer extractor genérico de tablas filtradas/paginadas
- Implementar checkpoints y resume por chunk
- Optimizar page size para extracciones grandes
- Deduplicación robusta

## Sprint 4 - Reports Extraction
- Extracción de ventas, compras, pagos, gastos, inventario, cartera
- Validación cruzada de montos y registros
- Reportes de calidad de datos

## Sprint 5 - PDF & Excel Extractors
- Extractores para reportes en PDF y Excel
- Normalización de formatos a JSON estructurado
- Manejo de tablas anidadas y multi-hoja

## Sprint 6 - ASNO Full Site Audit
- Auditoría incremental completa read-only del sitio
- Mapeo de todas las páginas, módulos y formularios
- Detección de páginas peligrosas (write/delete)

## Sprint 7 - ASNO Mirror Database
- SQLite / base de datos local para espejo de datos
- Esquema de tablas normalizado
- Ingesta de datos extraídos
- Consultas y reportes desde la DB local

## Sprint 8 - Data Normalization
- Normalización de fechas a ISO 8601
- Normalización de montos a decimal consistente
- Normalización de cantidades y unidades
- IDs estables y deduplicación cruzada

## Sprint 9 - Financial Analysis Layer
- Métricas financieras automáticas
- Resúmenes para análisis por IA
- Detección de anomalías y patrones

## Sprint 10 - Dashboard & Monitoring
- Dashboard local con reportes visuales
- Monitoreo de extracciones en curso
- Alertas de errores y discrepacias

## Sprint 11 - Hardening & Documentation
- Tests automatizados (unitarios + integración)
- Manuales de uso y operación
- Recuperación de errores y resiliencia
- MVP estable y empaquetado
