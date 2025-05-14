from fastapi import Depends, APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Annotated
from funcs.users import get_current_active_user
from models.users import User
import os

IconsAPI = APIRouter()

PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")

# @IconsAPI.get("/packs/")
# async def list_icon_packs():
#     try:
#         packs = [d for d in os.listdir(PUBLIC_DIR) if os.path.isdir(os.path.join(PUBLIC_DIR, d))]
#         return {"packs": packs}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@IconsAPI.get("/packs_with_icons/")
async def list_packs_with_icons(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        packs = [d for d in os.listdir(PUBLIC_DIR) if os.path.isdir(os.path.join(PUBLIC_DIR, d))]
        packs_with_icons = {}
        for pack in packs:
            pack_path = os.path.join(PUBLIC_DIR, pack)
            icons = [f for f in os.listdir(pack_path) if os.path.isfile(os.path.join(pack_path, f))]
            packs_with_icons[pack] = icons
        return {"packs": packs_with_icons}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @IconsAPI.get("/pack/{pack_name}/")
# async def list_icons_in_pack(pack_name: str):
#     pack_path = os.path.join(PUBLIC_DIR, pack_name)
#     if not os.path.isdir(pack_path):
#         raise HTTPException(status_code=404, detail="Pack no encontrado")
#     try:
#         icons = [f for f in os.listdir(pack_path) if os.path.isfile(os.path.join(pack_path, f))]
#         return {"icons": icons}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@IconsAPI.get("/pack/{pack_name}/{icon_name}")
async def get_icon_image(pack_name: str, icon_name: str):
    icon_path = os.path.join(PUBLIC_DIR, pack_name, icon_name)
    if not os.path.isfile(icon_path):
        raise HTTPException(status_code=404, detail="Icono no encontrado")
    return FileResponse(
            icon_path,
            media_type="image/webp",
            headers={"Cache-Control": "public, max-age=3600, immutable"}
        )

