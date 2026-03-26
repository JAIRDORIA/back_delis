from flask import jsonify , request
from  services.usuarios_servicies import listado_usuarios



def cntListado():
    try:
        datos = listado_usuarios()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500