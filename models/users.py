from pydantic import BaseModel


# Modelo para representar un usuario
class User(BaseModel):
    username: str  # Nombre de usuario
    email: str | None = None  # Email opcional
    full_name: str | None = None  # Nombre completo opcional
    disabled: bool | None = None  # Indicador de si el usuario está deshabilitado

# Extensión del modelo User para incluir la contraseña hasheada
class UserInDB(User):
    hashed_password: str  # Contraseña hasheada
