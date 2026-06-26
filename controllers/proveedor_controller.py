from flask import jsonify, request
from services.proveedor_services import (
    listado_proveedores,
    listado_proveedores_activos,
    obtener_proveedor,
    registro_proveedor,
    actualizar_proveedor,
    eliminar_proveedor,
    buscar_proveedores_por_nombre,
    buscar_proveedores_por_email
)


# ═══════════════════════════════════════════════
#  LISTADO
# ═══════════════════════════════════════════════

def cntListadoProveedores():
    """
    Obtiene el listado de todos los proveedores
    GET /proveedores/
    """
    try:
        datos = listado_proveedores()
        return jsonify({
            "exito": True,
            "total": len(datos),
            "datos": datos
        }), 200
    except Exception as e:
        return jsonify({
            "exito": False,
            "error": f"Error al obtener proveedores: {str(e)}"
        }), 500


def cntListadoProveedoresActivos():
    """
    ✅ NUEVO: Obtiene solo los proveedores activos
    GET /proveedores/activos
    """
    try:
        datos = listado_proveedores_activos()
        return jsonify({
            "exito": True,
            "total": len(datos),
            "datos": datos
        }), 200
    except Exception as e:
        return jsonify({
            "exito": False,
            "error": f"Error al obtener proveedores activos: {str(e)}"
        }), 500


# ═══════════════════════════════════════════════
#  OBTENER UNO
# ═══════════════════════════════════════════════

def cntObtenerProveedor(id):
    """
    Obtiene un proveedor específico
    GET /proveedores/<id>
    """
    try:
        # Validar que ID es número
        try:
            id_num = int(id)
            if id_num <= 0:
                return jsonify({
                    "exito": False,
                    "error": "El ID debe ser un número mayor a 0"
                }), 400
        except ValueError:
            return jsonify({
                "exito": False,
                "error": "El ID debe ser un número entero válido"
            }), 400
        
        dato, error = obtener_proveedor(id)
        if error:
            return jsonify({
                "exito": False,
                "error": error
            }), 404
        
        return jsonify({
            "exito": True,
            "dato": dato
        }), 200
    
    except Exception as e:
        return jsonify({
            "exito": False,
            "error": f"Error al obtener proveedor: {str(e)}"
        }), 500


# ═══════════════════════════════════════════════
#  BÚSQUEDA
# ═══════════════════════════════════════════════

def cntBuscarPorNombre():
    """
    ✅ NUEVO: Busca proveedores por nombre
    GET /proveedores/buscar/nombre?q=criterio
    """
    criterio = request.args.get('q', '').strip()
    
    if not criterio:
        return jsonify({
            "exito": False,
            "error": "El criterio de búsqueda no puede estar vacío"
        }), 400
    
    if len(criterio) < 2:
        return jsonify({
            "exito": False,
            "error": "El criterio debe tener al menos 2 caracteres"
        }), 400
    
    try:
        datos = buscar_proveedores_por_nombre(criterio)
        return jsonify({
            "exito": True,
            "total": len(datos),
            "criterio": criterio,
            "datos": datos
        }), 200
    
    except Exception as e:
        return jsonify({
            "exito": False,
            "error": f"Error en la búsqueda: {str(e)}"
        }), 500


def cntBuscarPorEmail():
    """
    ✅ NUEVO: Busca proveedores por email
    GET /proveedores/buscar/email?q=criterio
    """
    criterio = request.args.get('q', '').strip()
    
    if not criterio:
        return jsonify({
            "exito": False,
            "error": "El criterio de búsqueda no puede estar vacío"
        }), 400
    
    if len(criterio) < 5:
        return jsonify({
            "exito": False,
            "error": "El criterio debe tener al menos 5 caracteres (mínimo para email)"
        }), 400
    
    try:
        datos = buscar_proveedores_por_email(criterio)
        return jsonify({
            "exito": True,
            "total": len(datos),
            "criterio": criterio,
            "datos": datos
        }), 200
    
    except Exception as e:
        return jsonify({
            "exito": False,
            "error": f"Error en la búsqueda: {str(e)}"
        }), 500


# ═══════════════════════════════════════════════
#  REGISTRO
# ═══════════════════════════════════════════════

def cntRegistroProveedor():
    """
    Registra un nuevo proveedor
    POST /proveedores/
    
    ✅ Validaciones en servicios:
    - Nombre sin números
    - Nombre único (no duplicado)
    - Email válido y único
    - Teléfono válido
    - Dirección válida
    """
    # Validar que sea JSON
    if not request.is_json:
        return jsonify({
            "exito": False,
            "error": "El cuerpo debe ser JSON"
        }), 400

    # Validar campos requeridos
    requeridos = ['nombre', 'telefono', 'direccion', 'email']
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({
            "exito": False,
            "error": f"Faltan los siguientes campos: {', '.join(faltantes)}"
        }), 400

    # Obtener datos
    try:
        nombre = request.json['nombre'].strip() if isinstance(request.json.get('nombre'), str) else ''
        telefono = request.json['telefono'].strip() if isinstance(request.json.get('telefono'), str) else ''
        direccion = request.json['direccion'].strip() if isinstance(request.json.get('direccion'), str) else ''
        email = request.json['email'].strip() if isinstance(request.json.get('email'), str) else ''
    except AttributeError:
        return jsonify({
            "exito": False,
            "error": "Los datos no tienen el formato correcto"
        }), 400

    try:
        # Las validaciones se hacen en services/proveedor_services.py
        dato, error = registro_proveedor(nombre, telefono, direccion, email)
        
        if error:
            # Retornar 409 si es un conflicto (duplicado)
            status = 409 if "ya existe" in error.lower() or "duplicado" in error.lower() else 400
            return jsonify({
                "exito": False,
                "error": error
            }), status
        
        return jsonify({
            "exito": True,
            "mensaje": "Proveedor registrado exitosamente",
            "dato": dato
        }), 201
    
    except Exception as e:
        return jsonify({
            "exito": False,
            "error": f"Error al registrar proveedor: {str(e)}"
        }), 500


# ═══════════════════════════════════════════════
#  ACTUALIZACIÓN
# ═══════════════════════════════════════════════

def cntActualizarProveedor(id):
    """
    Actualiza un proveedor existente
    PUT /proveedores/<id>
    
    ✅ Validaciones en servicios:
    - ID válido
    - Nombre sin números
    - Nombre único (si cambió)
    - Email válido y único (si cambió)
    - Teléfono válido
    - Dirección válida
    - Estado activo válido
    """
    # Validar ID
    try:
        id_num = int(id)
        if id_num <= 0:
            return jsonify({
                "exito": False,
                "error": "El ID debe ser un número mayor a 0"
            }), 400
    except ValueError:
        return jsonify({
            "exito": False,
            "error": "El ID debe ser un número entero válido"
        }), 400

    # Validar que sea JSON
    if not request.is_json:
        return jsonify({
            "exito": False,
            "error": "El cuerpo debe ser JSON"
        }), 400

    # Validar campos requeridos
    requeridos = ['nombre', 'telefono', 'direccion', 'email', 'activo']
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({
            "exito": False,
            "error": f"Faltan los siguientes campos: {', '.join(faltantes)}"
        }), 400

    # Obtener datos
    try:
        nombre = request.json['nombre'].strip() if isinstance(request.json.get('nombre'), str) else ''
        telefono = request.json['telefono'].strip() if isinstance(request.json.get('telefono'), str) else ''
        direccion = request.json['direccion'].strip() if isinstance(request.json.get('direccion'), str) else ''
        email = request.json['email'].strip() if isinstance(request.json.get('email'), str) else ''
        activo = request.json['activo']
    except AttributeError:
        return jsonify({
            "exito": False,
            "error": "Los datos no tienen el formato correcto"
        }), 400

    try:
        # Las validaciones se hacen en services/proveedor_services.py
        dato, error = actualizar_proveedor(id, nombre, telefono, direccion, email, activo)
        
        if error:
            if "no encontrado" in error.lower():
                return jsonify({
                    "exito": False,
                    "error": error
                }), 404
            else:
                # Retornar 409 si es un conflicto (duplicado)
                status = 409 if "ya existe" in error.lower() or "duplicado" in error.lower() else 400
                return jsonify({
                    "exito": False,
                    "error": error
                }), status
        
        return jsonify({
            "exito": True,
            "mensaje": "Proveedor actualizado exitosamente",
            "dato": dato
        }), 200
    
    except Exception as e:
        return jsonify({
            "exito": False,
            "error": f"Error al actualizar proveedor: {str(e)}"
        }), 500


# ═══════════════════════════════════════════════
#  ELIMINACIÓN (Soft Delete)
# ═══════════════════════════════════════════════

def cntEliminarProveedor(id):
    """
    Elimina un proveedor (soft delete)
    DELETE /proveedores/<id>
    
    Nota: Marca el proveedor como inactivo (activo = 0)
    """
    # Validar ID
    try:
        id_num = int(id)
        if id_num <= 0:
            return jsonify({
                "exito": False,
                "error": "El ID debe ser un número mayor a 0"
            }), 400
    except ValueError:
        return jsonify({
            "exito": False,
            "error": "El ID debe ser un número entero válido"
        }), 400

    try:
        ok, error = eliminar_proveedor(id)
        
        if error:
            return jsonify({
                "exito": False,
                "error": error
            }), 404
        
        return jsonify({
            "exito": True,
            "mensaje": f"Proveedor {id} eliminado correctamente"
        }), 200
    
    except Exception as e:
        return jsonify({
            "exito": False,
            "error": f"Error al eliminar proveedor: {str(e)}"
        }), 500