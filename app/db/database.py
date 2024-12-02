# db/database.py
from pymongo import ASCENDING
from core.config import settings

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = settings.mongo_uri

client = AsyncIOMotorClient(MONGO_URI)
db = client["peace"]
users_collection = db["users"]


async def create_indexes():
    await users_collection.create_index([("email", ASCENDING)], unique=True)


def get_db():
    return db
