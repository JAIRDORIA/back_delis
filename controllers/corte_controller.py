from flask import jsonify , request
from  services.cortes_services import listado_cortes,registrar_primer_corte, cerrar_corte,obtener_corte ,obtener_corte_abierto  , obtener_corte_futuro, actualizar_corte



def cntListado():
    try:
        datos = listado_cortes()
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    



def cntPrimerCorte():
    try:
        # Intentar crear el primer corte
        resultado = registrar_primer_corte()
        
        # Si retorna None significa que ya existen cortes
        # el primer corte solo se puede crear una vez
        if resultado is None:
            return jsonify({
                "mensaje": "ya existen cortes registrados, no puedes iniciar de nuevo"
            }), 400
        
        return jsonify({
            "mensaje": "primer corte iniciado correctamente",
            "datos": resultado
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntCerrarCorte():
    try:
        # Verificar que existe un corte abierto
        c_abierto = obtener_corte_abierto()
        if not c_abierto:
            return jsonify({
                "mensaje": "no existe ningun corte abierto en este momento"
            }), 400
        
        # Verificar que existe un corte futuro
        # sin corte futuro no se puede cerrar el actual
        c_futuro = obtener_corte_futuro()
        if not c_futuro:
            return jsonify({
                "mensaje": "no existe corte futuro, contacte al administrador"
            }), 400
        
        resultado = cerrar_corte()
        
        return jsonify({
            "mensaje": f"corte #{c_abierto['numero']} cerrado correctamente, corte #{c_futuro['numero']} ahora esta abierto",
            "datos": resultado
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
   

def cntActualizar(id):  # ← agrégale el id aquí
    try:
        requeridos = ["estado"]
        faltantes = [x for x in requeridos if x not in request.json]
        if faltantes:
            return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

        estado = request.json["estado"]

        # validar que el corte existe
        corte = obtener_corte(id)  # ← usa el id de e la URL
        if not corte:
            return jsonify({"mensaje": f"el corte con id {id} no existe"}), 404

        # no permitir modificar un corte cerrado
        if corte["estado"] == "cerrado":
            return jsonify({"mensaje": "no puedes modificar un corte cerrado"}), 400

        # validar estado enviado
        estados_validos = ["abierto", "futuro"]
        if estado not in estados_validos:
            return jsonify({"mensaje": f"estado invalido, debe ser: {estados_validos}"}), 400

        resultado = actualizar_corte(id, estado)
        return jsonify({"mensaje": "corte actualizado", "datos": resultado}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500