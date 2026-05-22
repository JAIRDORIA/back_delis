from flask import Blueprint
# Importamos las funciones con los nombres que definimos en el controlador
from controllers.combos_controller import get_combos, cntRegistrarCombo, cntActualizarCombo, cntEliminarCombo
from utils.decorators import token_requerido

combos_bp = Blueprint('combos', __name__, url_prefix='/combos')

# 1. Ruta para LISTAR (GET)
@combos_bp.route('/', methods=['GET'])
@token_requerido
def listar_combos():
    return get_combos()

# 2. Ruta para REGISTRAR (POST)
@combos_bp.route('/', methods=['POST'])
@token_requerido
def crear_nuevo_combo():
    # Aquí llamamos a la función que tiene todas las validaciones (.strip, etc)
    return cntRegistrarCombo()

@combos_bp.route('/<int:id>', methods=['PUT'])
@token_requerido
def actualizar_combo(id):
    return cntActualizarCombo(id)

@combos_bp.route('/<int:id>', methods=['DELETE'])
@token_requerido
def eliminar_combo(id):
    return cntEliminarCombo(id)