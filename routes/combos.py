from flask import Blueprint
# Importamos las funciones con los nombres que definimos en el controlador
from controllers.combos_controller import get_combos, cntRegistrarCombo


combos_bp = Blueprint('combos', __name__, url_prefix='/combos')

# 1. Ruta para LISTAR (GET)
@combos_bp.route('/', methods=['GET'])
def listar_combos():
    return get_combos()

# 2. Ruta para REGISTRAR (POST)
@combos_bp.route('/', methods=['POST'])
def crear_nuevo_combo():
    # Aquí llamamos a la función que tiene todas las validaciones (.strip, etc)
    return cntRegistrarCombo()