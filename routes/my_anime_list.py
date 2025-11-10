from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from typing import Annotated, Optional
from models.users import User
from models.user_mal import AnimeAPIResponse
from funcs.users import get_current_active_user

from database.mongo import get_db


load_dotenv()

MyAL = APIRouter()


@MyAL.post("/add_data")
async def add_data(
    current_user: Annotated[User, Depends(get_current_active_user)],
    request: Request,
):
    """
    Agregar datos de MAL a la base de datos
    """
    user_id = current_user.user_id

    try:
        data: AnimeAPIResponse = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    print("Received MAL data:", data['data'][0]['node'])

    db = await get_db()

    mal_data = db.mal_data

    try:
        await mal_data.update_one(
            {"user_id": user_id},
            {"$set": {"data": data['data']}},
            upsert=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Database error: " + str(e))

    return JSONResponse(content={"message": "MAL data added/updated successfully"}, status_code=200)


@MyAL.get("/get_data")
async def get_data(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_id: Optional[int] = None,
    status: Optional[str] = "completed",
    page: int = 0,
    limit: int = 6
):
    """
    Obtener datos de MAL desde la base de datos
    """
    db = await get_db()
    mal_data = db.mal_data

    if user_id:
        pass
    else:
        user_id = current_user.user_id

    if page < 1:
        page = 1

    skip = (page - 1) * limit

    pipeline = [
        {
            '$unwind': '$data'
        }, {
            '$match': {
                'data.list_status.status': status,
                "user_id": user_id
            }
        }, {
            '$project': {
                '_id': 0,
                'title': '$data.node.title',
                'status': '$data.list_status.status',
                'num_episodes_watched': '$data.list_status.num_episodes_watched',
                'score': '$data.list_status.score',
                'image': '$data.node.main_picture.medium',
                'nsfw': '$data.node.nsfw'

            }
        }, 
        { '$sort': { 'score': -1 } },
        { '$skip': skip }, 
        { '$limit': limit }
    ]

    user_data = await mal_data.aggregate(pipeline).to_list(length=limit)

    return JSONResponse(content={"data": user_data}, status_code=200)
