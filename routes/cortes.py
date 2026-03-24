from flask import Blueprint
from controllers.corte_controller import cntListado

cortes_bp = Blueprint ('cortes', __name__)


@cortes_bp.route('/')
def listado():
    return cntListado()