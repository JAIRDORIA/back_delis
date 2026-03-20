class cliente:
      def _init_(self, id, nombre, apellido, celular, correo):
          self.ID_Cliente   = id
          self.Cli_Nombre   = nombre
          self.Cli_Apellido = apellido
          self.Cli_Celular  = celular
          self.Cli_Correo   = correo
      def toDic(self):
          return {
               "ID_Cliente":self.ID_Cliente     ,
               "Cli_Nombre":self.Cli_Nombre     ,
               "Cli_Apellido":self.Cli_Apellido ,
               "Cli_Celular":self.Cli_Celular   ,
               "Cli_Correo":self.Cli_Correo 
          }