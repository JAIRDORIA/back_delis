class proveedores:
    def __init__(self,id,nombre,contacto,direccion,compra):
        self.ID_Proveedor = id
        self.PROO_Nombre = nombre
        self.PROO_Contacto = contacto
        self.PROODireccion = direccion
        self.ID_Compra = compra
    
    def todic(self):
        return{
            "proo_id" : self.ID_Proveedor ,
            "proo_nom" : self.PROO_Nombre ,
            "proo_cont" : self.PROO_Contacto ,
            "proo_dir" : self.PROODireccion ,
            "proo_compra" : self.ID_Compra
        } 
    
        
           