from fastapi import Depends, HTTPException, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from database.mongo import get_user
from dotenv import load_dotenv
load_dotenv()

import os
import jwt

from models.users import User
from models.token import TokenData
from funcs.settings import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))

#Fake
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$4znb874wXMsVGkjnUlZPYeJSbbTVLnXj6Z4axHPknEhdfS0MZK3R2",  # Contraseña hasheada
        "disabled": False,  # Indicador si la cuenta está deshabilitada
    }
}

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)  # Busca al usuario en la base de datos
    if not user:
        print("no existe usuario")
        return False  # Retorna False si el usuario no existe
    if not verify_password(password, user.hashed_password):
        print("la contraseña no coincide")
        return False  # Retorna False si la contraseña no coincide
    return user  # Retorna el usuario si se autentica correctamente

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """ Dependencia que obtiene el usuario actual basado en el token JWT """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",  # Mensaje de error si la validación falla
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Decodifica el token JWT
        username: str = payload.get("sub")  # Obtiene el nombre de usuario del payload
        if username is None:
            raise credentials_exception  # Lanza excepción si no hay nombre de usuario
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception  # Lanza excepción si el token es inválido
    user = get_user(fake_users_db, username=token_data.username)  # Obtiene el usuario de la base de datos
    if user is None:
        raise credentials_exception  # Lanza excepción si el usuario no existe
    return user  # Retorna el usuario autenticado


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """ Dependencia que obtiene el usuario actual si está activo """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")  # Lanza excepción si el usuario está deshabilitado
    return current_user  # Retorna el usuario si está activo


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """ Dependencia que obtiene el usuario actual basado en el token JWT """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",  # Mensaje de error si la validación falla
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Decodifica el token JWT
        username: str = payload.get("sub")  # Obtiene el nombre de usuario del payload
        if username is None:
            raise credentials_exception  # Lanza excepción si no hay nombre de usuario
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception  # Lanza excepción si el token es inválido
    user = get_user(fake_users_db, username=token_data.username)  # Obtiene el usuario de la base de datos
    if user is None:
        raise credentials_exception  # Lanza excepción si el usuario no existe
    return user  # Retorna el usuario autenticado