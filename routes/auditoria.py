from flask import Blueprint
from controllers.auditoria_controller import cntListado
from utils.decorators import token_requerido

auditoria_bp = Blueprint('auditoria', __name__)

@auditoria_bp.route('/', methods=['GET'])
@token_requerido
def listado():
    return cntListado()