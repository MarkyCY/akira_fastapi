from bson import ObjectId
from pydantic import BaseModel
class User(BaseModel):
    """Modelo para representar un usuario"""
    _id: ObjectId
    user_id: int
    username: str
    avatar: str | None = None
    warnings: int | None = None
    description: str | None = None
    contest: bool | None = None
    role: list | None = ["user"]
    disabled: bool | None = None 

class UserInDB(User):
    """Extensión del modelo User para incluir la contraseña hasheada"""
    hashed_password: str | None = None  # Contraseña hasheada
