# abono_model.py
class Abono:
    def __init__(self, id, venta_id, corte_id, usuario_id,
                 monto, fecha, observacion, medio_pago):
        self.id          = id
        self.venta_id    = venta_id
        self.corte_id    = corte_id
        self.usuario_id  = usuario_id
        self.monto       = monto
        self.fecha       = fecha
        self.observacion = observacion
        self.medio_pago  = medio_pago

    def to_dict(self):
        return {
            "id"         : self.id,
            "venta_id"   : self.venta_id,
            "corte_id"   : self.corte_id,
            "usuario_id" : self.usuario_id,
            "monto"      : float(self.monto),
            "fecha"      : str(self.fecha),
            "observacion": self.observacion,
            "medio_pago" : self.medio_pago
        }
           