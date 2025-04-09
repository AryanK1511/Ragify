# app/database/mongodb.py

from typing import List

from config import settings
from database.qdrant import QdrantDatabase
from pymongo import MongoClient


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
            print(f"Error getting links: {e}")
            return []

    def add_links(self, new_links: List[str]) -> None:
        try:
            existing_doc = self.links_collection.find_one({})
            current_links = existing_doc.get("all_links", []) if existing_doc else []

            removed_links = [link for link in current_links if link not in new_links]
            added_links = [link for link in new_links if link not in current_links]

            print("Removed links:", removed_links)
            print("Added links:", added_links)

            self.qdrant_db.add_webpage_docs(added_links, removed_links)

            self.links_collection.replace_one(
                {},
                {"all_links": new_links},
                upsert=True,
            )

        except Exception as e:
            print(f"Error adding links: {e}")
