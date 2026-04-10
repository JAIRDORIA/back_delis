from flask import Blueprint
# Importamos ambas funciones del controlador
from controllers.clientes_controller import get_clientes, cntRegistrar

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')

# 1. Ruta para OBTENER la lista (GET)
@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    return get_clientes()

# 2. Ruta para REGISTRAR un cliente (POST)
@clientes_bp.route('/', methods=['POST'])
def registrar_cliente():
    return cntRegistrar()
