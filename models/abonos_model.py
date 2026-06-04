
class Abono:
    def __init__(self, id, venta_id, corte_id, usuario_id,
                 monto, fecha, observacion, medio_pago,venta_estado,venta_saldo_pendiente,nombre_cliente):
        self.id          = id
        self.venta_id    = venta_id
        self.corte_id    = corte_id
        self.usuario_id  = usuario_id
        self.monto       = monto
        self.fecha       = fecha
        self.observacion = observacion
        self.medio_pago  = medio_pago
        self.venta_estado= venta_estado
        self.venta_saldo_pendiente = venta_saldo_pendiente
        self.nombre_cliente = nombre_cliente
        
    def to_dict(self):
        return {
            "id"         : self.id,
            "venta_id"   : self.venta_id,
            "corte_id"   : self.corte_id,
            "usuario_id" : self.usuario_id,
            "monto"      : float(self.monto),
            "fecha"      : str(self.fecha),
            "observacion": self.observacion,
            "medio_pago" : self.medio_pago,
            "venta_estado" :self.venta_estado,
            "venta_saldo_pendiente" :float(self.venta_saldo_pendiente),
            "nombre_cliente" : self.nombre_cliente
        }
           