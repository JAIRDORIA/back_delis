    
class cortes:
    def __init__(self, id, numero, fecha_inicio, fecha_cierre, estado, 
                 saldo_inicial):
        self.id = id
        self.numero = numero
        self.fecha_inicio = fecha_inicio
        self.fecha_cierre = fecha_cierre
        self.estado = estado
        self.saldo_inicial = saldo_inicial
        

    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "fecha_inicio": str (self.fecha_inicio) ,
            "fecha_cierre": str(self.fecha_cierre) ,
            "estado": self.estado,
            "saldo_inicial": float(self.saldo_inicial)
        }