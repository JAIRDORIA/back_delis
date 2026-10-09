"""
Rutas del panel de produccion (pantalla fija de la sala).

El usuario de la sala entra con rol 'produccion' y registra bandejas/unidades
sueltas de un producto para un empleado. El registro queda en estado
'pendiente' (no toca inventario; la validacion es de otro modulo).

Como 'produccion' es rechazado por @token_requerido (403), estas rutas usan
@token_requerido_cocina + @rol_requerido, igual que /empleados/activos y
/pedidos-cocina. Roles permitidos: 'produccion' y 'admin'.
"""
from flask import Blueprint

from controllers.produccion_empleados_controller import (
    cntListadoProductos,
    cntRegistro,
    cntListadoPendientes,
    cntAceptar,
    cntRechazar,
    cntListadoRegistros,
)
from utils.decorators import (
    token_requerido,
    token_requerido_cocina,
    rol_requerido,
)

produccion_empleados_bp = Blueprint("produccion_empleados", __name__)


@produccion_empleados_bp.route("/productos", methods=["GET"])
@token_requerido_cocina
@rol_requerido(["produccion", "admin"])
def listado_productos():
    return cntListadoProductos()


@produccion_empleados_bp.route("/registros", methods=["GET"])
@token_requerido_cocina
@rol_requerido(["produccion", "admin"])
def listado_registros():
    return cntListadoRegistros()


@produccion_empleados_bp.route("/", methods=["POST"])
@token_requerido_cocina
@rol_requerido(["produccion", "admin"])
def registro():
    return cntRegistro()


# ─── Panel admin: validar lo que registraron los empleados ───

@produccion_empleados_bp.route("/pendientes", methods=["GET"])
@token_requerido
@rol_requerido(["admin"])
def listado_pendientes():
    return cntListadoPendientes()


@produccion_empleados_bp.route("/<int:id>/aceptar", methods=["PUT"])
@token_requerido
@rol_requerido(["admin"])
def aceptar(id):
    return cntAceptar(id)


@produccion_empleados_bp.route("/<int:id>/rechazar", methods=["PUT"])
@token_requerido
@rol_requerido(["admin"])
def rechazar(id):
    return cntRechazar(id)
