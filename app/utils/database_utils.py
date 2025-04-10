# app/utils/database_utils.py

import tempfile
from typing import Any, List, Optional

from database.s3 import S3Storage
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    WebBaseLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger import logger

s3 = S3Storage()


class DatabaseUtils:
    @staticmethod
    def get_webpage_text(url: str) -> Optional[List[Any]]:
        try:
            logger.info(f"Fetching content from webpage: {url}")
            loader = WebBaseLoader([url])
            docs = loader.load()
            if docs and len(docs) > 0:
                for doc in docs:
                    doc.metadata["source_url"] = url
                logger.info(f"Successfully fetched content from webpage: {url}")
                return docs
            return None
        except Exception as e:
            logger.error(f"Error fetching webpage content: {str(e)}")
            return None

    @staticmethod
    def get_document_text(s3_filename: str) -> Optional[List[Any]]:
        try:
            file_content, content_type = s3.download_file(s3_filename)

            if content_type == "application/pdf":
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                loader = PyPDFLoader(tmp_path)

            elif content_type == "text/plain":
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".txt"
                ) as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                loader = TextLoader(tmp_path)

            else:
                raise ValueError(f"Unsupported file type: {content_type}")

            docs = loader.load()

            for doc in docs:
                doc.metadata["source_filename"] = s3_filename

            return docs if docs else None

        except Exception as e:
            logger.error(f"Error fetching document text: {str(e)}")
            return None

    @staticmethod
    def chunk_documents(docs: List[Any]) -> List[Any]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )
        return splitter.split_documents(docs)
