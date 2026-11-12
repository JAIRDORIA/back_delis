from flask import Blueprint
from controllers.venta_controller import cntListado,cntregistrar, cntActualizar, cntAnular,cntGenerarComprobante
from utils.decorators import token_requerido
from controllers.venta_controller import cntDetalle,cntActualizarDetalle,cntVentasPorDiaSemana
from controllers.venta_controller import cntSerieDiariaVentas, cntVentasConDomicilio

ventas_bp = Blueprint ('ventas', __name__)


@ventas_bp.route('/')
@token_requerido
def listado():
    return cntListado()

@ventas_bp.route('/con-domicilio', methods=['GET'])
@token_requerido
def con_domicilio():
    return cntVentasConDomicilio()

@ventas_bp.route('/por-dia-semana', methods=['GET'])
@token_requerido
def por_dia_semana():
    return cntVentasPorDiaSemana()

@ventas_bp.route('/serie-diaria', methods=['GET'])
@token_requerido
def serie_diaria():
    return cntSerieDiariaVentas()

@ventas_bp.route('/<int:id>/detalle', methods=['GET'])
@token_requerido
def detalle(id):
    return cntDetalle(id)

@ventas_bp.route('/<int:id>/detalle', methods=['PUT'])
@token_requerido
def actualizar_detalle(id):
    return cntActualizarDetalle(id)

@ventas_bp.route('/', methods = ["POST"])
@token_requerido
def registro():
    return cntregistrar()

@ventas_bp.route('/<int:id>', methods=['PUT'])
@token_requerido
def actualizar(id):
    return cntActualizar(id)

@ventas_bp.route('/<int:id>/anulacion', methods=['PUT'])
@token_requerido
def anular(id):
    return cntAnular(id)

@ventas_bp.route('/<int:id>/comprobante', methods=['GET'])
@token_requerido
def comprobante(id):
    return cntGenerarComprobante(id)