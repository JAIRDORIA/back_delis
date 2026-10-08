"""
Rutas del modulo de empleados (personas de la sala de produccion).

Los empleados NO son usuarios del sistema: no tienen contrasena. El panel de
produccion inicia sesion con un usuario de rol 'produccion' y luego elige el
empleado en pantalla.

`/empleados/activos` es el UNICO endpoint al que debe entrar el rol 'produccion':
usa @token_requerido_cocina (que deja pasar cualquier rol validado) + @rol_requerido,
igual que las rutas de /pedidos-cocina.
Los demas son exclusivos de admin.
"""
from flask import Blueprint

from controllers.empleados_controller import (
    cntListado,
    cntListadoActivos,
    cntRegistro,
    cntActualizar,
)
from utils.decorators import token_requerido, token_requerido_cocina, rol_requerido

empleados_bp = Blueprint("empleados", __name__)


@empleados_bp.route("/", methods=["GET"])
@token_requerido
@rol_requerido(["admin"])
def listado():
    return cntListado()


@empleados_bp.route("/activos", methods=["GET"])
@token_requerido_cocina
@rol_requerido(["produccion", "admin"])
def listado_activos():
    return cntListadoActivos()


@empleados_bp.route("/", methods=["POST"])
@token_requerido
@rol_requerido(["admin"])
def registro():
    return cntRegistro()


@empleados_bp.route("/<int:id>", methods=["PUT"])
@token_requerido
@rol_requerido(["admin"])
def actualizar(id):
    return cntActualizar(id)
