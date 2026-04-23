from flask import jsonify, request
from datetime import datetime
from services.abono_services import (
    listado_abonos, registro, obtener_abono,
    actualizar_abono, eliminar_abono
)
from services.ventas_services import obtener_venta
from services.cortes_services import obtener_corte, obtener_corte_abierto
from services.usuarios_servicies import obtener_usuario

def cntListado():
    try:
        pagina = request.args.get("pagina", 1, type=int)
        limite = request.args.get("limite", 20, type=int)

        if pagina < 1:
            return jsonify({"mensaje": "la pagina debe ser mayor a 0"}), 400
        if limite < 1 or limite > 100:
            return jsonify({"mensaje": "el limite debe ser entre 1 y 100"}), 400

        datos = listado_abonos(pagina, limite)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntregistrar():
    try:
        requeridos = ["venta_id", "corte_id", "usuario_id",
                      "monto", "fecha", "medio_pago"]
        faltantes = [x for x in requeridos if x not in request.json]
        if faltantes:
            return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

        vacios = [x for x in requeridos if request.json[x] == ""
                  or request.json[x] is None]
        if vacios:
            return jsonify({"mensaje": f"los siguientes campos estan vacios {vacios}"}), 400

        id_venta   = request.json["venta_id"]
        corte      = request.json["corte_id"]
        usuario    = request.json["usuario_id"]
        monto      = request.json["monto"]
        fecha      = request.json["fecha"]
        medio_pago = request.json["medio_pago"]
        obs        = request.json.get("observacion", None)

        medios_validos = ["efectivo", "transferencia", "otro"]
        if medio_pago not in medios_validos:
            return jsonify({"mensaje": f"medio de pago invalido, debe ser: {medios_validos}"}), 400

        venta_db = obtener_venta(id_venta)
        if not venta_db:
            return jsonify({"mensaje": f"la venta con id {id_venta} no existe"}), 404

        if venta_db["estado"] == "entregada":
            return jsonify({"mensaje": "no puedes abonar a una venta ya entregada"}), 400

        if venta_db["estado"] == "anulada":
            return jsonify({"mensaje": "no puedes abonar a una venta anulada"}), 400

        corte_db = obtener_corte(corte)
        if not corte_db:
            return jsonify({"mensaje": f"el corte con id {corte} no existe"}), 404
        if corte_db["estado"] == "cerrado":
            return jsonify({"mensaje": "no puedes registrar abonos en un corte cerrado"}), 400

        usuario_db = obtener_usuario(usuario)
        if not usuario_db:
            return jsonify({"mensaje": f"el usuario con id {usuario} no existe"}), 404

        if monto <= 0:
            return jsonify({"mensaje": "el monto debe ser mayor a 0"}), 400

        if monto > venta_db["saldo_pendiente"]:
            return jsonify({
                "mensaje": f"el abono de ${monto} supera el saldo pendiente de ${venta_db['saldo_pendiente']}"
            }), 400

        try:
            fecha = datetime.strptime(fecha, "%d/%m/%Y")
        except ValueError:
            return jsonify({"mensaje": "formato de fecha incorrecto, use DD/MM/YYYY"}), 400

        if fecha.date() < datetime.now().date():
            return jsonify({"mensaje": "la fecha del abono no puede ser en el pasado"}), 400

        fecha = fecha.strftime("%Y-%m-%d")

        p = registro(id_venta, corte, usuario, monto, fecha, obs, medio_pago)
        return jsonify({"mensaje": "abono registrado", "datos": p}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntActualizar(id):
    try:
        requeridos = ["monto", "fecha", "medio_pago"]
        faltantes = [x for x in requeridos if x not in request.json]
        if faltantes:
            return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

        vacios = [x for x in requeridos if request.json[x] == ""
                  or request.json[x] is None]
        if vacios:
            return jsonify({"mensaje": f"los siguientes campos estan vacios {vacios}"}), 400

        monto       = request.json["monto"]
        fecha       = request.json["fecha"]
        medio_pago  = request.json["medio_pago"]
        observacion = request.json.get("observacion", None)

        medios_validos = ["efectivo", "transferencia", "otro"]
        if medio_pago not in medios_validos:
            return jsonify({"mensaje": f"medio de pago invalido, debe ser: {medios_validos}"}), 400

        abono = obtener_abono(id)
        if not abono:
            return jsonify({"mensaje": f"el abono con id {id} no existe"}), 404

        venta = obtener_venta(abono["venta_id"])
        if not venta:
            return jsonify({"mensaje": "la venta asociada no existe"}), 404

        if venta["estado"] != "pendiente":
            return jsonify({"mensaje": "no puedes editar un abono de una venta que no esta pendiente"}), 400

        if monto <= 0:
            return jsonify({"mensaje": "el monto debe ser mayor a 0"}), 400

        maximo = venta["saldo_pendiente"] + abono["monto"]
        if monto > maximo:
            return jsonify({"mensaje": f"el monto no puede superar {maximo}"}), 400

        try:
            fecha_dt = datetime.strptime(fecha, "%d/%m/%Y")
        except ValueError:
            return jsonify({"mensaje": "formato de fecha incorrecto, use DD/MM/YYYY"}), 400

        if fecha_dt.date() < datetime.now().date():
            return jsonify({"mensaje": "la fecha del abono no puede ser en el pasado"}), 400

        fecha = fecha_dt.strftime("%Y-%m-%d")

        resultado = actualizar_abono(id, monto, fecha, observacion, medio_pago)
        return jsonify({"mensaje": "abono actualizado", "datos": resultado}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntEliminar(id):
    try:
        abono = obtener_abono(id)
        if not abono:
            return jsonify({"mensaje": f"el abono con id {id} no existe"}), 404

        venta = obtener_venta(abono["venta_id"])
        if not venta:
            return jsonify({"mensaje": "la venta asociada no existe"}), 404

        if venta["estado"] != "pendiente":
            return jsonify({"mensaje": "no puedes eliminar un abono de una venta que no esta pendiente"}), 400

        corte_abierto = obtener_corte_abierto()
        if abono["corte_id"] != corte_abierto["id"]:
            return jsonify({"mensaje": "solo puedes eliminar abonos del corte actual"}), 400

        resultado = eliminar_abono(id)
        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500