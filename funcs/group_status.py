
from database.mongo import get_db
from models.group_stats import StatsDaily

from PIL import Image
from io import BytesIO
import base64
import os
    
def resize_and_convert_to_base64(image_bytes, user_id, output_size=(200, 200)):
    # Abrir la imagen desde los bytes
    img = Image.open(BytesIO(image_bytes))
    
    # Redimensionar la imagen (aquí puedes personalizar el tamaño)
    img = img.resize(output_size, Image.LANCZOS)
    
    # Crear la carpeta si no existe
    os.makedirs("users/photo", exist_ok=True)
    
    # Guardar la imagen en formato JPEG en la ruta /users/photo
    image_filename = f"{user_id}.jpg"
    image_full_path = os.path.join("users/photo", image_filename)
    img.save(image_full_path, format="JPEG")
    
    # Convertir la imagen a formato base64
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return img_base64

async def get_stats_daily():
    db = await get_db()
    Stats = db.stats

    stats = await Stats.find_one({"_id": "status_daily"})
    
    return StatsDaily(**stats)