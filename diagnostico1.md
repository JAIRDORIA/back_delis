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
