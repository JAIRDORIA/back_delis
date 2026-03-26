class inventarios:
      def __init__(self, id, producto_id, stock_actual, unidades_sueltas, stock_minimo, updated_at):
          self.id               = id
          self.producto_id      = producto_id
          self.stock_actual     = stock_actual
          self.unidades_sueltas = unidades_sueltas
          self.stock_minimo     = stock_minimo
          self.updated_at       = updated_at
      def toDic(self):
          return {
               "id":self.id                             ,
               "producto_id":self.producto_id           ,
               "stock_actual":self.stock_actual         ,
               "unidades_sueltas":self.unidades_sueltas ,
               "stock_minimo":self.stock_minimo         ,
               "updated_at":self.updated_at
          } 