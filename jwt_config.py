import jwt
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "clave_secreta_por_defecto_CAMBIAR")
EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 8))

def generar_token(payload: dict) -> str:
    ahora = datetime.now(timezone.utc)
    claims = {
        **payload,
        "iat": ahora,
        "exp": ahora + timedelta(hours=EXPIRATION_HOURS),
    }
    token = jwt.encode(claims, SECRET_KEY, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def verificar_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])