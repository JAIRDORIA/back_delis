from flask import current_app
from models.corte_model import cortes


def listado_cortes(pagina=1, limite=20):
    offset = (pagina - 1) * limite

    c = current_app.mysql.connection.cursor()

    c.execute("SELECT COUNT(*) FROM cortes")
    total = c.fetchone()[0]

    c.execute("""
        SELECT id, numero, fecha_inicio, fecha_cierre,
               estado, saldo_inicial
        FROM cortes
        ORDER BY numero ASC
        LIMIT %s OFFSET %s
    """, (limite, offset))
    datos = c.fetchall()
    c.close()

    lista = []
    for p in datos:
        lista.append({
            "id"           : p[0],
            "numero"       : p[1],
            "fecha_inicio" : str(p[2]) if p[2] else None,
            "fecha_cierre" : str(p[3]) if p[3] else None,
            "estado"       : p[4],
            "saldo_inicial": float(p[5])
        })

    return {
        "total"        : total,
        "pagina"       : pagina,
        "limite"       : limite,
        "total_paginas": -(-total // limite),
        "datos"        : lista
    }

def obtener_corte(id):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT id, numero, fecha_inicio, fecha_cierre, estado, saldo_inicial
        FROM cortes 
        WHERE id = %s
    """, (id,))
    corte = c.fetchone()
    c.close()
    if corte:
        return {
            "id"           : corte[0],
            "numero"       : corte[1],
            "fecha_inicio" : str(corte[2]) if corte[2] else None,
            "fecha_cierre" : str(corte[3]) if corte[3] else None,
            "estado"       : corte[4],
            "saldo_inicial": float(corte[5])
        }
    return None

def registrar_primer_corte():
    c = current_app.mysql.connection.cursor()
    
    # Verificar que no exista ningun corte
    # si ya existe no se puede crear el primer corte de nuevo
    c.execute("SELECT COUNT(*) FROM cortes")
    total = c.fetchone()[0]
    
    if total > 0:
        c.close()
        return None  # ya existen cortes, no hace nada
    
    # Crear corte 1 abierto con fecha inicio ahora
    c.execute("""
        INSERT INTO cortes (numero, fecha_inicio, fecha_cierre, estado, saldo_inicial)
        VALUES (%s, NOW(), NULL, %s, %s)
    """, (1, 'abierto', 0.00))
    
    # Crear corte 2 futuro sin fechas
    c.execute("""
        INSERT INTO cortes (numero, fecha_inicio, fecha_cierre, estado, saldo_inicial)
        VALUES (%s, NULL, NULL, %s, %s)
    """, (2, 'futuro', 0.00))
    
    current_app.mysql.connection.commit()
    
    # Traer el corte 1 recien creado para devolverlo
    c.execute("""
        SELECT id, numero, fecha_inicio, fecha_cierre, estado, saldo_inicial
        FROM cortes WHERE numero = 1
    """)
    corte = c.fetchone()
    c.close()
    
    return {
        "id"           : corte[0],
        "numero"       : corte[1],
        "fecha_inicio" : str(corte[2]) if corte[2] else None,
        "fecha_cierre" : str(corte[3]) if corte[3] else None,
        "estado"       : corte[4],
        "saldo_inicial": float(corte[5])
    }


def cerrar_corte():
    c = current_app.mysql.connection.cursor()
    
    # Buscar el corte actualmente abierto
    c.execute("""
        SELECT id, numero, saldo_inicial
        FROM cortes WHERE estado = 'abierto'
    """)
    corte_abierto = c.fetchone()
    
    # Buscar el corte futuro que pasara a abierto
    c.execute("""
        SELECT id, numero
        FROM cortes WHERE estado = 'futuro'
        ORDER BY numero ASC LIMIT 1
    """)
    corte_futuro = c.fetchone()
    
    # Calcular saldo inicial del proximo corte
    # son los abonos que entraron en el corte actual
    # pero pertenecen a ventas del corte futuro
    c.execute("""
        SELECT COALESCE(SUM(a.monto), 0)
        FROM abonos a
        JOIN ventas v ON v.id = a.venta_id
        WHERE a.corte_id = %s
        AND v.corte_id = %s
    """, (corte_abierto[0], corte_futuro[0]))
    saldo_heredado = c.fetchone()[0]
    
    # 1. Cerrar el corte actual
    c.execute("""
        UPDATE cortes
        SET estado = 'cerrado', fecha_cierre = NOW()
        WHERE id = %s
    """, (corte_abierto[0],))
    
    # 2. Abrir el corte futuro y asignarle fecha inicio ahora
    c.execute("""
        UPDATE cortes
        SET estado = 'abierto', fecha_inicio = NOW(),
            saldo_inicial = %s
        WHERE id = %s
    """, (float(saldo_heredado), corte_futuro[0]))
    
    # 3. Crear el siguiente corte futuro automaticamente
    siguiente_numero = corte_futuro[1] + 1
    c.execute("""
        INSERT INTO cortes (numero, fecha_inicio, fecha_cierre, estado, saldo_inicial)
        VALUES (%s, NULL, NULL, %s, %s)
    """, (siguiente_numero, 'futuro', 0.00))
    
    current_app.mysql.connection.commit()
    
    # Traer el corte recien abierto para devolverlo
    c.execute("""
        SELECT id, numero, fecha_inicio, fecha_cierre, estado, saldo_inicial
        FROM cortes WHERE id = %s
    """, (corte_futuro[0],))
    corte = c.fetchone()
    c.close()
    
    return {
        "id"           : corte[0],
        "numero"       : corte[1],
        "fecha_inicio" : str(corte[2]) if corte[2] else None,
        "fecha_cierre" : str(corte[3]) if corte[3] else None,
        "estado"       : corte[4],
        "saldo_inicial": float(corte[5])
    }
    
    
    

def obtener_corte_abierto():
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT id, numero, fecha_inicio, fecha_cierre, estado, saldo_inicial
        FROM cortes WHERE estado = 'abierto'
    """)
    corte = c.fetchone()
    c.close()
    if corte:
        return {
            "id"           : corte[0],
            "numero"       : corte[1],
            "fecha_inicio" : str(corte[2]) if corte[2] else None,
            "fecha_cierre" : str(corte[3]) if corte[3] else None,
            "estado"       : corte[4],
            "saldo_inicial": float(corte[5])
        }
    return None


def obtener_corte_futuro():
    c = current_app.mysql.connection.cursor()
    c.execute("""
        SELECT id, numero, fecha_inicio, fecha_cierre, estado, saldo_inicial
        FROM cortes WHERE estado = 'futuro'
        ORDER BY numero ASC LIMIT 1
    """)
    corte = c.fetchone()
    c.close()
    if corte:
        return {
            "id"           : corte[0],
            "numero"       : corte[1],
            "fecha_inicio" : str(corte[2]) if corte[2] else None,
            "fecha_cierre" : str(corte[3]) if corte[3] else None,
            "estado"       : corte[4],
            "saldo_inicial": float(corte[5])
        }
    return None


def actualizar_corte(id, estado):
    c = current_app.mysql.connection.cursor()
    c.execute("""
        UPDATE cortes SET estado = %s
        WHERE id = %s
    """, (estado, id))
    current_app.mysql.connection.commit()
    c.close()
    return obtener_corte(id)


def balance_corte_actual():
    c = current_app.mysql.connection.cursor()

    # buscar el corte abierto
    c.execute("""
        SELECT id, numero, fecha_inicio, saldo_inicial
        FROM cortes WHERE estado = 'abierto'
    """)
    corte = c.fetchone()

    if not corte:
        c.close()
        return None

    corte_id = corte[0]

    # total de ventas del corte actual
    c.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE corte_id = %s AND estado != 'anulada'
    """, (corte_id,))
    total_ventas = float(c.fetchone()[0])

    # total de compras del corte actual
    c.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM compras
        WHERE corte_id = %s AND eliminada = 0
    """, (corte_id,))
    total_compras = float(c.fetchone()[0])

    # dinero en caja = ingresos - egresos de movimientos_caja
    c.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN tipo = 'egreso'  THEN monto ELSE 0 END), 0)
        FROM movimientos_caja
        WHERE corte_id = %s
    """, (corte_id,))
    dinero_caja = float(c.fetchone()[0])

    # abonos en efectivo del corte actual
    c.execute("""
        SELECT COALESCE(SUM(monto), 0)
        FROM abonos
        WHERE corte_id = %s AND medio_pago = 'efectivo'
    """, (corte_id,))
    total_efectivo = float(c.fetchone()[0])

    # abonos en transferencia del corte actual
    c.execute("""
        SELECT COALESCE(SUM(monto), 0)
        FROM abonos
        WHERE corte_id = %s AND medio_pago = 'transferencia'
    """, (corte_id,))
    total_transferencia = float(c.fetchone()[0])

    c.close()

    return {
        "corte_numero"      : corte[1],
        "fecha_inicio"      : str(corte[2]) if corte[2] else None,
        "saldo_inicial"     : float(corte[3]),
        "total_ventas"      : total_ventas,
        "total_compras"     : total_compras,
        "dinero_caja"       : dinero_caja,
        "total_efectivo"    : total_efectivo,
        "total_transferencia": total_transferencia,
        "resultado"         : total_ventas - total_compras
    }