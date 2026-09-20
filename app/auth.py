"""Autenticación JWT y control de acceso por roles (RNF01).

- Hash de contraseñas con PBKDF2-HMAC-SHA256 (sin dependencias compiladas).
- Tokens JWT firmados con SECRET_KEY (variable de entorno en producción).
- Roles: admin > gestor > admision > lector.
"""
import datetime as dt
import hashlib
import hmac
import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Usuario

settings = get_settings()
_bearer = HTTPBearer(auto_error=False)

# Acceso mínimo requerido por rol (jerarquía simple).
JERARQUIA = {"lector": 0, "admision": 1, "gestor": 2, "admin": 3}


# ---------- Contraseñas ----------
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}:{dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split(":")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 120_000)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except ValueError:
        return False


# ---------- Tokens ----------
def create_access_token(user: Usuario) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "rol": user.rol,
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ---------- Dependencias ----------
def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token no proporcionado")
    try:
        payload = decode_token(creds.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")

    user = db.get(Usuario, int(payload["sub"]))
    if user is None or not user.activo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inexistente o inactivo")
    return user


def require_rol(minimo: str):
    """Devuelve una dependencia que exige un rol de jerarquía >= minimo."""
    def checker(user: Usuario = Depends(get_current_user)) -> Usuario:
        if JERARQUIA.get(user.rol, -1) < JERARQUIA[minimo]:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requiere rol '{minimo}' o superior (tu rol: '{user.rol}')",
            )
        return user
    return checker
