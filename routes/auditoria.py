from flask import Blueprint
from controllers.auditoria_controller import cntListado

auditoria_bp = Blueprint('auditoria', __name__)

@auditoria_bp.route('/', methods=['GET'])
def listado():
    return cntListado()