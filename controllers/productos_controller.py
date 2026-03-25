from flask import jsonify , request
from  services.productos_services import listado_productos

def cntListado():
    try:
        datos = listado_productos()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500