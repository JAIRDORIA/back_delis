class produccion:

    def _init_(self, id, Cantidad, Fecha, IdProduct):
        self.ID_Produccion                  = id
        self.PRO_Cantidad_Producida         =Cantidad
        self.PRO_Fecha                      =Fecha
        self.ID_Producto                    =IdProduct
    def toDic(self):
        return{
            "ID_Produccion":self.ID_Produccion                          ,
            "PRO_Cantidad_Producida ":self.PRO_Cantidad_Producida       ,
            "PRO_Fecha":self.PRO_Fecha                                  ,
            "ID_Producto":self.ID_Producto                              , 
        }