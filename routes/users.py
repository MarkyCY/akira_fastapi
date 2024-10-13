from fastapi import Depends, APIRouter, Security, HTTPException, Response
from typing import Annotated

from models.users import User
from funcs.users import get_current_active_user

from database.mongo import get_db

import requests
from io import BytesIO

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


# @Users.get("/user/photo/{user_id}")
# async def get_user_photo(user_id: int):
#     # Construir el nombre de archivo esperado basado en el user_id
#     image_filename = f"{user_id}.jpg"
#     image_full_path = os.path.join("users/photo", image_filename)

#     # Verificar si el archivo existe
#     if not os.path.exists(image_full_path):
#         raise HTTPException(status_code=404, detail="Image not found")
    
#     # Devolver la imagen como respuesta con encabezados de cache
#     response = FileResponse(image_full_path, media_type="image/jpeg")
#     response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
#     return response


@Users.get("/user/photo/{user_id}")
async def get_user_photo(user_id: int):
    db = await get_db()
    users = db.users
    user = await users.find_one({"user_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="Image not found")
    
    avatar = user.get("avatar")

    if not avatar:
        raise HTTPException(status_code=404, detail="Image not found")
    print(avatar)
    response = requests.get(avatar)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Image not found")

    image_data = BytesIO(response.content)
    return Response(content=image_data.getvalue(), media_type="image/jpeg", headers={"Cache-Control": "public, max-age=31536000, immutable"})