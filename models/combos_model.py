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
            "ID_Combos":self.ID_Combos     ,
            "Comb_Nombre":self.Comb_Nombre     ,
            "Comb_Descripcion":self.Comb_Descripcion ,
            "Comb_Precio":self.Comb_Precio ,
            "Comb_Activo":self.Comb_Activo ,
            "Comb_Creado":self.Comb_Creado ,
            "Comb_Actualizado":self.Comb_Actualizado
          }
      