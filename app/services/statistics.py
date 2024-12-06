from datetime import datetime
from typing import Optional, OrderedDict
from db.database import get_db
from schemas.statistics import Score, StatisticsRequest, StatisticsRespond
from bson import ObjectId
from pymongo.errors import PyMongoError

db = get_db()
statistics_collection = db["statistics"]


async def save_statistics(statistics_entry: StatisticsRequest) -> bool:
    try:
        entry_dict = statistics_entry.model_dump(by_alias=True)
        entry_dict["date"] = datetime.combine(entry_dict["date"], datetime.min.time())
        await statistics_collection.insert_one(entry_dict)
        return True
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")


async def get_statistics(user_id: str) -> Optional[StatisticsRespond]:
    try:
        if not ObjectId.is_valid(user_id):
            return None
        stats = await statistics_collection.find({"user_id": user_id}).to_list(None)
        result_dict = {}
        if stats:
            for stat in stats:
                date = stat["date"].date()
                score = Score(**stat["scores"])
                result_dict[date] = score
            return StatisticsRespond(user_id=user_id, statistics=result_dict)
        return None
    except PyMongoError as e:
        raise Exception(f"Database error: {e}")
