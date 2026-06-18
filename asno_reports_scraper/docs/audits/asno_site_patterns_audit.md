# Auditoría de patrones ASNO

## Resumen

- Total páginas detectadas: **175**
- Total patrones encontrados: **9**
- Páginas clasificadas: **174**
- Páginas desconocidas: **1**
- Páginas con acciones peligrosas: **106**

## Patrones encontrados

| Patrón | Cantidad páginas | Ejemplos | Extractor recomendado |
|---|---:|---|---|
| `filter_paginated_table` | 70 | Lista de afiliados, Lista Sucursales, Lista Clientes | `generic_filter_paginated_table_extractor` |
| `filter_table` | 27 | Agregar Nota Débito, Agregar Venta POS, POS Mayorista | `generic_filter_table_extractor` |
| `form_transaction` | 23 | Agregar afiliado, Clave dinámica, Lista de Creditos | `manual_review_transaction_form` |
| `detail_page` | 22 | Presupuestos de Venta, Lista Anticipos, Lista Factura POS Electrónico | `generic_detail_page_reader` |
| `report_document` | 11 | Código QR para registrar cliente, Tablero Financiero, Tablero POS Actions | `generic_document_report_detector` |
| `list_table` | 10 | Calendario, Agregar cliente, Inicio | `generic_table_extractor` |
| `settings_page` | 7 | Ajustes, Parámetros POS, Lista Ajustes de Cantidades | `manual_review_settings_reader` |
| `paginated_table` | 4 | Compras Diarias, Compras Mensuales, Ventas Diarias | `generic_paginated_table_extractor` |
| `unknown` | 1 | Ventas suspendidas | `inspect_manually` |

## Páginas por patrón

### detail_page

- Presupuestos de Venta: `https://wappsi336.com/holamigo/admin/budget`
- Lista Anticipos: `https://wappsi336.com/holamigo/admin/customers/list_deposits/`
- Lista Factura POS Electrónico: `https://wappsi336.com/holamigo/admin/pos/fe_index`
- Lista Facturas POS: `https://wappsi336.com/holamigo/admin/pos/sales`
- Movimientos de Caja: `https://wappsi336.com/holamigo/admin/pos/pos_register_movements`
- Servidor de Impresión: `https://wappsi336.com/holamigo/admin/pos/pos_print_server`
- Ver Cajas Abiertas: `https://wappsi336.com/holamigo/admin/pos/registers`
- Lista de conteos físicos ⚠️: `https://wappsi336.com/holamigo/admin/products/stock_counts`
- Informe de Clientes: `https://wappsi336.com/holamigo/admin/reports/customers`
- Informe de Sucursales de clientes: `https://wappsi336.com/holamigo/admin/reports/customers_addresses`
- Informe de Usuarios: `https://wappsi336.com/holamigo/admin/reports/users`
- Informe de Usuarios: `https://wappsi336.com/holamigo/admin/reports/users`
- Reporte de Proveedor: `https://wappsi336.com/holamigo/admin/reports/suppliers`
- Agregar Venta ⚠️: `https://wappsi336.com/holamigo/admin/sales/add`
- Agregar Venta por CSV ⚠️: `https://wappsi336.com/holamigo/admin/sales/sale_by_csv`
- Bonos: `https://wappsi336.com/holamigo/admin/sales/gift_cards`
- Despachos: `https://wappsi336.com/holamigo/admin/sales/deliveries`
- Lista Facturas: `https://wappsi336.com/holamigo/admin/sales`
- Lista Facturas Electrónicas: `https://wappsi336.com/holamigo/admin/sales/fe_index`
- Ejecución Presupuesto de Ventas: `https://wappsi336.com/holamigo/admin/sales_reports/budget_execution`
- Agregar Garantía: `https://wappsi336.com/holamigo/admin/warranty/add`
- Lista Garantías: `https://wappsi336.com/holamigo/admin/warranty`

### filter_paginated_table

- Lista de afiliados: `https://wappsi336.com/holamigo/admin/affiliates`
- Lista Sucursales: `https://wappsi336.com/holamigo/admin/billers`
- Lista Clientes: `https://wappsi336.com/holamigo/admin/customers`
- Cupones: `https://wappsi336.com/holamigo/admin/marketing/coupons`
- Notificaciones: `https://wappsi336.com/holamigo/admin/notifications`
- Lista Impresoras ⚠️: `https://wappsi336.com/holamigo/admin/pos/printers`
- Lista de órdenes de confección: `https://wappsi336.com/holamigo/admin/production_order`
- Órdenes de corte ⚠️: `https://wappsi336.com/holamigo/admin/production_order/cutting_orders`
- Órdenes de empaque ⚠️: `https://wappsi336.com/holamigo/admin/production_order/packing_orders`
- Órdenes de ensamble ⚠️: `https://wappsi336.com/holamigo/admin/production_order/assemble_orders`
- Conteos Secuenciales ⚠️: `https://wappsi336.com/holamigo/admin/products/sequential_counts`
- Lista Productos ⚠️: `https://wappsi336.com/holamigo/admin/products`
- Lista Transformación de Productos ⚠️: `https://wappsi336.com/holamigo/admin/products/product_transformations`
- Órdenes de Producción ⚠️: `https://wappsi336.com/holamigo/admin/products/production_orders`
- Importaciones: `https://wappsi336.com/holamigo/admin/purchases/imports`
- Lista Compras: `https://wappsi336.com/holamigo/admin/purchases`
- Lista de Órdenes de Compra/Gasto: `https://wappsi336.com/holamigo/admin/purchases/purchase-orders`
- Lista Cotizaciones: `https://wappsi336.com/holamigo/admin/quotes`
- Actividad de usuarios ⚠️: `https://wappsi336.com/holamigo/admin/reports/user_activities`
- Alertas Caducidad del Producto: `https://wappsi336.com/holamigo/admin/reports/expiry_alerts`
- Alertas Cantidad de Producto ⚠️: `https://wappsi336.com/holamigo/admin/reports/quantity_alerts`
- Informe Flujo de Caja Detallado ⚠️: `https://wappsi336.com/holamigo/admin/reports/closed_register_details`
- Informe Movimiento de Productos ⚠️: `https://wappsi336.com/holamigo/admin/reports/products`
- Informe Ventas y Compras por Categoría ⚠️: `https://wappsi336.com/holamigo/admin/reports/categories`
- Informe de Cierres (X) ⚠️: `https://wappsi336.com/holamigo/admin/reports/register`
- Informe de Comisiones por Recaudo ⚠️: `https://wappsi336.com/holamigo/admin/reports/collection_commissions`
- Informe de Compras ⚠️: `https://wappsi336.com/holamigo/admin/reports/purchases`
- Informe de Marcas ⚠️: `https://wappsi336.com/holamigo/admin/reports/brands`
- Informe de Ventas ⚠️: `https://wappsi336.com/holamigo/admin/reports/sales`
- Informe de Ventas mensuales por sucursal y formas de pago ⚠️: `https://wappsi336.com/holamigo/admin/reports/billers_monthly_sales`
- Informe de agendamientos ⚠️: `https://wappsi336.com/holamigo/admin/reports/tasks`
- Informe de cierres (X) por serial ⚠️: `https://wappsi336.com/holamigo/admin/reports/serial_register`
- Informe de cierres (X) por sucursal ⚠️: `https://wappsi336.com/holamigo/admin/reports/biller_register`
- Informe de gastos ⚠️: `https://wappsi336.com/holamigo/admin/reports/expenses`
- Informe de ingresos diarios ⚠️: `https://wappsi336.com/holamigo/admin/reports/daily_incomes`
- Informe de Órdenes de Pedido ⚠️: `https://wappsi336.com/holamigo/admin/reports/order_sales`
- Informe para Solicitud de compras: `https://wappsi336.com/holamigo/admin/reports/purchases_request`
- Rentabilidad por Cliente ⚠️: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_customer`
- Rentabilidad por Documento ⚠️: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_doc`
- Rentabilidad por Producto ⚠️: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_producto`
- Lista Órdenes de Pedido: `https://wappsi336.com/holamigo/admin/sales/orders`
- Listar Vendedores: `https://wappsi336.com/holamigo/admin/seller`
- Lista Anticipos de Proveedores/Acreedores: `https://wappsi336.com/holamigo/admin/suppliers/list_deposits`
- Lista Proveedores: `https://wappsi336.com/holamigo/admin/suppliers`
- Bodegas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/warehouses`
- Categorías ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/categories`
- Categorías de Gastos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/expense_categories`
- Colores ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/colors`
- Conceptos de Notas: `https://wappsi336.com/holamigo/admin/system_settings/configuration_concept_notes`
- Etiquetas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/tags`
- Grupos de Clientes ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/customer_groups`
- Instancias BPM ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/instances`
- Lista Precios ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/price_groups`
- Marcas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/brands`
- Materiales ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/materials`
- Monedas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/currencies`
- Notas de Documentos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/invoice_notes`
- Perfiles de Usuario ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/user_groups`
- Precios por Unidad ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/w_units`
- Retenciones ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/withholding_tax`
- Tasas de Impuestos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/tax_rates`
- Tipos de Documentos: `https://wappsi336.com/holamigo/admin/system_settings/document_types`
- Ubicación ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/ubication`
- Unidades ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/units`
- Variantes de Productos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/variants`
- Lista de traslados ⚠️: `https://wappsi336.com/holamigo/admin/transfers`
- Ordenes de traslado ⚠️: `https://wappsi336.com/holamigo/admin/transfers/orders`
- Lista Usuarios: `https://wappsi336.com/holamigo/admin/users`
- Mis Facturas: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/invoices`
- Mis Facturas: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/invoices`

### filter_table

- Agregar Nota Débito ⚠️: `https://wappsi336.com/holamigo/admin/debit_notes/add`
- Agregar Venta POS ⚠️: `https://wappsi336.com/holamigo/admin/pos`
- POS Mayorista ⚠️: `https://wappsi336.com/holamigo/admin/pos/add_wholesale`
- Agregar orden de confección ⚠️: `https://wappsi336.com/holamigo/admin/production_order/add`
- Agregar Ajuste de Cantidad ⚠️: `https://wappsi336.com/holamigo/admin/products/add_adjustment`
- Agregar Orden de Producción ⚠️: `https://wappsi336.com/holamigo/admin/products/add_production_order`
- Agregar Producto: `https://wappsi336.com/holamigo/admin/products/add`
- Agregar Transformación de Productos ⚠️: `https://wappsi336.com/holamigo/admin/products/add_product_transformation`
- Agregar conteo físico desde archivo ⚠️: `https://wappsi336.com/holamigo/admin/products/count_stock`
- Agregar conteo rápido: `https://wappsi336.com/holamigo/admin/products/add_express_count`
- Conteo Secuencial ⚠️: `https://wappsi336.com/holamigo/admin/products/sequentialCount`
- Imprimir Etiquetas ⚠️: `https://wappsi336.com/holamigo/admin/products/print_barcodes`
- Agregar Compra ⚠️: `https://wappsi336.com/holamigo/admin/purchases/add`
- Agregar Compra por XLS ⚠️: `https://wappsi336.com/holamigo/admin/purchases/purchase_by_csv`
- Agregar Orden de Compra: `https://wappsi336.com/holamigo/admin/purchases/add-purchase-order`
- Agregar importación ⚠️: `https://wappsi336.com/holamigo/admin/purchases/add_import`
- Agregar Cotización: `https://wappsi336.com/holamigo/admin/quotes/add`
- Agregar Orden de Gasto ⚠️: `https://wappsi336.com/holamigo/admin/quotes/addqexpense`
- Informe Inventario Valorizado: `https://wappsi336.com/holamigo/admin/reports/valued_products`
- Informe de traslados ⚠️: `https://wappsi336.com/holamigo/admin/reports/transfers`
- Puntos Premio ⚠️: `https://wappsi336.com/holamigo/admin/reports/award_points`
- Agregar Devolución de compra de Años Anteriores ⚠️: `https://wappsi336.com/holamigo/admin/returns/add_past_years_purchase_return`
- Agregar Devolución de venta de Años Anteriores ⚠️: `https://wappsi336.com/holamigo/admin/returns/add_past_years_sale_return`
- Agregar Orden de Pedido ⚠️: `https://wappsi336.com/holamigo/admin/sales/add_order`
- Agregar traslado ⚠️: `https://wappsi336.com/holamigo/admin/transfers/add`
- Añadir orden de traslado ⚠️: `https://wappsi336.com/holamigo/admin/transfers/add_order`
- Mis Consumos Electrónicos: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/electronic_hits`

### form_transaction

- Agregar afiliado: `https://wappsi336.com/holamigo/admin/affiliates/add`
- Clave dinámica: `https://wappsi336.com/holamigo/admin/billers/random_pin_code`
- Lista de Creditos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings`
- Lista de Cuotas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings`
- Agregar Impresora ⚠️: `https://wappsi336.com/holamigo/admin/pos/add_printer`
- Agregar conteo físico desde archivo con variantes ⚠️: `https://wappsi336.com/holamigo/admin/products/count_stock_variants`
- Importar Productos ⚠️: `https://wappsi336.com/holamigo/admin/products/import_csv`
- Cartera de Clientes por Edades ⚠️: `https://wappsi336.com/holamigo/admin/reports/portfolio_report_2`
- Cartera de Vendedores por Edades ⚠️: `https://wappsi336.com/holamigo/admin/reports/portfolio_report`
- Informe Comprobante Diario (Z): `https://wappsi336.com/holamigo/admin/reports/load_zeta`
- Informe Diario por sucursal: `https://wappsi336.com/holamigo/admin/reports/b_load_zeta`
- Informe de Cartera por Vendedor ⚠️: `https://wappsi336.com/holamigo/admin/reports/portfolio`
- Informe de Impuestos ⚠️: `https://wappsi336.com/holamigo/admin/reports/tax`
- Informe de Lista de Precios ⚠️: `https://wappsi336.com/holamigo/admin/reports/price_groups`
- Informe de Ventas por Vendedor ⚠️: `https://wappsi336.com/holamigo/admin/reports/load_bills`
- Informe de ordenes de confección ⚠️: `https://wappsi336.com/holamigo/admin/reports/production_order_report`
- Informe de ventas por Categorías ⚠️: `https://wappsi336.com/holamigo/admin/reports/categories2`
- Inventario Bodega por Variantes ⚠️: `https://wappsi336.com/holamigo/admin/reports/warehouse_inventory_variants`
- Rentabilidad producto, Costo compra ⚠️: `https://wappsi336.com/holamigo/admin/reports/product_profitability`
- Agregar Vendedor: `https://wappsi336.com/holamigo/admin/seller/add`
- Plantillas de Correo Electrónico ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/email_templates`
- Agregar traslado por archivo CSV ⚠️: `https://wappsi336.com/holamigo/admin/transfers/transfer_by_csv`
- Cambiar contraseña ⚠️: `https://wappsi336.com/holamigo/admin/users/profile/24/`

### list_table

- Calendario: `https://wappsi336.com/holamigo/admin/calendar`
- Agregar cliente: `https://wappsi336.com/holamigo/admin/calendar`
- Inicio: `https://wappsi336.com/holamigo/admin/calendar`
- Agregar Movimiento de Caja: `https://wappsi336.com/holamigo/admin/calendar`
- Ventas de Hoy: `https://wappsi336.com/holamigo/admin/pos/today_sale`
- Órdenes de pedido: `https://wappsi336.com/holamigo/admin/calendar`
- Exportar Notas Contables: `https://wappsi336.com/holamigo/admin/calendar`
- Servidor de impresión: `https://wappsi336.com/holamigo/admin/sales/printServer`
- Agregar Proveedor: `https://wappsi336.com/holamigo/admin/calendar`
- Cargar Imágenes: `https://wappsi336.com/holamigo/admin/calendar`

### paginated_table

- Compras Diarias ⚠️: `https://wappsi336.com/holamigo/admin/reports/daily_purchases`
- Compras Mensuales ⚠️: `https://wappsi336.com/holamigo/admin/reports/monthly_purchases`
- Ventas Diarias: `https://wappsi336.com/holamigo/admin/reports/daily_sales`
- Ventas Mensuales: `https://wappsi336.com/holamigo/admin/reports/monthly_sales`

### report_document

- Código QR para registrar cliente: `https://wappsi336.com/holamigo/admin/auth/qr_rau`
- Tablero Financiero ⚠️: `https://wappsi336.com/holamigo/admin/dashboard/financial`
- Tablero POS Actions: `https://wappsi336.com/holamigo/admin/dashboard/posActions`
- Tablero Ventas ⚠️: `https://wappsi336.com/holamigo/admin/dashboard/sales`
- Verificador de productos: `https://wappsi336.com/holamigo/admin/pos/price_checker`
- Cantidades en Bodega ⚠️: `https://wappsi336.com/holamigo/admin/reports/warehouse_stock`
- Enlaces Directos ⚠️: `https://wappsi336.com/holamigo/admin/reports`
- Indicadores Rápidos ⚠️: `https://wappsi336.com/holamigo/admin/reports/profit_loss`
- Informe Productos más Vendidos ⚠️: `https://wappsi336.com/holamigo/admin/reports/best_sellers`
- Cierre mensual: `https://wappsi336.com/holamigo/admin/system_settings/monthly_closing`
- Copias de Seguridad ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/backups`

### settings_page

- Ajustes: `https://wappsi336.com/holamigo/admin/marketing/settings`
- Parámetros POS ⚠️: `https://wappsi336.com/holamigo/admin/pos/settings`
- Lista Ajustes de Cantidades ⚠️: `https://wappsi336.com/holamigo/admin/products/quantity_adjustments`
- Informe de Ajustes ⚠️: `https://wappsi336.com/holamigo/admin/reports/adjustments`
- Parámetros Generales ⚠️: `https://wappsi336.com/holamigo/admin/system_settings`
- Preferencias del Producto ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/product_preferences`
- Perfil ⚠️: `https://wappsi336.com/holamigo/admin/users/profile/24`

### unknown

- Ventas suspendidas: `https://wappsi336.com/holamigo/admin/pos/opened_bills`

## Excepciones

### Páginas unknown
- Ventas suspendidas: `https://wappsi336.com/holamigo/admin/pos/opened_bills`

### Páginas con acciones peligrosas
- Tablero Financiero: `https://wappsi336.com/holamigo/admin/dashboard/financial` — Actualizar datos
- Tablero Ventas: `https://wappsi336.com/holamigo/admin/dashboard/sales` — Actualizar datos
- Agregar Nota Débito: `https://wappsi336.com/holamigo/admin/debit_notes/add` — Guardar
- Lista de Creditos: `https://wappsi336.com/holamigo/admin/system_settings` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación, Actualizar parámetros
- Lista de Cuotas: `https://wappsi336.com/holamigo/admin/system_settings` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación, Actualizar parámetros
- Agregar Impresora: `https://wappsi336.com/holamigo/admin/pos/add_printer` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Agregar Venta POS: `https://wappsi336.com/holamigo/admin/pos` — Pagar $ 0.00
- Lista Impresoras: `https://wappsi336.com/holamigo/admin/pos/printers` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- POS Mayorista: `https://wappsi336.com/holamigo/admin/pos/add_wholesale` — Pagar
- Parámetros POS: `https://wappsi336.com/holamigo/admin/pos/settings` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación, Guardar parámetros
- Agregar orden de confección: `https://wappsi336.com/holamigo/admin/production_order/add` — Actualizar Precios (Costo + Márgen), Guardar, Guardar e iniciar corte
- Órdenes de corte: `https://wappsi336.com/holamigo/admin/production_order/cutting_orders` — Actualizar Precios (Costo + Márgen)
- Órdenes de empaque: `https://wappsi336.com/holamigo/admin/production_order/packing_orders` — Actualizar Precios (Costo + Márgen)
- Órdenes de ensamble: `https://wappsi336.com/holamigo/admin/production_order/assemble_orders` — Actualizar Precios (Costo + Márgen)
- Agregar Ajuste de Cantidad: `https://wappsi336.com/holamigo/admin/products/add_adjustment` — Actualizar Precios (Costo + Márgen), Guardar
- Agregar Orden de Producción: `https://wappsi336.com/holamigo/admin/products/add_production_order` — Actualizar Precios (Costo + Márgen), Guardar, Guardar sin aprobar
- Agregar Transformación de Productos: `https://wappsi336.com/holamigo/admin/products/add_product_transformation` — Actualizar Precios (Costo + Márgen), Guardar
- Agregar conteo físico desde archivo: `https://wappsi336.com/holamigo/admin/products/count_stock` — Actualizar Precios (Costo + Márgen), Guardar
- Agregar conteo físico desde archivo con variantes: `https://wappsi336.com/holamigo/admin/products/count_stock_variants` — Actualizar Precios (Costo + Márgen), Guardar
- Conteo Secuencial: `https://wappsi336.com/holamigo/admin/products/sequentialCount` — Actualizar Precios (Costo + Márgen), Guardar
- Conteos Secuenciales: `https://wappsi336.com/holamigo/admin/products/sequential_counts` — Actualizar Precios (Costo + Márgen)
- Importar Productos: `https://wappsi336.com/holamigo/admin/products/import_csv` — Actualizar Precios (Costo + Márgen)
- Imprimir Etiquetas: `https://wappsi336.com/holamigo/admin/products/print_barcodes` — Actualizar Precios (Costo + Márgen), Actualizar
- Lista Ajustes de Cantidades: `https://wappsi336.com/holamigo/admin/products/quantity_adjustments` — Actualizar Precios (Costo + Márgen)
- Lista Productos: `https://wappsi336.com/holamigo/admin/products` — Actualizar Precios (Costo + Márgen)
- Lista Transformación de Productos: `https://wappsi336.com/holamigo/admin/products/product_transformations` — Actualizar Precios (Costo + Márgen)
- Lista de conteos físicos: `https://wappsi336.com/holamigo/admin/products/stock_counts` — Actualizar Precios (Costo + Márgen)
- Órdenes de Producción: `https://wappsi336.com/holamigo/admin/products/production_orders` — Actualizar Precios (Costo + Márgen)
- Agregar Compra: `https://wappsi336.com/holamigo/admin/purchases/add` — Guardar
- Agregar Compra por XLS: `https://wappsi336.com/holamigo/admin/purchases/purchase_by_csv` — Guardar
- Agregar importación: `https://wappsi336.com/holamigo/admin/purchases/add_import` — Guardar
- Agregar Orden de Gasto: `https://wappsi336.com/holamigo/admin/quotes/addqexpense` — Guardar
- Actividad de usuarios: `https://wappsi336.com/holamigo/admin/reports/user_activities` — Cuentas por Pagar por Edades
- Alertas Cantidad de Producto: `https://wappsi336.com/holamigo/admin/reports/quantity_alerts` — Cuentas por Pagar por Edades
- Cantidades en Bodega: `https://wappsi336.com/holamigo/admin/reports/warehouse_stock` — Cuentas por Pagar por Edades
- Cartera de Clientes por Edades: `https://wappsi336.com/holamigo/admin/reports/portfolio_report_2` — Enviar
- Cartera de Vendedores por Edades: `https://wappsi336.com/holamigo/admin/reports/portfolio_report` — Cuentas por Pagar por Edades, Guardar
- Compras Diarias: `https://wappsi336.com/holamigo/admin/reports/daily_purchases` — Cuentas por Pagar por Edades
- Compras Mensuales: `https://wappsi336.com/holamigo/admin/reports/monthly_purchases` — Cuentas por Pagar por Edades
- Enlaces Directos: `https://wappsi336.com/holamigo/admin/reports` — Cuentas por Pagar por Edades
- Indicadores Rápidos: `https://wappsi336.com/holamigo/admin/reports/profit_loss` — Cuentas por Pagar por Edades
- Informe Flujo de Caja Detallado: `https://wappsi336.com/holamigo/admin/reports/closed_register_details` — Guardar
- Informe Movimiento de Productos: `https://wappsi336.com/holamigo/admin/reports/products` — Cuentas por Pagar por Edades
- Informe Productos más Vendidos: `https://wappsi336.com/holamigo/admin/reports/best_sellers` — Cuentas por Pagar por Edades
- Informe Ventas y Compras por Categoría: `https://wappsi336.com/holamigo/admin/reports/categories` — Cuentas por Pagar por Edades, Guardar
- Informe de Ajustes: `https://wappsi336.com/holamigo/admin/reports/adjustments` — Cuentas por Pagar por Edades, Guardar
- Informe de Cartera por Vendedor: `https://wappsi336.com/holamigo/admin/reports/portfolio` — Guardar
- Informe de Cierres (X): `https://wappsi336.com/holamigo/admin/reports/register` — Cuentas por Pagar por Edades, Guardar
- Informe de Comisiones por Recaudo: `https://wappsi336.com/holamigo/admin/reports/collection_commissions` — Guardar
- Informe de Compras: `https://wappsi336.com/holamigo/admin/reports/purchases` — Cuentas por Pagar por Edades, Guardar
- Informe de Impuestos: `https://wappsi336.com/holamigo/admin/reports/tax` — Cuentas por Pagar por Edades, Guardar
- Informe de Lista de Precios: `https://wappsi336.com/holamigo/admin/reports/price_groups` — Cuentas por Pagar por Edades, Guardar
- Informe de Marcas: `https://wappsi336.com/holamigo/admin/reports/brands` — Cuentas por Pagar por Edades, Guardar
- Informe de Ventas: `https://wappsi336.com/holamigo/admin/reports/sales` — Cuentas por Pagar por Edades
- Informe de Ventas mensuales por sucursal y formas de pago: `https://wappsi336.com/holamigo/admin/reports/billers_monthly_sales` — Cuentas por Pagar por Edades
- Informe de Ventas por Vendedor: `https://wappsi336.com/holamigo/admin/reports/load_bills` — Cuentas por Pagar por Edades, Guardar
- Informe de agendamientos: `https://wappsi336.com/holamigo/admin/reports/tasks` — Cuentas por Pagar por Edades
- Informe de cierres (X) por serial: `https://wappsi336.com/holamigo/admin/reports/serial_register` — Guardar
- Informe de cierres (X) por sucursal: `https://wappsi336.com/holamigo/admin/reports/biller_register` — Cuentas por Pagar por Edades, Guardar
- Informe de gastos: `https://wappsi336.com/holamigo/admin/reports/expenses` — Cuentas por Pagar por Edades, Guardar
- Informe de ingresos diarios: `https://wappsi336.com/holamigo/admin/reports/daily_incomes` — Cuentas por Pagar por Edades
- Informe de ordenes de confección: `https://wappsi336.com/holamigo/admin/reports/production_order_report` — Cuentas por Pagar por Edades, Enviar
- Informe de traslados: `https://wappsi336.com/holamigo/admin/reports/transfers` — Cuentas por Pagar por Edades, Guardar
- Informe de ventas por Categorías: `https://wappsi336.com/holamigo/admin/reports/categories2` — Guardar
- Informe de Órdenes de Pedido: `https://wappsi336.com/holamigo/admin/reports/order_sales` — Cuentas por Pagar por Edades
- Inventario Bodega por Variantes: `https://wappsi336.com/holamigo/admin/reports/warehouse_inventory_variants` — Cuentas por Pagar por Edades
- Puntos Premio: `https://wappsi336.com/holamigo/admin/reports/award_points` — Cuentas por Pagar por Edades, Guardar
- Rentabilidad por Cliente: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_customer` — Cuentas por Pagar por Edades, Guardar
- Rentabilidad por Documento: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_doc` — Guardar
- Rentabilidad por Producto: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_producto` — Cuentas por Pagar por Edades, Guardar
- Rentabilidad producto, Costo compra: `https://wappsi336.com/holamigo/admin/reports/product_profitability` — Guardar
- Agregar Devolución de compra de Años Anteriores: `https://wappsi336.com/holamigo/admin/returns/add_past_years_purchase_return` — Guardar
- Agregar Devolución de venta de Años Anteriores: `https://wappsi336.com/holamigo/admin/returns/add_past_years_sale_return` — Guardar
- Agregar Orden de Pedido: `https://wappsi336.com/holamigo/admin/sales/add_order` — Guardar
- Agregar Venta: `https://wappsi336.com/holamigo/admin/sales/add` — Guardar
- Agregar Venta por CSV: `https://wappsi336.com/holamigo/admin/sales/sale_by_csv` — Guardar
- Bodegas: `https://wappsi336.com/holamigo/admin/system_settings/warehouses` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Categorías: `https://wappsi336.com/holamigo/admin/system_settings/categories` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Categorías de Gastos: `https://wappsi336.com/holamigo/admin/system_settings/expense_categories` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Colores: `https://wappsi336.com/holamigo/admin/system_settings/colors` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Copias de Seguridad: `https://wappsi336.com/holamigo/admin/system_settings/backups` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación, Borrar
- Etiquetas: `https://wappsi336.com/holamigo/admin/system_settings/tags` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Grupos de Clientes: `https://wappsi336.com/holamigo/admin/system_settings/customer_groups` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Instancias BPM: `https://wappsi336.com/holamigo/admin/system_settings/instances` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Lista Precios: `https://wappsi336.com/holamigo/admin/system_settings/price_groups` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Marcas: `https://wappsi336.com/holamigo/admin/system_settings/brands` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Materiales: `https://wappsi336.com/holamigo/admin/system_settings/materials` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Monedas: `https://wappsi336.com/holamigo/admin/system_settings/currencies` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Notas de Documentos: `https://wappsi336.com/holamigo/admin/system_settings/invoice_notes` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Parámetros Generales: `https://wappsi336.com/holamigo/admin/system_settings` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación, Actualizar parámetros
- Perfiles de Usuario: `https://wappsi336.com/holamigo/admin/system_settings/user_groups` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Plantillas de Correo Electrónico: `https://wappsi336.com/holamigo/admin/system_settings/email_templates` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación, Guardar
- Precios por Unidad: `https://wappsi336.com/holamigo/admin/system_settings/w_units` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Preferencias del Producto: `https://wappsi336.com/holamigo/admin/system_settings/product_preferences` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Retenciones: `https://wappsi336.com/holamigo/admin/system_settings/withholding_tax` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Tasas de Impuestos: `https://wappsi336.com/holamigo/admin/system_settings/tax_rates` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Ubicación: `https://wappsi336.com/holamigo/admin/system_settings/ubication` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Unidades: `https://wappsi336.com/holamigo/admin/system_settings/units` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Variantes de Productos: `https://wappsi336.com/holamigo/admin/system_settings/variants` — Actualizar Precios por Margen, Actualizar Costos de Envío por Ubicación
- Agregar traslado: `https://wappsi336.com/holamigo/admin/transfers/add` — Actualizar Precios (Costo + Márgen), Guardar
- Agregar traslado por archivo CSV: `https://wappsi336.com/holamigo/admin/transfers/transfer_by_csv` — Actualizar Precios (Costo + Márgen), Guardar
- Añadir orden de traslado: `https://wappsi336.com/holamigo/admin/transfers/add_order` — Guardar
- Lista de traslados: `https://wappsi336.com/holamigo/admin/transfers` — Actualizar Precios (Costo + Márgen)
- Ordenes de traslado: `https://wappsi336.com/holamigo/admin/transfers/orders` — Actualizar Precios (Costo + Márgen)
- Cambiar contraseña: `https://wappsi336.com/holamigo/admin/users/profile/24/` — Editar, Actualizar
- Perfil: `https://wappsi336.com/holamigo/admin/users/profile/24` — Editar, Actualizar

## Próximo paso recomendado

Construir primero `generic_filter_paginated_table_extractor` para el patrón `filter_paginated_table`, porque cubre 70 página(s) y permite reutilización segura read-only.
