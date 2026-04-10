from flask import Blueprint
from controllers.proveedor_controller import cntListadoProveedores, cntRegistroProveedor

proveedores_bp = Blueprint('proveedores', __name__)

@proveedores_bp.route('/', methods=['GET'])
def listado():
    return cntListadoProveedores()

@proveedores_bp.route('/', methods=['POST'])  
def registro():
    return cntRegistroProveedor()