class usuarios:
      def __init__(self, id, nombre, username, password_hash, rol, activo, created_at, updated_at):
          self.id              = id
          self.nombre          = nombre
          self.username        = username
          self.password_hash   = password_hash
          self.rol             = rol
          self.activo          = activo
          self.created_at      = created_at
          self.updated_at      = updated_at
      def toDic(self):
          return {
               "id":self.id                         ,
               "nombre":self.nombre                 ,
               "username":self.username             ,
               "password_hash":self.password_hash   ,
               "rol":self.rol                       ,
               "activo":self.activo                 ,
               "created_at":self.created_at         ,
               "updated_at":self.updated_at
          } 