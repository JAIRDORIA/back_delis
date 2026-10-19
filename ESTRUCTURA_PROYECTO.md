# SnackFlow — Estructura de carpetas y archivos

Documento de referencia rápida: qué hay en cada carpeta y de qué se encarga cada archivo.
El contexto funcional (reglas de negocio, cortes, inventario, combos, cocina, JWT…) está en
`SnackFlow_contexto (1).md`. Este archivo solo describe **el mapa del repositorio**.

## Resumen

`Delisback` es el **backend** del sistema SnackFlow (negocio Delis). Es una API REST en
**Flask 3** sobre **MySQL** (vía `Flask-MySQLdb`, SQL crudo con cursores, **sin ORM**),
autenticación con **JWT** y CORS abierto. El frontend (React + Vite) vive en otro repositorio
y consume estos endpoints; la documentación interactiva se sirve con **Swagger UI** desde el
propio backend.

Arquitectura en capas, muy consistente:

```
routes/  →  controllers/  →  services/  →  models/
(HTTP: url +   (validación y      (SQL crudo y    (clases que
 decoradores)   reglas HTTP)       transacciones)   representan filas)
```

- `routes/` expone la URL, el método HTTP y los decoradores de seguridad (`@token_requerido`, `@rol_requerido`). No tiene lógica: llama al controller.
- `controllers/` valida la entrada (paginación, formatos, 400/404/409) y arma el JSON de respuesta. Llama a uno o varios services.
- `services/` es donde está la lógica real y todo el SQL (`current_app.mysql.connection.cursor()`), incluyendo el manejo de cortes, inventario y transacciones.
- `models/` son clases simples con un `toDic()`/`to_dict()`; no tienen lógica de persistencia (el "modelo" efectivo es el SQL de los services).

---

## Raíz del proyecto

| Archivo | De qué se encarga |
| --- | --- |
| `app.py` | Punto de entrada. Crea la app Flask, carga la config, inicializa `MySQL`, `JWTManager` y `CORS`, registra el blueprint de auth (`/auth`) y llama a `cargarRuta(app)` para montar todos los blueprints. En local corre en el puerto `4000` con `debug=True`. |
| `config.py` | Clase `config` con las credenciales de MySQL leídas de variables de entorno (`.env`) vía `python-dotenv`. |
| `jwt_config.py` | Generación y verificación manual de JWT (`generar_token`, `verificar_token`) con `PyJWT`/HS256 y `EXPIRATION_HOURS` (por defecto 8 h). Es el que usan los decoradores. |
| `requirements.txt` | Dependencias: Flask, flask-cors, Flask-JWT-Extended, Flask-MySQLdb, mysqlclient, bcrypt, PyJWT, python-dotenv, gunicorn, tzdata. |
| `Procfile` | Comando de arranque en producción (Render): `web: gunicorn app:app`. |
| `swagger.json` | Especificación OpenAPI de toda la API (fuente de la documentación Swagger). |
| `.env` | Variables de entorno: `MYSQL_HOST/USER/PASSWORD/PORT/DATABASE`, `JWT_SECRET_KEY`, `RESET_MASTER_KEY`. **No se versiona** (está en `.gitignore`). |
| `.gitignore` | Ignora `__pycache__/`, `*.pyc/pyo/pyd` y `.env`. |
| `.vscode/settings.json` | Configuración del entorno de Python para VS Code. |
| `README.md` | Nota mínima del repositorio (instalar `requirements.txt`). |
| `back_delis` | Archivo vacío; probablemente marcador/placeholder, sin uso en el código. |
| `SnackFlow_contexto (1).md` | Documento de contexto técnico del proyecto (negocio, bugs, decisiones, tablas). |
| `ESTRUCTURA_PROYECTO.md` | Este documento. |

---

## `routes/` — definición de endpoints

Cada archivo crea un `Blueprint` y registra las URLs; casi todas las rutas llevan
`@token_requerido` (que además **rechaza al rol `cocina` con 403**).

| Archivo | Prefijo | Endpoints principales |
| --- | --- | --- |
| `__init__.py` | — | `cargarRuta(app)`: importa y registra **todos** los blueprints con su `url_prefix` (`/ventas`, `/cortes`, `/usuarios`, `/productos`, `/inventarios`, `/combos`, `/clientes`, `/abonos`, `/compras`, `/proveedores`, `/producciones`, `/auditoria`, `/prestamos`, `/pedidos-cocina`, `/documentacion`, `/medios-pago`). Es el índice real de la API. |
| `ventas.py` | `/ventas` | Listar, detalle (`GET/PUT /<id>/detalle`), crear (abonos iniciales validados con `resolver_medio_pago` y guardan `medio_pago_id`; el `usuario_id` sale del token, no del cuerpo), actualizar (cambia `estado`, dispara el descuento/anulación de inventario), anular (`PUT /<id>/anulacion`) y comprobante. |
| `abonos.py` | `/abonos` | Listar, registrar (valida con `resolver_medio_pago` y guarda `medio_pago_id`; el `usuario_id` sale del token, no del cuerpo), actualizar (edita `medio_pago` y `medio_pago_id` juntos), eliminar y `GET /<id>/recibo` (recibo del abono). |
| `clientes.py` | `/clientes` | CRUD de clientes más `GET /top` (clientes con más consumo). |
| `productos.py` | `/productos` | CRUD de productos más `GET /mas-vendidos`. |
| `combos.py` | `/combos` | CRUD de combos (crear/actualizar incluyen su composición `combo_detalle`). |
| `inventario.py` | `/inventarios` | Listar, registrar, actualizar stock mínimo, obtener, `GET /bajo-stock` y `PUT /<id>/cantidades` (edición manual de bandejas/unidades sueltas). |
| `compra.py` | `/compras` | CRUD de compras (asociadas a un `corte_id` y `medio_pago`; POST/PUT guardan `medio_pago_id` y el `usuario_id` sale del token, no del cuerpo). |
| `proovedores.py` | `/proveedores` | CRUD de proveedores + búsqueda por nombre y por email + listado de activos. |
| `cortes.py` | `/cortes` | `GET /` (listado), `GET /historial`, `PUT /<id>`, `POST /iniciar` (abre primer corte), `POST /cerrar` (cierre de corte) y `GET /balance` (balance del corte actual). |
| `prestamos.py` | `/prestamos` | Listar préstamos, registrar (valida medio con `resolver_medio_pago`, guarda `medio_pago_id` y valida disponible por cuenta; el `usuario_id` sale del token) y `GET/POST /<id>/abonos` (abonos parciales; el POST guarda `medio_pago_id` y toma el `usuario_id` del token). *Nota: el `GET /` tiene el `@token_requerido` comentado.* |
| `producciones.py` | `/producciones` | Listar producciones, registrar producción y obtener una. |
| `usuarios.py` | `/usuarios` y `/auth` | Define **dos** blueprints: `auth_bp` (`/auth/login`, `/auth/verificar-clave-maestra`, `/auth/recuperar-password`) y `usuarios_bp` (`/setup`, `/check-setup` y el CRUD de usuarios protegido). `auth_bp` se registra directo en `app.py`. |
| `auditoria.py` | `/auditoria` | `GET /` paginado: consulta del log de auditoría. |
| `pedidos_cocina_routes.py` | `/pedidos-cocina` | Único módulo accesible por el rol `cocina`: `GET /` (pedidos del día) y `PUT /<id>/entregar` con `@token_requerido_cocina` + `@rol_requerido(['cocina','admin'])`. Además `GET /por-confirmar` (solo `admin`/`cajero`) para el aviso del panel admin. |
| `documentacion.py` | `/documentacion` | Sirve `swagger.json` y la página HTML de Swagger UI (apoyada en `static/swagger-ui/`). Sin autenticación. |
| `medios_pago.py` | `/medios-pago` | CRUD de medios de pago: listado con filtros (`activos`, `tipo`, `asignables`), detalle, `GET /saldos` (cuentas de transferencia con saldo, filtro `?buscar=`), `GET /<id>/movimientos` (movimientos de la cuenta desde `v_movimientos_cuenta`, paginado), crear/editar (admin), cambiar estado (`PATCH /<id>/estado`, admin), eliminar (admin), `POST /<id>/retiros` (retiro de una cuenta de transferencia a ahorros) y `POST /retiros/vaciar` (vaciado de todas las cuentas de transferencia con saldo; declarado antes de `/<int:id>`). Ambos usan los mismos roles que `POST /cortes/cerrar`, es decir solo `@token_requerido`. |

---

## `controllers/` — validación HTTP y armado de respuestas

Reciben el `request`, validan parámetros y devuelven `(jsonify(...), status)`. La lógica pesada
está delegada a `services/`.

| Archivo | Responsabilidad |
| --- | --- |
| `venta_controller.py` | Ventas: listado paginado/filtrado por corte o cliente, alta, cambio de estado, anulación, comprobante y el par `cntDetalle` / `cntActualizarDetalle` (detalle de venta y edición de líneas/combos de una venta pendiente). |
| `abonos_controller.py` | Abonos a ventas: validación de monto contra `saldo_pendiente`, corte abierto, registro/edición/anulación y generación del recibo. Registro y edición validan `medio_pago`/`medio_pago_id` con `resolver_medio_pago`. |
| `corte_controller.py` | Cortes de caja: listado, apertura del primer corte, cierre, historial y `cntBalance` (balance del corte actual). |
| `inventario_controller.py` | Inventario: listado, registro por producto, stock mínimo, bajo stock y `cntActualizarCantidades` (edición manual normalizando bandejas/sueltas y dejando rastro en auditoría). |
| `productos_controller.py` | Productos: CRUD con validaciones de nombre/formato y `mas-vendidos`. |
| `combos_controller.py` | Combos: CRUD validando la composición enviada (`productos`). |
| `compra_controller.py` | Compras: CRUD, siempre asociadas a un corte (abierto o indicado). POST/PUT validan `medio_pago`/`medio_pago_id` con `resolver_medio_pago`. |
| `clientes_controller.py` | Clientes: CRUD con validación de email/identificación y `top`. |
| `proveedor_controller.py` | Proveedores: CRUD, búsquedas y validación de duplicados (nombre/email). |
| `prestamos_controller.py` | Préstamos a clientes: alta (valida `medio_pago`/`medio_pago_id` con `resolver_medio_pago`; disponible de efectivo por `movimientos_caja` y de transferencia por `v_saldos_cuenta`), abonos parciales (valida `medio_pago`/`medio_pago_id` con `resolver_medio_pago`) y consulta de pagos. |
| `producciones_controller.py` | Producciones: registro (suma inventario vía service) y consulta. |
| `abonos` / `auditoria_controller.py` | Auditoría: `cntListado` con paginación (límite máximo 100). |
| `usuarios_controller.py` | Autenticación y usuarios: `login_post` (verifica bcrypt y **genera el JWT**), alta/baja/edición/listado de usuarios, `cntPrimerAdmin` (`/setup`), clave maestra y recuperación de contraseña. Contiene el hash bcrypt (`hashear_password`). |
| `pedidos_cocina_controller.py` | Panel de cocina: `cntListarPedidosCocina`, `cntEntregarPedido` (marca `entregada_cocina_at`, con control de doble marcado y 409 por condición de carrera) y `cntPedidosPorConfirmar`. |
| `medios_pago_controller.py` | Medios de pago: listado con filtros, detalle, saldos (`cntSaldos`), movimientos de cuenta (`cntMovimientos`, paginado con filtros `desde`/`hasta`), alta (tipo siempre `transferencia`), edición, cambio de estado y eliminación con validaciones (409 duplicado, 409 si tiene movimientos asociados) y registro en auditoría. Incluye `cntRetiro` (`POST /<id>/retiros`): valida monto (> 0, máx. 2 decimales) y descripción (máx. 255), usa el usuario del token y delega la transacción al service. También `cntVaciar` (`POST /retiros/vaciar`): body opcional con descripción (default `Retiro a ahorros (cierre de corte)`) y usuario del token. |

---

## `services/` — lógica de negocio + SQL

Aquí vive todo el SQL crudo y las reglas del negocio (cortes, inventario, combos, caja).

| Archivo | Responsabilidad |
| --- | --- |
| `ventas_services.py` | El más grande (≈700 líneas) y el núcleo del sistema: listado de ventas, registro con detalle (abonos iniciales guardan `medio_pago_id`), cálculo de saldos, estados, comprobante, **anulación con reversión de inventario** y todo el manejo de combos: `descontar_inventario_venta`, `descontar_inventario_combo`, `descontar_inventario_combo_personalizado`, `revertir_inventario_detalle`, `_sumar_inventario` (fórmula bandejas/unidades sueltas) y `obtener_venta_detalle` / `actualizar_detalle_venta`. El detalle devuelve en cada abono `medio_pago_id` y `medio_pago_nombre`. |
| `cortes_services.py` | Núcleo de la lógica de caja: `registrar_primer_corte`, `cerrar_corte`, `obtener_corte_abierto`, `obtener_corte_futuro`, `listar_historial_cortes` y `balance_corte_actual` (ventas, compras, dinero en caja, efectivo/transferencia, saldos pendientes, y campos nuevos `transferencia_cuentas`, `transferencia_adelantada`, `efectivo_caja`, `dinero_caja_total`). |
| `abono_services.py` | Abonos a ventas: listado, registro (guarda `medio_pago_id` además de `medio_pago`; inserta también en `movimientos_caja`), `generar_recibo` (arma el recibo), actualización (actualiza `medio_pago` y `medio_pago_id` en la misma sentencia) y eliminación. Listado/obtener/recibo devuelven `medio_pago_id` y `medio_pago_nombre` vía LEFT JOIN a `medios_pago`. |
| `compra_services.py` | Compras: listado con búsqueda, obtener, registrar/actualizar (impactan caja y corte; guardan `medio_pago_id`) y eliminar (baja lógica `eliminada`). Listado/obtener devuelven `medio_pago_id` y `medio_pago_nombre` vía LEFT JOIN a `medios_pago`. |
| `inventario_services.py` | Inventario: listado, registro por producto, stock mínimo, `productos_bajo_stock`, y los helpers de unidad: `obtener_unidades_por_bandeja`, `normalizar_bandejas_sueltas` y `actualizar_cantidades`. |
| `productos_services.py` | Productos: listado, alta, actualización, borrado (lógico), `existe_producto`/`existe_nombre` y `productos_mas_vendidos`. |
| `combos_services.py` | Combos: listado, alta/actualización con su `combo_detalle`, borrado y `obtener_combo_id`. |
| `clientes_services.py` | Clientes: listado con búsqueda, alta, actualización, borrado lógico, validaciones de email/teléfono/identificación y `clientes_top`. |
| `proveedor_services.py` | Proveedores: CRUD, búsquedas y validaciones de formato/duplicados. |
| `prestamos_services.py` | Préstamos v2: `registrar` (egreso en caja; guarda `medio_pago_id` en `prestamos` y `movimientos_caja`), `obtener_saldo_cuenta` (saldo por cuenta desde `v_saldos_cuenta`), `abonar_prestamo` (ingreso en caja + fila en `pagos_prestamos`; guarda `medio_pago_id` y `medio_pago_pago_id`), listados, `obtener_prestamo` y `obtener_disponible_caja` (caja disponible por corte y medio de pago). |
| `producciones_services.py` | Producciones: registro (suma al inventario) y consulta. |
| `pedidos_cocina_service.py` | Panel de cocina: `pedidos_del_dia` (trae en una sola respuesta los pedidos pendientes del día en hora Colombia, con detalle de productos/combos, celular, dirección y saldo pendiente), `estado_para_cocina`, `marcar_entregado_cocina` y `entregadas_en_cocina_por_confirmar`. Usa `zoneinfo` para el rango del día en `America/Bogota`. |
| `auditoria_services.py` | Lectura paginada del log de auditoría con JOIN a usuarios. |
| `medios_pago_services.py` | Medios de pago: listado/detalle (filtro `asignables`), `saldos_transferencias` (vista `v_saldos_cuenta`), `movimientos_cuenta` (vista `v_movimientos_cuenta`, paginado y con filtro de fechas), `resolver_medio_pago` (validación reutilizable con excepción `MedioPagoInvalido`), alta (tipo fijo `transferencia`), edición (sin cambiar tipo ni nombre de filas de sistema), cambio de estado (no desactiva `efectivo`), eliminación con chequeo de referencias y auditoría de todas las escrituras. `retirar_cuenta` registra un retiro en `retiros_cuentas` con `SELECT ... FOR UPDATE` sobre la cuenta, saldo validado contra `v_saldos_cuenta`, corte abierto y auditoría en la misma transacción. `vaciar_cuentas_transferencia` hace lo mismo para todas las cuentas de transferencia no de sistema con saldo > 0, en una sola transacción. |
| `usuarios_servicies.py` | Usuarios y sesión: `login` (compara bcrypt), CRUD de usuarios, `existe_admin`, clave maestra (`verificar_clave_maestra`, `cambiar_password_maestra`) y `obtener_usuario_por_username`. *(El nombre del archivo está escrito con la errata "servicies"; se importa así en todo el proyecto.)* |

---

## `models/` — clases de dominio

Clases planas que representan una fila de la tabla, con un método `toDic()`/`to_dict()` para
serializar. No contienen SQL.

| Archivo | Clase |
| --- | --- |
| `venta_model.py` | `Ventas` (incluye `nombre_cliente` y `corte_numero`, que vienen de JOINs). |
| `abonos_model.py` | `Abono`. |
| `compra_model.py` | `compra` (incluye `medio_pago_id` y `medio_pago_nombre`). |
| `corte_model.py` | `cortes` (incluye `saldo_inicial`). |
| `inventario_model.py` | `inventarios` (`stock_actual`, `unidades_sueltas`, `stock_minimo`). |
| `productos_model.py` | `productos` (incluye `unidades_por_bandeja`). |
| `combos_model.py` | `combos` (precio frito/congelado). |
| `cliente_model.py` | `cliente` — **ojo**: expone campos con nombres distintos (`ID_Cliente`, `Cli_Nombre`, …), a diferencia del resto. |
| `proveedor_model.py` | `proveedores`. |
| `producciones_model.py` | `producciones`. |
| `usuarios_model.py` | `usuarios` (rol, `password_hash`, activo). |
| `medios_pago_model.py` | `medios_pago` (`nombre`, `tipo`, `titular`, `saldo_inicial`, `activo`, `es_sistema`, `orden`). |

---

## `utils/` — utilidades transversales

| Archivo | De qué se encarga |
| --- | --- |
| `decorators.py` | Seguridad de endpoints. `token_requerido` valida el `Bearer` y **rechaza a `cocina` (403)**; `token_requerido_cocina` permite cualquier rol; `rol_requerido([...])` restringe por rol. Deja el payload en `g.usuario` (`id`, `username`, `rol`, `nombre`). Es la pieza que cierra todo SnackFlow al rol de cocina salvo `/pedidos-cocina/*`. |

---

## `static/` — recursos servidos por Flask

| Ruta | De qué se encarga |
| --- | --- |
| `static/swagger-ui/` | Copia local de Swagger UI (JS, CSS, favicons) usada por `routes/documentacion.py` para renderizar la documentación de la API en `/documentacion/` sin depender de un CDN. |

---

## Archivos y carpetas generados (no versionados)

| Elemento | Nota |
| --- | --- |
| `__pycache__/` | Bytecode de Python; ignorado por git. |
| `.git/` | Metadatos del repositorio. |
| `.env` | Credenciales locales; ignorado por git. |

---

## Notas rápidas de arquitectura

- **Sin ORM**: todo el SQL está en `services/`, con cursores de `Flask-MySQLdb` (`current_app.mysql.connection.cursor()`).
- **Seguridad centralizada**: los decoradores de `utils/decorators.py` son la única puerta; por defecto todo queda cerrado a `cocina` y solo `/pedidos-cocina/*` la abre explícitamente.
- **Punto de entrada único**: añadir un módulo nuevo implica crear `routes/x.py`, `controllers/x_controller.py`, `services/x_services.py` (+ `models/`) y registrarlo en `routes/__init__.py`.
- **Cocina separada del admin**: la lógica contable (descuento de inventario, cambio de estado de venta) sigue ocurriendo solo cuando el **admin** confirma la entrega en `/ventas`; cocina únicamente deja la marca `entregada_cocina_at`.
- **Erratas heredadas** a tener presentes: `usuarios_servicies.py` (servicies) y `routes/proovedores.py` (proovedores).
