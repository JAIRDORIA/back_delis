class produccion_empleado:
    """
    Fila de `producciones_empleado` mas los nombres que vienen de los JOIN con
    `empleados` y `productos` (mismo patron que venta_model con nombre_cliente).
    """

    def __init__(self, id, empleado_id, empleado_nombre, producto_id, producto_nombre,
                 bandejas, unidades_sueltas, convertido, created_at):
        self.id               = id
        self.empleado_id      = empleado_id
        self.empleado_nombre  = empleado_nombre
        self.producto_id      = producto_id
        self.producto_nombre  = producto_nombre
        self.bandejas         = bandejas
        self.unidades_sueltas = unidades_sueltas
        self.convertido       = convertido
        self.created_at       = created_at

    def toDic(self):
        return {
            "id":               self.id,
            "empleado_id":      self.empleado_id,
            "empleado_nombre":  self.empleado_nombre,
            "producto_id":      self.producto_id,
            "producto_nombre":  self.producto_nombre,
            "bandejas":         self.bandejas,
            "unidades_sueltas": self.unidades_sueltas,
            "convertido":       self.convertido,
            "created_at":       str(self.created_at) if self.created_at is not None else None,
        }
