class compra:
      def _init_(self, id, fecha, descripcion, total):
          self.ID_Compra   = id
          self.COM_Fecha   = fecha
          self.COM_Descripcion = descripcion
          self.COM_Total  = total

      def toDic(self):
          return {
               "ID_Compra ":self.ID_Compra            ,
               "COM_Fecha":self.COM_Fecha             ,
               "COM_Descripcion":self.COM_Descripcion ,
               "COM_Total":self.COM_Total  
          }