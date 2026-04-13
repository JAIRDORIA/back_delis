from flask import Blueprint
from controllers.corte_controller import cntListado,cntPrimerCorte,cntCerrarCorte

cortes_bp = Blueprint ('cortes', __name__)


@cortes_bp.route('/')
def listado():
    return cntListado()


@cortes_bp.route('/iniciar', methods=['POST'])
def iniciar():
    return cntPrimerCorte()

# Se llama cada vez que el admin decide cerrar el corte
@cortes_bp.route('/cerrar', methods=['POST'])
def cerrar():
    return cntCerrarCorte()