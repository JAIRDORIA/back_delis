from flask import Blueprint
from controllers.clientes_controller import get_clientes, get_cliente, create_cliente, update_cliente

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')

# Ruta para obtener la lista de clientes
@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    return get_clientes()

# Ruta para obtener un cliente específico por ID
@clientes_bp.route('/<int:id>', methods=['GET'])
def obtener_cliente(id):
    return get_cliente(id)

# Ruta para crear un nuevo cliente
@clientes_bp.route('/', methods=['POST'])
def crear_cliente():
    return create_cliente()

# Ruta para actualizar un cliente existente
@clientes_bp.route('/<int:id>', methods=['PUT'])
def actualizar_cliente(id):
    return update_cliente(id)