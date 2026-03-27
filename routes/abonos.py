from flask import Blueprint
from controllers.abonos_controller import cntListado

abono_bp = Blueprint ('abonos', __name__)

@abono_bp.route('/')
def listado():
    return cntListado()