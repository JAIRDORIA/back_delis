from flask import Blueprint
from controllers.inventario_controller import cntListado, cntRegistro, cntActualizar, cntObtenerInventario, cntProductosBajoStock

inventario_bp = Blueprint ('inventarios', __name__)

@inventario_bp.route('/')
def listado():
    return cntListado()

@inventario_bp.route('/', methods=["POST"])
def registro():
    return cntRegistro()

@inventario_bp.route('/<int:id>', methods=["PUT"])
def actualizar(id):
    return cntActualizar(id)

@inventario_bp.route('/<int:id>', methods=["GET"])
def obtener_inventario(id):
    return cntObtenerInventario(id)

@inventario_bp.route('/bajo-stock', methods=["GET"]) 
def bajo_stock():
    return cntProductosBajoStock()
