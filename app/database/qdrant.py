# app/database/qdrant.py

from typing import Any, List

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
from utils.logger import logger


class QdrantDatabase:
    def __init__(self) -> None:
        try:
            if settings.PYTHON_ENV.lower() == "prod":
                logger.info("Connecting to Qdrant Cloud (PROD)")
                self.client = QdrantClient(
                    url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY
                )
            else:
                logger.info("Connecting to Qdrant Local (DEV)")
                self.client = QdrantClient(url="http://localhost:6333")

            self.client.get_collections()
            logger.info("Successfully connected to Qdrant")

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
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise Exception(f"Failed to connect to Qdrant database: {str(e)}")

    def _ensure_collection_exists(self) -> None:
        collections = self.client.get_collections()
        collection_exists = any(
            collection.name == settings.QDRANT_COLLECTION_NAME
            for collection in collections.collections
        )

        if not collection_exists:
            logger.info(
                f"Creating collection {settings.QDRANT_COLLECTION_NAME} in Qdrant",
            )
            self.client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=OPENAI_EMBEDDING_DIMENSION, distance=Distance.COSINE
                ),
            )
        else:
            logger.info(
                f"Collection {settings.QDRANT_COLLECTION_NAME} already exists in Qdrant",
            )

    def search(self, query: str, k: int = 3) -> List[Any]:
        logger.info(f"Searching for {query}")
        results = self.vector_store.similarity_search_with_score(query, k=k)
        processed_results = []

        for doc, score in results:
            doc.metadata["score"] = round(score, 4)
            processed_results.append(doc)

        return processed_results

    def remove_embeddings_by_metadata_field(
        self, field_key: str, values: List[str]
    ) -> None:
        try:
            logger.info(f"Removing embeddings where `{field_key}` matches {values}")
            for value in values:
                all_point_ids = []
                offset = None

                while True:
                    scroll_results = self.client.scroll(
                        collection_name=settings.QDRANT_COLLECTION_NAME,
                        scroll_filter=Filter(
                            must=[
                                FieldCondition(
                                    key=f"metadata.{field_key}",
                                    match=MatchValue(value=value),
                                )
                            ]
                        ),
                        limit=100,
                        offset=offset,
                    )

                    points = scroll_results[0]
                    next_offset = scroll_results[1]

                    for point in points:
                        point_id = str(point.id)
                        all_point_ids.append(point_id)

                    if not next_offset:
                        break

                    offset = next_offset

                for i in range(0, len(all_point_ids), 100):
                    batch = all_point_ids[i : i + 100]
                    logger.info(f"Deleting batch {i//100 + 1} with {len(batch)} points")
                    self.client.delete(
                        collection_name=settings.QDRANT_COLLECTION_NAME,
                        points_selector=PointIdsList(points=batch),
                    )

            logger.info(f"Finished removing embeddings for {len(values)} values")

        except Exception as e:
            logger.error(f"Failed to remove embeddings: {str(e)}")
            raise Exception(f"Failed to remove embeddings: {str(e)}")

    def embed_documents(self, documents: List[Any]) -> None:
        try:
            if not documents:
                logger.warning("No documents provided for embedding.")
                return

            logger.info(f"Chunking and embedding {len(documents)} documents...")
            chunked_docs = DatabaseUtils.chunk_documents(documents)
            logger.info(f"Generated {len(chunked_docs)} chunks from input documents.")

            self.vector_store.add_documents(chunked_docs)
            logger.info("Successfully added chunks to Qdrant.")

        except Exception as e:
            logger.error(f"Failed to embed documents: {str(e)}")
            raise Exception(f"Failed to embed documents: {str(e)}")

    def sync_webpage_embeddings(
        self, added_links: List[str], removed_links: List[str]
    ) -> None:
        try:
            if removed_links:
                self.remove_embeddings_by_metadata_field("source_url", removed_links)

            if added_links:
                logger.info(f"Processing {len(added_links)} new links")
                for link in added_links:
                    docs = DatabaseUtils.get_webpage_text(link)
                    if docs:
                        self.embed_documents(docs)

        except Exception as e:
            logger.error(f"Error syncing webpage embeddings: {str(e)}")
            raise Exception(f"Failed to sync webpage documents: {str(e)}")

    def sync_document_embeddings(
        self, added_filenames: List[str], removed_filenames: List[str]
    ) -> None:
        try:
            if removed_filenames:
                self.remove_embeddings_by_metadata_field(
                    "source_filename", removed_filenames
                )

            if added_filenames:
                logger.info(f"Processing {len(added_filenames)} new files")
                for filename in added_filenames:
                    docs = DatabaseUtils.get_document_text(filename)
                    if docs:
                        self.embed_documents(docs)

        except Exception as e:
            logger.error(f"Error syncing document embeddings: {str(e)}")
            raise Exception(f"Failed to sync document embeddings: {str(e)}")
