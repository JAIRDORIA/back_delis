class cliente:
    def __init__(self, id, nombre, telefono, direccion, email,activo,created_at,updated_at):
        self.ID_Cliente   = id
        self.Cli_Nombre   = nombre
        self.Cli_Telefono = telefono
        self.Cli_Direccion = direccion
        self.Cli_email   = email
        self.Cli_Activo   = activo
        self.Cli_Creado   = created_at
        self.Cli_Actualizado = updated_at
          
    def toDic(self):
          return {
            "ID_Cliente":self.ID_Cliente     ,
            "Cli_Nombre":self.Cli_Nombre     ,
            "Cli_Telefono":self.Cli_Telefono ,
            "Cli_Direccion":self.Cli_Direccion ,
            "Cli_email":self.Cli_email ,
            "Cli_Activo":self.Cli_Activo ,
            "Cli_Creado":self.Cli_Creado ,
            "Cli_Actualizado":self.Cli_Actualizado
          }
      