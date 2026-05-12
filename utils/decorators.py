from functools import wraps
from flask import request, g, jsonify
from jwt_config import verificar_token

def token_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token de acceso faltante o mal formado"}), 401

        token = auth_header.split(' ')[1]
        try:
            payload = verificar_token(token)
            g.usuario = payload   # {'id', 'username', 'rol', 'nombre'}
        except Exception:
            return jsonify({"error": "Token inválido o expirado"}), 401

        return f(*args, **kwargs)
    return decorated

def rol_requerido(roles_permitidos):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not hasattr(g, 'usuario') or g.usuario.get('rol') not in roles_permitidos:
                return jsonify({"error": "No tienes permisos para esta acción"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator