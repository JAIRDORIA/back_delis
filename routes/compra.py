from flask import Blueprint
from controllers.compra_controller import cntListadoCompra, cntRegistroCompra

compra_bp = Blueprint('compra', __name__)

@compra_bp.route('/', methods=['GET'])
def listado():
    return cntListadoCompra()

@compra_bp.route('/', methods=['POST'])  
def registro():
    return cntRegistroCompra()