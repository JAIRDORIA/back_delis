from flask import Blueprint
from controllers.combos_controller import get_combos, get_combo, create_combo, update_combo

combos_bp = Blueprint('combos', __name__, url_prefix='/combos')

@combos_bp.route('/', methods=['GET'])
def listar_combos():
    return get_combos()

@combos_bp.route('/<int:id>', methods=['GET'])
def obtener_combo_por_id(id):
    return get_combo(id)

@combos_bp.route('/', methods=['POST'])
def crear_nuevo_combo():
    return create_combo()

@combos_bp.route('/<int:id>', methods=['PUT'])
def actualizar_combo_por_id(id):
    return update_combo(id)