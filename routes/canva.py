from fastapi import Depends, APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Annotated
from io import BytesIO
from fastapi.responses import StreamingResponse
import httpx
from PIL import Image
from database.mongo import get_db
from funcs.users import get_current_active_user
from models.users import User
import os

CanvaAPI = APIRouter()

class CanvaItem(BaseModel):
    id: str
    src: str
    x: int | float
    y: int | float
    width: int
    height: int
    rotation: Optional[float] = 0
    isFixed: Optional[bool] = False

class CanvaRequest(BaseModel):
    items: List[CanvaItem]
    bgColor: Optional[str] = "#ffffff"
    bgImage: Optional[str] = None
    canvas_width: Optional[int] = 318
    canvas_height: Optional[int] = 158
    scale: Optional[float] = 1.0

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")

# @CanvaAPI.post("/export")
# async def export_canva(data: CanvaRequest):
#     scale = data.scale if data.scale else 1.0
#     canvas_width = int(data.canvas_width * scale)
#     canvas_height = int(data.canvas_height * scale)
#     canvas = Image.new("RGBA", (canvas_width, canvas_height), data.bgColor)

#     # Si hay imagen de fondo, cargarla
#     if data.bgImage:
#         try:
#             async with httpx.AsyncClient() as client:
#                 resp = await client.get(data.bgImage)
#                 resp.raise_for_status()
#                 bg_img = Image.open(BytesIO(resp.content)).convert("RGBA")
#                 bg_img = bg_img.resize((canvas_width, canvas_height))
#                 canvas.paste(bg_img, (0, 0))
#         except Exception:
#             pass  # Si falla, solo deja el color de fondo

#     # Procesar cada imagen
#     for item in data.items:
#         try:
#             async with httpx.AsyncClient() as client:
#                 resp = await client.get(item.src)
#                 resp.raise_for_status()
#                 img = Image.open(BytesIO(resp.content)).convert("RGBA")
#                 new_width = int(item.width * scale)
#                 new_height = int(item.height * scale)
#                 img = img.resize((new_width, new_height))
#                 if item.rotation:
#                     img = img.rotate(-item.rotation, expand=True, resample=Image.BICUBIC)
#                 pos_x = int(item.x * scale)
#                 pos_y = int(item.y * scale)
#                 canvas.paste(img, (pos_x, pos_y), img)
#         except Exception:
#             continue

#     # Convertir a PNG y devolver
#     output = BytesIO()
#     canvas = canvas.convert("RGBA")
#     canvas.save(output, format="PNG")
#     output.seek(0)
#     return StreamingResponse(output, media_type="image/png")


@CanvaAPI.get("/export")
async def export_canva(
    current_user: Annotated[User, Depends(get_current_active_user)],
    ):
    db = await get_db()
    users = db.users

    user = await users.find_one({"user_id": current_user.user_id})
    if not user or not user.get("canva_json"):
        raise HTTPException(status_code=404, detail="No se encontró el canva para este usuario")
    
    canva_data = user["canva_json"]
    return canva_data


@CanvaAPI.post("/import")
async def import_canva(
    current_user: Annotated[User, Depends(get_current_active_user)],
    data: CanvaRequest
):
    db = await get_db()
    users = db.users
    
    data = CanvaRequest(**data.model_dump())
    scale = 2
    canvas_width = int(data.canvas_width * scale)
    canvas_height = int(data.canvas_height * scale)
    canvas = Image.new("RGBA", (canvas_width, canvas_height), data.bgColor)
    if data.bgImage:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(data.bgImage)
                resp.raise_for_status()
                bg_img = Image.open(BytesIO(resp.content)).convert("RGBA")
                bg_img = bg_img.resize((canvas_width, canvas_height))
                canvas.paste(bg_img, (0, 0))
        except Exception:
            pass
    for item in data.items:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(item.src)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGBA")
                new_width = int(item.width * scale)
                new_height = int(item.height * scale)
                img = img.resize((new_width, new_height))
                if item.rotation:
                    img = img.rotate(-item.rotation, expand=True, resample=Image.BICUBIC)
                pos_x = int(item.x * scale)
                pos_y = int(item.y * scale)
                canvas.paste(img, (pos_x, pos_y), img)
        except Exception:
            continue
    output = BytesIO()
    canvas = canvas.convert("RGBA")
    canvas.save(output, format="WEBP", quality=85)
    output.seek(0)

    output_path = os.path.join(PUBLIC_DIR, "canvas", f"{current_user.user_id}.webp")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(output.getbuffer())

    # Guardar el JSON recibido en el campo canva_json
    await users.update_one({"user_id": current_user.user_id}, {"$set": {"canva_json": data.model_dump()}})
    return {"message": "Canva importado correctamente"}


@CanvaAPI.get("/user_canva/{user_id}")
async def get_user_canva(user_id: int):
    file_path = os.path.join(PUBLIC_DIR, "canvas", f"{user_id}.webp")

    # Si el archivo NO existe, lo generamos
    if not os.path.exists(file_path):
        db = await get_db()
        users = db.users
        user = await users.find_one({"user_id": user_id})

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if not user.get("canva_json"):
            raise HTTPException(status_code=404, detail="Canva no encontrado para este usuario")

        data = CanvaRequest(**user["canva_json"])
        scale = 2
        canvas_width = int(data.canvas_width * scale)
        canvas_height = int(data.canvas_height * scale)
        
        canvas = Image.new("RGBA", (canvas_width, canvas_height), data.bgColor)

        # ... (Lógica de generación de imagen igual que antes) ...
        if data.bgImage:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(data.bgImage)
                    resp.raise_for_status()
                    bg_img = Image.open(BytesIO(resp.content)).convert("RGBA")
                    bg_img = bg_img.resize((canvas_width, canvas_height))
                    canvas.paste(bg_img, (0, 0))
            except Exception:
                pass

        for item in data.items:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(item.src)
                    resp.raise_for_status()
                    img = Image.open(BytesIO(resp.content)).convert("RGBA")
                    new_width = int(item.width * scale)
                    new_height = int(item.height * scale)
                    img = img.resize((new_width, new_height))
                    if item.rotation:
                        img = img.rotate(-item.rotation, expand=True, resample=Image.BICUBIC)
                    pos_x = int(item.x * scale)
                    pos_y = int(item.y * scale)
                    canvas.paste(img, (pos_x, pos_y), img)
            except Exception:
                continue

        output = BytesIO()
        canvas = canvas.convert("RGBA")
        canvas.save(output, format="WEBP", quality=85)
        output.seek(0)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(output.getbuffer())

    # Retornar el archivo (ya sea que existía antes o lo acabamos de crear)
    output = open(file_path, "rb")
    return StreamingResponse(output, media_type="image/webp")

