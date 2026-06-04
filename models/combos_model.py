class combos:
    def __init__(self, id, nombre, descripcion, precio,activo,created_at,updated_at):
        self.ID_Combos   = id
        self.Comb_Nombre   = nombre
        self.Comb_Descripcion = descripcion
        self.Comb_Precio = precio
        self.Comb_Activo   = activo
        self.Comb_Creado   = created_at
        self.Comb_Actualizado = updated_at


    def toDic(self):
       return {
        "id": self.ID_Combos,
        "nombre": self.Comb_Nombre,
        "descripcion": self.Comb_Descripcion,
        "precio": self.Comb_Precio,
        "activo": self.Comb_Activo,
        "created_at": str(self.Comb_Creado),
        "updated_at": str(self.Comb_Actualizado)
    }
      