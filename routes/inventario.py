from flask import Blueprint
from controllers.inventario_controller import cntListado, cntRegistro

inventario_bp = Blueprint ('inventarios', __name__)

@inventario_bp.route('/')
def listado():
    return cntListado()

@inventario_bp.route('/', methods=["POST"])
def registro():
    return cntRegistro()

