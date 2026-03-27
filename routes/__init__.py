# __init__.py
# __init__.py
from .ventas import ventas_bp
from .cortes import cortes_bp
from .usuarios import usuarios_bp
from .productos import productos_bp
from .inventario import inventario_bp
from .combos import combos_bp
from .clientes import clientes_bp
from .abonos import abono_bp


def cargarRuta(app):
    app.register_blueprint(ventas_bp, url_prefix='/ventas')
    app.register_blueprint(cortes_bp, url_prefix='/cortes')
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    app.register_blueprint(productos_bp, url_prefix='/productos')
    app.register_blueprint(inventario_bp, url_prefix='/inventarios')
    app.register_blueprint(combos_bp, url_prefix='/combos')
    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    app.register_blueprint(abono_bp, url_prefix='/abonos')
    



    
    
    # http://10.0.0.5:5000/productos
    # http://10.0.0.5:5000/roles