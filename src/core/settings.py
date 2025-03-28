# Third-Party Libraries
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(SettingsConfigDict):
    env_file: str = '.env'
    env_file_encoding: str = 'utf-8'
    extra: str = 'ignore'

    
class ClientSettings(BaseSettings):
    max_concurrent_requests: int = 450
    max_retry_attempts: int = 3
    max_connections: int = 300
    interval: int | float = 0
    timeout: int | None = None
    follow_redirects: bool = True

default_settings: ClientSettings = ClientSettings()


class AWSCredentials(BaseSettings):
    model_config = BaseConfig(env_prefix='AWS_')
    region: str
    access_key_id: str
    secret_access_key: str

aws_credentials: AWSCredentials = AWSCredentials()


class MongoDBSettings(BaseSettings):
    model_config = BaseConfig(env_prefix='MONGODB_')
    host: str
    port: int
    database: str
    username: str | None = None
    password: str | None = None
    auth_source: str = "admin"

mongodb_settings: MongoDBSettings = MongoDBSettings()


class S3Settings(BaseSettings):
    model_config = BaseConfig(env_prefix='S3_')
    bucket_name: str
    folder_name: str

s3_settings: S3Settings = S3Settings()
