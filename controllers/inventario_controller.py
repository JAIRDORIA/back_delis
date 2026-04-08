from flask import jsonify , request
from  services.inventario_services import listado_inventarios, registro, existe_producto, existe_inventario


def cntListado():
    try:
        datos = listado_inventarios()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def cntRegistro():
    #validar en la peticion(body) atributos requeridos
    requeridos = ['producto_id']

    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400
    
    #Validar que no existan campos vacios en los requeridos
    vacios = []
    for clave in request.json:
        if str(request.json[clave]).strip() == "":
            vacios.append(clave)

    if vacios:
        return jsonify({"mensaje": f"los siguientes campos no pueden estar vacios {vacios}"}), 400
    
    #validar que no esten vacios
    producto_id  = request.json['producto_id'] 

    #validar campos 
    try:
        producto_id = int(producto_id)
    except:
        return jsonify({"mensaje": "El producto_id debe ser numérico"}), 400

    # validar positivo
    if producto_id <= 0:
        return jsonify({"mensaje": "El producto_id debe ser mayor a 0"}), 400

    # validar que el producto exista
    if not existe_producto(producto_id):
        return jsonify({"mensaje": "El producto no existe"}), 400

    # validar que no exista inventario
    if existe_inventario(producto_id):
        return jsonify({"mensaje": "El inventario ya existe para este producto"}), 400
    
    p             = registro(producto_id=producto_id)
    return jsonify({"mensaje":"Inventario registrado","datos":p}), 201