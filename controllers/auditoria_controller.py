from flask import jsonify, request
from services.auditoria_services import listar_auditoria

def cntListado():
    try:
        pagina = request.args.get("pagina", 1, type=int)
        limite = request.args.get("limite", 20, type=int)

        if pagina < 1:
            return jsonify({"mensaje": "La página debe ser mayor a 0"}), 400
        if limite < 1 or limite > 100:
            return jsonify({"mensaje": "El límite debe ser entre 1 y 100"}), 400

        datos = listar_auditoria(pagina, limite)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500