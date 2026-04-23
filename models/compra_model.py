class compra:
    def __init__(self, id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion=None):
        self.id           = id
        self.proveedor_id = proveedor_id
        self.corte_id     = corte_id
        self.usuario_id   = usuario_id
        self.fecha        = fecha
        self.total        = total
        self.descripcion  = descripcion

    def toDic(self):
        return {
            "id":           self.id,
            "proveedor_id": self.proveedor_id,
            "corte_id":     self.corte_id,
            "usuario_id":   self.usuario_id,
            "fecha":        str(self.fecha),
            "total":        float(self.total) if self.total is not None else None,
            "descripcion":  self.descripcion
        }