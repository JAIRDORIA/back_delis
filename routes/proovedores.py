"""
Rutas (Blueprint) para Proveedores
Actualizado con nuevas funcionalidades y validaciones
"""

from flask import Blueprint
from controllers.proveedor_controller import (
    cntListadoProveedores,
    cntListadoProveedoresActivos,
    cntObtenerProveedor,
    cntRegistroProveedor,
    cntActualizarProveedor,
    cntEliminarProveedor,
    cntBuscarPorNombre,
    cntBuscarPorEmail
)
from utils.decorators import token_requerido

proveedores_bp = Blueprint('proveedores', __name__, url_prefix='/proveedores')




@proveedores_bp.route('/', methods=['GET'])
@token_requerido
def listado():
  
    return cntListadoProveedores()


@proveedores_bp.route('/activos', methods=['GET'])
@token_requerido
def listado_activos():
   
    return cntListadoProveedoresActivos()



@proveedores_bp.route('/buscar/nombre', methods=['GET'])
@token_requerido
def buscar_nombre():
    
    return cntBuscarPorNombre()


@proveedores_bp.route('/buscar/email', methods=['GET'])
@token_requerido
def buscar_email():
    
    return cntBuscarPorEmail()




@proveedores_bp.route('/<int:id>', methods=['GET'])
@token_requerido
def obtener(id):
    
    return cntObtenerProveedor(id)



@proveedores_bp.route('/', methods=['POST'])
@token_requerido
def registro():
    
    return cntRegistroProveedor()




@proveedores_bp.route('/<int:id>', methods=['PUT'])
@token_requerido
def actualizar(id):
    
    return cntActualizarProveedor(id)



@proveedores_bp.route('/<int:id>', methods=['DELETE'])
@token_requerido
def eliminar(id):
    
    return cntEliminarProveedor(id)