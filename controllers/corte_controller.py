from flask import jsonify , request
from  services.cortes_services import listado_cortes



def cntListado():
    try:
        datos = listado_cortes()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500