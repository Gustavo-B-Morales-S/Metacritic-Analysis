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

    def __init__(self, bucket_name: str = s3_settings.bucket_name) -> None:
        self._bucket_name = bucket_name
        self._s3 = boto3.client('s3')

    def get_file_path(
        self,
        layer: Literal['raw', 'cleansed'],
        date: Optional[str] = None,
        file_name: str | Literal['unknown'] = 'unknown',
        file_extension: str | Literal['txt'] = 'txt',
    ) -> str:
        current_date: str = date_.today().strftime('%Y-%m-%d')

        s3_file_path: str = (
            f's3://{s3_settings.bucket_name}/{s3_settings.folder_name}/{layer}'
            f'/{layer}_{file_name}_{date or current_date}.{file_extension}'
        )
        return s3_file_path
    def upload_json(self, file_path: str, json_like: list[dict]) -> None:
        """Uploads a JSON-like data structure (list of dictionaries) to a specified S3 path."""
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
        """Convert a dataframe to parquet file and upload it to a specified S3 path."""
        if df.empty:
            raise EmptyDataError('The DataFrame is empty and cannot be sent.')

        try:
            s3.to_parquet(df=df, path=file_path, **extra_settings)
            logger.info(f'Parquet file uploaded to {file_path}')

        except ClientError as e:
            logger.error(f'S3 Client Error: {e.response['Error']['Message']}')

        except BotoCoreError as e:
            logger.error(f'AWS connection or configuration error: {e}')

        except Exception as e:
            logger.error(f'An unexpected error occurred: {e}')


s3_client: S3Client = S3Client()
