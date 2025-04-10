# app/utils/database_utils.py


import io

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    WebBaseLoader,
)
from utils.logger import logger


class DatabaseUtils:
    @staticmethod
    def get_webpage_text(url):
        try:
            logger.info(f"Fetching content from webpage: {url}")
            loader = WebBaseLoader([url])
            docs = loader.load()
            if docs and len(docs) > 0:
                logger.info(f"Successfully fetched content from webpage: {url}")
                return docs[0].page_content
            return None
        except Exception as e:
            logger.error(f"Error fetching webpage content: {str(e)}")
            return None

    @staticmethod
    def get_document_text(doc_name, file_obj=None, content_type=None):
        try:
            logger.info(f"Extracting text from document: {doc_name}")

            # If file_obj is not provided, fetch from S3
            if file_obj is None:
                # Import here to avoid circular imports
                from database.s3 import S3Storage

                s3_storage = S3Storage()
                file_content, content_type = s3_storage.download_file(doc_name)
                file_obj = io.BytesIO(file_content)

            # Determine file type from extension if not provided
            if content_type is None:
                if doc_name.endswith(".pdf"):
                    content_type = "application/pdf"
                else:
                    content_type = "text/plain"

            # Process based on content type
            if content_type == "application/pdf" or doc_name.endswith(".pdf"):
                # For PDF files, use PyPDFLoader
                loader = PyPDFLoader(file_obj)
                docs = loader.load()
                if docs and len(docs) > 0:
                    text = "\n\n".join([doc.page_content for doc in docs])
                    logger.info(f"Successfully extracted text from PDF: {doc_name}")
                    return text
            else:
                # For text files, use TextLoader
                # TextLoader expects a string path, so we need to write to a temporary file
                import tempfile

                # Get file extension from doc_name or default to .txt
                extension = doc_name.split(".")[-1] if "." in doc_name else "txt"

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{extension}"
                ) as temp_file:
                    # If file_obj is a BytesIO, we need to get its value
                    if isinstance(file_obj, io.BytesIO):
                        temp_file.write(file_obj.getvalue())
                    else:
                        # Otherwise, assume it's a file-like object with read method
                        temp_file.write(file_obj.read())
                    temp_file_path = temp_file.name

                try:
                    loader = TextLoader(temp_file_path)
                    docs = loader.load()
                    if docs and len(docs) > 0:
                        logger.info(
                            f"Successfully extracted text from text file: {doc_name}"
                        )
                        return docs[0].page_content
                finally:
                    # Clean up the temporary file
                    import os

                    os.unlink(temp_file_path)

            logger.warning(f"No text content extracted from document: {doc_name}")
            return None
        except Exception as e:
            logger.error(f"Error extracting text from document {doc_name}: {str(e)}")
            return None

    @staticmethod
    def chunk_documents(docs, chunk_size=1000, chunk_overlap=200):
        try:
            logger.info(f"Chunking {len(docs)} documents")

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

            logger.info(
                f"Created {len(chunked_docs)} chunks from {len(docs)} documents"
            )
            return chunked_docs
        except Exception as e:
            logger.error(f"Error chunking documents: {str(e)}")
            raise Exception(f"Failed to chunk documents: {str(e)}")
