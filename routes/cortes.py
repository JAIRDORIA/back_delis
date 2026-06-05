from flask import Blueprint
from controllers.corte_controller import cntListado,cntPrimerCorte,cntCerrarCorte,cntActualizar,cntBalance
from utils.decorators import token_requerido

cortes_bp = Blueprint ('cortes', __name__)


@cortes_bp.route('/')

def listado():
    return cntListado()

@cortes_bp.route('/historial', methods=['GET'])
def historial():
    return cntHistorial()

@cortes_bp.route('/<int:id>', methods=['PUT'])
@token_requerido
def actualizar(id):
    return cntActualizar(id)

@cortes_bp.route('/iniciar', methods=['POST'])
@token_requerido
def iniciar():
    return cntPrimerCorte()

# Se llama cada vez que el admin decide cerrar el corte
@cortes_bp.route('/cerrar', methods=['POST'])
@token_requerido
def cerrar():
    return cntCerrarCorte()

@cortes_bp.route('/balance', methods=['GET'])
@token_requerido
def balance():
    return cntBalance()