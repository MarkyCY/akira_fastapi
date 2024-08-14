from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()

import jwt
import os

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

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