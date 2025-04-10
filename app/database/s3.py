# app/database/s3.py

import boto3
from botocore.exceptions import ClientError
from config import settings
from database.qdrant import QdrantDatabase
from utils.logger import logger


class S3Storage:
    def __init__(self):
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            self.bucket_name = settings.AWS_BUCKET_NAME
            self.qdrant_db = QdrantDatabase()
            logger.info("S3Storage initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing S3Storage: {e}")
            raise Exception(f"Error initializing S3Storage: {e}")

    def upload_file(self, file_obj, file_name, content_type):
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                file_name,
                ExtraArgs={"ContentType": content_type},
            )

            url = f"https://{self.bucket_name}.s3.amazonaws.com/{file_name}"
            return url

        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            raise

    def upload_files(self, documents):
        """
        Upload files to S3.

        Args:
            documents: List of document objects, each containing:
                - name: Document name
                - file_obj: File object
                - content_type: Content type

        Returns:
            List of uploaded file names
        """
        uploaded_files = []
        for doc in documents:
            try:
                self.upload_file(doc["file_obj"], doc["name"], doc["content_type"])
                uploaded_files.append(doc["name"])
            except Exception as e:
                logger.error(f"Error uploading file {doc['name']}: {e}")

        if uploaded_files:
            logger.info(f"Documents added: {', '.join(uploaded_files)}")

        return uploaded_files

    def delete_file(self, file_name):
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_name)
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            raise

    def delete_files(self, file_names):
        deleted_files = []
        for file_name in file_names:
            try:
                self.delete_file(file_name)
                deleted_files.append(file_name)
            except Exception as e:
                logger.error(f"Error deleting file {file_name}: {e}")

        if deleted_files:
            logger.info(f"Documents removed: {', '.join(deleted_files)}")

        return deleted_files

    def get_all_files(self):
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)

            files = []
            if "Contents" in response:
                for item in response["Contents"]:
                    files.append(item["Key"])

            return files

        except ClientError as e:
            logger.error(f"Error listing files from S3: {e}")
            raise

    def download_file(self, file_name):
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_name)
            return response["Body"].read(), response["ContentType"]
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {e}")
            raise

    def update_documents(self, documents):
        try:
            current_files = set(self.get_all_files())

            new_doc_names = {doc["name"] for doc in documents}

            files_to_remove = list(current_files - new_doc_names)

            new_docs = [doc for doc in documents if "file_obj" in doc]

            added_files = []
            if new_docs:
                added_files = self.upload_files(new_docs)

                for doc in new_docs:
                    if "file_obj" in doc:
                        del doc["file_obj"]

            removed_files = []
            if files_to_remove:
                removed_files = self.delete_files(files_to_remove)

            self.qdrant_db.add_document_docs(documents, files_to_remove)

            return added_files, removed_files

        except Exception as e:
            logger.error(f"Error updating documents: {e}")
            raise
