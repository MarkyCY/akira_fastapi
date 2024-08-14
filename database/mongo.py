import os
import motor.motor_asyncio
from models.users import UserInDB

async def get_db():
    mongo_uri = os.getenv('MONGO_URI')
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    return client.otakusenpai


#Fake
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)