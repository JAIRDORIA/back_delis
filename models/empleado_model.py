class empleados:
    def __init__(self, id, nombre, activo=1, created_at=None, updated_at=None):
        self.id         = id
        self.nombre     = nombre
        self.activo     = activo
        self.created_at = created_at
        self.updated_at = updated_at

    def toDic(self):
        return {
            "id":         self.id,
            "nombre":     self.nombre,
            "activo":     self.activo,
            "created_at": str(self.created_at) if self.created_at is not None else None,
            "updated_at": str(self.updated_at) if self.updated_at is not None else None,
        }
