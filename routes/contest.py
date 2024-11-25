from fastapi import Depends, APIRouter, HTTPException
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
    
    async for contest in contests_collection.find({"status": "active"}):
        contest["id"] = str(contest["_id"])
        contest_list.append(ContestModel(**contest)) 

    return contest_list

from pydantic import BaseModel
from bson import ObjectId

class Item(BaseModel):
    contest_id: str

@Contest.post("/contests/subscribe")
async def suscribe_contest(
    current_user: Annotated[User, Depends(get_current_active_user)],
    item: Item,
):
    try:
        ContestId = ObjectId(item.contest_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid contest id")
    
    user_id = current_user.user_id
    db = await get_db()

    contests_collection = db.contest
    contest = await contests_collection.find_one({"_id": ContestId})

    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    
    if contest["status"] != "active":
        raise HTTPException(status_code=400, detail="Contest is not active")
    
    found = any(sub['user'] == user_id for sub in contest['subscription'])

    if found:
        raise HTTPException(status_code=400, detail="Already subscribed")
    
    if 'disqualified' in contest:
        disc = any(disq['user'] == user_id for disq in contest['disqualified'])

        if disc:
            raise HTTPException(status_code=400, detail="Already disqualified")
        
    filter = {'_id': ContestId}
    update = {'$push': {'subscription': {'user': user_id}}}
    result = await contests_collection.update_one(filter, update)
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Already subscribed")
    
    return {"success": True}

@Contest.post("/contests/unsubscribe")
async def unsubscribe_contest(
    current_user: Annotated[User, Depends(get_current_active_user)],
    item: Item,
):
    try:
        ContestId = ObjectId(item.contest_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid contest id")
    
    user_id = current_user.user_id

    db = await get_db()

    contests_collection = db.contest
    contest = await contests_collection.find_one({"_id": ContestId})


    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    
    if contest["status"] != "active":
        raise HTTPException(status_code=400, detail="Contest is not active")
    
    found = any(sub['user'] == user_id for sub in contest['subscription'])

    if not found:
        raise HTTPException(status_code=400, detail="Not subscribed")
    
    filter = {'_id': ContestId}
    update = {'$pull': {'subscription': {'user': user_id}}}
    result = await contests_collection.update_one(filter, update)

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Not subscribed")
    
    return {"success": True}