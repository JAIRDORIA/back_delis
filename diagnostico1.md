# Diagnóstico: uso de `medio_pago` en el backend

- **Tipo:** diagnóstico de solo lectura (no se modificó ningún archivo de código).
- **Fecha:** 2026-10-13
- **Rama / commit:** `feature/cuentas` → `e84296a`
- **Objetivo:** inventariar todos los usos de `medio_pago`, `medio_pago_pago`, `efectivo`, `transferencia` y `otro` antes de reemplazar el medio fijo por una tabla `medios_pago`.

Equivalencias buscadas: `medio_pago`, `medio_pago_pago`, `efectivo`, `transferencia`, `otro` (como valor de medio de pago).

---

# 1. Uso de `medio_pago` por archivo

## controllers/abonos_controller.py
| Línea | Función | Qué hace con el medio de pago |
|---|---|---|
| 28-29 | `cntregistrar` | `medio_pago` en la lista de campos requeridos (`POST /abonos/`). |
| 44 | `cntregistrar` | Lee `request.json["medio_pago"]`. |
| 47-49 | `cntregistrar` | **Validación**: lista blanca `["efectivo","transferencia","otro"]`. |
| 86 | `cntregistrar` | Lo pasa a `abono_services.registro(...)`. |
| 107 | `cntActualizar` | `medio_pago` requerido (`PUT /abonos/{id}`). |
| 119 | `cntActualizar` | Lee el valor. |
| 122-124 | `cntActualizar` | **Validación**: misma lista `["efectivo","transferencia","otro"]`. |
| 153 | `cntActualizar` | Lo pasa a `actualizar_abono(...)`. |
| 21, 99 | `cntListado`, `cntGenerarRecibo` | Solo se devuelve dentro del JSON (vía modelo / recibo). |

## controllers/compra_controller.py
| Línea | Función | Qué hace |
|---|---|---|
| 58 | `cntRegistroCompra` | `request.json.get('medio_pago', 'efectivo')` → **opcional, default `efectivo`, SIN validación**. |
| 74 | `cntRegistroCompra` | Lo pasa a `registro_compra(...)`. |
| 86 | `cntActualizarCompra` | `medio_pago` requerido (`PUT /compras/{id}`). |
| 94 | `cntActualizarCompra` | Lee el valor, **sin validación de lista blanca**. |
| 109 | `cntActualizarCompra` | Lo pasa a `actualizar_compra(...)`. |
| 8, 36 | `cntListadoCompra`, `cntObtenerCompra` | Solo se devuelve en el JSON (y ver "sorpresas" más abajo). |

## controllers/prestamos_controller.py
| Línea | Función | Qué hace |
|---|---|---|
| 39, 51 | `cntRegistrarPrestamo` | Requerido y leído (`POST /prestamos/`). |
| 54-56 | `cntRegistrarPrestamo` | **Validación**: `["efectivo","transferencia"]` ← **no incluye `otro`**. |
| 74-81 | `cntRegistrarPrestamo` | Se usa para `obtener_disponible_caja(corte_id, medio_pago)` y el mensaje de saldo insuficiente. |
| 83 | `cntRegistrarPrestamo` | Pasa a `registrar(...)`. |
| 97, 108 | `cntAbonarPrestamo` | Requerido y leído (`POST /prestamos/{id}/abonos`). |
| 111-113 | `cntAbonarPrestamo` | **Validación**: `["efectivo","transferencia"]`. |
| 141 | `cntAbonarPrestamo` | Pasa a `abonar_prestamo(...)`. |
| 20, 31 | `cntListarPrestamos`, `cntListarPagosPrestamo` | Solo se devuelve en el JSON. |

## controllers/venta_controller.py
| Línea | Función | Qué hace |
|---|---|---|
| 13 | (constante) | `TIPOS_PAGO_VALIDOS = ["efectivo","transferencia","otro","deben","error"]` (valores del **filtro** de listado). |
| 56 | `cntListado` | Valida el query param `tipos_pago` contra esa lista. |
| 227-228 | `cntregistrar` | Exige `medio_pago` en cada elemento de `abonos_iniciales`. |
| 229-231 | `cntregistrar` | **Validación**: `["efectivo","transferencia","otro"]`. |
| 232-236 | `cntregistrar` | Rama legacy `abono_inicial` (singular): **NO valida `medio_pago`** (el default lo pone el service). |

## services/ventas_services.py
| Línea | Función | Qué hace |
|---|---|---|
| 14 | (constante) | `MEDIOS_PAGO = ("efectivo","transferencia","otro")`. |
| 76-82 | `listado_ventas` | Filtro `tipos_pago`: por cada medio genera `EXISTS (... ab.medio_pago = %s)`. |
| 83-89 | `listado_ventas` | `'deben'` → `saldo_pendiente > 0`; `'error'` → tolerancia aritmética (pseudo-valores, no son medios reales). |
| 233 | `obtener_venta_detalle` | `SELECT ... a.medio_pago ...` de `abonos`. |
| 285 | `obtener_venta_detalle` | Lo devuelve en el JSON `abonos[]`. |
| 446-457 | `registro` | `INSERT INTO abonos (..., medio_pago)` para `abonos_iniciales`, con default `abono.get("medio_pago","efectivo")` (456). |

## services/abono_services.py
| Línea | Función | Qué hace |
|---|---|---|
| 14, 38 | `listado_abonos` | SELECT + devuelve en JSON. |
| 56-60 | `registro` | `INSERT INTO abonos (..., medio_pago)`. |
| 70, 107 | `generar_recibo` | SELECT y **el recibo devuelve `medio_pago`**. |
| 119, 139 | `obtener_abono` | SELECT + devuelve. |
| 152-159 | `actualizar_abono` | `UPDATE abonos SET ... medio_pago = %s` (**se puede cambiar el medio de un abono ya registrado**). |
| 174 | `eliminar_abono` | DELETE; no toca medio de pago. |

## services/compra_services.py
| Línea | Función | Qué hace |
|---|---|---|
| 32 | `listado_compra` | `SELECT ... c.medio_pago ...`. |
| 66-72 | `obtener_compra` | `SELECT` **NO incluye** `medio_pago` (ver sorpresas). |
| 101-103 | `registro_compra` | `INSERT INTO compras (..., medio_pago, ...)`. |
| 131-137 | `actualizar_compra` | `UPDATE compras SET ... medio_pago = %s ...`. |
| 150-151 | `eliminar_compra` | Soft-delete; no toca medio de pago. |

## services/cortes_services.py
| Línea | Función | Qué hace |
|---|---|---|
| 277 | `balance_corte_actual` | Filtro `WHERE a.medio_pago = 'efectivo'` sobre `abonos` → `total_efectivo`. |
| 286 | `balance_corte_actual` | Filtro `compras.medio_pago = 'efectivo'` → `compras_efectivo`. |
| 294 | `balance_corte_actual` | Filtro `compras.medio_pago = 'transferencia'` → `compras_transferencia`. |
| 304 | `balance_corte_actual` | Filtro `abonos.medio_pago = 'transferencia'` → `total_transferencia`. |
| 359 | `balance_corte_actual` | Filtro `movimientos_caja.medio_pago = 'efectivo'` (conceptos `prestamo`/`pago_prestamo`) → `neto_prestamos_efectivo`. |
| 370 | `balance_corte_actual` | Ídem con `'transferencia'` → `neto_prestamos_transferencia`. |
| 387-388 | `balance_corte_actual` | Devuelve `total_efectivo` y `total_transferencia` (claves fijas). |
| 392-416 | `ingresos_ventas_corte_abierto` | Suma `abonos.monto` **sin discriminar por medio_pago**. |

## services/prestamos_services.py
| Línea | Función | Qué hace |
|---|---|---|
| 13-21 | `obtener_disponible_caja` | Filtro `movimientos_caja.medio_pago = %s`. |
| 40-41 | `obtener_prestamo` | Lee `p.medio_pago` y `p.medio_pago_pago`. |
| 56-57 | `listar_prestamos` | Ídem. |
| 77, 86 | `listar_pagos_prestamo` | Lee `pagos_prestamos.medio_pago`. |
| 95-97 | `registrar` | `INSERT INTO prestamos (..., medio_pago, ...)`. |
| 101-107 | `registrar` | `INSERT INTO movimientos_caja (..., medio_pago)` (concepto `prestamo`, tipo `egreso`). |
| 127-130 | `abonar_prestamo` | `INSERT INTO pagos_prestamos (..., medio_pago, ...)`. |
| 133-140 | `abonar_prestamo` | `INSERT INTO movimientos_caja (..., medio_pago)` (concepto `pago_prestamo`, tipo `ingreso`). |
| 148-153 | `abonar_prestamo` | `UPDATE prestamos ... medio_pago_pago = %s` (medio del abono que dejó el préstamo `pagado`). |
| 176, 182 | `_row_a_dict` | Devuelve `medio_pago` y `medio_pago_pago` en el JSON. |

## models/
- **models/abonos_model.py**: atributo `medio_pago` (L4, L12) y en `to_dict()` (L26).
- **models/compra_model.py**: atributo `medio_pago` (L2, L10) y en `toDic()` (L19).

---

# 2. Todas las validaciones que restringen valores permitidos

| Ubicación | Lista permitida | Endpoint |
|---|---|---|
| `controllers/abonos_controller.py:47` | `["efectivo","transferencia","otro"]` | `POST /abonos/` |
| `controllers/abonos_controller.py:122` | `["efectivo","transferencia","otro"]` | `PUT /abonos/{id}` |
| `controllers/prestamos_controller.py:54` | `["efectivo","transferencia"]` | `POST /prestamos/` |
| `controllers/prestamos_controller.py:111` | `["efectivo","transferencia"]` | `POST /prestamos/{prestamo_id}/abonos` |
| `controllers/venta_controller.py:229` | `["efectivo","transferencia","otro"]` | `POST /ventas/` → `abonos_iniciales[]` |
| `controllers/venta_controller.py:13` | `["efectivo","transferencia","otro","deben","error"]` | Filtro `GET /ventas/?tipos_pago=` (lista blanca de filtro, no de almacenamiento) |
| `services/ventas_services.py:14` | `("efectivo","transferencia","otro")` | Constante `MEDIOS_PAGO`, usada en el filtro del listado (L76) |

**Sin validación (relevante):** `compra_controller.py:58` (default `efectivo`) y `compra_controller.py:94` aceptan **cualquier** cadena; dependen del `ENUM` de la BD. La ruta legacy `abono_inicial` (`venta_controller.py:232-236`) tampoco valida.

---

# 3. SQL que suma/agrupa por `medio_pago`

> No existe ningún `GROUP BY ... medio_pago`. Son filtros `WHERE medio_pago = '<literal>'` y sumas condicionales. Tablas leídas: `abonos`, `compras`, `movimientos_caja`. **No hay suma/agrupación por `pagos_prestamos.medio_pago` ni por `prestamos.medio_pago`.**

### `balance_corte_actual` — `services/cortes_services.py` (completas, tal como están)

Lectura de `abonos` (efectivo, L272-279):
```sql
SELECT COALESCE(SUM(a.monto), 0)
    FROM abonos a
    JOIN ventas v ON v.id = a.venta_id
    WHERE a.corte_id = %s
    AND a.medio_pago = 'efectivo'
    AND v.estado IN ('pendiente', 'entregada')
```

Lectura de `compras` (efectivo, L283-287):
```sql
SELECT COALESCE(SUM(total), 0)
FROM compras
WHERE corte_id = %s AND medio_pago = 'efectivo' AND eliminada = 0
```

Lectura de `compras` (transferencia, L291-295):
```sql
SELECT COALESCE(SUM(total), 0)
FROM compras
WHERE corte_id = %s AND medio_pago = 'transferencia' AND eliminada = 0
```

Lectura de `abonos` (transferencia, L299-306):
```sql
SELECT COALESCE(SUM(a.monto), 0)
    FROM abonos a
    JOIN ventas v ON v.id = a.venta_id
    WHERE a.corte_id = %s
    AND a.medio_pago = 'transferencia'
    AND v.estado IN ('pendiente', 'entregada')
```

Lectura de `movimientos_caja` (neto préstamos efectivo, L354-361):
```sql
SELECT
    COALESCE(SUM(CASE WHEN concepto = 'prestamo'      THEN monto ELSE 0 END), 0) -
    COALESCE(SUM(CASE WHEN concepto = 'pago_prestamo' THEN monto ELSE 0 END), 0)
FROM movimientos_caja
WHERE corte_id = %s AND medio_pago = 'efectivo'
  AND concepto IN ('prestamo', 'pago_prestamo')
```

Lectura de `movimientos_caja` (neto préstamos transferencia, L365-372):
```sql
SELECT
    COALESCE(SUM(CASE WHEN concepto = 'prestamo'      THEN monto ELSE 0 END), 0) -
    COALESCE(SUM(CASE WHEN concepto = 'pago_prestamo' THEN monto ELSE 0 END), 0)
FROM movimientos_caja
WHERE corte_id = %s AND medio_pago = 'transferencia'
  AND concepto IN ('prestamo', 'pago_prestamo')
```

Resultado (L387-388): `total_efectivo = total_efectivo - compras_efectivo - neto_prestamos_efectivo` y `total_transferencia = total_transferencia - compras_transferencia - neto_prestamos_transferencia`. (`'otro'` nunca entra al balance.)

### `obtener_disponible_caja` — `services/prestamos_services.py` (completa, L15-21)
```sql
SELECT
    COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) -
    COALESCE(SUM(CASE WHEN tipo = 'egreso'  THEN monto ELSE 0 END), 0)
FROM movimientos_caja
WHERE corte_id = %s AND medio_pago = %s
```
(los parámetros son `(corte_id, medio_pago)`).

---

# 4. INSERT directos a `movimientos_caja` desde Python

Solo en **`services/prestamos_services.py`** (no hay archivos `.sql` ni trigger versionado en el repo):

1. **`registrar` (L100-107)** — al crear préstamo: `tipo='egreso'`, `concepto='prestamo'`, `medio_pago=<medio del préstamo>`.
2. **`abonar_prestamo` (L133-140)** — al abonar préstamo: `tipo='ingreso'`, `concepto='pago_prestamo'`, `medio_pago=<medio del abono>`.

Los **abonos de ventas** (`abono_services.registro` y `ventas_services.registro`) NO insertan en `movimientos_caja` en Python. La inserción aquí la hace un **trigger de BD que no está en el repo** (el `AGENTS.md` y `ESTRUCTURA_PROYECTO.md:108` lo dan por hecho; el código no lo muestra → no verificable desde el código).

---

# 5. `swagger.json` — campos que documentan `medio_pago` y sus enums

| Líneas | Endpoint / sección | Tipo | Descripción/enum |
|---|---|---|---|
| 2288-2290 | `GET /ventas/` → query `tipos_pago` | entrada | `example: efectivo`, `description: "efectivo\|transferencia\|otro\|deben\|error (CSV)"` |
| 2471-2473 | `POST /ventas/` → body `abonos_iniciales[].medio_pago` | entrada | `example: efectivo` (sin description/enum) |
| 2790-2792 | `GET /ventas/{id}/detalle` → `abonos[].medio_pago` | salida | `example: efectivo` |
| 2973-2975 | `GET /abonos/` (listado) → `medio_pago` | salida | `example: efectivo` |
| 3049-3065 | `POST /abonos/` → body `medio_pago` | entrada, **required** | `description: "efectivo\|transferencia\|otro"` |
| 3127-3139 | `PUT /abonos/{id}` → body `medio_pago` | entrada, **required** | `example: efectivo` (sin description) |
| 3250-3252 | `GET /abonos/{id}/recibo` → `medio_pago` | salida | `example: efectivo` |
| 3352-3354 | `GET /prestamos/` → `medio_pago` | salida | `example: efectivo` |
| 3411-3425 | `POST /prestamos/` → body `medio_pago` | entrada, **required** | `description: "efectivo\|transferencia"` |
| 3503-3505 | `GET /prestamos/{prestamo_id}/abonos` → `medio_pago` | salida | `example: efectivo` |
| 3568-3581 | `POST /prestamos/{prestamo_id}/abonos` → body `medio_pago` | entrada, **required** | `description: "efectivo\|transferencia"` |
| 3822-3826 | `GET /cortes/balance` → `total_efectivo`, `total_transferencia` | salida | claves fijas por medio (sin `total_otro`) |
| 5401-5403 | `GET /compras/` → `medio_pago` | salida | `example: efectivo` |
| 5469-5472 | `POST /compras/` → body `medio_pago` | entrada, **opcional** | `description: "Opcional; por defecto efectivo"` |
| 5563-5565 | `GET /compras/{id}` → `medio_pago` | salida | `example: efectivo` |
| 5632-5649 | `PUT /compras/{id}` → body `medio_pago` | entrada, **required** | sin description/enum |

No encontré `enum` real de JSON Schema en ningún punto: los valores se documentan como texto libre en `description`/`example`.

---

# 6. Otras cosas que pueden sorprender

1. **`GET /compras/{id}` no selecciona `medio_pago` y desalinea los argumentos del modelo.** `compra_services.obtener_compra` (L66-72) hace `SELECT c.id, c.proveedor_id, p.nombre, c.corte_id, c.usuario_id, c.fecha, c.total, c.descripcion` (8 columnas, sin `medio_pago`), pero en L75 construye `compra(fila[0], fila[1], fila[3], fila[4], fila[5], fila[6], fila[7])` contra `__init__(self, id, proveedor_id, corte_id, usuario_id, fecha, medio_pago, total, descripcion=None)`. Resultado: `medio_pago = fila[6]` (el **total**), `total = fila[7]` (la **descripción**) y `descripcion = None`. El listado (`listado_compra`) sí lo hace bien. Es una inconsistencia latente que tocará el módulo.
2. **`compras.medio_pago` no tiene lista blanca en código**: acepta cualquier texto (default `efectivo`); la única restricción es el `ENUM` de la columna. Distinto de abonos/prestamos que sí validan en Python.
3. **Prestamos usan una lista más angosta** (`efectivo|transferencia`, sin `otro`) que abonos/ventas (`...|otro`). Inconsistencia entre módulos.
4. **`abonos.medio_pago` es editable** con `PUT /abonos/{id}` (`actualizar_abono`, L152-159) pero el `movimientos_caja` ya generado (por trigger) **no se recalcula**: puede quedar el medio viejo en el libro mayor. Relevante al migrar a cuentas.
5. **El recibo de abono sí imprime el medio de pago** (`generar_recibo`, L70/L107), pero **el comprobante de venta NO** (`ventas_services.generar_comprobante`, L484-553 no incluye `medio_pago` ni abonos).
6. **`balance_corte_actual` sólo conoce dos medios** (`total_efectivo`/`total_transferencia`); `otro` se ignora por completo en las KPI. Además, `total_efectivo`/`total_transferencia` se calculan desde `abonos`/`compras` y se les suma a mano el neto de `movimientos_caja` de préstamos.
7. **Dos fuentes de verdad para el medio de pago**: `abonos.medio_pago` (y `pagos_prestamos.medio_pago`) por un lado, y `movimientos_caja.medio_pago` por otro. `compras` **no inserta** en `movimientos_caja` (se lee aparte).
8. **`prestamos.medio_pago_pago`** guarda solo el medio del **último** abono que completó el pago (L148-153); si hubo abonos parciales con medios distintos, se pierde el detalle salvo en `pagos_prestamos`.
9. **`ingresos_ventas_corte_abierto`** (L392-416) suma todos los abonos del corte abierto sin separar por medio.
10. **Valores pseudo-medio en el filtro de ventas**: `deben` y `error` (venta_controller L13) no son medios de pago almacenados; son criterios derivados (`saldo_pendiente>0` y descuadre aritmético).
11. **Documentación ya anticipa esta tarea**: `SnackFlow_contexto (1).md:121` describe exactamente el reemplazo del `ENUM` fijo por la tabla `medios_pago` y lista las tablas afectadas (`ventas`/`abonos`, `compras`, `prestamos`, `pagos_prestamos`, `movimientos_caja`). `ESTRUCTURA_PROYECTO.md:64` y `:107` también mencionan `medio_pago` de compras y el cálculo efectivo/transferencia.

---

**Archivos modificados:** ninguno (diagnóstico de solo lectura).

**Supuestos:**
- Los números de línea corresponden al commit `e84296a` (HEAD de `feature/cuentas`).
- Los INSERT a `movimientos_caja` de los **abonos de ventas** los asumo hechos por un **trigger de BD**, porque no existen en el código ni en archivos `.sql` del repo (no verificable aquí); la documentación los da por existentes.
- `GET /compras/{id}` lo marco como bug probable según lectura estática del código; no lo confirmé contra un dato real de BD.

---

**Actualización 2026-10-18:** se agregó `POST /medios-pago/<id>/retiros` (`cntRetiro` en `controllers/medios_pago_controller.py` y `retirar_cuenta` en `services/medios_pago_services.py`). Los retiros se insertan en `retiros_cuentas` y `v_movimientos_cuenta` ya los expone como `egreso`/`retiro`, por lo que `v_saldos_cuenta` los descuenta. No se modificó el esquema ni la vista. También se agregó `POST /medios-pago/retiros/vaciar` (`cntVaciar` y `vaciar_cuentas_transferencia`), que retira el saldo completo de todas las cuentas de transferencia no de sistema con saldo > 0 en una sola transacción.

---

**Actualización 2026-11-03 (paginación y búsqueda en listados):** se paginó y/o se agregó búsqueda `q` en cuatro listados, sin tocar lógica de negocio ni esquema.
- `GET /prestamos/`: ahora devuelve `{datos, total, pagina, limite, total_paginas, resumen}` (antes era un array). Params: `pagina` (≥1), `limite` (1–100, def. 20), `q` (cliente, observación o id), `estado` (`pendiente|pagado`, validado), `cliente_id`. `resumen` (`resumen_prestamos()` en `services/prestamos_services.py`) trae los totales globales `total_prestado`/`total_abonado`/`saldo_por_cobrar`/`pendientes`/`pagados`, independientes de filtros y paginación.
- `GET /proveedores/`: mantiene `exito` y `datos`; `total` ahora es el total real e incluye `pagina`, `limite`, `total_paginas`. Params: `pagina`, `limite` (1–100), `q` (nombre, email, teléfono). `/activos` y `/buscar/*` no cambian.
- `GET /inventarios/`: se agrega `q` (nombre de producto) y tope `limite` ≤ 200. Mismo shape.
- `GET /productos/`: se agrega `q` (nombre o descripción) y tope `limite` ≤ 200. Mismo shape.
- Todos con `ORDER BY` estable y SQL parametrizado. Queda pendiente: clientes, combos, producciones, usuarios, abonos, auditoría, cortes y `produccion-empleados/pendientes` (ver diagnóstico anterior). `swagger.json` no se actualizó.

---

**Actualización 2026-11-06 (valor del inventario):** se agregó `GET /inventarios/valor` (`cntValorInventario` y `valor_inventario`). Solo lectura, sin cambios de esquema. Respuesta `{valor_detal, valor_mayor}`; usa bandejas completas de productos activos, ignora sueltas y stock negativo. `swagger.json` no se actualizó.

**Actualización 2026-11-06 (compras):** `GET /compras/` amplía `q` (descripción, proveedor, id) y agrega `resumen` global por corte (`cantidad_compras`, `total_gastado`). Sin cambios de esquema. `swagger.json` no se actualizó.

**Actualización 2026-10-21 (pool de conexiones):**

- **Problema:** el plan free de Clever Cloud limita a **5 conexiones por usuario** (`@@max_user_connections = 5`, medido). El backend abría 1 conexión MySQL por request (Flask-MySQLdb sin pool), así que los picos de requests simultáneos (ej. módulo de cuentas: POST + recargas en paralelo) agotaban el límite con `1226`.
- **Solución aplicada:** pool por proceso en `utils/db.py` (`PoolMySQL` + `_adquirir` + `_liberar` + `init_pool`) y activación condicional en `app.py`.
  - Env: `DB_POOL_SIZE=2` (conexiones por proceso), `DB_POOL_TIMEOUT=10`, `DB_POOL_ENABLED=1` (default; `0` vuelve al comportamiento original).
  - Los services/controllers no cambiaron para el pool: `current_app.mysql.connection` y los `commit()/rollback()` siguen igual (el proxy presta la conexión).
  - La conexión se guarda en `g._pool_conn` (no en `g.mysql_db`) para que el teardown de Flask-MySQLdb no la cierre; `_liberar` hace `rollback()` y devuelve la conexión al pool.
- **Verificado:** compilación/import sin conexión y smoke test con contexto de aplicación: 2 requests reutilizan 1 conexión (`SELECT 1`/`SELECT 2`), `conexiones_vivas = 1` y la conexión vuelve a la cola.
- **Rollback:** poner `DB_POOL_ENABLED=0` y redeployar (sin revertir código).
- **Pendiente en Render:** revisar `WEB_CONCURRENCY` (gunicorn) y confirmar que el usuario nunca supera `workers × DB_POOL_SIZE` conexiones.

---

**Actualización 2026-11-09 (ventas por día de la semana):** se agregó `GET /ventas/por-dia-semana?semanas=N` (`cntVentasPorDiaSemana` y `ventas_por_dia_semana`). `semanas` 1–8, def. 3 (fuera de rango = 400). Suma `ventas.total` por día de la semana (Lun..Dom) agrupando los homólogos de los últimos 7×N días corridos (incluye hoy, hora Colombia), por `fecha_entrega` y estados `pendiente`/`entregada`. Respuesta `{semanas, desde, hasta, dias:[{dia,nombre,total,cantidad}] (siempre 7), mejor_dia}`. Sin cambios de esquema. `swagger.json` no se actualizó.

**Actualización 2026-11-09 (swagger):** `swagger.json` sincronizado. Nuevas rutas: `GET /inventarios/valor`, `GET /ventas/por-dia-semana`, `POST /medios-pago/{id}/retiros`, `POST /medios-pago/retiros/vaciar`. Contratos actualizados: `GET /prestamos/` (objeto paginado con `resumen`, params `pagina`/`limite`/`q`/`cliente_id`), `GET /proveedores/` (paginado con `q`), `GET /inventarios/` y `GET /productos/` (`q`, `limite` ≤ 200) y `GET /compras/` (`q` ampliado y `resumen`). Sin cambios de código.

---

**Actualización 2026-11-10 (diagnóstico: gráfica "Ventas del corte"):** diagnóstico de solo lectura, sin cambios de código ni de esquema. Pregunta: ¿el frontend ya tiene los datos para la gráfica de línea (puntos por fecha 5→11 nov, tooltip por día, total `$2,48 M`, toggle "Este corte"/"30 días")?

- **Veredicto: no.** No existe endpoint de serie por fecha. Lo único más cercano es `GET /ventas/por-dia-semana`, que agrupa por **día de la semana** (Lun..Dom sumando N semanas), no por fecha, y no acepta `corte_id`; `semanas` es entero 1–8, así que "30 días" no encaja.
- **Total de la pestaña "Este corte":** disponible con `GET /cortes/balance` → `total_ventas` (corte abierto). El front ya lo pinta como KPI "Ventas del corte" en `Balance.jsx` (`useBalanceStore.balance`).
- **Serie diaria:** solo se podría derivar en el cliente desde `GET /ventas/?corte_id=X` paginando todo (`useBalanceStore.fetchTodasLasPaginas` + `fetchDetalleCorte`, 100 por página) y agrupando `fecha_entrega` (UTC → `America/Bogota`). Inconveniente grave: para un corte no `futuro` el `WHERE` incluye `OR (v.saldo_pendiente > 0 AND co.estado = 'cerrado')`, o sea **suma morosas de todos los cortes cerrados** ⇒ la serie y cualquier total calculado así quedan inflados (hoy también afecta a `detalleCorte.totalVentas`).
- **"30 días":** imposible con los filtros actuales: `GET /ventas/` no acepta rango de fechas; `GET /abonos/` no acepta `corte_id` ni fechas, así que "cobrado por día" tampoco se puede agregar en el servidor ni de forma fiable en el cliente.
- **Recomendación (sin cambios de esquema):** `GET /ventas/serie-diaria?corte_id=&dias=` con `GROUP BY DATE(DATE_SUB(fecha_entrega, INTERVAL 5 HOUR))`, estados `pendiente`/`entregada`, relleno de días en 0 y total; reutiliza el patrón de `ventas_por_dia_semana` (desfase fijo de 5 h, sin DST).
- **Decisiones de negocio pendientes:** (1) métrica: `ventas.total` por `fecha_entrega` vs `abonos.monto` por `abonos.fecha` (el subtítulo dice "ingreso del día", la leyenda "Ventas"); (2) `fecha_entrega` vs `fecha_venta`; (3) qué significa "Este corte" si dura ≠ 7 días y si el total debe ser la suma de los puntos o `balance.total_ventas` (no coinciden cuando hay ventas del corte con `fecha_entrega` fuera del rango, p. ej. ventas de corte futuro).

**Implementado 2026-11-10 (resueltas las 3 decisiones):** el cliente respondió (1) solo **dinero cobrado** — cada venta aporta su `total_abonado`, full si ya está pagada o lo abonado si sigue pendiente; (2) se agrupa por **`fecha_entrega`** (la que llena el usuario en el modal de nueva venta); (3) el total es la **suma de los puntos**, las ventas del corte futuro no entran hasta que su corte se abra, y una venta del corte abierto ya abonada con `fecha_entrega` futura **sí** genera su punto futuro (el front recorta).

- Nuevo endpoint `GET /ventas/serie-diaria` (`routes/ventas.py` → `cntSerieDiariaVentas` → `serie_diaria_ventas`, `@token_requerido`, `cocina` 403).
  - `modo=corte` (def.): solo `corte_id` del corte **abierto**; rango del inicio del corte a hoy, extendido hasta el último día con datos; 404 `{"mensaje": "no existe corte abierto"}` si no hay corte abierto.
  - `modo=dias`: últimos `dias` (1–366, def. 30) días corridos con hoy incluido, sin filtrar por corte.
  - SQL: `SELECT DATE(DATE_SUB(fecha_entrega, INTERVAL 5 HOUR)), SUM(total_abonado), COUNT(*) ... WHERE estado IN ('pendiente','entregada') AND total_abonado > 0 GROUP BY dia` (parametrizado; en `modo=dias` con rango UTC calculado con `zoneinfo`). Rellena con 0 los días sin ventas y topa la serie a `MAX_DIAS_SERIE = 366` puntos.
  - Respuesta: `{modo, desde, hasta, corte_id, corte_numero, corte_fecha_inicio, dias:[{fecha,total,cantidad}], total, cantidad}`. `cantidad` = ventas con abono de ese día.
  - Efecto conocido: como se mira el acumulado, un abono hecho después del día de entrega **mueve** el punto de ese día pasado (no crea un punto en la fecha del abono).
- `swagger.json`: ruta `/ventas/serie-diaria` documentada. `ESTRUCTURA_PROYECTO.md` y `SnackFlow_contexto (1).md` actualizados. Sin cambios de esquema ni SQL de migración.
- Verificado con cursor falso (sin tocar la BD): `modo=corte` 5→11 nov devuelve 7 puntos y suma correcta; `modo=dias` con 30 devuelve 30 puntos terminando hoy; sin corte abierto devuelve `None`; un corte de 800 días se recorta a 366 puntos. La ruta queda registrada en `url_map`.

---

**Actualización 2026-11-11 (domicilios como compras `categoria='domicilio'`):**

### Paso 0 — hallazgos (verificados en código, no supuestos)

**Endpoints/consultas que suman dinero de ventas**

| Lugar | Qué sumaba | Estado |
| --- | --- | --- |
| `services/cortes_services.py:balance_corte_actual` | `SUM(ventas.total)` → `total_ventas` (incluía domicilio) | **Cambiado** a `SUM(GREATEST(total - valor_domicilio, 0))` |
| `services/cortes_services.py:ingresos_ventas_corte_abierto` (`GET /cortes/ingresos-ventas`) | `SUM(abonos.monto)` sin separar | **Cambiado**: `AND a.es_domicilio = 0` |
| `services/ventas_services.py:ventas_por_dia_semana` (`GET /ventas/por-dia-semana`) | `SUM(ventas.total)` | **Cambiado** a productos |
| `services/ventas_services.py:serie_diaria_ventas` (`GET /ventas/serie-diaria`) | `SUM(ventas.total_abonado)` (incluía domicilio) | **Cambiado** a `SUM(abonos.monto)` con `es_domicilio = 0` (`COUNT(DISTINCT v.id)`) |
| `services/clientes_services.py:clientes_top` (`GET /clientes/top`) | `SUM(v.total) AS total_comprado` | **Sin cambios** (mide consumo del cliente, no ingreso) |
| `services/productos_services.py:productos_mas_vendidos` | `SUM(vd.subtotal)` de `venta_detalle` | Ya era solo productos |
| `GET /cortes/historial` | No suma: devuelve solo las filas de `cortes` | El detalle lo arma el frontend sumando `GET /ventas` y `GET /compras` |
| Dashboard / exportaciones | **No existen endpoints de dashboard ni export en el backend** | Nada que cambiar |

`subtotal_productos` no es columna: se calcula como `total - valor_domicilio`. Ya lo devolvía `GET /ventas/<id>/detalle`; ahora también el listado, `por-dia-semana` y `balance`.

**Cómo calcula el balance (antes)**: `total_ventas` = `SUM(ventas.total)` no anuladas del corte; `total_compras` = `SUM(compras.total)` no eliminadas; `total_efectivo`/`total_transferencia` = `SUM(abonos)` por `medio_pago` − `SUM(compras)` por `medio_pago` − neto de préstamos; `efectivo_caja` = `saldo_inicial − transferencia_adelantada + neto_efectivo` de `movimientos_caja`; `dinero_caja_total = efectivo_caja + transferencia_cuentas` (`v_saldos_cuenta`). **La caja ya incluía el domicilio** (entra por abonos, sale por compras), así que no se tocó.

**Modelo de compra**: `compras(id, proveedor_id, corte_id, usuario_id, fecha, medio_pago, medio_pago_id, total, descripcion, eliminada, updated_at)`. No tiene detalle ni tabla hija. Se anula con baja lógica `eliminada = 1` (`DELETE /compras/<id>`). El `corte_id` lo pone el controller (corte abierto) y no inserta en `movimientos_caja` desde Python.

**Cierre de corte**: `cerrar_corte()` **no usa `total_ventas`** ni guarda totales: solo pasa el corte abierto a `cerrado`, el futuro a `abierto` y crea el siguiente futuro. Por eso no hay nada que "recalcular" en cortes cerrados: el balance se calcula al vuelo y las compras viejas (ahora `insumo`) siguen sumando igual.

**Motor y migración**: MySQL 8.x en Clever Cloud, sin ORM, cursores MySQLdb. No hay carpeta de migraciones ni `.sql` versionados: el esquema se entrega aparte y se ejecuta a mano **antes** de desplegar (regla del repo).

### Qué se creó / modificó

- **Esquema (archivo nuevo `migracion_compras_domicilio.sql`)**: `compras.categoria ENUM('insumo','domicilio') NOT NULL DEFAULT 'insumo'`, `compras.venta_id INT NULL`, índices `idx_compras_categoria` e `idx_compras_venta`; procedimiento idempotente con checks en `information_schema`, `UPDATE` defensivo, SELECT de comprobación y bloque de ROLLBACK. Sin FK (no verificable el tipo de `ventas.id`).
- **`services/compra_services.py`**: `CATEGORIAS_COMPRA`, `CompraInvalida`, `_validar_categoria_venta`; `listado_compra(..., categoria)` con filtro, joins a `ventas`/`clientes` y `resumen.por_categoria`; `registro_compra`/`actualizar_compra` aceptan `categoria`/`venta_id`; `obtener_compra` devuelve los campos nuevos. `eliminar_compra` sigue siendo la baja lógica.
- **`controllers/compra_controller.py`**: filtro `categoria` (lista blanca), `categoria`/`venta_id` en POST/PUT y captura de `CompraInvalida` → **400** `{"mensaje": ...}`. En `PUT`, si `categoria` no se envía, el service conserva la categoría y el `venta_id` actuales (el frontend viejo no reclasifica una compra de domicilio).
- **`models/compra_model.py`**: `categoria`, `venta_id`, `venta_cliente`, `venta_estado`.
- **`services/ventas_services.py`**: `ventas_con_domicilio` (nuevo selector); `listado_ventas` y `obtener_venta_detalle` con `subtotal_productos`, `domicilio_pagado_compra`, `domicilio_pendiente_compra`, `domicilio_compra_completa`; `ventas_por_dia_semana` y `serie_diaria_ventas` solo productos; `anular_venta` informa las compras de domicilio ligadas.
- **`controllers/venta_controller.py`** + **`routes/ventas.py`**: `GET /ventas/con-domicilio` (`pagina`, `limite` ≤ 100, `q`, `solo_pendientes`).
- **`services/cortes_services.py`**: `balance_corte_actual` con `ventas_productos`, `domicilios_cobrados`, `domicilios_pagados`, `diferencia_domicilios`, `compras_insumos`, `compras_domicilios`; `total_ventas` = productos; `resultado` = `ventas_productos - compras_insumos`; `ingresos_ventas_corte_abierto` excluye domicilio.
- **`models/venta_model.py`**: los 4 campos nuevos del listado.
- **`swagger.json`**: `/ventas/con-domicilio` nueva; compras (GET listado/detalle, POST, PUT) con `categoria`/`venta_id`/`venta_cliente`/`venta_estado` y `resumen.por_categoria`; ventas (listado y detalle) con los campos de domicilio-compra; `/cortes/balance` con el desglose; descripciones de `por-dia-semana` y `serie-diaria` corregidas a "solo productos"; `/ventas/{id}/anulacion` documenta `datos.compras_domicilio`/`advertencia`.
- **Docs**: `ESTRUCTURA_PROYECTO.md` y `SnackFlow_contexto (1).md` (sección 11 nueva).

### Reglas elegidas (para revisar con el cliente)

1. `total_ventas` del balance pasa a ser **solo productos**; se agrega `ventas_productos` con el mismo valor para que el front no tenga que interpretar el cambio.
2. `domicilios_cobrados` = abonos `es_domicilio = 1` **del corte** (dinero real cobrado), no el `valor_domicilio` facturado de las ventas del corte.
3. `resultado` = `ventas_productos - compras_insumos` (el domicilio no infla ni ingresos ni egresos; su neto queda en `diferencia_domicilios`).
4. Anular una venta **no** anula sus compras de domicilio: se informan en la respuesta para que el admin decida.
5. En ventas anuladas los campos `*_compra` reflejan lo realmente pagado (histórico); el selector `/ventas/con-domicilio` no las lista.
6. `clientes_top` sigue usando `ventas.total` (consumo del cliente, no ingreso).

### Verificación

`py_compile` de los 8 archivos tocados + pruebas con cursor falso (sin BD): filtro y resumen por categoría del listado de compras, validaciones de `categoria`/`venta_id` (incluye venta inexistente/anulada/sin domicilio), `ventas_con_domicilio`, `ventas_por_dia_semana` (productos), `serie_diaria_ventas` (abonos `es_domicilio = 0`) y `balance_corte_actual` con el desglose nuevo. `app.url_map` registra `/ventas/con-domicilio`.

---

**Actualización 2026-11-12 (dashboard: productos sin movimiento):**

Nueva métrica para la gráfica "Productos sin movimiento". **Sin cambios de esquema ni migración SQL.**

### Decisiones de negocio (confirmadas)
1. Cuenta como movimiento la **venta directa y los componentes de combos** (catálogo y personalizados).
2. La fecha de referencia es **`ventas.fecha_entrega`**, con día local por desfase fijo de 5 h (Colombia sin DST).
3. Solo entran productos **activos con stock total > 0** (`stock_actual * unidades_por_bandeja + unidades_sueltas`).
4. Un producto **nunca vendido** cuenta sus días desde `productos.created_at`; solo aparece si se creó hace al menos `dias`.

### Implementación
- `services/productos_services.py` → `productos_sin_movimiento(dias=15, limite=5)`. Última venta por producto con `UNION ALL` de: producto directo (`venta_detalle.es_combo = 0`), componente de combo de catálogo (`combo_detalle`) y componente de combo personalizado (`JSON_TABLE` sobre `combo_productos`, protegido con `JSON_VALID`). Excluye ventas `anulada`; `MAX(fecha_entrega)` por producto. Stock agregado desde `inventario`. Usa `cursor_ctx` y SQL parametrizado.
- `controllers/productos_controller.py` → `cntProductosSinMovimiento`: `dias` 1–365 (def. 15) y `limite` 1–50 (def. 5); no numérico o fuera de rango = **400** `{"mensaje": ...}`.
- `routes/productos.py` → `GET /productos/sin-movimiento` con `@token_requerido` (cocina 403).
- Respuesta: `{dias, desde, hasta, limite, total, productos:[{id, nombre, dias_sin_venta, ultima_venta, nunca_vendido, stock_bandejas, unidades_sueltas, stock_unidades}]}`. `total` es el total real antes del `limite`. Orden: `dias_sin_venta DESC`, luego nombre.
- `swagger.json` documentado. `ESTRUCTURA_PROYECTO.md` y `SnackFlow_contexto (1).md` actualizados.

### Supuestos
- `JSON_TABLE` está disponible: el proyecto corre sobre **MySQL 8.x** en Clever Cloud (documentado en `diagnostico1.md`).
- `combo_productos` contiene JSON válido; aun así se usa `IF(JSON_VALID(...), ..., JSON_ARRAY())` para no romper la consulta con datos heredados.
- Para combos de catálogo se usa la composición **actual** de `combo_detalle` (el sistema no versiona la composición histórica; coincide con cómo se descuenta inventario).
- El frontend decide cómo pintar la barra y el aviso; el backend solo entrega días, última venta y stock.

### Verificación
`py_compile` de los 3 archivos Python; `swagger.json` parsea con `json.load`; `app.url_map` registra `/productos/sin-movimiento`; prueba con cursor falso (sin BD) del shape de respuesta, orden, `nunca_vendido`, stock y placeholders parametrizados (2 en el `COUNT`, 3 en el `SELECT`).
