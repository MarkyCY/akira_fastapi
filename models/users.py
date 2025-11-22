from bson import ObjectId
from pydantic import BaseModel
class User(BaseModel):
    """Modelo para representar un usuario"""
    user_id: int
    first_name: str | None = None
    username: str | None = None
    avatar: str | None = None
    warnings: int | None = None
    description: str | None = None
    contest: bool | None = None
    role: list | None = ["user"]
    is_mod: bool | None = None
    enter_date: float | None = None
    disabled: bool | None = None 

class UserInDB(User):
    """Extensión del modelo User para incluir la contraseña hasheada"""
    hashed_password: str | None = None  # Contraseña hasheada
