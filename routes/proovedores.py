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


# ═══════════════════════════════════════════════
#  LISTADOS
# ═══════════════════════════════════════════════

@proveedores_bp.route('/', methods=['GET'])
@token_requerido
def listado():
    """
    Obtiene el listado de todos los proveedores
    GET /proveedores/
    """
    return cntListadoProveedores()


@proveedores_bp.route('/activos', methods=['GET'])
@token_requerido
def listado_activos():
    """
    ✅ NUEVO: Obtiene solo los proveedores activos
    GET /proveedores/activos
    """
    return cntListadoProveedoresActivos()


# ═══════════════════════════════════════════════
#  BÚSQUEDAS
# ═══════════════════════════════════════════════

@proveedores_bp.route('/buscar/nombre', methods=['GET'])
@token_requerido
def buscar_nombre():
    """
    ✅ NUEVO: Busca proveedores por nombre (búsqueda parcial)
    GET /proveedores/buscar/nombre?q=criterio
    
    Ejemplo:
        GET /proveedores/buscar/nombre?q=acme
    """
    return cntBuscarPorNombre()


@proveedores_bp.route('/buscar/email', methods=['GET'])
@token_requerido
def buscar_email():
    """
    ✅ NUEVO: Busca proveedores por email (búsqueda parcial)
    GET /proveedores/buscar/email?q=criterio
    
    Ejemplo:
        GET /proveedores/buscar/email?q=ejemplo@
    """
    return cntBuscarPorEmail()


# ═══════════════════════════════════════════════
#  OBTENER ESPECÍFICO
# ═══════════════════════════════════════════════

@proveedores_bp.route('/<int:id>', methods=['GET'])
@token_requerido
def obtener(id):
    """
    Obtiene un proveedor específico por ID
    GET /proveedores/<id>
    
    Ejemplo:
        GET /proveedores/1
    """
    return cntObtenerProveedor(id)


# ═══════════════════════════════════════════════
#  CREAR
# ═══════════════════════════════════════════════

@proveedores_bp.route('/', methods=['POST'])
@token_requerido
def registro():
    """
    Registra un nuevo proveedor
    POST /proveedores/
    
    ✅ Validaciones aplicadas:
    - Nombre sin números
    - Nombre único
    - Email válido y único
    - Teléfono válido
    - Dirección válida
    
    Ejemplo de JSON:
    {
        "nombre": "Acme Corporation",
        "telefono": "+1 (555) 123-4567",
        "direccion": "Calle Principal 123, Apto 4",
        "email": "contacto@acmecorp.com"
    }
    """
    return cntRegistroProveedor()


# ═══════════════════════════════════════════════
#  ACTUALIZAR
# ═══════════════════════════════════════════════

@proveedores_bp.route('/<int:id>', methods=['PUT'])
@token_requerido
def actualizar(id):
    """
    Actualiza un proveedor existente
    PUT /proveedores/<id>
    
    ✅ Validaciones aplicadas:
    - Nombre sin números
    - Nombre único (si cambió)
    - Email válido y único (si cambió)
    - Teléfono válido
    - Dirección válida
    - Estado activo válido (0 o 1)
    
    Ejemplo de JSON:
    {
        "nombre": "Acme Corporation",
        "telefono": "+1 (555) 123-4567",
        "direccion": "Calle Principal 123, Apto 4",
        "email": "contacto@acmecorp.com",
        "activo": 1
    }
    """
    return cntActualizarProveedor(id)


# ═══════════════════════════════════════════════
#  ELIMINAR
# ═══════════════════════════════════════════════

@proveedores_bp.route('/<int:id>', methods=['DELETE'])
@token_requerido
def eliminar(id):
    """
    Elimina un proveedor (soft delete)
    DELETE /proveedores/<id>
    
    Nota: Marca el proveedor como inactivo (activo = 0)
    
    Ejemplo:
        DELETE /proveedores/1
    """
    return cntEliminarProveedor(id)