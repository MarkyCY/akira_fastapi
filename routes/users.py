from fastapi import Depends, APIRouter, Security, HTTPException
from fastapi.responses import FileResponse
from typing import Annotated

from models.users import User
from funcs.users import get_current_active_user

import os

Users = APIRouter()


@Users.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user  # Retorna la información del usuario actual

@Users.get("/users/admin/")
async def read_admin_data(
    current_user: Annotated[User, Security(get_current_active_user, scopes=["admin"])],
):
    return {"admin_data": "This is secret data only for admins!"}


@Users.get("/user/photo/{user_id}")
async def get_user_photo(user_id: int):
    # Construir el nombre de archivo esperado basado en el user_id
    image_filename = f"{user_id}.jpg"
    image_full_path = os.path.join("users/photo", image_filename)

    # Verificar si el archivo existe
    if not os.path.exists(image_full_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Devolver la imagen como respuesta con encabezados de cache
    response = FileResponse(image_full_path, media_type="image/jpeg")
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response