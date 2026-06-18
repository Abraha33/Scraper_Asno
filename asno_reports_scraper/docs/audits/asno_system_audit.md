# Auditoría completa ASNO

## Resumen

- URLs detectadas: **175**
- Páginas auditadas: **175**
- Módulos encontrados: **28**
- Patrones encontrados: **9**
- Páginas seguras: **69**
- Páginas peligrosas: **106**
- Páginas desconocidas: **1**

## Módulos detectados

- `affiliates`: 2 página(s)
- `auth`: 1 página(s)
- `billers`: 2 página(s)
- `budget`: 1 página(s)
- `calendar`: 1 página(s)
- `customers`: 3 página(s)
- `dashboard`: 4 página(s)
- `debit_notes`: 1 página(s)
- `financing`: 2 página(s)
- `marketing`: 2 página(s)
- `notifications`: 1 página(s)
- `pos`: 14 página(s)
- `production_order`: 5 página(s)
- `products`: 16 página(s)
- `purchases`: 7 página(s)
- `quotes`: 3 página(s)
- `reports`: 51 página(s)
- `returns`: 2 página(s)
- `root`: 1 página(s)
- `sales`: 10 página(s)
- `sales_reports`: 1 página(s)
- `seller`: 2 página(s)
- `suppliers`: 3 página(s)
- `system_settings`: 27 página(s)
- `transfers`: 5 página(s)
- `users`: 3 página(s)
- `wappsi_invoicing`: 3 página(s)
- `warranty`: 2 página(s)

## Patrones detectados

| Patrón | Páginas | Extractor recomendado |
|---|---:|---|
| `filter_paginated_table` | 70 | `generic_filter_paginated_table_extractor` |
| `filter_table` | 27 | `generic_filter_table_extractor` |
| `transaction_form` | 23 | `manual_review_transaction_form` |
| `detail_page` | 22 | `generic_detail_page_reader` |
| `document_report` | 11 | `generic_document_report_detector` |
| `list_table` | 10 | `generic_table_extractor` |
| `settings_page` | 7 | `manual_review_settings_reader` |
| `paginated_table` | 4 | `generic_paginated_table_extractor` |
| `unknown` | 1 | `inspect_manually` |

## Páginas por módulo

### affiliates

- `transaction_form` — Agregar afiliado: `https://wappsi336.com/holamigo/admin/affiliates/add`
- `filter_paginated_table` — Lista de afiliados: `https://wappsi336.com/holamigo/admin/affiliates`

### auth

- `document_report` — Código QR para registrar cliente: `https://wappsi336.com/holamigo/admin/auth/qr_rau`

### billers

- `transaction_form` — Clave dinámica: `https://wappsi336.com/holamigo/admin/billers/random_pin_code`
- `filter_paginated_table` — Lista Sucursales: `https://wappsi336.com/holamigo/admin/billers`

### budget

- `detail_page` — Presupuestos de Venta: `https://wappsi336.com/holamigo/admin/budget`

### calendar

- `list_table` — Calendario: `https://wappsi336.com/holamigo/admin/calendar`

### customers

- `list_table` — Agregar cliente: `https://wappsi336.com/holamigo/admin/calendar`
- `detail_page` — Lista Anticipos: `https://wappsi336.com/holamigo/admin/customers/list_deposits/`
- `filter_paginated_table` — Lista Clientes: `https://wappsi336.com/holamigo/admin/customers`

### dashboard

- `list_table` — Inicio: `https://wappsi336.com/holamigo/admin/calendar`
- `document_report` — Tablero Financiero ⚠️: `https://wappsi336.com/holamigo/admin/dashboard/financial`
- `document_report` — Tablero POS Actions: `https://wappsi336.com/holamigo/admin/dashboard/posActions`
- `document_report` — Tablero Ventas ⚠️: `https://wappsi336.com/holamigo/admin/dashboard/sales`

### debit_notes

- `filter_table` — Agregar Nota Débito ⚠️: `https://wappsi336.com/holamigo/admin/debit_notes/add`

### financing

- `transaction_form` — Lista de Creditos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings`
- `transaction_form` — Lista de Cuotas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings`

### marketing

- `settings_page` — Ajustes: `https://wappsi336.com/holamigo/admin/marketing/settings`
- `filter_paginated_table` — Cupones: `https://wappsi336.com/holamigo/admin/marketing/coupons`

### notifications

- `filter_paginated_table` — Notificaciones: `https://wappsi336.com/holamigo/admin/notifications`

### pos

- `transaction_form` — Agregar Impresora ⚠️: `https://wappsi336.com/holamigo/admin/pos/add_printer`
- `list_table` — Agregar Movimiento de Caja: `https://wappsi336.com/holamigo/admin/calendar`
- `filter_table` — Agregar Venta POS ⚠️: `https://wappsi336.com/holamigo/admin/pos`
- `detail_page` — Lista Factura POS Electrónico: `https://wappsi336.com/holamigo/admin/pos/fe_index`
- `detail_page` — Lista Facturas POS: `https://wappsi336.com/holamigo/admin/pos/sales`
- `filter_paginated_table` — Lista Impresoras ⚠️: `https://wappsi336.com/holamigo/admin/pos/printers`
- `detail_page` — Movimientos de Caja: `https://wappsi336.com/holamigo/admin/pos/pos_register_movements`
- `filter_table` — POS Mayorista ⚠️: `https://wappsi336.com/holamigo/admin/pos/add_wholesale`
- `settings_page` — Parámetros POS ⚠️: `https://wappsi336.com/holamigo/admin/pos/settings`
- `detail_page` — Servidor de Impresión: `https://wappsi336.com/holamigo/admin/pos/pos_print_server`
- `list_table` — Ventas de Hoy: `https://wappsi336.com/holamigo/admin/pos/today_sale`
- `unknown` — Ventas suspendidas: `https://wappsi336.com/holamigo/admin/pos/opened_bills`
- `detail_page` — Ver Cajas Abiertas: `https://wappsi336.com/holamigo/admin/pos/registers`
- `document_report` — Verificador de productos: `https://wappsi336.com/holamigo/admin/pos/price_checker`

### production_order

- `filter_table` — Agregar orden de confección ⚠️: `https://wappsi336.com/holamigo/admin/production_order/add`
- `filter_paginated_table` — Lista de órdenes de confección: `https://wappsi336.com/holamigo/admin/production_order`
- `filter_paginated_table` — Órdenes de corte ⚠️: `https://wappsi336.com/holamigo/admin/production_order/cutting_orders`
- `filter_paginated_table` — Órdenes de empaque ⚠️: `https://wappsi336.com/holamigo/admin/production_order/packing_orders`
- `filter_paginated_table` — Órdenes de ensamble ⚠️: `https://wappsi336.com/holamigo/admin/production_order/assemble_orders`

### products

- `filter_table` — Agregar Ajuste de Cantidad ⚠️: `https://wappsi336.com/holamigo/admin/products/add_adjustment`
- `filter_table` — Agregar Orden de Producción ⚠️: `https://wappsi336.com/holamigo/admin/products/add_production_order`
- `filter_table` — Agregar Producto: `https://wappsi336.com/holamigo/admin/products/add`
- `filter_table` — Agregar Transformación de Productos ⚠️: `https://wappsi336.com/holamigo/admin/products/add_product_transformation`
- `filter_table` — Agregar conteo físico desde archivo ⚠️: `https://wappsi336.com/holamigo/admin/products/count_stock`
- `transaction_form` — Agregar conteo físico desde archivo con variantes ⚠️: `https://wappsi336.com/holamigo/admin/products/count_stock_variants`
- `filter_table` — Agregar conteo rápido: `https://wappsi336.com/holamigo/admin/products/add_express_count`
- `filter_table` — Conteo Secuencial ⚠️: `https://wappsi336.com/holamigo/admin/products/sequentialCount`
- `filter_paginated_table` — Conteos Secuenciales ⚠️: `https://wappsi336.com/holamigo/admin/products/sequential_counts`
- `transaction_form` — Importar Productos ⚠️: `https://wappsi336.com/holamigo/admin/products/import_csv`
- `filter_table` — Imprimir Etiquetas ⚠️: `https://wappsi336.com/holamigo/admin/products/print_barcodes`
- `settings_page` — Lista Ajustes de Cantidades ⚠️: `https://wappsi336.com/holamigo/admin/products/quantity_adjustments`
- `filter_paginated_table` — Lista Productos ⚠️: `https://wappsi336.com/holamigo/admin/products`
- `filter_paginated_table` — Lista Transformación de Productos ⚠️: `https://wappsi336.com/holamigo/admin/products/product_transformations`
- `detail_page` — Lista de conteos físicos ⚠️: `https://wappsi336.com/holamigo/admin/products/stock_counts`
- `filter_paginated_table` — Órdenes de Producción ⚠️: `https://wappsi336.com/holamigo/admin/products/production_orders`

### purchases

- `filter_table` — Agregar Compra ⚠️: `https://wappsi336.com/holamigo/admin/purchases/add`
- `filter_table` — Agregar Compra por XLS ⚠️: `https://wappsi336.com/holamigo/admin/purchases/purchase_by_csv`
- `filter_table` — Agregar Orden de Compra: `https://wappsi336.com/holamigo/admin/purchases/add-purchase-order`
- `filter_table` — Agregar importación ⚠️: `https://wappsi336.com/holamigo/admin/purchases/add_import`
- `filter_paginated_table` — Importaciones: `https://wappsi336.com/holamigo/admin/purchases/imports`
- `filter_paginated_table` — Lista Compras: `https://wappsi336.com/holamigo/admin/purchases`
- `filter_paginated_table` — Lista de Órdenes de Compra/Gasto: `https://wappsi336.com/holamigo/admin/purchases/purchase-orders`

### quotes

- `filter_table` — Agregar Cotización: `https://wappsi336.com/holamigo/admin/quotes/add`
- `filter_table` — Agregar Orden de Gasto ⚠️: `https://wappsi336.com/holamigo/admin/quotes/addqexpense`
- `filter_paginated_table` — Lista Cotizaciones: `https://wappsi336.com/holamigo/admin/quotes`

### reports

- `filter_paginated_table` — Actividad de usuarios ⚠️: `https://wappsi336.com/holamigo/admin/reports/user_activities`
- `filter_paginated_table` — Alertas Caducidad del Producto: `https://wappsi336.com/holamigo/admin/reports/expiry_alerts`
- `filter_paginated_table` — Alertas Cantidad de Producto ⚠️: `https://wappsi336.com/holamigo/admin/reports/quantity_alerts`
- `document_report` — Cantidades en Bodega ⚠️: `https://wappsi336.com/holamigo/admin/reports/warehouse_stock`
- `transaction_form` — Cartera de Clientes por Edades ⚠️: `https://wappsi336.com/holamigo/admin/reports/portfolio_report_2`
- `transaction_form` — Cartera de Vendedores por Edades ⚠️: `https://wappsi336.com/holamigo/admin/reports/portfolio_report`
- `paginated_table` — Compras Diarias ⚠️: `https://wappsi336.com/holamigo/admin/reports/daily_purchases`
- `paginated_table` — Compras Mensuales ⚠️: `https://wappsi336.com/holamigo/admin/reports/monthly_purchases`
- `document_report` — Enlaces Directos ⚠️: `https://wappsi336.com/holamigo/admin/reports`
- `document_report` — Indicadores Rápidos ⚠️: `https://wappsi336.com/holamigo/admin/reports/profit_loss`
- `transaction_form` — Informe Comprobante Diario (Z): `https://wappsi336.com/holamigo/admin/reports/load_zeta`
- `transaction_form` — Informe Diario por sucursal: `https://wappsi336.com/holamigo/admin/reports/b_load_zeta`
- `filter_paginated_table` — Informe Flujo de Caja Detallado ⚠️: `https://wappsi336.com/holamigo/admin/reports/closed_register_details`
- `filter_table` — Informe Inventario Valorizado: `https://wappsi336.com/holamigo/admin/reports/valued_products`
- `filter_paginated_table` — Informe Movimiento de Productos ⚠️: `https://wappsi336.com/holamigo/admin/reports/products`
- `document_report` — Informe Productos más Vendidos ⚠️: `https://wappsi336.com/holamigo/admin/reports/best_sellers`
- `filter_paginated_table` — Informe Ventas y Compras por Categoría ⚠️: `https://wappsi336.com/holamigo/admin/reports/categories`
- `settings_page` — Informe de Ajustes ⚠️: `https://wappsi336.com/holamigo/admin/reports/adjustments`
- `transaction_form` — Informe de Cartera por Vendedor ⚠️: `https://wappsi336.com/holamigo/admin/reports/portfolio`
- `filter_paginated_table` — Informe de Cierres (X) ⚠️: `https://wappsi336.com/holamigo/admin/reports/register`
- `detail_page` — Informe de Clientes: `https://wappsi336.com/holamigo/admin/reports/customers`
- `filter_paginated_table` — Informe de Comisiones por Recaudo ⚠️: `https://wappsi336.com/holamigo/admin/reports/collection_commissions`
- `filter_paginated_table` — Informe de Compras ⚠️: `https://wappsi336.com/holamigo/admin/reports/purchases`
- `transaction_form` — Informe de Impuestos ⚠️: `https://wappsi336.com/holamigo/admin/reports/tax`
- `transaction_form` — Informe de Lista de Precios ⚠️: `https://wappsi336.com/holamigo/admin/reports/price_groups`
- `filter_paginated_table` — Informe de Marcas ⚠️: `https://wappsi336.com/holamigo/admin/reports/brands`
- `detail_page` — Informe de Sucursales de clientes: `https://wappsi336.com/holamigo/admin/reports/customers_addresses`
- `detail_page` — Informe de Usuarios: `https://wappsi336.com/holamigo/admin/reports/users`
- `detail_page` — Informe de Usuarios: `https://wappsi336.com/holamigo/admin/reports/users`
- `filter_paginated_table` — Informe de Ventas ⚠️: `https://wappsi336.com/holamigo/admin/reports/sales`
- `filter_paginated_table` — Informe de Ventas mensuales por sucursal y formas de pago ⚠️: `https://wappsi336.com/holamigo/admin/reports/billers_monthly_sales`
- `transaction_form` — Informe de Ventas por Vendedor ⚠️: `https://wappsi336.com/holamigo/admin/reports/load_bills`
- `filter_paginated_table` — Informe de agendamientos ⚠️: `https://wappsi336.com/holamigo/admin/reports/tasks`
- `filter_paginated_table` — Informe de cierres (X) por serial ⚠️: `https://wappsi336.com/holamigo/admin/reports/serial_register`
- `filter_paginated_table` — Informe de cierres (X) por sucursal ⚠️: `https://wappsi336.com/holamigo/admin/reports/biller_register`
- `filter_paginated_table` — Informe de gastos ⚠️: `https://wappsi336.com/holamigo/admin/reports/expenses`
- `filter_paginated_table` — Informe de ingresos diarios ⚠️: `https://wappsi336.com/holamigo/admin/reports/daily_incomes`
- `transaction_form` — Informe de ordenes de confección ⚠️: `https://wappsi336.com/holamigo/admin/reports/production_order_report`
- `filter_table` — Informe de traslados ⚠️: `https://wappsi336.com/holamigo/admin/reports/transfers`
- `transaction_form` — Informe de ventas por Categorías ⚠️: `https://wappsi336.com/holamigo/admin/reports/categories2`
- `filter_paginated_table` — Informe de Órdenes de Pedido ⚠️: `https://wappsi336.com/holamigo/admin/reports/order_sales`
- `filter_paginated_table` — Informe para Solicitud de compras: `https://wappsi336.com/holamigo/admin/reports/purchases_request`
- `transaction_form` — Inventario Bodega por Variantes ⚠️: `https://wappsi336.com/holamigo/admin/reports/warehouse_inventory_variants`
- `filter_table` — Puntos Premio ⚠️: `https://wappsi336.com/holamigo/admin/reports/award_points`
- `filter_paginated_table` — Rentabilidad por Cliente ⚠️: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_customer`
- `filter_paginated_table` — Rentabilidad por Documento ⚠️: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_doc`
- `filter_paginated_table` — Rentabilidad por Producto ⚠️: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_producto`
- `transaction_form` — Rentabilidad producto, Costo compra ⚠️: `https://wappsi336.com/holamigo/admin/reports/product_profitability`
- `detail_page` — Reporte de Proveedor: `https://wappsi336.com/holamigo/admin/reports/suppliers`
- `paginated_table` — Ventas Diarias: `https://wappsi336.com/holamigo/admin/reports/daily_sales`
- `paginated_table` — Ventas Mensuales: `https://wappsi336.com/holamigo/admin/reports/monthly_sales`

### returns

- `filter_table` — Agregar Devolución de compra de Años Anteriores ⚠️: `https://wappsi336.com/holamigo/admin/returns/add_past_years_purchase_return`
- `filter_table` — Agregar Devolución de venta de Años Anteriores ⚠️: `https://wappsi336.com/holamigo/admin/returns/add_past_years_sale_return`

### root

- `list_table` — Órdenes de pedido: `https://wappsi336.com/holamigo/admin/calendar`

### sales

- `filter_table` — Agregar Orden de Pedido ⚠️: `https://wappsi336.com/holamigo/admin/sales/add_order`
- `detail_page` — Agregar Venta ⚠️: `https://wappsi336.com/holamigo/admin/sales/add`
- `detail_page` — Agregar Venta por CSV ⚠️: `https://wappsi336.com/holamigo/admin/sales/sale_by_csv`
- `detail_page` — Bonos: `https://wappsi336.com/holamigo/admin/sales/gift_cards`
- `detail_page` — Despachos: `https://wappsi336.com/holamigo/admin/sales/deliveries`
- `list_table` — Exportar Notas Contables: `https://wappsi336.com/holamigo/admin/calendar`
- `detail_page` — Lista Facturas: `https://wappsi336.com/holamigo/admin/sales`
- `detail_page` — Lista Facturas Electrónicas: `https://wappsi336.com/holamigo/admin/sales/fe_index`
- `filter_paginated_table` — Lista Órdenes de Pedido: `https://wappsi336.com/holamigo/admin/sales/orders`
- `list_table` — Servidor de impresión: `https://wappsi336.com/holamigo/admin/sales/printServer`

### sales_reports

- `detail_page` — Ejecución Presupuesto de Ventas: `https://wappsi336.com/holamigo/admin/sales_reports/budget_execution`

### seller

- `transaction_form` — Agregar Vendedor: `https://wappsi336.com/holamigo/admin/seller/add`
- `filter_paginated_table` — Listar Vendedores: `https://wappsi336.com/holamigo/admin/seller`

### suppliers

- `list_table` — Agregar Proveedor: `https://wappsi336.com/holamigo/admin/calendar`
- `filter_paginated_table` — Lista Anticipos de Proveedores/Acreedores: `https://wappsi336.com/holamigo/admin/suppliers/list_deposits`
- `filter_paginated_table` — Lista Proveedores: `https://wappsi336.com/holamigo/admin/suppliers`

### system_settings

- `filter_paginated_table` — Bodegas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/warehouses`
- `list_table` — Cargar Imágenes: `https://wappsi336.com/holamigo/admin/calendar`
- `filter_paginated_table` — Categorías ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/categories`
- `filter_paginated_table` — Categorías de Gastos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/expense_categories`
- `document_report` — Cierre mensual: `https://wappsi336.com/holamigo/admin/system_settings/monthly_closing`
- `filter_paginated_table` — Colores ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/colors`
- `filter_paginated_table` — Conceptos de Notas: `https://wappsi336.com/holamigo/admin/system_settings/configuration_concept_notes`
- `document_report` — Copias de Seguridad ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/backups`
- `filter_paginated_table` — Etiquetas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/tags`
- `filter_paginated_table` — Grupos de Clientes ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/customer_groups`
- `filter_paginated_table` — Instancias BPM ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/instances`
- `filter_paginated_table` — Lista Precios ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/price_groups`
- `filter_paginated_table` — Marcas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/brands`
- `filter_paginated_table` — Materiales ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/materials`
- `filter_paginated_table` — Monedas ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/currencies`
- `filter_paginated_table` — Notas de Documentos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/invoice_notes`
- `settings_page` — Parámetros Generales ⚠️: `https://wappsi336.com/holamigo/admin/system_settings`
- `filter_paginated_table` — Perfiles de Usuario ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/user_groups`
- `transaction_form` — Plantillas de Correo Electrónico ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/email_templates`
- `filter_paginated_table` — Precios por Unidad ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/w_units`
- `settings_page` — Preferencias del Producto ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/product_preferences`
- `filter_paginated_table` — Retenciones ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/withholding_tax`
- `filter_paginated_table` — Tasas de Impuestos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/tax_rates`
- `filter_paginated_table` — Tipos de Documentos: `https://wappsi336.com/holamigo/admin/system_settings/document_types`
- `filter_paginated_table` — Ubicación ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/ubication`
- `filter_paginated_table` — Unidades ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/units`
- `filter_paginated_table` — Variantes de Productos ⚠️: `https://wappsi336.com/holamigo/admin/system_settings/variants`

### transfers

- `filter_table` — Agregar traslado ⚠️: `https://wappsi336.com/holamigo/admin/transfers/add`
- `transaction_form` — Agregar traslado por archivo CSV ⚠️: `https://wappsi336.com/holamigo/admin/transfers/transfer_by_csv`
- `filter_table` — Añadir orden de traslado ⚠️: `https://wappsi336.com/holamigo/admin/transfers/add_order`
- `filter_paginated_table` — Lista de traslados ⚠️: `https://wappsi336.com/holamigo/admin/transfers`
- `filter_paginated_table` — Ordenes de traslado ⚠️: `https://wappsi336.com/holamigo/admin/transfers/orders`

### users

- `transaction_form` — Cambiar contraseña ⚠️: `https://wappsi336.com/holamigo/admin/users/profile/24/`
- `filter_paginated_table` — Lista Usuarios: `https://wappsi336.com/holamigo/admin/users`
- `settings_page` — Perfil ⚠️: `https://wappsi336.com/holamigo/admin/users/profile/24`

### wappsi_invoicing

- `filter_table` — Mis Consumos Electrónicos: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/electronic_hits`
- `filter_paginated_table` — Mis Facturas: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/invoices`
- `filter_paginated_table` — Mis Facturas: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/invoices`

### warranty

- `detail_page` — Agregar Garantía: `https://wappsi336.com/holamigo/admin/warranty/add`
- `detail_page` — Lista Garantías: `https://wappsi336.com/holamigo/admin/warranty`

## Páginas por patrón

### detail_page

- Presupuestos de Venta: `https://wappsi336.com/holamigo/admin/budget`
- Lista Anticipos: `https://wappsi336.com/holamigo/admin/customers/list_deposits/`
- Lista Factura POS Electrónico: `https://wappsi336.com/holamigo/admin/pos/fe_index`
- Lista Facturas POS: `https://wappsi336.com/holamigo/admin/pos/sales`
- Movimientos de Caja: `https://wappsi336.com/holamigo/admin/pos/pos_register_movements`
- Servidor de Impresión: `https://wappsi336.com/holamigo/admin/pos/pos_print_server`
- Ver Cajas Abiertas: `https://wappsi336.com/holamigo/admin/pos/registers`
- Lista de conteos físicos: `https://wappsi336.com/holamigo/admin/products/stock_counts`
- Informe de Clientes: `https://wappsi336.com/holamigo/admin/reports/customers`
- Informe de Sucursales de clientes: `https://wappsi336.com/holamigo/admin/reports/customers_addresses`
- Informe de Usuarios: `https://wappsi336.com/holamigo/admin/reports/users`
- Informe de Usuarios: `https://wappsi336.com/holamigo/admin/reports/users`
- Reporte de Proveedor: `https://wappsi336.com/holamigo/admin/reports/suppliers`
- Agregar Venta: `https://wappsi336.com/holamigo/admin/sales/add`
- Agregar Venta por CSV: `https://wappsi336.com/holamigo/admin/sales/sale_by_csv`
- Bonos: `https://wappsi336.com/holamigo/admin/sales/gift_cards`
- Despachos: `https://wappsi336.com/holamigo/admin/sales/deliveries`
- Lista Facturas: `https://wappsi336.com/holamigo/admin/sales`
- Lista Facturas Electrónicas: `https://wappsi336.com/holamigo/admin/sales/fe_index`
- Ejecución Presupuesto de Ventas: `https://wappsi336.com/holamigo/admin/sales_reports/budget_execution`
- Agregar Garantía: `https://wappsi336.com/holamigo/admin/warranty/add`
- Lista Garantías: `https://wappsi336.com/holamigo/admin/warranty`

### document_report

- Código QR para registrar cliente: `https://wappsi336.com/holamigo/admin/auth/qr_rau`
- Tablero Financiero: `https://wappsi336.com/holamigo/admin/dashboard/financial`
- Tablero POS Actions: `https://wappsi336.com/holamigo/admin/dashboard/posActions`
- Tablero Ventas: `https://wappsi336.com/holamigo/admin/dashboard/sales`
- Verificador de productos: `https://wappsi336.com/holamigo/admin/pos/price_checker`
- Cantidades en Bodega: `https://wappsi336.com/holamigo/admin/reports/warehouse_stock`
- Enlaces Directos: `https://wappsi336.com/holamigo/admin/reports`
- Indicadores Rápidos: `https://wappsi336.com/holamigo/admin/reports/profit_loss`
- Informe Productos más Vendidos: `https://wappsi336.com/holamigo/admin/reports/best_sellers`
- Cierre mensual: `https://wappsi336.com/holamigo/admin/system_settings/monthly_closing`
- Copias de Seguridad: `https://wappsi336.com/holamigo/admin/system_settings/backups`

### filter_paginated_table

- Lista de afiliados: `https://wappsi336.com/holamigo/admin/affiliates`
- Lista Sucursales: `https://wappsi336.com/holamigo/admin/billers`
- Lista Clientes: `https://wappsi336.com/holamigo/admin/customers`
- Cupones: `https://wappsi336.com/holamigo/admin/marketing/coupons`
- Notificaciones: `https://wappsi336.com/holamigo/admin/notifications`
- Lista Impresoras: `https://wappsi336.com/holamigo/admin/pos/printers`
- Lista de órdenes de confección: `https://wappsi336.com/holamigo/admin/production_order`
- Órdenes de corte: `https://wappsi336.com/holamigo/admin/production_order/cutting_orders`
- Órdenes de empaque: `https://wappsi336.com/holamigo/admin/production_order/packing_orders`
- Órdenes de ensamble: `https://wappsi336.com/holamigo/admin/production_order/assemble_orders`
- Conteos Secuenciales: `https://wappsi336.com/holamigo/admin/products/sequential_counts`
- Lista Productos: `https://wappsi336.com/holamigo/admin/products`
- Lista Transformación de Productos: `https://wappsi336.com/holamigo/admin/products/product_transformations`
- Órdenes de Producción: `https://wappsi336.com/holamigo/admin/products/production_orders`
- Importaciones: `https://wappsi336.com/holamigo/admin/purchases/imports`
- Lista Compras: `https://wappsi336.com/holamigo/admin/purchases`
- Lista de Órdenes de Compra/Gasto: `https://wappsi336.com/holamigo/admin/purchases/purchase-orders`
- Lista Cotizaciones: `https://wappsi336.com/holamigo/admin/quotes`
- Actividad de usuarios: `https://wappsi336.com/holamigo/admin/reports/user_activities`
- Alertas Caducidad del Producto: `https://wappsi336.com/holamigo/admin/reports/expiry_alerts`
- Alertas Cantidad de Producto: `https://wappsi336.com/holamigo/admin/reports/quantity_alerts`
- Informe Flujo de Caja Detallado: `https://wappsi336.com/holamigo/admin/reports/closed_register_details`
- Informe Movimiento de Productos: `https://wappsi336.com/holamigo/admin/reports/products`
- Informe Ventas y Compras por Categoría: `https://wappsi336.com/holamigo/admin/reports/categories`
- Informe de Cierres (X): `https://wappsi336.com/holamigo/admin/reports/register`
- Informe de Comisiones por Recaudo: `https://wappsi336.com/holamigo/admin/reports/collection_commissions`
- Informe de Compras: `https://wappsi336.com/holamigo/admin/reports/purchases`
- Informe de Marcas: `https://wappsi336.com/holamigo/admin/reports/brands`
- Informe de Ventas: `https://wappsi336.com/holamigo/admin/reports/sales`
- Informe de Ventas mensuales por sucursal y formas de pago: `https://wappsi336.com/holamigo/admin/reports/billers_monthly_sales`
- Informe de agendamientos: `https://wappsi336.com/holamigo/admin/reports/tasks`
- Informe de cierres (X) por serial: `https://wappsi336.com/holamigo/admin/reports/serial_register`
- Informe de cierres (X) por sucursal: `https://wappsi336.com/holamigo/admin/reports/biller_register`
- Informe de gastos: `https://wappsi336.com/holamigo/admin/reports/expenses`
- Informe de ingresos diarios: `https://wappsi336.com/holamigo/admin/reports/daily_incomes`
- Informe de Órdenes de Pedido: `https://wappsi336.com/holamigo/admin/reports/order_sales`
- Informe para Solicitud de compras: `https://wappsi336.com/holamigo/admin/reports/purchases_request`
- Rentabilidad por Cliente: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_customer`
- Rentabilidad por Documento: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_doc`
- Rentabilidad por Producto: `https://wappsi336.com/holamigo/admin/reports/load_rentabilidad_producto`
- Lista Órdenes de Pedido: `https://wappsi336.com/holamigo/admin/sales/orders`
- Listar Vendedores: `https://wappsi336.com/holamigo/admin/seller`
- Lista Anticipos de Proveedores/Acreedores: `https://wappsi336.com/holamigo/admin/suppliers/list_deposits`
- Lista Proveedores: `https://wappsi336.com/holamigo/admin/suppliers`
- Bodegas: `https://wappsi336.com/holamigo/admin/system_settings/warehouses`
- Categorías: `https://wappsi336.com/holamigo/admin/system_settings/categories`
- Categorías de Gastos: `https://wappsi336.com/holamigo/admin/system_settings/expense_categories`
- Colores: `https://wappsi336.com/holamigo/admin/system_settings/colors`
- Conceptos de Notas: `https://wappsi336.com/holamigo/admin/system_settings/configuration_concept_notes`
- Etiquetas: `https://wappsi336.com/holamigo/admin/system_settings/tags`
- Grupos de Clientes: `https://wappsi336.com/holamigo/admin/system_settings/customer_groups`
- Instancias BPM: `https://wappsi336.com/holamigo/admin/system_settings/instances`
- Lista Precios: `https://wappsi336.com/holamigo/admin/system_settings/price_groups`
- Marcas: `https://wappsi336.com/holamigo/admin/system_settings/brands`
- Materiales: `https://wappsi336.com/holamigo/admin/system_settings/materials`
- Monedas: `https://wappsi336.com/holamigo/admin/system_settings/currencies`
- Notas de Documentos: `https://wappsi336.com/holamigo/admin/system_settings/invoice_notes`
- Perfiles de Usuario: `https://wappsi336.com/holamigo/admin/system_settings/user_groups`
- Precios por Unidad: `https://wappsi336.com/holamigo/admin/system_settings/w_units`
- Retenciones: `https://wappsi336.com/holamigo/admin/system_settings/withholding_tax`
- Tasas de Impuestos: `https://wappsi336.com/holamigo/admin/system_settings/tax_rates`
- Tipos de Documentos: `https://wappsi336.com/holamigo/admin/system_settings/document_types`
- Ubicación: `https://wappsi336.com/holamigo/admin/system_settings/ubication`
- Unidades: `https://wappsi336.com/holamigo/admin/system_settings/units`
- Variantes de Productos: `https://wappsi336.com/holamigo/admin/system_settings/variants`
- Lista de traslados: `https://wappsi336.com/holamigo/admin/transfers`
- Ordenes de traslado: `https://wappsi336.com/holamigo/admin/transfers/orders`
- Lista Usuarios: `https://wappsi336.com/holamigo/admin/users`
- Mis Facturas: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/invoices`
- Mis Facturas: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/invoices`

### filter_table

- Agregar Nota Débito: `https://wappsi336.com/holamigo/admin/debit_notes/add`
- Agregar Venta POS: `https://wappsi336.com/holamigo/admin/pos`
- POS Mayorista: `https://wappsi336.com/holamigo/admin/pos/add_wholesale`
- Agregar orden de confección: `https://wappsi336.com/holamigo/admin/production_order/add`
- Agregar Ajuste de Cantidad: `https://wappsi336.com/holamigo/admin/products/add_adjustment`
- Agregar Orden de Producción: `https://wappsi336.com/holamigo/admin/products/add_production_order`
- Agregar Producto: `https://wappsi336.com/holamigo/admin/products/add`
- Agregar Transformación de Productos: `https://wappsi336.com/holamigo/admin/products/add_product_transformation`
- Agregar conteo físico desde archivo: `https://wappsi336.com/holamigo/admin/products/count_stock`
- Agregar conteo rápido: `https://wappsi336.com/holamigo/admin/products/add_express_count`
- Conteo Secuencial: `https://wappsi336.com/holamigo/admin/products/sequentialCount`
- Imprimir Etiquetas: `https://wappsi336.com/holamigo/admin/products/print_barcodes`
- Agregar Compra: `https://wappsi336.com/holamigo/admin/purchases/add`
- Agregar Compra por XLS: `https://wappsi336.com/holamigo/admin/purchases/purchase_by_csv`
- Agregar Orden de Compra: `https://wappsi336.com/holamigo/admin/purchases/add-purchase-order`
- Agregar importación: `https://wappsi336.com/holamigo/admin/purchases/add_import`
- Agregar Cotización: `https://wappsi336.com/holamigo/admin/quotes/add`
- Agregar Orden de Gasto: `https://wappsi336.com/holamigo/admin/quotes/addqexpense`
- Informe Inventario Valorizado: `https://wappsi336.com/holamigo/admin/reports/valued_products`
- Informe de traslados: `https://wappsi336.com/holamigo/admin/reports/transfers`
- Puntos Premio: `https://wappsi336.com/holamigo/admin/reports/award_points`
- Agregar Devolución de compra de Años Anteriores: `https://wappsi336.com/holamigo/admin/returns/add_past_years_purchase_return`
- Agregar Devolución de venta de Años Anteriores: `https://wappsi336.com/holamigo/admin/returns/add_past_years_sale_return`
- Agregar Orden de Pedido: `https://wappsi336.com/holamigo/admin/sales/add_order`
- Agregar traslado: `https://wappsi336.com/holamigo/admin/transfers/add`
- Añadir orden de traslado: `https://wappsi336.com/holamigo/admin/transfers/add_order`
- Mis Consumos Electrónicos: `https://wappsi336.com/holamigo/admin/wappsi_invoicing/electronic_hits`

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

- Compras Diarias: `https://wappsi336.com/holamigo/admin/reports/daily_purchases`
- Compras Mensuales: `https://wappsi336.com/holamigo/admin/reports/monthly_purchases`
- Ventas Diarias: `https://wappsi336.com/holamigo/admin/reports/daily_sales`
- Ventas Mensuales: `https://wappsi336.com/holamigo/admin/reports/monthly_sales`

### settings_page

- Ajustes: `https://wappsi336.com/holamigo/admin/marketing/settings`
- Parámetros POS: `https://wappsi336.com/holamigo/admin/pos/settings`
- Lista Ajustes de Cantidades: `https://wappsi336.com/holamigo/admin/products/quantity_adjustments`
- Informe de Ajustes: `https://wappsi336.com/holamigo/admin/reports/adjustments`
- Parámetros Generales: `https://wappsi336.com/holamigo/admin/system_settings`
- Preferencias del Producto: `https://wappsi336.com/holamigo/admin/system_settings/product_preferences`
- Perfil: `https://wappsi336.com/holamigo/admin/users/profile/24`

### transaction_form

- Agregar afiliado: `https://wappsi336.com/holamigo/admin/affiliates/add`
- Clave dinámica: `https://wappsi336.com/holamigo/admin/billers/random_pin_code`
- Lista de Creditos: `https://wappsi336.com/holamigo/admin/system_settings`
- Lista de Cuotas: `https://wappsi336.com/holamigo/admin/system_settings`
- Agregar Impresora: `https://wappsi336.com/holamigo/admin/pos/add_printer`
- Agregar conteo físico desde archivo con variantes: `https://wappsi336.com/holamigo/admin/products/count_stock_variants`
- Importar Productos: `https://wappsi336.com/holamigo/admin/products/import_csv`
- Cartera de Clientes por Edades: `https://wappsi336.com/holamigo/admin/reports/portfolio_report_2`
- Cartera de Vendedores por Edades: `https://wappsi336.com/holamigo/admin/reports/portfolio_report`
- Informe Comprobante Diario (Z): `https://wappsi336.com/holamigo/admin/reports/load_zeta`
- Informe Diario por sucursal: `https://wappsi336.com/holamigo/admin/reports/b_load_zeta`
- Informe de Cartera por Vendedor: `https://wappsi336.com/holamigo/admin/reports/portfolio`
- Informe de Impuestos: `https://wappsi336.com/holamigo/admin/reports/tax`
- Informe de Lista de Precios: `https://wappsi336.com/holamigo/admin/reports/price_groups`
- Informe de Ventas por Vendedor: `https://wappsi336.com/holamigo/admin/reports/load_bills`
- Informe de ordenes de confección: `https://wappsi336.com/holamigo/admin/reports/production_order_report`
- Informe de ventas por Categorías: `https://wappsi336.com/holamigo/admin/reports/categories2`
- Inventario Bodega por Variantes: `https://wappsi336.com/holamigo/admin/reports/warehouse_inventory_variants`
- Rentabilidad producto, Costo compra: `https://wappsi336.com/holamigo/admin/reports/product_profitability`
- Agregar Vendedor: `https://wappsi336.com/holamigo/admin/seller/add`
- Plantillas de Correo Electrónico: `https://wappsi336.com/holamigo/admin/system_settings/email_templates`
- Agregar traslado por archivo CSV: `https://wappsi336.com/holamigo/admin/transfers/transfer_by_csv`
- Cambiar contraseña: `https://wappsi336.com/holamigo/admin/users/profile/24/`

### unknown

- Ventas suspendidas: `https://wappsi336.com/holamigo/admin/pos/opened_bills`

## Acciones peligrosas detectadas

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

## Extractores recomendados

- `filter_paginated_table` → `generic_filter_paginated_table_extractor`
- `filter_table` → `generic_filter_table_extractor`
- `transaction_form` → `manual_review_transaction_form`
- `detail_page` → `generic_detail_page_reader`
- `document_report` → `generic_document_report_detector`
- `list_table` → `generic_table_extractor`
- `settings_page` → `manual_review_settings_reader`
- `paginated_table` → `generic_paginated_table_extractor`
- `unknown` → `inspect_manually`

## Próximo paso

Construir primero `generic_filter_paginated_table_extractor` porque el patrón `filter_paginated_table` cubre 70 página(s).
