from fastapi import Depends, APIRouter
from typing import Annotated

from models.users import User
from funcs.users import get_current_active_user
from funcs.settings import get_password_hash

Users = APIRouter()


#@Users.get("/users/items", dependencies=[Security(verify_token_scoped, scopes=["write:admin"])])
#async def get_items(request: Request, search: str = None):

@Users.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user  # Retorna la información del usuario actual

# Endpoint para obtener los items del usuario actual
@Users.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]  # Retorna una lista de items pertenecientes al usuario

print(get_password_hash("4950"))