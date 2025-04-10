# app/database/mongodb.py

from typing import List

from config import settings
from database.qdrant import QdrantDatabase
from pymongo import MongoClient
from utils.logger import logger


class MongoDB:
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGODB_URI)
            self.db = self.client.ragify_database
            self.links_collection = self.db.links
            self.qdrant_db = QdrantDatabase()
            logger.info("MongoDB initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MongoDB: {e}")
            raise Exception(f"Error initializing MongoDB: {e}")

    def get_all_links(self) -> List[str]:
        try:
            doc = self.links_collection.find_one({}, {"_id": 0})
            logger.info(f"Fetched {len(doc.get('all_links', []))} links from MongoDB")
            return doc.get("all_links", []) if doc else []
        except Exception as e:
            logger.error(f"Error getting links: {e}")
            return []

    def add_links(self, new_links: List[str]) -> None:
        try:
            existing_doc = self.links_collection.find_one({})
            current_links = existing_doc.get("all_links", []) if existing_doc else []

            removed_links = [link for link in current_links if link not in new_links]
            added_links = [link for link in new_links if link not in current_links]

            logger.info(f"Removed links: {removed_links}")
            logger.info(f"Added links: {added_links}")

            self.qdrant_db.add_webpage_docs(added_links, removed_links)

            self.links_collection.replace_one(
                {},
                {"all_links": new_links},
                upsert=True,
            )

            logger.info("Links added successfully to MongoDB")

        except Exception as e:
            logger.error(f"Error adding links: {e}")
            raise Exception(f"Error adding links: {e}")
