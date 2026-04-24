from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Annotated
from io import BytesIO
import httpx
from PIL import Image
import boto3, os

from database.mongo import get_db
from funcs.users import get_current_active_user
from models.users import User

# -------------------- S3 CONFIG --------------------
AWS_ACCESS_KEY = os.getenv("S3_AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("S3_AWS_SECRET_KEY")
BUCKET = os.getenv("BUCKET_NAME")

s3 = boto3.client(
    "s3",
    region_name="us-east-1",
    endpoint_url="https://objstorage.leapcell.io",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)



# -------------------- API --------------------
CanvaAPI = APIRouter()

# -------------------- MODELOS --------------------
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


# -------------------- UTIL: GENERAR IMAGEN --------------------
async def generate_canvas_image(data: CanvaRequest) -> BytesIO:
    scale = 2
    canvas_width = int(data.canvas_width * scale)
    canvas_height = int(data.canvas_height * scale)

    canvas = Image.new("RGBA", (canvas_width, canvas_height), data.bgColor)

    async with httpx.AsyncClient() as client:

        # Background
        if data.bgImage:
            try:
                resp = await client.get(data.bgImage)
                resp.raise_for_status()
                bg_img = Image.open(BytesIO(resp.content)).convert("RGBA")
                bg_img = bg_img.resize((canvas_width, canvas_height))
                canvas.paste(bg_img, (0, 0))
            except:
                pass

        # Items
        for item in data.items:
            try:
                resp = await client.get(item.src)
                resp.raise_for_status()

                img = Image.open(BytesIO(resp.content)).convert("RGBA")
                img = img.resize(
                    (int(item.width * scale), int(item.height * scale))
                )

                if item.rotation:
                    img = img.rotate(
                        -item.rotation,
                        expand=True,
                        resample=Image.BICUBIC
                    )

                canvas.paste(
                    img,
                    (int(item.x * scale), int(item.y * scale)),
                    img
                )
            except:
                continue

    output = BytesIO()
    canvas.save(output, format="WEBP", quality=85)
    output.seek(0)

    return output


# -------------------- EXPORT --------------------
@CanvaAPI.get("/export")
async def export_canva(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    db = await get_db()
    users = db.users

    user = await users.find_one({"user_id": current_user.user_id})

    if not user or not user.get("canva_json"):
        raise HTTPException(status_code=404, detail="No se encontró el canva")

    return user["canva_json"]


# -------------------- IMPORT (GUARDAR + SUBIR A S3) --------------------
@CanvaAPI.post("/import")
async def import_canva(
    current_user: Annotated[User, Depends(get_current_active_user)],
    data: CanvaRequest
):
    db = await get_db()
    users = db.users

    data = CanvaRequest(**data.model_dump())

    # 🔥 Generar imagen
    output = await generate_canvas_image(data)

    key = f"canvas/{current_user.user_id}.webp"

    # 🔥 Subir a S3 (overwrite automático)
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=output.getvalue(),
        ContentType="image/webp",
        CacheControl="public, max-age=3600, immutable"
    )

    # Guardar JSON en Mongo
    await users.update_one(
        {"user_id": current_user.user_id},
        {"$set": {"canva_json": data.model_dump()}}
    )

    return {"message": "Canva importado correctamente"}


# -------------------- GET USER CANVA --------------------
@CanvaAPI.get("/user_canva/{user_id}")
async def get_user_canva(user_id: int):
    key = f"canvas/{user_id}.webp"

    try:
        # 🔍 Verificar si ya existe en S3
        s3.head_object(Bucket=BUCKET, Key=key)

    except s3.exceptions.ClientError:
        # ❌ No existe → generarlo
        db = await get_db()
        users = db.users

        user = await users.find_one({"user_id": user_id})

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if not user.get("canva_json"):
            raise HTTPException(status_code=404, detail="Canva no encontrado")

        data = CanvaRequest(**user["canva_json"])

        output = await generate_canvas_image(data)

        # 🔥 Subir a S3
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=output.getvalue(),
            ContentType="image/webp",
            CacheControl="public, max-age=3600, immutable"
        )

    from fastapi.responses import StreamingResponse

    obj = s3.get_object(Bucket=BUCKET, Key=key)
    
    return StreamingResponse(
        obj["Body"],
        media_type="image/webp",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )