# app/database/mongodb.py

from typing import List

from config import settings
from database.qdrant import QdrantDatabase
from pymongo import MongoClient
from utils.logger import logger


class MongoDB:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client.ragify_database
        self.links_collection = self.db.links
        self.qdrant_db = QdrantDatabase()

    def get_all_links(self) -> List[str]:
        try:
            doc = self.links_collection.find_one({}, {"_id": 0})
            return doc.get("all_links", []) if doc else []
        except Exception as e:
            logger.error(f"Error getting links: {e}")
            return []

    def sync_links(self, new_links: List[str]) -> None:
        try:
            self.links_collection.replace_one(
                {},
                {"all_links": new_links},
                upsert=True,
            )

        except Exception as e:
            logger.error(f"Error adding links: {e}")
