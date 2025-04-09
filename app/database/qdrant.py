# app/database/qdrant.py


from config import settings
from constants import OPENAI_EMBEDDING_DIMENSION, OPENAI_EMBEDDING_MODEL
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    VectorParams,
)
from utils.database_utils import DatabaseUtils
from utils.logger import CustomLogger


class QdrantDatabase:
    def __init__(self):
        try:
            if settings.PYTHON_ENV.lower() == "prod":
                CustomLogger.create_log("info", "Connecting to Qdrant Cloud (PROD)")
                self.client = QdrantClient(
                    url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY
                )
            else:
                CustomLogger.create_log("info", "Connecting to Qdrant Local (DEV)")
                self.client = QdrantClient(url="http://localhost:6333")

            self.client.get_collections()
            CustomLogger.create_log("info", "Successfully connected to Qdrant")

            self.embeddings = OpenAIEmbeddings(
                model=OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY
            )

            self._ensure_collection_exists()

            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=settings.QDRANT_COLLECTION_NAME,
                embedding=self.embeddings,
            )
        except Exception as e:
            CustomLogger.create_log("error", f"Failed to connect to Qdrant: {str(e)}")
            raise Exception(f"Failed to connect to Qdrant database: {str(e)}")

    def _ensure_collection_exists(self):
        collections = self.client.get_collections()
        collection_exists = any(
            collection.name == settings.QDRANT_COLLECTION_NAME
            for collection in collections.collections
        )

        if not collection_exists:
            CustomLogger.create_log(
                "info",
                f"Creating collection {settings.QDRANT_COLLECTION_NAME} in Qdrant",
            )
            self.client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=OPENAI_EMBEDDING_DIMENSION, distance=Distance.COSINE
                ),
            )
        else:
            CustomLogger.create_log(
                "info",
                f"Collection {settings.QDRANT_COLLECTION_NAME} already exists in Qdrant",
            )

    def search(self, query, k=3):
        CustomLogger.create_log("info", f"Searching for {query}")
        results = self.vector_store.similarity_search_with_score(query, k=k)
        processed_results = []

        for doc, score in results:
            doc.metadata["score"] = round(score, 4)
            processed_results.append(doc)

        return processed_results

    def add_webpage_docs(self, added_links, removed_links):
        try:
            if removed_links:
                CustomLogger.create_log(
                    "info", f"Removing embeddings for {len(removed_links)} links"
                )
                for url in removed_links:
                    print(f"\nProcessing URL: {url}")
                    all_point_ids = []
                    offset = None

                    # Use pagination to get all points for this URL
                    while True:
                        # Get points for this URL with pagination
                        scroll_results = self.client.scroll(
                            collection_name=settings.QDRANT_COLLECTION_NAME,
                            scroll_filter=Filter(
                                must=[
                                    FieldCondition(
                                        key="metadata.url",
                                        match=MatchValue(value=url),
                                    )
                                ]
                            ),
                            limit=100,  # Increased limit
                            offset=offset,
                        )

                        points = scroll_results[0]
                        next_offset = scroll_results[1]

                        print(f"Found {len(points)} points in this batch")

                        # Extract point IDs from the scroll results
                        for point in points:
                            print(f"Point ID: {point.id}")
                            if isinstance(point.id, str):
                                all_point_ids.append(point.id)
                            elif isinstance(point.id, int):
                                all_point_ids.append(str(point.id))

                        # Break if no more points
                        if not next_offset:
                            break

                        offset = next_offset

                    print(f"Total points to delete for URL {url}: {len(all_point_ids)}")

                    if all_point_ids:
                        print(f"Deleting points with IDs: {all_point_ids}")
                        # Delete in batches to avoid potential issues with large lists
                        batch_size = 100
                        for i in range(0, len(all_point_ids), batch_size):
                            batch = all_point_ids[i : i + batch_size]
                            print(
                                f"Deleting batch {i//batch_size + 1} with {len(batch)} points"
                            )
                            self.client.delete(
                                collection_name=settings.QDRANT_COLLECTION_NAME,
                                points_selector=PointIdsList(points=batch),
                            )
                CustomLogger.create_log(
                    "info", "Successfully removed embeddings for removed links"
                )

            if added_links:
                CustomLogger.create_log(
                    "info", f"Processing {len(added_links)} new links"
                )

                docs = DatabaseUtils.get_text_from_webpages(added_links)
                chunked_docs = DatabaseUtils.chunk_documents(docs)

                if chunked_docs:
                    self.vector_store.add_documents(chunked_docs)
                    CustomLogger.create_log(
                        "info", f"Added {len(chunked_docs)} chunks to vector store"
                    )

        except Exception as e:
            CustomLogger.create_log("error", f"Error in add_webpage_docs: {str(e)}")
            raise Exception(f"Failed to update webpage documents: {str(e)}")
