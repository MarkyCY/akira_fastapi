from fastapi import Depends, HTTPException, status, Security
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt.exceptions import InvalidTokenError
from database.mongo import get_db
from dotenv import load_dotenv
load_dotenv()

import os
import jwt

from models.users import User
from models.token import TokenData
from funcs.settings import verify_password
from models.users import UserInDB

from database.mongo import get_db

# Definir la jerarquía de roles
role_hierarchy = {
    "admin": 4,
    "user": 1,
}

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token", 
    scopes={"admin": "Admin access", "user": "User access"}
)

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

#Fake
async def get_user(username: str):
    db = await get_db()
    users = db.users

    user = await users.find_one({"username": username})
    if user:
        return UserInDB(**user)

async def authenticate_user(username: str, password: str):
    user = await get_user(username)  # Busca al usuario en la base de datos
    if not user:
        return False  # Retorna False si el usuario no existe
    if not verify_password(password, user.hashed_password):
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
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except InvalidTokenError:
        raise credentials_exception  # Lanza excepción si el token es inválido
    user = await get_user(username=token_data.username)  # Obtiene el usuario de la base de datos
    if user is None:
        raise credentials_exception  # Lanza excepción si el usuario no existe
    return user  # Retorna el usuario autenticado


async def get_current_active_user(
    security_scopes: SecurityScopes,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """ Dependencia que obtiene el usuario actual si está activo """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Si no se requieren scopes específicos, permitir el acceso
    if not security_scopes.scopes:
        return current_user
    
    # Obtener el nivel máximo requerido por la ruta
    required_level = max(role_hierarchy.get(scope, 0) for scope in security_scopes.scopes)
    
    # Verifica que el usuario tenga al menos uno de los scopes requeridos
    user_level = max(role_hierarchy.get(role, 0) for role in current_user.role)
    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
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
    user = await get_user(username=token_data.username)  # Obtiene el usuario de la base de datos
    if user is None:
        raise credentials_exception  # Lanza excepción si el usuario no existe
    return user  # Retorna el usuario autenticado