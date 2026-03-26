from flask import Blueprint
from controllers.inventario_controller import cntListado

inventario_bp = Blueprint ('inventario', __name__)

@inventario_bp.route('/')
def listado():
    return cntListado() 