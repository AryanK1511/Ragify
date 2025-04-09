# app/utils/database_utils.py

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from utils.logger import CustomLogger


class DatabaseUtils:
    @staticmethod
    def get_text_from_webpages(urls):
        try:
            CustomLogger.create_log(
                "info", f"Fetching content from {len(urls)} webpages"
            )
            loader = WebBaseLoader(urls)
            docs = loader.load()
            CustomLogger.create_log(
                "info", f"Successfully fetched content from {len(docs)} webpages"
            )
            return docs
        except Exception as e:
            CustomLogger.create_log(
                "error", f"Error fetching webpage content: {str(e)}"
            )
            raise Exception(f"Failed to fetch webpage content: {str(e)}")

    @staticmethod
    def chunk_documents(docs, chunk_size=1000, chunk_overlap=200):
        try:
            CustomLogger.create_log("info", f"Chunking {len(docs)} documents")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )

            chunked_docs = []
            for doc in docs:
                url = doc.metadata.get("source", "")

                chunks = text_splitter.split_text(doc.page_content)

                for chunk in chunks:
                    chunked_docs.append(
                        Document(page_content=chunk, metadata={"url": url})
                    )

            CustomLogger.create_log(
                "info", f"Created {len(chunked_docs)} chunks from {len(docs)} documents"
            )
            return chunked_docs
        except Exception as e:
            CustomLogger.create_log("error", f"Error chunking documents: {str(e)}")
            raise Exception(f"Failed to chunk documents: {str(e)}")
