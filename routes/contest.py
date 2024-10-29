from fastapi import Depends, APIRouter, Security, HTTPException, Response
from typing import Annotated, List

from models.contest import ContestModel

from funcs.users import get_current_active_user
from models.users import User
from database.mongo import get_db

Contest = APIRouter()

@Contest.get("/contests", response_model=List[ContestModel])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    db = await get_db()
    contests_collection = db.contest
    contest_list = []
    
    # Recorrer y mapear resultados a `ContestModel`
    async for contest in contests_collection.find():
        contest["_id"] = str(contest["_id"])  # Convierte ObjectId a str
        contest_list.append(ContestModel(**contest))  # Usar `**contest` para mapear al modelo
    
    return contest_list
