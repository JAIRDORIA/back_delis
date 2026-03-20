class movimiento_contable:

    def _init_(self, COD, Tipo, Fecha, Monto, Descripcion, Venta, Compra):
        self.COD_Movimiento_Contable        = COD
        self.MVC_Tipo                       =Tipo
        self.MVC_Fecha                      =Fecha
        self.MVC_Monto                      =Monto
        self.MVC_Descripcion                =Descripcion
        self.COD_Venta                      =Venta
        self.ID_Compra                      =Compra
    def toDic(self):
        return{
            "COD_Movimiento_Contable":self.COD_Movimiento_Contable    ,
            "MVC_Tipo":self.MVC_Tipo                                  ,
            "MVC_Fecha":self.MVC_Fecha                                ,
            "MVC_Monto":self.MVC_Monto                                ,
            "MVC_Descripcion":self.MVC_Descripcion                    ,
            "COD_Venta":self.COD_Venta                                ,
            "ID_Compra":self.ID_Compra                                , 
        }