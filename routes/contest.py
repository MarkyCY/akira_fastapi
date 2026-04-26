from bson import ObjectId
from pydantic import BaseModel
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

    pipeline = [
        # 1. Solo concursos activos
        {"$match": {"status": "active"}},

        # 2. Desanidar el array subscription para hacer lookup por cada elemento
        {"$unwind": {"path": "$subscription", "preserveNullAndEmptyArrays": True}},

        # 3. Lookup a users usando subscription.user → user_id
        {
            "$lookup": {
                "from": "users",
                "localField": "subscription.user",
                "foreignField": "user_id",
                "as": "subscription_user_data"
            }
        },

        # 4. Inyectar el avatar dentro del objeto subscription
        {
            "$addFields": {
                "subscription.avatar": {
                    "$ifNull": [
                        {"$arrayElemAt": [
                            "$subscription_user_data.avatar", 0]},
                        None
                    ]
                }
            }
        },

        # 5. Reagrupar el array subscription por documento original
        {
            "$group": {
                "_id": "$_id",
                "root": {"$first": "$$ROOT"},
                "subscription": {
                    "$push": {
                        "$cond": {
                            "if": {"$gt": ["$subscription.user", None]},
                            "then": "$subscription",
                            "else": "$$REMOVE"
                        }
                    }
                }
            }
        },

        # 6. Reconstruir el documento con el array subscription actualizado
        {
            "$replaceRoot": {
                "newRoot": {
                    "$mergeObjects": [
                        "$root",
                        {"subscription": "$subscription"}
                    ]
                }
            }
        },

        # 7. Limpiar campos temporales
        {
            "$project": {
                "subscription_user_data": 0
            }
        }
    ]

    contest_list = []
    async for contest in contests_collection.aggregate(pipeline):
        contest["id"] = str(contest["_id"])
        contest_list.append(ContestModel(**contest))

    return contest_list


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
