from flask import Blueprint
from controllers.productos_controller import cntListado, cntRegistro, cntEliminar

productos_bp = Blueprint ('productos', __name__)


@productos_bp.route('/')
def listado():
    return cntListado()

@productos_bp.route('/', methods=["POST"])
def registro():
    return cntRegistro()

@productos_bp.route('/<int:id>', methods=["DELETE"])
def eliminar(id):
    return cntEliminar(id)