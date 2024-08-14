# Importamos las bibliotecas necesarias
from datetime import datetime, timedelta, timezone  # Manejo de fechas y tiempos
from typing import Annotated  # Para anotaciones de tipos de datos

import jwt  # Biblioteca para manejar JSON Web Tokens (JWT)
from fastapi import Depends, FastAPI, HTTPException, status  # Importaciones de FastAPI para construir la API
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # Manejo de seguridad OAuth2 en FastAPI
from jwt.exceptions import InvalidTokenError  # Excepción para manejar errores de tokens JWT
from passlib.context import CryptContext  # Manejo de hash de contraseñas
from pydantic import BaseModel  # Base para la creación de modelos de datos en FastAPI

# Generar una clave secreta (puede ser generada con openssl)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"  # Algoritmo usado para firmar los JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Tiempo de expiración del token en minutos

# Base de datos simulada de usuarios
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$4znb874wXMsVGkjnUlZPYeJSbbTVLnXj6Z4axHPknEhdfS0MZK3R2",  # Contraseña hasheada
        "disabled": False,  # Indicador si la cuenta está deshabilitada
    }
}

# Definición del modelo para representar un Token
class Token(BaseModel):
    access_token: str  # Token de acceso
    token_type: str  # Tipo de token (ej. "bearer")

# Modelo para manejar datos del token
class TokenData(BaseModel):
    username: str | None = None  # Nombre de usuario opcional, puede ser None

# Modelo para representar un usuario
class User(BaseModel):
    username: str  # Nombre de usuario
    email: str | None = None  # Email opcional
    full_name: str | None = None  # Nombre completo opcional
    disabled: bool | None = None  # Indicador de si el usuario está deshabilitado

# Extensión del modelo User para incluir la contraseña hasheada
class UserInDB(User):
    hashed_password: str  # Contraseña hasheada

# Contexto para manejar las contraseñas (bcrypt es el algoritmo usado)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de seguridad OAuth2, especifica el endpoint para obtener el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Instancia de la aplicación FastAPI
app = FastAPI()

# Función para verificar la contraseña
def verify_password(plain_password, hashed_password):
    """ Función para verificar la contraseña """
    return pwd_context.verify(plain_password, hashed_password)

# Función para hashear la contraseña
def get_password_hash(password):
    """ Función para hashear la contraseña """
    return pwd_context.hash(password)

# Función para obtener un usuario de la base de datos simulada
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)  # Retorna un objeto UserInDB con los datos del usuario

# Función para autenticar al usuario, comparando la contraseña ingresada con la almacenada
def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)  # Busca al usuario en la base de datos
    if not user:
        print("no existe usuario")
        return False  # Retorna False si el usuario no existe
    if not verify_password(password, user.hashed_password):
        print("la contraseña no coincide")
        return False  # Retorna False si la contraseña no coincide
    return user  # Retorna el usuario si se autentica correctamente

# Función para crear un token de acceso JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """ Función para crear un token de acceso JWT """
    to_encode = data.copy()  # Copia los datos a codificar en el token
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta  # Calcula la expiración del token
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)  # Expira en 15 minutos por defecto
    to_encode.update({"exp": expire})  # Agrega la expiración a los datos a codificar
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # Codifica los datos en un JWT
    return encoded_jwt  # Retorna el JWT

# Dependencia que obtiene el usuario actual basado en el token JWT
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

# Dependencia que obtiene el usuario actual si está activo
async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """ Dependencia que obtiene el usuario actual si está activo """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")  # Lanza excepción si el usuario está deshabilitado
    return current_user  # Retorna el usuario si está activo

# Endpoint para obtener un token de acceso
@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)  # Autentica al usuario
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",  # Mensaje de error si las credenciales son incorrectas
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Calcula la expiración del token
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires  # Crea el token de acceso
    )
    return Token(access_token=access_token, token_type="bearer")  # Retorna el token de acceso

# Endpoint para obtener la información del usuario actual
@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user  # Retorna la información del usuario actual

# Endpoint para obtener los items del usuario actual
@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]  # Retorna una lista de items pertenecientes al usuario

print(get_password_hash("4950"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
