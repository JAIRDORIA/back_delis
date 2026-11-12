class compra:
    def __init__(self, id, proveedor_id, corte_id, usuario_id, fecha,medio_pago, total, descripcion=None,
                 medio_pago_id=None, medio_pago_nombre=None,
                 categoria='insumo', venta_id=None, venta_cliente=None, venta_estado=None):
        self.id           = id
        self.proveedor_id = proveedor_id
        self.corte_id     = corte_id
        self.usuario_id   = usuario_id
        self.fecha        = fecha
        self.total        = total
        self.descripcion  = descripcion
        self.medio_pago = medio_pago
        self.medio_pago_id    = medio_pago_id
        self.medio_pago_nombre = medio_pago_nombre
        # 'insumo' (default, sin venta) o 'domicilio' (pago al domiciliario,
        # ligado obligatoriamente a una venta).
        self.categoria     = categoria
        self.venta_id      = venta_id
        # Datos minimos de la venta ligada (solo para mostrar en el listado).
        self.venta_cliente = venta_cliente
        self.venta_estado  = venta_estado

    def toDic(self):
        return {
            "id":           self.id,
            "proveedor_id": self.proveedor_id,
            "corte_id":     self.corte_id,
            "usuario_id":   self.usuario_id,
            "fecha":        str(self.fecha),
            "medio_pago": self.medio_pago,
            "medio_pago_id"    : self.medio_pago_id,
            "medio_pago_nombre": self.medio_pago_nombre,
            "total":        float(self.total) if self.total is not None else None,
            "descripcion":  self.descripcion,
            "categoria":    self.categoria,
            "venta_id":     self.venta_id,
            "venta_cliente": self.venta_cliente,
            "venta_estado": self.venta_estado
        }