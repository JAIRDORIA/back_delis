class compra:
    def __init__(self, id, proveedor_id, corte_id, usuario_id, fecha,medio_pago, total, descripcion=None):
        self.id           = id
        self.proveedor_id = proveedor_id
        self.corte_id     = corte_id
        self.usuario_id   = usuario_id
        self.fecha        = fecha
        self.total        = total
        self.descripcion  = descripcion
        self.medio_pago = medio_pago

    def toDic(self):
        return {
            "id":           self.id,
            "proveedor_id": self.proveedor_id,
            "corte_id":     self.corte_id,
            "usuario_id":   self.usuario_id,
            "fecha":        str(self.fecha),
            "medio_pago": self.medio_pago,
            "total":        float(self.total) if self.total is not None else None,
            "descripcion":  self.descripcion
        }