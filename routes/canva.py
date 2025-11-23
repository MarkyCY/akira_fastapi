import asyncio
from fastapi import Depends, APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Annotated
from io import BytesIO
from fastapi.responses import StreamingResponse
import httpx
from PIL import Image
from database.mongo import get_db
from funcs.users import get_current_active_user
from models.users import User

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

    # Obtener el usuario actual
    user = await users.find_one({"user_id": current_user.user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Guardar el JSON recibido en el campo canva_json
    await users.update_one({"user_id": current_user.user_id}, {"$set": {"canva_json": data.dict()}})
    return {"message": "Canva importado correctamente"}


def generate_image_sync(data: CanvaRequest, scale: int, image_assets: dict):
    # 1. Configuración inicial
    canvas_width = int(data.canvas_width * scale)
    canvas_height = int(data.canvas_height * scale)
    canvas = Image.new("RGBA", (canvas_width, canvas_height), data.bgColor)

    # 2. Procesar Fondo
    if data.bgImage and data.bgImage in image_assets:
        try:
            bg_bytes = image_assets[data.bgImage]
            if bg_bytes:
                bg_img = Image.open(BytesIO(bg_bytes)).convert("RGBA")
                bg_img = bg_img.resize((canvas_width, canvas_height))
                canvas.paste(bg_img, (0, 0))
        except Exception:
            pass # Ignorar errores de imagen corrupta

    # 3. Procesar Ítems
    for item in data.items:
        if item.src not in image_assets or image_assets[item.src] is None:
            continue
        
        try:
            img_bytes = image_assets[item.src]
            img = Image.open(BytesIO(img_bytes)).convert("RGBA")
            
            # Calcular nuevas dimensiones
            new_width = int(item.width * scale)
            new_height = int(item.height * scale)
            img = img.resize((new_width, new_height))
            
            if item.rotation:
                # expand=True es importante para no cortar esquinas al rotar
                img = img.rotate(-item.rotation, expand=True, resample=Image.BICUBIC)
            
            pos_x = int(item.x * scale)
            pos_y = int(item.y * scale)
            
            # Usamos la misma imagen como máscara para transparencia
            canvas.paste(img, (pos_x, pos_y), img)
        except Exception:
            continue

    # 4. Guardar resultado
    output = BytesIO()
    canvas = canvas.convert("RGBA") # Asegurar formato antes de guardar
    canvas.save(output, format="WEBP", quality=85)
    output.seek(0)
    return output

# Helper para descargar una URL de forma segura sin romper el gather
async def fetch_image(client, url):
    if not url: 
        return url, None
    try:
        resp = await client.get(url, timeout=5.0) # Timeout para no colgarse eternamente
        resp.raise_for_status()
        return url, resp.content
    except Exception:
        return url, None

@CanvaAPI.get("/user_canva/{user_id}")
async def get_user_canva(user_id: int):
    # 1. Obtener datos del usuario
    db = await get_db()
    user = await db.users.find_one({"user_id": user_id})
    
    if not user or not user.get("canva_json"):
        raise HTTPException(status_code=404, detail="No se encontró el canva para este usuario")
    
    canva_data = user["canva_json"]
    data = CanvaRequest(**canva_data)
    
    # 2. Recolectar todas las URLs únicas necesarias (Fondo + Items)
    urls_to_fetch = set()
    if data.bgImage:
        urls_to_fetch.add(data.bgImage)
    for item in data.items:
        if item.src:
            urls_to_fetch.add(item.src)
            
    # 3. Descarga Paralela (IO Bound)
    # Usamos un solo cliente para todas las peticiones
    image_assets = {}
    async with httpx.AsyncClient() as client:
        tasks = [fetch_image(client, url) for url in urls_to_fetch]
        results = await asyncio.gather(*tasks)
        # Convertimos la lista de tuplas en un diccionario {url: bytes}
        image_assets = dict(results)

    # 4. Procesamiento de Imagen (CPU Bound)
    # run_in_threadpool mueve la lógica de PIL a otro hilo
    scale = 2
    final_image = await run_in_threadpool(generate_image_sync, data, scale, image_assets)
    
    # 5. Retornar con Headers de Caché
    # Agregamos Cache-Control para que el navegador no pida la imagen cada vez si no es necesario
    headers = {"Cache-Control": "public, max-age=3600"} 
    return StreamingResponse(final_image, media_type="image/webp", headers=headers)

