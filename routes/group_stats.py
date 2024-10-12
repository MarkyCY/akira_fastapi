from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from typing import Annotated
from models.users import User
from funcs.group_status import get_stats_daily, resize_and_convert_to_base64
from funcs.users import get_current_active_user
from fastapi import Depends
from models.group_stats import StatsDaily

import os

GroupStatsRoutes = APIRouter()

@GroupStatsRoutes.get("/group_stats/", response_model=StatsDaily)
async def read_group_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    stats = await get_stats_daily()
    return stats

@GroupStatsRoutes.post("/upload")
async def upload_image(
    user_id: int,  # Puedes usar el tipo de dato que prefieras para user_id
    file: UploadFile = File(...),  # El parámetro file es un UploadFile
):
    path = f"users/photo/{user_id}.jpg"
    if os.path.exists(path):
        raise HTTPException(status_code=201, detail="Image already exists")
    
    # Leer el archivo como bytes
    file_bytes = await file.read()
    
    # Redimensionar la imagen y convertirla a base64
    img_base64 = resize_and_convert_to_base64(file_bytes, user_id)
    
    # Aquí puedes realizar cualquier otra acción que necesites con img_base64
    return {"filename": file.filename, "user_id": user_id, "image_base64": img_base64}