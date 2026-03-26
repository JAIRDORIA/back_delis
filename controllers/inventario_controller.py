from flask import jsonify , request
from  services.inventario_services import listado_inventarios


def cntListado():
    try:
        datos = listado_inventarios()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500