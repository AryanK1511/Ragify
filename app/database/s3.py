# app/database/s3.py

import boto3
from botocore.exceptions import ClientError
from config import settings
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
            logger.info("S3Storage initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing S3Storage: {e}")
            raise Exception(f"Error initializing S3Storage: {e}")

    def get_stored_filenames(self):
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

    def upload_files(self, files):
        uploaded_files = []
        for user_file in files:
            try:
                self.upload_file(
                    user_file["file_obj"],
                    user_file["file_name"],
                    user_file["content_type"],
                )
                uploaded_files.append(user_file["file_name"])
            except Exception as e:
                logger.error(f"Error uploading file {user_file['file_name']}: {e}")

        if uploaded_files:
            logger.info(f"Files added: {', '.join(uploaded_files)}")

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
