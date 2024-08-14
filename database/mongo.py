import os
import motor.motor_asyncio

from dotenv import load_dotenv
load_dotenv()

async def get_db():
    mongo_uri = os.getenv('MONGO_URI')
    print(mongo_uri)
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    return client.otakusenpai
