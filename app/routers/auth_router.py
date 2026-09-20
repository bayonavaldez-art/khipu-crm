"""Endpoints de autenticación."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, verify_password
from app.database import get_db
from app.models import Usuario
from app.schemas import LoginIn, TokenOut, UsuarioOut

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.username == datos.username).first()
    # Mensaje genérico: no revelar si falló el usuario o la contraseña.
    if user is None or not verify_password(datos.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales incorrectas")
    if not user.activo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario inactivo")
    token = create_access_token(user)
    return TokenOut(access_token=token, rol=user.rol, full_name=user.full_name)


@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(get_current_user)):
    return user
