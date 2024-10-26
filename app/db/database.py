# db/database.py
from pymongo import ASCENDING, MongoClient
from core.config import settings

MONGO_URI = settings.mongo_uri

client = MongoClient(MONGO_URI)
db = client['face_analysis']
users_collection = db['users']

async def create_indexes():
    await users_collection.create_index(['email', ASCENDING], unique=True)