import os
import motor.motor_asyncio

# Resolve DNS for Termux [ Disable if you dont use Termux ]
import dns.resolver
dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']

from dotenv import load_dotenv
load_dotenv()

async def get_db():
    mongo_uri = os.getenv('MONGO_URI')
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    return client.otakusenpai
