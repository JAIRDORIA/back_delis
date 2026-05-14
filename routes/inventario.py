from flask import Blueprint
from utils.decorators import token_requerido, rol_requerido
from controllers.inventario_controller import cntListado, cntRegistro, cntActualizar, cntObtenerInventario, cntProductosBajoStock

inventario_bp = Blueprint ('inventarios', __name__)

@inventario_bp.route('/')
#@token_requerido
def listado():
    return cntListado()

@inventario_bp.route('/', methods=["POST"])
#@token_requerido
def registro():
    return cntRegistro()

@inventario_bp.route('/<int:id>', methods=["PUT"])
#@token_requerido
def actualizar(id):
    return cntActualizar(id)

@inventario_bp.route('/<int:id>', methods=["GET"])
#@token_requerido
def obtener_inventario(id):
    return cntObtenerInventario(id)

@inventario_bp.route('/bajo-stock', methods=["GET"]) 
#@token_requerido
def bajo_stock():
    return cntProductosBajoStock()
