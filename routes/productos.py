from flask import Blueprint
from controllers.productos_controller import cntListado

productos_bp = Blueprint ('productos', __name__)


@productos_bp.route('/')
def listado():
    return cntListado()