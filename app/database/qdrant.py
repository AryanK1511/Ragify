# app/database/qdrant.py


from config import settings
from constants import OPENAI_EMBEDDING_DIMENSION, OPENAI_EMBEDDING_MODEL
from langchain.docstore.document import Document
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
    def __init__(self):
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

    def _ensure_collection_exists(self):
        collections = self.client.get_collections()
        collection_exists = any(
            collection.name == settings.QDRANT_COLLECTION_NAME
            for collection in collections.collections
        )

        if not collection_exists:
            logger.info(
                f"Creating collection {settings.QDRANT_COLLECTION_NAME} in Qdrant"
            )
            self.client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=OPENAI_EMBEDDING_DIMENSION, distance=Distance.COSINE
                ),
            )
        else:
            logger.info(
                f"Collection {settings.QDRANT_COLLECTION_NAME} already exists in Qdrant"
            )

    def search(self, query, k=3):
        logger.info(f"Searching for {query}")
        results = self.vector_store.similarity_search_with_score(query, k=k)
        processed_results = []

        for doc, score in results:
            doc.metadata["score"] = round(score, 4)
            processed_results.append(doc)

        return processed_results

    def _get_point_ids_for_document(self, document_name):
        point_ids = []
        offset = None

        try:
            while True:
                scroll_results = self.client.scroll(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="source",
                                match=MatchValue(value=document_name),
                            )
                        ]
                    ),
                    offset=offset,
                    limit=100,
                )
                points = scroll_results[0]
                if not points:
                    break
                point_ids.extend([point.id for point in points])
                offset = scroll_results[1]

            return point_ids
        except Exception as e:
            logger.error(
                f"Error getting point IDs for document {document_name}: {str(e)}"
            )
            return []

    def remove_embeddings(self, document_names):
        if not document_names:
            return

        logger.info(f"Removing embeddings for {len(document_names)} documents")

        all_point_ids = []
        for doc_name in document_names:
            point_ids = self._get_point_ids_for_document(doc_name)
            all_point_ids.extend(point_ids)

        if all_point_ids:
            try:
                self.client.delete(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points_selector=PointIdsList(points=all_point_ids),
                )
                logger.info(f"Removed {len(all_point_ids)} embeddings")
            except Exception as e:
                logger.error(f"Error removing embeddings: {str(e)}")

    def add_embeddings(self, documents, is_webpage=False):
        if not documents:
            return

        item_type = "webpages" if is_webpage else "documents"
        logger.info(f"Adding embeddings for {len(documents)} {item_type}")

        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            docs_to_add = []

            for doc in batch:
                try:
                    doc_name = doc["name"]
                    content_type = doc.get("content_type")

                    if is_webpage:
                        text = DatabaseUtils.get_webpage_text(doc_name)
                    else:
                        text = DatabaseUtils.get_document_text(
                            doc_name, content_type=content_type
                        )

                    if text:
                        doc_obj = Document(
                            page_content=text,
                            metadata={
                                "source": doc_name,
                                "type": "webpage" if is_webpage else "document",
                            },
                        )
                        # Chunk the document before adding to vector store
                        chunked_docs = DatabaseUtils.chunk_documents([doc_obj])
                        docs_to_add.extend(chunked_docs)
                    else:
                        logger.warning(f"No text content found for {doc_name}")
                except Exception as e:
                    logger.error(f"Error processing {doc_name}: {str(e)}")

            if docs_to_add:
                try:
                    self.vector_store.add_documents(docs_to_add)
                    logger.info(f"Added {len(docs_to_add)} embeddings in batch")
                except Exception as e:
                    logger.error(f"Error adding embeddings batch: {str(e)}")

    def add_webpage_docs(self, added_links, removed_links):
        self.remove_embeddings(removed_links)
        documents = [{"name": link, "type": "webpage"} for link in added_links]
        self.add_embeddings(documents, is_webpage=True)

    def add_document_docs(self, documents, removed_documents):
        self.remove_embeddings(removed_documents)
        self.add_embeddings(documents, is_webpage=False)
