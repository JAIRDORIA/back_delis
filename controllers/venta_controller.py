from flask import jsonify , request
from  services.ventas_services import listado_ventas,registro, obtener_venta,actualizar_venta, anular_venta,generar_comprobante
from services.clientes_services import obtener_cliente
from services.cortes_services import obtener_corte ,obtener_corte_abierto, obtener_corte_futuro
from services.usuarios_servicies import obtener_usuario
from datetime import datetime
from services.ventas_services import obtener_venta_detalle,actualizar_detalle_venta
from zoneinfo import ZoneInfo


def cntListado():
    try:
        pagina   = request.args.get("pagina",   1,    type=int)
        limite   = request.args.get("limite",   20,   type=int)
        corte_id = request.args.get("corte_id", None, type=int)
        q        = request.args.get("q",        None, type=str) 
        cliente_id = request.args.get("cliente_id", None, type=int)

        if pagina < 1:
            return jsonify({"mensaje": "la pagina debe ser mayor a 0"}), 400
        if limite < 1 or limite > 200:
            return jsonify({"mensaje": "el limite debe ser entre 1 y 100"}), 400

        datos = listado_ventas(pagina, limite, corte_id,q,cliente_id)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"errores": str(e)}), 500


def cntActualizarDetalle(id):
    try:
        data = request.get_json()
        detalle = data.get('detalle', [])

        if not detalle or not isinstance(detalle, list):
            return jsonify({"mensaje": "El campo 'detalle' es requerido y debe ser un array"}), 400

        
        for item in detalle:
            if not all(k in item for k in ( 'nombre_producto', 'cantidad', 'precio_unitario')):
                return jsonify({"mensaje": "Cada producto debe tener producto_id, nombre_producto, cantidad y precio_unitario"}), 400
            if item.get('tipo', 'producto') == 'producto' and 'producto_id' not in item:
                return jsonify({"mensaje": "Los productos deben tener producto_id"}), 400
            
            
            if item.get('tipo') == 'combo' and 'combo_id' not in item:
                return jsonify({"mensaje": "Los combos deben tener combo_id"}), 400
            
            if item['cantidad'] <= 0 or item['precio_unitario'] <= 0:
                return jsonify({"mensaje": "La cantidad y el precio deben ser mayores a 0"}), 400

        
        resultado = actualizar_detalle_venta(id, detalle)
        if resultado is None:
            return jsonify({"mensaje": f"La venta con id {id} no existe o no está pendiente"}), 404

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntDetalle(id):
    try:
        datos = obtener_venta_detalle(id)
        if not datos:
            return jsonify({"mensaje": f"la venta con id {id} no existe"}), 404
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


def cntGenerarComprobante(id):
    try:
        venta = obtener_venta(id)
        if not venta:
            return jsonify({"mensaje": f"la venta con id {id} no existe"}), 404

        resultado = generar_comprobante(id)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntregistrar():
    try:
        
        requeridos = ["cliente_id", "corte_id", "usuario_id",
                      "fecha_entrega", "total", "detalle"]
        faltantes = [x for x in requeridos if x not in request.json]
        if faltantes:
            return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

        
        vacios = [x for x in requeridos if request.json[x] == ""
                  or request.json[x] is None]
        if vacios:
            return jsonify({"mensaje": f"los siguientes campos estan vacios {vacios}"}), 400

        id_cliente    = request.json["cliente_id"]
        corte         = request.json["corte_id"]
        usuario       = request.json["usuario_id"]
        fecha_entrega = request.json["fecha_entrega"]
        total         = request.json["total"]
        detalle       = request.json["detalle"]
        abono_inicial = request.json.get("abono_inicial", None)
        
        
        
        formatos = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  
            "%Y-%m-%dT%H:%M:%SZ",     
            "%Y-%m-%dT%H:%M:%S",      
            "%Y-%m-%d %H:%M:%S",      
            "%Y-%m-%d %H:%M",         
            "%Y-%m-%d",               
            ]
        
        fecha_convertida = None
        for formato in formatos:
            try:
                fecha_convertida = datetime.strptime(fecha_entrega, formato)
                break
            except ValueError:
                continue

        if not fecha_convertida:
            return jsonify({
        "mensaje": "formato de fecha incorrecto"
                }), 400

       
        if not detalle or len(detalle) == 0:
            return jsonify({"mensaje": "la venta debe tener al menos un producto"}), 400

        
        for item in detalle:
            if "producto_id" not in item:
                return jsonify({"mensaje": "cada producto debe tener producto_id"}), 400
            if "nombre_producto" not in item:
                return jsonify({"mensaje": "cada producto debe tener nombre_producto"}), 400
            if "cantidad" not in item:
                return jsonify({"mensaje": "cada producto debe tener cantidad"}), 400
            if "precio_unitario" not in item:
                return jsonify({"mensaje": "cada producto debe tener precio_unitario"}), 400
            if item["cantidad"] <= 0:
                return jsonify({"mensaje": "la cantidad debe ser mayor a 0"}), 400
            if item["precio_unitario"] <= 0:
                return jsonify({"mensaje": "el precio unitario debe ser mayor a 0"}), 400

        
        total_calculado = sum(
            item["cantidad"] * item["precio_unitario"] for item in detalle
        )
        if total != total_calculado:
            return jsonify({
                "mensaje": f"el total {total} no coincide con el detalle {total_calculado}"
            }), 400

        
        abonos_iniciales = []
        if "abonos_iniciales" in request.json:
            
            abonos_iniciales = request.json["abonos_iniciales"]
            if not isinstance(abonos_iniciales, list):
                return jsonify({"mensaje": "abonos_iniciales debe ser un array"}), 400
            for abono in abonos_iniciales:
                if "monto" not in abono or abono["monto"] <= 0:
                  return jsonify({"mensaje": "cada abono debe tener monto mayor a 0"}), 400
                if "medio_pago" not in abono:
                    return jsonify({"mensaje": "cada abono debe tener medio_pago"}), 400
                medios_validos = ["efectivo", "transferencia", "otro"]
                if abono["medio_pago"] not in medios_validos:
                    return jsonify({"mensaje": f"medio_pago invalido, debe ser: {medios_validos}"}), 400
        elif "abono_inicial" in request.json and request.json["abono_inicial"]:
                
            abono_antiguo = request.json["abono_inicial"]
            if abono_antiguo.get("monto", 0) > 0:
                abonos_iniciales = [abono_antiguo]

        
        suma_abonos = sum(a["monto"] for a in abonos_iniciales)
        if suma_abonos > total:
            return jsonify({"mensaje": "la suma de los abonos no puede superar el total"}), 400

       
        cliente_db = obtener_cliente(id_cliente)
        if not cliente_db:
            return jsonify({"mensaje": f"el cliente con id {id_cliente} no existe"}), 404

        
        corte_db = obtener_corte(corte)
        if not corte_db:
            return jsonify({"mensaje": f"el corte con id {corte} no existe"}), 404
        if corte_db["estado"] == "cerrado":
            return jsonify({"mensaje": "no puedes registrar ventas en un corte cerrado"}), 400

       
        usuario_db = obtener_usuario(usuario)
        if not usuario_db:
            return jsonify({"mensaje": f"el usuario con id {usuario} no existe"}), 404

        
        if total <= 0:
            return jsonify({"mensaje": "el total debe ser mayor a 0"}), 400

        
        

        fecha_convertida = fecha_convertida.replace(tzinfo=ZoneInfo("America/Bogota"))
        fecha_utc = fecha_convertida.astimezone(ZoneInfo("UTC"))
        fecha_entrega = fecha_utc.strftime("%Y-%m-%d %H:%M:%S")

        p = registro(id_cliente, corte, usuario, fecha_entrega,
                     total, detalle, abonos_iniciales)
        return jsonify({"mensaje": "venta registrada", "datos": p}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntActualizar(id):
    try:
        
        venta = obtener_venta(id)
        if not venta:
            return jsonify({"mensaje": f"la venta con id {id} no existe"}), 404

        
        if venta["estado"] != "pendiente":
            return jsonify({"mensaje": "solo puedes editar ventas en estado pendiente"}), 400

        
        fecha_entrega = request.json.get("fecha_entrega", venta["fecha_entrega"])
        total         = request.json.get("total",         venta["total"])
        estado        = request.json.get("estado",        venta["estado"])

        
        estados_validos = ["pendiente", "entregada", "anulada"]
        if estado not in estados_validos:
            return jsonify({"mensaje": f"estado invalido, debe ser: {estados_validos}"}), 400

       
        if total <= 0:
            return jsonify({"mensaje": "el total debe ser mayor a 0"}), 400

        
        formatos = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            ]

        fecha_convertida = None
        for formato in formatos:
            try:
               fecha_convertida = datetime.strptime(fecha_entrega, formato)
               break
            except ValueError:
                continue

        if fecha_convertida:
            fecha_entrega = fecha_convertida.strftime("%Y-%m-%d %H:%M:%S")
       
        resultado = actualizar_venta(id, fecha_entrega, total, estado)
        return jsonify({"mensaje": "venta actualizada", "datos": resultado}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cntAnular(id):
    try:
        
        venta = obtener_venta(id)
        if not venta:
            return jsonify({"mensaje": f"la venta con id {id} no existe"}), 404

        
        if venta["estado"] == "anulada":
            return jsonify({"mensaje": "la venta ya esta anulada"}), 400
        
        if venta["estado"] == "entregada":
            return jsonify({"mensaje": "la venta ya esta entregada, no se puede anular"}), 400

        

        
        corte_abierto = obtener_corte_abierto()
        corte_futuro  = obtener_corte_futuro()
        cortes_validos = [corte_abierto["id"], corte_futuro["id"]]

        if venta["corte_id"] not in cortes_validos:
            return jsonify({
                "mensaje": "solo puedes anular ventas del corte actual o del corte futuro"
            }), 400

        resultado = anular_venta(id)
        return jsonify({"mensaje": "venta anulada correctamente", "datos": resultado}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500