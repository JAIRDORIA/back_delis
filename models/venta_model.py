    
class Ventas:
    def __init__(self, id, cliente_id, nombre_cliente, corte_id, 
                 usuario_id, fecha_venta, fecha_entrega, total, 
                 total_abonado, saldo_pendiente, estado):
        self.id = id
        self.cliente_id = cliente_id
        self.nombre_cliente = nombre_cliente  # ← viene del JOIN
        self.corte_id = corte_id
        self.usuario_id = usuario_id
        self.fecha_venta = fecha_venta
        self.fecha_entrega = fecha_entrega
        self.total = total
        self.total_abonado = total_abonado
        self.saldo_pendiente = saldo_pendiente
        self.estado = estado

    def to_dict(self):
        return {
            "id"              : self.id,
            "cliente_id"      : self.cliente_id,
            "nombre_cliente"  : self.nombre_cliente,
            "corte_id"        : self.corte_id,
            "usuario_id"      : self.usuario_id,
            "fecha_venta"     : str(self.fecha_venta),
            "fecha_entrega"   : str(self.fecha_entrega),
            "total"           : float(self.total),
            "total_abonado"   : float(self.total_abonado),
            "saldo_pendiente" : float(self.saldo_pendiente),
            "estado"          : self.estado
        }