# SnackFlow — Contexto técnico

Documento de traspaso para continuar el desarrollo en otra conversación. Proyecto de Jair Doria para el negocio **Delis**. Backend Flask + MySQL (MySQLdb, sin ORM, por cursores), frontend React + Vite con Zustand (un store por módulo) y una capa `api/*.js` sobre una instancia de axios. BD en Clever Cloud (Montreal), backend en Render (`snackflow-api.onrender.com`). Autenticación por JWT, usuario guardado en `localStorage` (no hay store de auth).

---

## 1. Lógica de cortes

- Tabla `cortes`: `id, numero, fecha_inicio, saldo_inicial, estado` (`'futuro' | 'abierto' | 'cerrado'`).
- Solo puede haber **un corte `abierto`** a la vez. Se busca con `SELECT ... WHERE estado='abierto' LIMIT 1`.
- Ventas, compras, préstamos, abonos y `movimientos_caja` se asocian a un `corte_id`.
- Un préstamo (y cada abono a un préstamo) se asocia automáticamente al corte **abierto en ese momento** — no lo manda el frontend.
- Las ventas se pueden asignar a un corte **futuro**. Mientras ese corte no esté abierto, sus abonos se suman a `cortes.saldo_inicial` en vez de insertarse en `movimientos_caja`.
- `movimientos_caja` es el libro mayor de caja: `tipo` (`ingreso`/`egreso`), `concepto`, `monto`, `medio_pago`, `corte_id`, `referencia_id`.
- `balance_corte_actual()` calcula: `total_ventas`, `total_compras`, `dinero_caja` (ingresos-egresos de `movimientos_caja`), `dinero_caja_real` (incluye `saldo_inicial`, excluye abonos de ventas futuras), `total_efectivo`/`total_transferencia` (calculado desde `abonos`−`compras` por `medio_pago`, **no** directamente desde `movimientos_caja` — hubo que sumarle a mano el neto de `prestamo`/`pago_prestamo` porque los préstamos no pasan por `abonos`/`compras`), `saldo_pendiente_ventas`, `saldo_pendiente_anteriores`.
- Historial de cortes: al exportar/ver detalle de un corte hay que traer **todas** las páginas de ventas/compras (se corrigió un bug donde se limitaba a 100 registros).

## 2. Zona horaria

- Todo se guarda en **UTC** en la base de datos (`MYSQL_INIT_COMMAND` ya no fuerza `-05:00`).
- La conversión a hora Colombia (`America/Bogota`) se hace **solo en la capa de presentación** (frontend) o explícitamente con `zoneinfo` cuando el backend necesita saber "qué es hoy en Colombia" (ej. `pedidos_cocina_service.py`).
- Hubo un bug de doble conversión (se guardaba ya en hora Colombia pero se interpretaba como UTC al mostrar) — ya resuelto.

## 3. Inventario: bandejas + unidades sueltas

- Tabla `inventario`: `producto_id, stock_actual` (bandejas, puede ser negativo), `unidades_sueltas` (puede ser negativo), `stock_minimo`.
- `productos.unidades_por_bandeja` define la conversión.
- Fórmula estándar (se usa en todos lados: ventas, combos, producción, edición manual):
  ```
  total_unidades = stock_actual * unidades_por_bandeja + unidades_sueltas
  nuevas_bandejas = int(total_unidades / unidades_por_bandeja)   # trunca hacia 0, no floor
  nuevas_sueltas  = total_unidades - nuevas_bandejas * unidades_por_bandeja
  ```
- El descuento **no ocurre al crear la venta**, ocurre cuando `ventas.estado` pasa a `entregada` (acción del admin, `PUT /ventas/<id>`), vía `descontar_inventario_venta`.
- Productos simples: se descuentan bandejas directo (`stock_actual -= cantidad`), sin tocar `unidades_sueltas`.
- Combos: se descuenta en **unidades**, no en bandejas, usando la fórmula de arriba.
- Anular una venta revierte: trigger `trg_venta_anular` para productos simples, `revertir_inventario_detalle` + `_sumar_inventario` (Python) para combos.
- Edición manual de cantidades (`ModalEditarCantidades`, `cntActualizarCantidades`) normaliza con la misma fórmula y registra en `auditoria` (`datos_anteriores`/`datos_nuevos` en JSON).

## 4. Combos (catálogo vs. personalizados)

- `venta_detalle`: `producto_id` (NULL si es combo), `es_combo`, `combo_id`, `combo_productos` (JSON, solo si el combo fue **personalizado** en el momento de la venta).
- **Combo de catálogo**: `combo_id` con valor, `combo_productos = NULL`. Su composición vive en `combo_detalle` (`combo_id, producto_id, cantidad_unidades`).
- **Combo personalizado**: `combo_id = NULL`, `combo_productos` tiene el JSON `[{producto_id, cantidad_unidades}, ...]`.
- `descontar_inventario_venta` decide cuál de los dos casos usar mirando si `combo_productos` viene o no.

### Bug corregido recientemente
`actualizar_detalle_venta` (edición de una venta pendiente) borraba y reinsertaba `venta_detalle` **sin** `combo_productos`. Cualquier edición de una venta con combo personalizado (aunque fuera de otra línea) borraba su composición sin error visible — el panel de cocina lo mostraba vacío y el inventario no se descontaba bien.
**Ya corregido en backend:** `obtener_venta_detalle` devuelve `combo_productos` parseado; `actualizar_detalle_venta` lo persiste si `item["productos"]` viene; el controller valida su forma; `useEditarVentaStore.js` ya lo carga y lo reenvía.
**Resuelto en frontend:** `EditarVentaModal.jsx` ya permite **ver y editar la composición** de un combo (de catálogo o personalizado), replicando la UI de `nuevaVentaModal.jsx`:
- Botón por fila de combo que abre un sub-modal de composición (producto + `cantidad_unidades`, agregar/eliminar filas). No incluye campo de precio: el precio se sigue editando en la tabla principal (`precio_unitario`).
- Chip "Catálogo" / "Personalizado" junto al nombre del combo (según `productos` sea `null` o un array).
- Regla: si el combo de catálogo **no** se modifica (o la composición editada equivale a la del catálogo), se queda como catálogo (`combo_id` con valor, sin `productos`). Si la composición cambia, pasa a **personalizado** (`combo_id = null` + `productos`) y eso es lo que se descuenta del inventario. Nunca se envía `combo_id` junto con `productos`.
- La lógica vive en una acción del store (`actualizarComposicionCombo(index, productos | null)` en `useEditarVentaStore.js`); `guardarCambios` mantiene el mismo contrato de `PUT /ventas/<id>/detalle`.
- Los nombres de los productos de `combo_productos` se resuelven con la lista `productos` de `useNuevaVentaStore` (el JSON solo trae `producto_id` y `cantidad_unidades`).
**A verificar:** que el botón de editar (lápiz) en `Ventas.jsx` solo se muestre en ventas `pendiente`. Editar la composición de una venta ya `entregada` no revertiría ni reajustaría el inventario ya descontado.

## 5. Préstamos a clientes (v2, con abonos parciales)

- Tabla `prestamos`: `monto, total_abonado, saldo_pendiente, medio_pago` (con el que se prestó), `medio_pago_pago` (medio del último abono), `estado` (`pendiente`/`pagado`), `observacion`, `fecha`, `fecha_pago`, `usuario_pago_id`.
- Tabla `pagos_prestamos`: historial de cada abono individual (igual patrón que `abonos` para ventas).
- `movimientos_caja.concepto` incluye `'prestamo'` (egreso al prestar) y `'pago_prestamo'` (ingreso al abonar).
- Disponibilidad de caja para prestar se calcula sumando ingresos−egresos de `movimientos_caja` por `corte_id` + `medio_pago` (fuente única de verdad, no duplica lógica del balance).
- Un abono a préstamo se asocia al corte **abierto en el momento del abono**, no al corte original del préstamo (igual que los abonos de venta).
- Endpoints: `POST/GET /prestamos`, `GET/POST /prestamos/<id>/abonos`.

## 6. Autenticación y roles

- `usuarios.rol`: `enum('admin','cajero','cocina')`.
- Solo el admin principal (`id == 1`) puede crear usuarios nuevos.
- **Cambio de diseño clave:** `token_requerido` ahora **rechaza al rol `cocina` con 403 por defecto**. Así, todas las rutas existentes quedan cerradas para cocina sin tener que tocarlas una por una.
- `token_requerido_cocina` + `rol_requerido(['cocina','admin'])` son los únicos decoradores que sí dejan pasar a `cocina` — solo se usan en las rutas del panel de pedidos.
- Frontend: `RutaProtegida` en `App.jsx` acepta `rolesPermitidos` y redirige según el rol; el login redirige a `/cocina` o `/` según `res.data.usuario.rol`.
- El objeto `usuario` vive en `localStorage`, no en un store. Patrón usado en todo el código nuevo: `JSON.parse(localStorage.getItem('usuario') || 'null')?.id`.
- Claves de sesión en `localStorage`: **`access_token`** (JWT) y **`usuario`** (JSON con `id`, `nombre`, `rol`). Cualquier código que cierre sesión debe borrar exactamente esas dos claves.
- `Login.jsx`: si ya hay `access_token`, redirige según el rol (`cocina` → `/cocina`, resto → `/`) usando `replace`. Por eso entrar a `/login` con sesión iniciada no muestra el formulario: hay que cerrar sesión o borrar el `localStorage`.
- `api/axios.js`: el interceptor de respuesta ante un **401** limpia la sesión y manda a `/login`, **excepto** en `/auth/login` (ahí el 401 significa credenciales incorrectas y debe mostrarse el mensaje). El **403** no cierra sesión (es permiso denegado, como el de `cocina` en rutas del admin).
- **Pendiente:**
  - `useInactivityTimer()` corre en toda `RutaProtegida` y cerraría la sesión del panel de cocina tras 5 min sin clics. Se resolverá agregándole un parámetro de activación (`useInactivityTimer(rol !== 'cocina')`) para que solo aplique a `admin` y `cajero`.
  - Confirmar cuánto dura el JWT en el backend (si es de 1 hora, un turno completo de cocina lo vencería a la mitad aunque el temporizador esté desactivado, y el interceptor de 401 cerraría la sesión). Opciones: token más largo solo para el rol `cocina`, o refresh token.

## 7. Panel de Pedidos (cocina) — construido

Pantalla completamente separada del admin (ruta `/cocina`), sin sidebar ni módulos de SnackFlow visibles. Diseño de referencia provisto por el cliente en Figma (header oscuro con fecha/usuario/contadores, grilla de tarjetas, combo expandible, botón "Entregar" grande).

### Decisión de negocio importante (cambió a mitad del desarrollo)
Marcar "Entregar" desde el panel de cocina **no** descuenta inventario ni cambia `ventas.estado`. Solo dos columnas nuevas en `ventas`: `entregada_cocina_at`, `entregada_cocina_por`. El admin sigue siendo quien confirma de verdad (`PUT /ventas/<id>` con `estado=entregada`), exactamente como ya funcionaba — el descuento de inventario no se tocó.

### Backend (operativo, probado con datos reales)
- `GET /pedidos-cocina/` — pedidos pendientes del día (por `fecha_entrega` en hora Colombia), con detalle de productos/combos anidado. Por cada pedido devuelve además **celular**, **dirección** y **`saldo_pendiente`**. No expone precios por producto ni otros datos de dinero.
- `PUT /pedidos-cocina/<id>/entregar` — marca `entregada_cocina_at`. Protegido contra doble marcado con el propio `WHERE` del `UPDATE` (condición de carrera entre dos tablets).
- `GET /pedidos-cocina/por-confirmar` — para el admin: ventas que cocina ya entregó y el admin no ha confirmado. Alimenta el aviso "la venta {id} fue entregada en cocina".
- Acceso: solo `token_requerido_cocina` + `rol_requerido(['cocina','admin'])`; el resto de rutas del sistema rechaza a `cocina` con 403.

### Frontend (construido)
- **Archivos:** `src/pages/pedidos/panelcocina.jsx` (pantalla), `src/store/Usepedidoscocinastore.js` (estado, acción de entregar y polling/auto-refresco), `src/api/pedidoscocinaapi.js` (GET pedidos, PUT entregar).
- **Ruta:** `/cocina` en `App.jsx`, envuelta en `RutaProtegida rolesPermitidos={['cocina']}` y **sin** `Layout`. El login redirige al rol `cocina` a esta ruta; un `cocina` que intente entrar a `/` es devuelto a `/cocina`.
- **Estilos:** solo Tailwind, sin archivos CSS aparte.
- **Datos que muestra por pedido:** código (es el `id` del backend), celular, dirección y `saldo_pendiente` (el mismo valor en la card y en el modal; sin precios por producto), junto con el detalle de productos/combos.
- **Header:** chip con el texto "Cocina" y botón **"Cerrar sesión"** accesible sin sidebar. `cerrarSesion` borra `access_token` y `usuario` y navega a `/login` con `replace`.

### Pendiente del panel
- Que la sesión de `cocina` no se cierre por inactividad (ver sección 6).
- Confirmar la duración del JWT para turnos largos (ver sección 6).


### Aviso "por confirmar" en Ventas.jsx (admin) — resuelto
- Consume `GET /pedidos-cocina/por-confirmar` (array con `id` de la venta, `nombre_cliente`, `entregada_cocina_at` en UTC y `hora_local` ya en hora Colombia). Función `getPedidosPorConfirmar` en `api/pedidoscocinaapi.js` y store propio (`usePorConfirmarStore.js`), independiente de la lista `ventas` (que está paginada a 20 y filtrada por corte).
- **Banner** entre el header de Ventas y las KPI cards, solo si hay pedidos por confirmar: hasta 3 ítems con "Ver todos", y un botón "Confirmar" por ítem que reutiliza el modal de entrega existente (`setEntregarId`), sin tocar la lógica de `PUT /ventas/<id>` ni el descuento de inventario.
- **Chip** "En cocina · {hora_local}" junto al badge de Estado en la fila de cada venta que cocina ya entregó.
- Refresco silencioso cada ~30 s (pausado con `document.hidden`) y tras entregar o anular una venta.
- Si la petición falla (por ejemplo 403), el aviso simplemente no se muestra: no hay alertas ni cierre de sesión.
- **A decidir:** según la regla de acceso, `/pedidos-cocina/*` solo deja pasar a `cocina` y `admin`. Si el rol `cajero` también debe ver el aviso, hay que abrirle `GET /pedidos-cocina/por-confirmar` en el backend.

---

## 8. Módulos cotizados, no iniciados

Cotización enviada por **$600.000**, 3 semanas, anticipo 30%:
1. Panel de pedidos (arriba) — $150.000.
2. **Medios de pago personalizados** — $300.000. Reemplazar el `ENUM` fijo (`efectivo/transferencia/otro`) por una tabla `medios_pago` administrable (ej. "Nequi de Miguel"). Toca `ventas`/`abonos`, `compras`, `prestamos`, `pagos_prestamos`, `movimientos_caja`, y obliga a rediseñar el balance para sumar dinámicamente por cada medio configurado. Es el módulo más grande de los tres.
3. **Producción con selección de empleado** — $150.000. Pantalla tipo kiosco (sin contraseña) donde un empleado (entidad nueva, separada de `usuarios`) elige su nombre y registra lo producido. Reutiliza la lógica de bandejas/sueltas que ya existe (`_sumar_inventario`). Falta: tabla `empleados`, CRUD desde admin, la pantalla kiosco, y conectar con `auditoria` (hoy pensada para `usuarios`, no para `empleados`).

## 9. Bugs y patrones a vigilar (aprendizajes de esta conversación)

- **Endpoints con `LIMIT` fijo + filtro en frontend**: varios `getX(pagina, limite)` traían todo con un límite fijo (190-200) y filtraban en el cliente — se rompía al superar el límite. Corregido en clientes (parámetro `q` + debounce) y compras (mismo patrón). En ventas se optó por filtrar por `cliente_id` sin paginar, en vez de `q`, para el caso de "ver deudas de un cliente". **Inventario todavía tiene este problema pendiente de corregir.**
- **Cursores MySQL sin cerrar**: causó `1226 - max_user_connections exceeded`. Revisar que todo `service` cierre su cursor incluso si hay excepción (no está aplicado con `try/finally` en todos lados todavía).
- **Nombres de campo inconsistentes entre servicios de clientes**: unos devuelven `id`/`nombre`, otros (los que usan los modales de abonos y préstamos) devuelven `ID_Cliente`/`Cli_Nombre` (vía `cliente(...).toDic()`). **Nunca asumir el shape de un objeto sin confirmarlo con un dato real.**
- **`usuario_id` hardcodeado en `1`**: se fue corrigiendo módulo por módulo (ventas, compras, préstamos) reemplazándolo por el id real de `localStorage`. Revisar si queda en algún lado más.
- **`BIGINT UNSIGNED value is out of range`**: pasa cuando SQL crudo suma/resta una columna con signo (`stock_actual`) con una columna `UNSIGNED` (`cantidad`), y el resultado da negativo. MySQL promueve toda la expresión a unsigned. Corregido con `CAST(... AS SIGNED)` en `trg_produccion_insert` y `trg_venta_anular`. **Puede haber más casos sin descubrir** en cualquier trigger/SQL crudo que combine estos dos tipos.
- **Bucle de redirección + pantalla en blanco al cerrar sesión (panel de cocina):** `cerrarSesion` borraba la clave `'token'` en vez de `'access_token'`. El token seguía guardado, `Login` mandaba a `/`, y `RutaProtegida` (sin `usuario`, por tanto sin `rol`) se redirigía a sí misma en bucle, sin error en consola. **Regla:** las claves de sesión son `access_token` y `usuario`. Además, conviene que `RutaProtegida` limpie la sesión y mande a `/login` si hay token pero no hay rol.
- **401 del login vs. sesión vencida:** el interceptor de axios no debe actuar sobre el 401 de `/auth/login`, o se pierde el mensaje "Usuario o contraseña incorrectos".
- **Un 503 puntual en Render** (visto una vez, sin confirmar causa raíz) — sospecha de cold start del plan free o crash loop por conexiones agotadas. No se dio seguimiento cerrado a este incidente.

## 10. Estructura de tablas relevantes (nombres exactos usados en el código)

`cortes(id, numero, fecha_inicio, saldo_inicial, estado)` · `ventas(id, cliente_id, corte_id, usuario_id, fecha_venta, fecha_entrega, total, total_abonado, saldo_pendiente, estado, observacion, nombre_cliente, entregada_cocina_at, entregada_cocina_por)` · `venta_detalle(id, venta_id, producto_id, combo_id, nombre_producto, cantidad, precio_unitario, subtotal, es_combo, combo_productos)` · `abonos(id, venta_id, corte_id, usuario_id, monto, fecha, medio_pago, observacion)` · `inventario(id, producto_id, stock_actual, unidades_sueltas, stock_minimo, updated_at)` · `productos(id, nombre, unidades_por_bandeja, ...)` · `combo_detalle(combo_id, producto_id, cantidad_unidades)` · `compras(id, proveedor_id, corte_id, usuario_id, fecha, medio_pago, total, descripcion, eliminada)` · `movimientos_caja(id, corte_id, usuario_id, tipo, concepto, referencia_id, monto, descripcion, medio_pago)` · `prestamos(id, cliente_id, corte_id, usuario_id, monto, total_abonado, saldo_pendiente, medio_pago, medio_pago_pago, estado, observacion, fecha, fecha_pago, usuario_pago_id)` · `pagos_prestamos(id, prestamo_id, corte_id, usuario_id, monto, medio_pago, observacion, fecha)` · `usuarios(id, nombre, username, password_hash, rol, activo, created_at, updated_at)` · `auditoria(id, usuario_id, accion, tabla_afectada, registro_id, descripcion, datos_anteriores, datos_nuevos, fecha)` · `producciones(id, producto_id, cantidad, unidades_sueltas, usuario_id, fecha, observacion)`.
