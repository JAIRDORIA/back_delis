    
class Ventas:
    def __init__(self, id, cliente_id, nombre_cliente, corte_id, corte_numero,
                 usuario_id, fecha_venta, fecha_entrega, total, 
                 total_abonado, saldo_pendiente, estado,observacion,
                 valor_domicilio=None, domicilio_pendiente=None,
                 subtotal_productos=None, domicilio_pagado_compra=None,
                 domicilio_pendiente_compra=None, domicilio_compra_completa=None):
        self.id = id
        self.cliente_id = cliente_id
        self.nombre_cliente = nombre_cliente  # ← viene del JOIN
        self.corte_id = corte_id
        self.corte_numero = corte_numero
        self.usuario_id = usuario_id
        self.fecha_venta = fecha_venta
        self.fecha_entrega = fecha_entrega
        self.total = total
        self.total_abonado = total_abonado
        self.saldo_pendiente = saldo_pendiente
        self.estado = estado
        self.observacion= observacion
        self.valor_domicilio = valor_domicilio
        self.domicilio_pendiente = domicilio_pendiente
        # Ingreso real de la venta (sin domicilio) y estado del pago al
        # domiciliario (compras categoria='domicilio' no eliminadas).
        # OJO: domicilio_pendiente es el cobro AL CLIENTE; los campos
        # *_compra son el pago AL DOMICILIARIO. Son cosas distintas.
        self.subtotal_productos = subtotal_productos
        self.domicilio_pagado_compra = domicilio_pagado_compra
        self.domicilio_pendiente_compra = domicilio_pendiente_compra
        self.domicilio_compra_completa = domicilio_compra_completa

    def to_dict(self):
        return {
            "id_venta"              : self.id,
            "cliente_id"      : self.cliente_id,
            "nombre_cliente"  : self.nombre_cliente,
            "corte_id"        : self.corte_id,
            "corte_numero"    :self.corte_numero,
            "usuario_id"      : self.usuario_id,
            "fecha_venta"     : str(self.fecha_venta),
            "fecha_entrega"   : str(self.fecha_entrega),
            "total"           : float(self.total),
            "total_abonado"   : float(self.total_abonado),
            "saldo_pendiente" : float(self.saldo_pendiente),
            "estado"          : self.estado,
            "observacion" : self.observacion,
            "valor_domicilio"      : float(self.valor_domicilio) if self.valor_domicilio is not None else 0.0,
            "domicilio_pendiente"  : float(self.domicilio_pendiente) if self.domicilio_pendiente is not None else 0.0,
            "subtotal_productos"   : float(self.subtotal_productos) if self.subtotal_productos is not None else 0.0,
            "domicilio_pagado_compra"    : float(self.domicilio_pagado_compra) if self.domicilio_pagado_compra is not None else 0.0,
            "domicilio_pendiente_compra" : float(self.domicilio_pendiente_compra) if self.domicilio_pendiente_compra is not None else 0.0,
            "domicilio_compra_completa"  : bool(self.domicilio_compra_completa)
        }