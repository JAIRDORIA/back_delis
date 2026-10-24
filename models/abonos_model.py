
class Abono:
    def __init__(self, id, venta_id, corte_id, usuario_id,
                 monto, fecha, observacion, medio_pago,venta_estado,venta_saldo_pendiente,nombre_cliente,
                 medio_pago_id=None, medio_pago_nombre=None, es_domicilio=None):
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
        self.medio_pago_id    = medio_pago_id
        self.medio_pago_nombre = medio_pago_nombre
        self.es_domicilio     = es_domicilio
        
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
            "medio_pago_id"    : self.medio_pago_id,
            "medio_pago_nombre": self.medio_pago_nombre,
            "es_domicilio"     : bool(self.es_domicilio) if self.es_domicilio is not None else False,
            "venta_estado" :self.venta_estado,
            "venta_saldo_pendiente" :float(self.venta_saldo_pendiente),
            "nombre_cliente" : self.nombre_cliente
        }
           