from flask import jsonify, request
from services.inventario_services import (listado_inventarios, registro, existe_inventario,obtener_inventario, actualizar_stock_minimo, productos_bajo_stock,actualizar_cantidades )
from services.productos_services import existe_producto
from services.usuarios_servicies import obtener_usuario


def cntListado():
    try:
        pagina = int(request.args.get('pagina', 1))
        limite = int(request.args.get('limite', 20))

        if pagina < 1 or limite < 1:
            return jsonify({"mensaje": "pagina y limite deben ser mayores a 0"}), 400

        datos = listado_inventarios(pagina=pagina, limite=limite)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntRegistro():
    requeridos = ['producto_id']
    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    vacios = []
    for clave in request.json:
        if str(request.json[clave]).strip() == "":
            vacios.append(clave)
    if vacios:
        return jsonify({"mensaje": f"los siguientes campos no pueden estar vacios {vacios}"}), 400

    producto_id = request.json['producto_id']

    try:
        producto_id = int(producto_id)
    except:
        return jsonify({"mensaje": "El producto_id debe ser numérico"}), 400

    if producto_id <= 0:
        return jsonify({"mensaje": "El producto_id debe ser mayor a 0"}), 400

    if not existe_producto(producto_id):
        return jsonify({"mensaje": "El producto no existe"}), 400

    if existe_inventario(producto_id):
        return jsonify({"mensaje": "El inventario ya existe para este producto"}), 400

    p = registro(producto_id=producto_id)
    return jsonify({"mensaje": "Inventario registrado", "datos": p}), 201


def cntActualizar(id):
    """Solo se puede actualizar el stock_minimo manualmente.
    El stock_actual lo manejan los triggers automáticamente."""

    if not str(id).isdigit():
        return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    if not request.json:
        return jsonify({"mensaje": "Debe enviar datos"}), 400

    stock_minimo = request.json.get('stock_minimo')

    if stock_minimo is None:
        return jsonify({"mensaje": "Debe enviar el campo stock_minimo"}), 400

    try:
        stock_minimo = int(stock_minimo)
    except:
        return jsonify({"mensaje": "El stock_minimo debe ser un número entero"}), 400

    if stock_minimo < 0:
        return jsonify({"mensaje": "El stock_minimo no puede ser negativo"}), 400

    inventario_actual = obtener_inventario(id)
    if not inventario_actual:
        return jsonify({"mensaje": "Inventario no encontrado"}), 404

    if stock_minimo == inventario_actual["stock_minimo"]:
        return jsonify({"mensaje": "No hay cambios para actualizar"}), 400

    actualizado = actualizar_stock_minimo(id, stock_minimo)
    if not actualizado:
        return jsonify({"mensaje": "No se pudo actualizar"}), 400

    return jsonify({"mensaje": "Stock mínimo actualizado correctamente"}), 200


def cntObtenerInventario(id):
    if not str(id).isdigit():
        return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    inventario = obtener_inventario(id)
    if not inventario:
        return jsonify({"mensaje": "Inventario no encontrado"}), 404

    return jsonify(inventario), 200


def cntProductosBajoStock():
    """Retorna los productos que están por debajo del stock mínimo."""
    try:
        datos = productos_bajo_stock()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    



def cntActualizarCantidades(id):
    """
    Edicion manual de stock_actual (bandejas) y unidades_sueltas.
    A diferencia del stock_actual, que normalmente solo mueven los triggers
    de venta/anulacion, este endpoint permite al dueño corregir el inventario
    a mano (ej: conteo fisico). El resultado se normaliza automaticamente
    (si las sueltas igualan o superan unidades_por_bandeja, se forman
    bandejas completas) y queda registrado en auditoria.
    """
    if not str(id).isdigit():
        return jsonify({"mensaje": "El id debe ser un numero entero"}), 400
 
    if not request.json:
        return jsonify({"mensaje": "Debe enviar datos"}), 400
 
    requeridos = ["stock_actual", "unidades_sueltas", "usuario_id"]
    faltantes = [x for x in requeridos if x not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400
 
    try:
        stock_actual = int(request.json["stock_actual"])
        unidades_sueltas = int(request.json["unidades_sueltas"])
        usuario_id = int(request.json["usuario_id"])
    except (ValueError, TypeError):
        return jsonify({
            "mensaje": "stock_actual, unidades_sueltas y usuario_id deben ser numeros enteros"
        }), 400
 
    inventario_actual = obtener_inventario(id)
    if not inventario_actual:
        return jsonify({"mensaje": "Inventario no encontrado"}), 404
 
    usuario_db = obtener_usuario(usuario_id)
    if not usuario_db:
        return jsonify({"mensaje": f"el usuario con id {usuario_id} no existe"}), 404
 
    sin_cambios = (
        stock_actual == inventario_actual["stock_actual"]
        and unidades_sueltas == inventario_actual["unidades_sueltas"]
    )
    if sin_cambios:
        return jsonify({"mensaje": "No hay cambios para actualizar"}), 400
 
    try:
        resultado = actualizar_cantidades(id, stock_actual, unidades_sueltas, usuario_id)
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 400
 
    if not resultado:
        return jsonify({"mensaje": "No se pudo actualizar"}), 400
 
    return jsonify({
        "mensaje": "Cantidades actualizadas correctamente",
        "datos": resultado
    }), 200