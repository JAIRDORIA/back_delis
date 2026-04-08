from flask import Blueprint
from controllers.usuarios_controller import cntListado , cntRegistro, cntEliminar

usuarios_bp = Blueprint ('usuarios', __name__)

@usuarios_bp.route('/')
def listado():
    return cntListado()

@usuarios_bp.route('/', methods=["POST"])
def registro():
    return cntRegistro()

@usuarios_bp.route('/<int:id>', methods=["DELETE"])
def eliminar(id):
    return cntEliminar(id)