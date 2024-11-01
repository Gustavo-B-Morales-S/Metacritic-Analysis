# Native Libraries
import json
from typing import Literal, Optional
from datetime import date as date_

# Third-Party Libraries
from awswrangler import s3
import boto3
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import BotoCoreError, ClientError
from loguru import logger
from pandas import DataFrame
from pandas.errors import EmptyDataError

# Local Modules
from src.core.settings import s3_settings


class S3Client:
    '''
    A client for handling interactions with an S3 bucket, including uploading JSON and Parquet files.

    Args:
        bucket_name (str): The name of the S3 bucket.

    Attributes:
        _bucket_name (str): The S3 bucket name.
        _s3 (boto3.client): The boto3 S3 client instance.
    '''

    def __init__(self, bucket_name: str = s3_settings.bucket_name) -> None:
        '''
        Initializes the S3Client instance with the specified bucket name.

        Args:
            bucket_name (str): The name of the S3 bucket.
        '''
        self._bucket_name = bucket_name
        self._s3 = boto3.client('s3')

    def get_file_path(
        self,
        layer: Literal['raw', 'cleansed'],
        date: Optional[str] = None,
        file_name: str | Literal['unknown'] = 'unknown',
        file_extension: str | Literal['txt'] = 'txt',
    ) -> str:
        '''
        Generates an S3 file path based on the layer, date, file name, and file extension.

        Args:
            layer (Literal['raw', 'cleansed']): The data layer (e.g., raw or cleansed).
            date (Optional[str]): The date in 'YYYY-MM-DD' format; defaults to today if not provided.
            file_name (str | Literal['unknown']): The base name of the file.
            file_extension (str | Literal['txt']): The file extension.

        Returns:
            str: The generated S3 file path.
        '''
        current_date: str = date_.today().strftime('%Y-%m-%d')

        s3_file_path: str = (
            f's3://{s3_settings.bucket_name}/{s3_settings.folder_name}/{layer}'
            f'/{layer}_{file_name}_{date or current_date}.{file_extension}'
        )
        return s3_file_path

    def upload_json(self, file_path: str, json_like: list[dict]) -> None:
        '''
        Uploads a JSON-like data structure (list of dictionaries) to a specified S3 path.

        Args:
            file_path (str): The destination S3 path.
            json_like (list[dict]): The JSON-like data structure to upload.

        Raises:
            S3UploadFailedError: If the upload to S3 fails.
            Exception: For any other unexpected errors.
        '''
        body: str = json.dumps(json_like)
        key: str = file_path.removeprefix(f's3://{self._bucket_name}/')

        try:
            self._s3.put_object(
                ContentType='application/json',
                Bucket=self._bucket_name,
                Body=body,
                Key=key,
            )
            logger.info(f'JSON file uploaded to {file_path}')

        except S3UploadFailedError as e:
            logger.error(f'Upload failed for JSON file: {e}')

        except Exception as e:
            logger.error(f'Error uploading JSON data: {e}')

    def upload_parquet(
        self, df: DataFrame, file_path: str, **extra_settings
    ) -> None:
        '''
        Converts a DataFrame to a Parquet file and uploads it to a specified S3 path.

        Args:
            df (DataFrame): The DataFrame to be converted and uploaded.
            file_path (str): The destination S3 path.
            **extra_settings: Additional settings for the parquet upload.

        Raises:
            EmptyDataError: If the DataFrame is empty and cannot be uploaded.
            ClientError: If there is an error with the S3 client during upload.
            BotoCoreError: If there is an AWS connection or configuration error.
            Exception: For any other unexpected errors.
        '''
        if df.empty:
            raise EmptyDataError('The DataFrame is empty and cannot be sent.')

        try:
            s3.to_parquet(df=df, path=file_path, **extra_settings)
            logger.info(f'Parquet file uploaded to {file_path}')

        except ClientError as e:
            logger.error(f'S3 Client Error: {e.response["Error"]["Message"]}')

        except BotoCoreError as e:
            logger.error(f'AWS connection or configuration error: {e}')

        except Exception as e:
            logger.error(f'An unexpected error occurred: {e}')


s3_client: S3Client = S3Client()
