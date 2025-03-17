from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
mongo_uri = os.getenv('MONGO_URI')
client = AsyncIOMotorClient(mongo_uri)
db = client['otakusenpai']

async def get_db():
    return db