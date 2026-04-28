from flask import Blueprint,jsonify
from controllers.usuarios_controller import cntListado , cntRegistro, cntEliminar, cntActualizar, obtenerUsuario, cntPrimerAdmin
from utils.decorators import token_requerido, rol_requerido
from controllers.usuarios_controller import login_post

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
usuarios_bp = Blueprint ('usuarios', __name__)

@usuarios_bp.route('/setup', methods=['POST'])
def setup_admin():
    return cntPrimerAdmin()

@usuarios_bp.route('/check-setup', methods=['GET'])
def check_setup():
    """
    Retorna True si YA existe un admin (mostrar login).
    Retorna False si NO existe admin (mostrar formulario de setup).
    """
    from services.usuarios_servicies import existe_admin
    admin_existe = existe_admin()
    return jsonify({
        "setup_completado": admin_existe,
        "mensaje": "Sistema configurado" if admin_existe else "Sistema sin configurar"
    }), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    return login_post()

@usuarios_bp.route('/')
@token_requerido
def listado():  
    return cntListado()

@usuarios_bp.route('/', methods=["POST"])
@token_requerido
def registro():
    return cntRegistro()

@usuarios_bp.route('/<int:id>', methods=["DELETE"])
@token_requerido
def eliminar(id):
    return cntEliminar(id)

@usuarios_bp.route('/<int:id>', methods=["PUT"])
@token_requerido
def actualizar(id):
    return cntActualizar(id)

@usuarios_bp.route('/<int:id>', methods=["GET"])
@token_requerido
def obtener_usuario(id):
    return obtenerUsuario(id)


