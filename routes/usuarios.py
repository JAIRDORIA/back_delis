from flask import Blueprint
from controllers.usuarios_controller import cntListado

usuarios_bp = Blueprint ('usuarios', __name__)

@usuarios_bp.route('/')
def listado():
    return cntListado()