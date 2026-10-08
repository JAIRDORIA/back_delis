from flask import current_app
from MySQLdb import IntegrityError
from models.empleado_model import empleados
from utils.db import cursor_ctx


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _empleado_existe(cursor, id):
    cursor.execute("SELECT id FROM empleados WHERE id = %s", (id,))
    return cursor.fetchone() is not None


def _nombre_duplicado(cursor, nombre, excluir_id=None):
    """
    La columna `nombre` es utf8mb4_unicode_ci: la comparacion `=` es
    insensible a mayusculas y tildes, por eso no se usa LOWER().
    """
    if excluir_id is None:
        cursor.execute("SELECT id FROM empleados WHERE nombre = %s", (nombre,))
    else:
        cursor.execute(
            "SELECT id FROM empleados WHERE nombre = %s AND id != %s",
            (nombre, excluir_id)
        )
    return cursor.fetchone() is not None


# ─────────────────────────────────────────────
#  LISTADOS
# ─────────────────────────────────────────────

def listado_empleados(activo=None):
    """Todos los empleados (o solo los de un estado) ordenados por nombre."""
    with cursor_ctx() as c:
        if activo is None:
            c.execute(
                "SELECT id, nombre, activo, created_at, updated_at FROM empleados ORDER BY nombre"
            )
        else:
            c.execute(
                "SELECT id, nombre, activo, created_at, updated_at FROM empleados "
                "WHERE activo = %s ORDER BY nombre",
                (activo,)
            )
        filas = c.fetchall()

    return [
        empleados(f[0], f[1], f[2], f[3], f[4]).toDic()
        for f in filas
    ]


def listado_empleados_activos():
    """Solo id y nombre de los empleados activos (para el selector de produccion)."""
    with cursor_ctx() as c:
        c.execute("SELECT id, nombre FROM empleados WHERE activo = 1 ORDER BY nombre")
        filas = c.fetchall()

    return [{"id": f[0], "nombre": f[1]} for f in filas]


# ─────────────────────────────────────────────
#  REGISTRO
# ─────────────────────────────────────────────

def registro_empleado(nombre):
    try:
        with cursor_ctx() as c:
            if _nombre_duplicado(c, nombre):
                return None, f"Ya existe un empleado con el nombre '{nombre}'"

            c.execute("INSERT INTO empleados (nombre) VALUES (%s)", (nombre,))
            current_app.mysql.connection.commit()
            nuevo_id = c.lastrowid
        return empleados(nuevo_id, nombre, 1).toDic(), None
    except IntegrityError:
        # La columna es UNIQUE: cubre la carrera entre la validacion y el INSERT
        return None, f"Ya existe un empleado con el nombre '{nombre}'"


# ─────────────────────────────────────────────
#  ACTUALIZAR
# ─────────────────────────────────────────────

def actualizar_empleado(id, nombre=None, activo=None):
    try:
        with cursor_ctx() as c:
            if not _empleado_existe(c, id):
                return None, "Empleado no encontrado"

            if nombre is not None and _nombre_duplicado(c, nombre, excluir_id=id):
                return None, f"Ya existe otro empleado con el nombre '{nombre}'"

            # Los fragmentos del SET son literales fijos; los valores van parametrizados
            campos = []
            valores = []
            if nombre is not None:
                campos.append("nombre = %s")
                valores.append(nombre)
            if activo is not None:
                campos.append("activo = %s")
                valores.append(activo)
            campos.append("updated_at = CURRENT_TIMESTAMP")
            valores.append(id)

            c.execute(
                f"UPDATE empleados SET {', '.join(campos)} WHERE id = %s",
                tuple(valores)
            )
            current_app.mysql.connection.commit()

            c.execute(
                "SELECT id, nombre, activo, created_at, updated_at FROM empleados WHERE id = %s",
                (id,)
            )
            fila = c.fetchone()

        return empleados(fila[0], fila[1], fila[2], fila[3], fila[4]).toDic(), None
    except IntegrityError:
        return None, f"Ya existe otro empleado con el nombre '{nombre}'"
