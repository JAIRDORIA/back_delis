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



def cntObtenerProveedor(id):
    
    try:
        
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




def cntBuscarPorNombre():
    
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


def cntRegistroProveedor():
    
    if not request.is_json:
        return jsonify({
            "exito": False,
            "error": "El cuerpo debe ser JSON"
        }), 400

    
    requeridos = ['nombre', 'telefono', 'direccion', 'email']
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({
            "exito": False,
            "error": f"Faltan los siguientes campos: {', '.join(faltantes)}"
        }), 400

    
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
        
        dato, error = registro_proveedor(nombre, telefono, direccion, email)
        
        if error:
            
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




def cntActualizarProveedor(id):
    
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

    
    if not request.is_json:
        return jsonify({
            "exito": False,
            "error": "El cuerpo debe ser JSON"
        }), 400

    
    requeridos = ['nombre', 'telefono', 'direccion', 'email', 'activo']
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({
            "exito": False,
            "error": f"Faltan los siguientes campos: {', '.join(faltantes)}"
        }), 400

    
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
        
        dato, error = actualizar_proveedor(id, nombre, telefono, direccion, email, activo)
        
        if error:
            if "no encontrado" in error.lower():
                return jsonify({
                    "exito": False,
                    "error": error
                }), 404
            else:
                
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



def cntEliminarProveedor(id):
    
    
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