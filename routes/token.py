from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

import os

from models.token import Token
from funcs.users import authenticate_user
from funcs.token import create_access_token

TokenAPI = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

@TokenAPI.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await authenticate_user(form_data.username, form_data.password)  # Autentica al usuario
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",  # Mensaje de error si las credenciales son incorrectas
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Calcula la expiración del token
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.role},  # Incluimos scopes en el token
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")  # Retorna el token de acceso