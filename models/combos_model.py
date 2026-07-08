class combos:
    def __init__(self, id, nombre, descripcion, precio_frito,precio_congelado,activo,created_at,updated_at):
        self.ID_Combos   = id
        self.Comb_Nombre   = nombre
        self.Comb_Descripcion = descripcion
        self.Comb_Precio_frito = precio_frito
        self.Comb_Precio_congelado= precio_congelado
        self.Comb_Activo   = activo
        self.Comb_Creado   = created_at
        self.Comb_Actualizado = updated_at


    def toDic(self):
       return {
        "id": self.ID_Combos,
        "nombre": self.Comb_Nombre,
        "descripcion": self.Comb_Descripcion,
        "precio_frito": float(self.Comb_Precio_frito),
        "precio_congelado" :float(self.Comb_Precio_congelado) ,
        "activo": self.Comb_Activo,
        "created_at": str(self.Comb_Creado),
        "updated_at": str(self.Comb_Actualizado)
    }
      