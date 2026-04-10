class compra:
    def __init__(self, id, proveedor_id, corte_id, usuario_id, fecha, total, descripcion):
        self.ID_Compra       = id
        self.proveedor_id    = proveedor_id
        self.corte_id        = corte_id
        self.usuario_id      = usuario_id
        self.COM_Fecha       = fecha
        self.COM_Total       = total
        self.COM_Descripcion = descripcion

    def toDic(self):
        return {
            "id"          : self.ID_Compra,
            "proveedor_id": self.proveedor_id,
            "corte_id"    : self.corte_id,
            "usuario_id"  : self.usuario_id,
            "fecha"       : self.COM_Fecha,
            "total"       : self.COM_Total,
            "descripcion" : self.COM_Descripcion
        }