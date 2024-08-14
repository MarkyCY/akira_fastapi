from pydantic import BaseModel


class User(BaseModel):
    """Modelo para representar un usuario"""
    user_id: int
    warnings: int | None = None
    username: str  # Nombre de usuario
    disabled: bool | None = None  # Indicador de si el usuario está deshabilitado

class UserInDB(User):
    """Extensión del modelo User para incluir la contraseña hasheada"""
    hashed_password: str  # Contraseña hasheada
