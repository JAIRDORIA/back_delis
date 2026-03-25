class productos:
      def __init__(self, id, nombre, descripcion, precio_venta, unidades_por_bandeja, activo, created_at, updated_at):
          self.id                   = id
          self.nombre               = nombre
          self.descripcion          = descripcion
          self.precio_venta         = precio_venta
          self.unidades_por_bandeja = unidades_por_bandeja  
          self.activo               = activo
          self.created_at           = created_at
          self.updated_at           = updated_at
      def toDic(self):
          return {
               "id":self.id                                     ,
               "nombre":self.nombre                             ,
               "descripcion":self.descripcion                   ,
               "precio_venta":self.precio_venta                 ,
               "unidades_por_bandeja":self.unidades_por_bandeja ,
               "activo":self.activo                             ,
               "created_at":self.created_at                     ,
               "updated_at":self.updated_at
          }      