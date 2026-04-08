from flask import current_app
from models.venta_model import Ventas
from datetime import datetime


def listado_ventas():
    c = current_app.mysql.connection.cursor()
    sql = """
    SELECT v.id, v.cliente_id, c.nombre, v.corte_id, v.usuario_id,
           v.fecha_venta, v.fecha_entrega, v.total,
           v.total_abonado, v.saldo_pendiente, v.estado
    FROM ventas v
    inner JOIN clientes c ON c.id = v.cliente_id
    """
    c.execute(sql)
    datos = c.fetchall()
    c.close()
    lista = []
    for p in datos:
        venta = Ventas(
        id              = p[0],
        cliente_id      = p[1],
        nombre_cliente  = p[2],  
        corte_id        = p[3],
        usuario_id      = p[4],
        fecha_venta     = p[5],
        fecha_entrega   = p[6],
        total           = p[7],
        total_abonado   = p[8],
        saldo_pendiente = p[9],
        estado          = p[10]
        ).to_dict()
        lista.append(venta)
    return lista

    
    
    
    
  
def registro(cliente_id, corte_id, usuario_id,
             fecha_entrega, total, total_abonado):
    
    # Convierte fecha de DD/MM/YYYY a YYYY-MM-DD
    try:
        fecha_entrega = datetime.strptime(
            fecha_entrega, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        pass

    c = current_app.mysql.connection.cursor()
    sql = """
    INSERT INTO ventas (cliente_id, corte_id, usuario_id,
                        fecha_entrega, total, total_abonado)
    VALUES (%s, %s, %s, %s, %s, %s)"""
    c.execute(sql, (cliente_id, corte_id, usuario_id,
                    fecha_entrega, total, total_abonado))
    current_app.mysql.connection.commit()
    id = c.lastrowid

    # Consulta el registro completo con JOIN para traer nombre cliente
    c.execute("""
    SELECT v.id, v.cliente_id, c.nombre, v.corte_id, v.usuario_id,
           v.fecha_venta, v.fecha_entrega, v.total,
           v.total_abonado, v.saldo_pendiente, v.estado
    FROM ventas v
    JOIN clientes c ON c.id = v.cliente_id
    WHERE v.id = %s
    """, (id,))
    venta = c.fetchone()
    c.close()

    return {
        "id"              : venta[0],
        "cliente_id"      : venta[1],
        "nombre_cliente"  : venta[2],
        "corte_id"        : venta[3],
        "usuario_id"      : venta[4],
        "fecha_venta"     : str(venta[5]),
        "fecha_entrega"   : str(venta[6]),
        "total"           : float(venta[7]),
        "total_abonado"   : float(venta[8]),
        "saldo_pendiente" : float(venta[9]),
        "estado"          : venta[10]
    }
    
    

def obtener_venta(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT v.id, v.cliente_id, c.nombre, v.corte_id, v.usuario_id,
               v.fecha_venta, v.fecha_entrega, v.total,
               v.total_abonado, v.saldo_pendiente, v.estado
        FROM ventas v
        JOIN clientes c ON c.id = v.cliente_id
        WHERE v.id = %s
    """, (id,))
    venta = c.fetchone()
    c.close()
    if venta:
        return {
            "id"              : venta[0],
            "cliente_id"      : venta[1],
            "nombre_cliente"  : venta[2],
            "corte_id"        : venta[3],
            "usuario_id"      : venta[4],
            "fecha_venta"     : str(venta[5]),
            "fecha_entrega"   : str(venta[6]),
            "total"           : float(venta[7]),
            "total_abonado"   : float(venta[8]),
            "saldo_pendiente" : float(venta[9]),
            "estado"          : venta[10]
        }
    return None