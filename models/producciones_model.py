class producciones:
      def __init__(self, id, producto_id, cantidad, unidades_sueltas, usuario_id, fecha, observacion, created_at):
          self.id                   = id
          self.producto_id          = producto_id
          self.cantidad             = cantidad
          self.unidades_sueltas     = unidades_sueltas
          self.usuario_id           = usuario_id
          self.fecha                = fecha
          self.observacion          = observacion
          self.created_at           = created_at
      def toDic(self):
          return {
               "id":               self.id                ,
               "producto_id":      self.producto_id       ,
               "cantidad":         self.cantidad          ,
               "unidades_sueltas": self.unidades_sueltas  ,
               "usuario_id":       self.usuario_id        ,
               "fecha":            self.fecha             ,
               "observacion":      self.observacion       ,
               "created_at":       self.created_at                     
          }      