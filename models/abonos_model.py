class abonos:
    def __init__(self,id,venta_id,corte_id,usuario_id,monto,fecha,observacion):
        self.id = id
        self.venta_id = venta_id
        self.corte_id = corte_id
        self.usuario_id = usuario_id
        self.monto = monto
        self.fecha = fecha
        self.observacion = observacion
        
    
    def todic(self):
        return{
            "id_abono" : self.id,
            "id_venta" : self.venta_id ,
            "id_corte" : self.corte_id ,
            "id_usuario" : self.usuario_id ,
            "monto" : float(self.monto)  ,
            "fecha" : str(self.fecha) ,
            "observacion": self.observacion
            
        } 
    
        
           