class medios_pago:
    """Representa una fila de la tabla medios_pago."""

    def __init__(self, id, nombre, tipo, titular=None, saldo_inicial=0.0,
                 activo=1, es_sistema=0, orden=0, created_at=None, updated_at=None):
        self.id            = id
        self.nombre        = nombre
        self.tipo          = tipo
        self.titular       = titular
        self.saldo_inicial = saldo_inicial
        self.activo        = activo
        self.es_sistema    = es_sistema
        self.orden         = orden
        self.created_at    = created_at
        self.updated_at    = updated_at

    def toDic(self):
        return {
            "id"           : self.id,
            "nombre"       : self.nombre,
            "tipo"         : self.tipo,
            "titular"      : self.titular,
            "saldo_inicial": float(self.saldo_inicial) if self.saldo_inicial is not None else 0.0,
            "activo"       : self.activo,
            "es_sistema"   : self.es_sistema,
            "orden"        : self.orden,
            "created_at"   : str(self.created_at) if self.created_at is not None else None,
            "updated_at"   : str(self.updated_at) if self.updated_at is not None else None,
        }
