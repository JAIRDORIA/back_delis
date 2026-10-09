# SnackFlow — Backend (negocio Delis)

Explora el repo tú mismo; no pidas archivos. Responde breve, con edición mínima y sin refactors no pedidos. Al terminar, lista archivos modificados y cualquier supuesto que hayas hecho.

## Stack y despliegue
- Flask + MySQL con MySQLdb, **sin ORM**, por cursores. Estructura: controllers + services (+ modelos donde existan).
- Backend en Render (`snackflow-api.onrender.com`), BD MySQL en Clever Cloud. Hay una BD de prueba y una de producción.
- Los cambios de esquema (ALTER/CREATE) NO se ejecutan desde el código: entrégalos como SQL aparte, con rollback, avisando que en producción se corren **antes** de desplegar el backend.

## Convenciones obligatorias
- **Cursores:** todo cursor se cierra siempre (`try/finally` o el helper del proyecto si existe). Cursores sin cerrar ya causaron `1226 max_user_connections`. Haz `fetch` antes de cerrar; no muevas `commit`/`rollback` existentes.
- SQL **siempre parametrizado**; valida valores contra listas blancas; paginación con página ≥ 1 y límite máximo razonable.
- Errores: JSON con `mensaje` y el código HTTP que ya usa el controller.
- **Fechas en UTC** en la BD. Solo se convierte a `America/Bogota` (con `zoneinfo`) cuando el backend necesita saber "qué es hoy en Colombia" (ej. `pedidos_cocina_service.py`).
- Roles `admin` / `cajero` / `cocina`. `token_requerido` rechaza a `cocina` con 403 por defecto; solo los decoradores `*_cocina` lo permiten. No lo cambies.
- No uses `usuario_id` hardcodeado; sale del token/sesión.
- **Nunca asumas el shape de un objeto o el nombre de un campo**: verifícalo en el código o con un dato real. Los servicios de clientes mezclan `id`/`nombre` con `ID_Cliente`/`Cli_Nombre` (vía `toDic()`).

## Reglas de negocio que no se deben romper
- **Cortes:** solo uno `abierto` a la vez. Préstamos y sus abonos se asocian al corte abierto del momento (no lo manda el frontend). Abonos de ventas a un corte `futuro` suman a `cortes.saldo_inicial` en vez de `movimientos_caja`.
- **Inventario:** bandejas + unidades sueltas. Fórmula: `total = stock*unidades_por_bandeja + sueltas`; `bandejas = int(total/unidades_por_bandeja)` (trunca hacia 0); `sueltas = total - bandejas*unidades_por_bandeja`. El descuento ocurre cuando `ventas.estado` pasa a `entregada` (`descontar_inventario_venta`), **no** al crear la venta. Productos simples descuentan bandejas; combos descuentan en unidades.
- **Combos:** catálogo = `combo_id` con valor y `combo_productos` NULL; personalizado = `combo_id` NULL y `combo_productos` JSON `[{producto_id, cantidad_unidades}]`. Nunca guardar `combo_id` junto con `combo_productos`. `actualizar_detalle_venta` debe conservar `combo_productos`.
- **Cocina:** "Entregar" en el panel solo llena `entregada_cocina_at/por`; no cambia `estado` ni descuenta inventario. El admin confirma con `PUT /ventas/<id>` (`estado = entregada`). `GET /pedidos-cocina/por-confirmar` lista las pendientes de esa confirmación.
- **Dirección por pedido:** `ventas.direccion_entrega` (NULL por defecto). Cocina muestra `COALESCE(NULLIF(TRIM(direccion_entrega),''), dirección del cliente)`. Si el cliente no tiene dirección y llega una al crear la venta, se guarda también en el cliente (UPDATE condicional en la misma transacción).
- Anular una venta revierte inventario (trigger `trg_venta_anular` para simples; `revertir_inventario_detalle` para combos).

## Trampas conocidas
- **`BIGINT UNSIGNED out of range`:** restar/sumar una columna con signo (`stock_actual`) con una `UNSIGNED` (`cantidad`) en SQL crudo/triggers; usar `CAST(... AS SIGNED)`.
- Endpoints con `LIMIT` fijo y filtro en frontend se rompen al crecer los datos: filtra y pagina en el servidor. El de inventario aún tiene este problema.
- El listado de cortes/historial necesita traer **todas** las páginas de ventas/compras; no rompas ese consumo al tocar los listados.
- Edición manual de inventario y otras acciones sensibles se registran en `auditoria` (`datos_anteriores` / `datos_nuevos` JSON).
