# db/database.py
from pymongo import ASCENDING, MongoClient
from core.config import settings

MONGO_URI = settings.mongo_uri

client = MongoClient(MONGO_URI)
db = client["peace"]
users_collection = db["users"]


async def create_indexes():
    users_collection.create_index([("email", ASCENDING)], unique=True)
