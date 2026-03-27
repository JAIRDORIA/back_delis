from flask import Blueprint
from controllers.clientes_controller import get_clientes 

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')

# Ruta para obtener la lista de clientes
@clientes_bp.route('/', methods=['GET'])
def listar_clientes():
    return get_clientes()

