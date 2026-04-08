from flask import Blueprint
from controllers.abonos_controller import cntListado,cntregistrar


abono_bp = Blueprint ('abonos', __name__)

@abono_bp.route('/')
def listado():
    return cntListado()

@abono_bp.route('/', methods = ["POST"])
def registro():
    return cntregistrar()