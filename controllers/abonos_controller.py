from flask import jsonify , request
from  services.abono_services import listado_abonos



def cntListado():
    try:
        datos = listado_abonos()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500