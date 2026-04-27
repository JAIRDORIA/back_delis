from flask import Blueprint
from controllers.corte_controller import cntListado,cntPrimerCorte,cntCerrarCorte,cntActualizar,cntBalance
from flask_jwt_extended import jwt_required

cortes_bp = Blueprint ('cortes', __name__)


@cortes_bp.route('/')
#@jwt_required()
def listado():
    return cntListado()


@cortes_bp.route('/<int:id>', methods=['PUT'])
#@jwt_required()
def actualizar(id):
    return cntActualizar(id)

@cortes_bp.route('/iniciar', methods=['POST'])
#@jwt_required()
def iniciar():
    return cntPrimerCorte()

# Se llama cada vez que el admin decide cerrar el corte
@cortes_bp.route('/cerrar', methods=['POST'])
#@jwt_required()
def cerrar():
    return cntCerrarCorte()

@cortes_bp.route('/balance', methods=['GET'])
def balance():
    return cntBalance()