from pydantic import BaseModel

# Definición del modelo para representar un Token
class Token(BaseModel):
    access_token: str  # Token de acceso
    token_type: str  # Tipo de token (ej. "bearer")

# Modelo para manejar datos del token
class TokenData(BaseModel):
    username: str | None = None  # Nombre de usuario opcional, puede ser None