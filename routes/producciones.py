from flask import Blueprint
from controllers.producciones_controller import cntListado, cntRegistro,cntObtenerProduccion
from utils.decorators import token_requerido, rol_requerido
producciones_bp = Blueprint ('producciones', __name__)


@producciones_bp.route('/')
@token_requerido
def listado():
    return cntListado()

@producciones_bp.route('/', methods=["POST"])
@token_requerido
def registro():
    return cntRegistro()

@producciones_bp.route('/<int:id>', methods=["GET"])
@token_requerido
def obtener(id):
    return cntObtenerProduccion(id)