# Auditoría Firecrawl para ASNO Reports Scraper

Fecha: 2026-06-17  
Proyecto: ASNO/Wappsi Reports Scraper  
Decisión corta: **Playwright sigue como motor principal. Firecrawl queda como auxiliar opcional, no como base.**

## Resumen ejecutivo

Firecrawl es una plataforma/API potente para **buscar, mapear, scrapear, crawlear e interactuar con sitios web a escala**, con salida en Markdown, HTML, screenshots, links y JSON estructurado. Su repositorio lo describe como una API para buscar, scrapear e interactuar con la web a escala, orientada a convertir contenido web en Markdown limpio o datos estructurados para agentes IA.

Para ASNO/Wappsi, el problema no es un crawler general: es un **RPA interno controlado** sobre un sistema autenticado, con formularios, sesión activa, filtros de fecha, loaders, tablas, Excel, modales, paginación y cuidado de carga.

Conclusión:

```text
Base principal: Python + Playwright
Firecrawl: auxiliar opcional para mapeo/HTML/links si aporta algo medible
No integrar Firecrawl todavía
```

La prioridad inmediata ya está cumplida parcialmente por el scraper actual:

```text
python -m app.main discover
```

Resultado actual del proyecto:

```text
REPORTS_DETECTED: 52
reports_index.json generado
Informe de Ventas inspeccionado
```

## Qué hace Firecrawl

Según documentación oficial/repo:

- `Search`: buscar contenido web y devolver páginas.
- `Scrape`: convertir una URL en Markdown, HTML, raw HTML, screenshot, links, JSON estructurado, imágenes, etc.
- `Interact`: interactuar con una página luego de scrapearla.
- `Crawl`: recorrer todas las URLs alcanzables de un sitio.
- `Map`: descubrir URLs.
- `Batch Scrape`: scrapear miles de URLs de forma asíncrona.
- `Agent`: describir una tarea y dejar que un agente navegue/recupere datos.

Firecrawl soporta formatos de salida útiles como `markdown`, `html`, `rawHtml`, `screenshot`, `links` y `json` estructurado. También documenta acciones como escribir, presionar teclas, clickear, esperar y tomar screenshots antes de extraer contenido.

## Qué partes sirven para ASNO

Firecrawl podría servir como **herramienta auxiliar** para:

1. Mapear links simples del módulo Informes.
2. Extraer HTML limpio o raw HTML de páginas ya accesibles.
3. Obtener screenshots de páginas simples.
4. Probar extracción estructurada rápida con JSON schema.
5. Hacer auditorías externas de URLs cuando no se requiere control fino del navegador.
6. Explorar documentación o sitios públicos relacionados.

Dónde podría entrar en nuestra arquitectura:

```text
asno_reports_scraper/
  app/
    firecrawl_audit_adapter.py  # futuro, opcional
```

Pero sólo después de tener métricas claras:

- ¿Detecta más informes que Playwright?
- ¿Reduce tiempo de inspección?
- ¿No rompe sesión?
- ¿No sube costos?
- ¿No expone credenciales ni HTML sensible?

## Qué partes no sirven como núcleo principal

ASNO necesita acciones muy determinísticas:

```text
login
resolver sesión activa
abrir /admin/calendar
abrir Informes
elegir informe
aplicar fechas mensuales
presionar generar/guardar
esperar loader/tabla
descargar Excel si existe
si no, extraer tabla paginada
guardar evidencia local
continuar si falla
no duplicar
no saturar ASNO
```

Firecrawl puede interactuar con páginas, pero el flujo ASNO exige **control exacto de estado, sesión, descargas, modales y recuperación**. Eso lo resolvemos mejor con Playwright puro.

Especialmente delicado:

- Descargas Excel reales.
- Paginación con DataTables.
- Inputs hidden de fecha como `start_date_dh` / `end_date_dh`.
- Select2 ocultos.
- Sesión activa con `a[href*='log_out_session']`.
- Evidencia local saneada.
- Reintentos sin duplicar.
- Rate limiting propio.
- Chunks mensuales/trimestrales.

## Tabla feature Firecrawl vs necesidad ASNO

| Necesidad ASNO | Firecrawl | Playwright puro | Veredicto |
|---|---:|---:|---|
| Login privado | Medio | Alto | Playwright |
| Resolver sesión activa Wappsi | Bajo/Medio | Alto | Playwright |
| Sesión autenticada persistente | Medio | Alto | Playwright |
| Ir directo a URL interna | Alto | Alto | Ambos |
| Detectar links/reportes | Alto | Alto | Ambos |
| Inspeccionar DOM real | Medio/Alto | Alto | Playwright |
| Clicks determinísticos | Medio | Alto | Playwright |
| Formularios complejos | Medio | Alto | Playwright |
| Select2/inputs hidden | Bajo/Medio | Alto | Playwright |
| Loaders/DataTables | Medio | Alto | Playwright |
| Descargar Excel | Dudoso | Alto | Playwright |
| Extraer tabla HTML | Alto | Alto | Ambos |
| Paginación delicada | Medio | Alto | Playwright |
| Modales internos | Medio | Alto | Playwright |
| Extracción por lotes | Alto | Alto | Ambos |
| Rate limit propio para ASNO | Requiere lógica propia | Alto | Playwright |
| Logs locales | Medio | Alto | Playwright |
| Screenshots | Alto | Alto | Ambos |
| HTML diagnóstico local | Alto | Alto | Ambos |
| Integración pandas/openpyxl | Indirecta | Directa | Playwright |
| Costos por página/crédito | Sí | No externo | Playwright |
| Riesgo de dependencia externa | Mayor | Menor | Playwright |

## Riesgos técnicos

### 1. Abstracción incorrecta

Firecrawl abstrae navegación y scraping para casos generales. ASNO no es “web abierta”: es un sistema transaccional interno. Si el motor oculta demasiado el navegador, perdemos control justo donde más lo necesitamos.

### 2. Sesión y credenciales

Usar Firecrawl cloud implicaría evaluar cómo manejar credenciales de ASNO, sesión autenticada y posibles datos sensibles de la empresa. Para un sistema contable/comercial interno, esto es un riesgo mayor.

### 3. Descargas

Nuestro objetivo incluye Excel/PDF originales. Playwright maneja `expect_download()` y guarda archivos localmente de forma directa. Firecrawl está más orientado a contenido transformado/extracción, no a flujos RPA de descarga empresarial.

### 4. Control de carga

ASNO puede colgarse si pedimos cuatro años de una vez. La lógica de chunks mensuales, backoff y reintento debe vivir en nuestro código, no en un crawler genérico.

### 5. Debuggability

Cuando falla un informe, necesitamos:

```text
HTML exacto
screenshot exacto
URL
filtro aplicado
chunk mensual
descarga generada
tabla encontrada
error recuperable
```

Eso ya está alineado con nuestra arquitectura Playwright.

## Riesgos de licencia, costos y dependencia externa

### Licencia

El repositorio Firecrawl usa **GNU AGPL v3**. AGPL es copyleft fuerte y está diseñada para exigir publicación de código fuente modificado cuando el software se opera como servicio de red. Esto no significa que consumir la API cloud automáticamente contamine el proyecto, pero **sí vuelve delicado modificar/self-hostear/integrar código del repo**. Hay que revisar legalmente antes de copiar código o self-hostear.

### Costos

Firecrawl documenta consumo por créditos:

- cada scrape consume crédito;
- JSON/LLM modes, proxy mejorado, PDF parsing y otros formatos pueden sumar créditos;
- crawl tiene `limit` por defecto alto y chequea créditos disponibles.

Para ASNO, donde podemos recorrer 52 informes × meses × filtros, el costo puede crecer rápido si lo usamos de forma masiva.

### Dependencia externa

Riesgos:

- API key.
- Límite de créditos.
- Cambios de pricing.
- Latencia.
- Disponibilidad.
- Riesgo de enviar HTML/metadata sensible a un tercero.

## Comparación contra Playwright puro

Playwright puro nos da:

- control total del navegador;
- storage state local;
- descargas Excel reales;
- manejo directo de modales;
- inspección de inputs ocultos;
- screenshots locales;
- logs locales;
- rate limiting nuestro;
- reintentos específicos por informe/chunk;
- integración directa con pandas/openpyxl;
- menor dependencia externa.

Firecrawl gana en:

- mapeo rápido de sitios públicos;
- convertir páginas a Markdown/JSON;
- búsqueda/crawl a escala;
- extracción LLM-ready;
- agentes para investigación web general.

Pero ASNO no necesita “investigar la web”; necesita operar un sistema interno como un usuario disciplinado.

## Decisión recomendada

```text
Opción A — Firecrawl como base principal: RECHAZADA
Opción B — Firecrawl como módulo auxiliar: POSIBLE FUTURO
Opción C — Playwright puro como base: APROBADA
```

Decisión:

```text
No migrar a Firecrawl.
No instalar Firecrawl todavía.
No copiar código de Firecrawl.
Mantener Python + Playwright como núcleo.
Usar Firecrawl sólo si un spike demuestra valor real después de tener extracción funcional.
```

## Plan de integración si aplica

Sólo consideraría Firecrawl después de estos hitos:

1. `discover` estable con 52 informes.
2. `inspect` estable para informes prioritarios.
3. `extract` mensual funcionando para `Informe de Ventas`.
4. Descarga Excel o tabla paginada resuelta.
5. Resumen final con filas/errores/evidencia.

Si después de eso queremos probar Firecrawl:

```text
Spike 1: pasar 3 URLs públicas/no sensibles de informes ya autenticados no aplica si requiere sesión.
Spike 2: comparar detección de links Firecrawl vs reports_index.json.
Spike 3: comparar HTML limpio Firecrawl vs HTML local Playwright.
Spike 4: medir costo/crédito por informe.
Spike 5: decidir si aporta algo.
```

Regla:

```text
Firecrawl nunca debe recibir credenciales ASNO ni HTML sensible sin aprobación explícita.
```

## Próximos pasos

1. Mantener foco en Playwright:

```powershell
python -m app.main discover
python -m app.main inspect --report "Informe de Ventas"
```

2. Siguiente paso técnico real:

```powershell
python -m app.main extract --report "Informe de Ventas" --from 2022-01-01 --to 2022-01-31 --chunk monthly
```

3. Ajustar extracción de fechas para `Informe de Ventas`:

```text
date_records_filter_dh
start_date_dh
end_date_dh
submit_report
```

4. Confirmar Excel:

```text
exports=1
```

5. Si Excel funciona, priorizar descarga original sobre scraping de tabla.

## Fuentes consultadas

- Firecrawl GitHub README: describe Firecrawl como API para search/scrape/interact web at scale y lista Search, Scrape, Interact, Agent, Crawl, Map y Batch Scrape.
- Firecrawl docs `/scrape`: formatos soportados (`markdown`, `html`, `rawHtml`, `screenshot`, `links`, `json`, etc.), acciones, Interact y costos por crédito/formato.
- Firecrawl docs `/crawl`: crawl recursivo, límites, crédito por página, scrape options, polling/webhooks.
- Firecrawl LICENSE: GNU Affero General Public License v3.

