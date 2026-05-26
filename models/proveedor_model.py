class proveedores:
    def __init__(self, id, nombre, telefono, direccion, email, activo=1):
        self.id        = id
        self.nombre    = nombre
        self.telefono  = telefono
        self.direccion = direccion
        self.email     = email
        self.activo    = activo

    def todic(self):
        return {
            "id":        self.id,
            "nombre":    self.nombre,
            "telefono":  self.telefono,
            "direccion": self.direccion,
            "email":     self.email,
            "activo":    self.activo
        }