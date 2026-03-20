    
class ventas:    
    def __init__(self,cod_venta,ven_domi,ven_est,ven_fech_entre,ven_detalle,id_cliente):
        self.COD_Venta = cod_venta
        self.Ven_Domiciliario = ven_domi
        self.VEN_Estado = ven_est
        self.VEN_Fecha_Entrega = ven_fech_entre
        self.VEN_Detalle = ven_detalle
        self.ID_Cliente = id_cliente
    
    def todic(self):
        return{
            "cod_venta" : self.COD_Venta ,
            "ven_domi" : self.Ven_Domiciliario ,
            "ven_est" : self.VEN_Estado ,
            "ven_fech_entre" : self.VEN_Fecha_Entrega ,
            "ven_detalle" : self.VEN_Detalle,
            "id_cliente" : self.ID_Cliente
            
        } 