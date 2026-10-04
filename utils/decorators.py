"""
Decoradores de autenticacion (reemplaza el contenido de tu archivo actual).

CAMBIO DE FONDO: `token_requerido` ahora RECHAZA al rol 'cocina' (403).
Asi, todas las rutas que ya existen (clientes, compras, balance, prestamos,
inventario...) quedan cerradas para cocina SIN tener que tocarlas una por una.

Si en el futuro se agrega una ruta nueva y se olvida el decorador, el
resultado es "cocina no entra", nunca "cocina entra por descuido".

Las unicas rutas que cocina puede usar son las que lleven explicitamente
`@token_requerido_cocina` (ver pedidos_cocina_routes.py).
"""
from functools import wraps
from flask import request, g, jsonify
from jwt_config import verificar_token


def _validar_token(f, permitir_cocina):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token de acceso faltante o mal formado"}), 401

        token = auth_header.split(' ')[1]
        try:
            payload = verificar_token(token)
        except Exception:
            return jsonify({"error": "Token inválido o expirado"}), 401

        if payload.get('rol') == 'cocina' and not permitir_cocina:
            return jsonify({"error": "No tienes permisos para esta acción"}), 403

        g.usuario = payload   # {'id', 'username', 'rol', 'nombre'}
        return f(*args, **kwargs)
    return decorated


def token_requerido(f):
    """Token valido. NO permite al rol 'cocina'."""
    return _validar_token(f, permitir_cocina=False)


def token_requerido_cocina(f):
    """Token valido de cualquier rol, incluido 'cocina'.
    Usar SOLO en los endpoints del panel de cocina, y combinarlo con
    @rol_requerido([...]) para decir exactamente quien puede entrar."""
    return _validar_token(f, permitir_cocina=True)


def rol_requerido(roles_permitidos):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not hasattr(g, 'usuario') or g.usuario.get('rol') not in roles_permitidos:
                return jsonify({"error": "No tienes permisos para esta acción"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
