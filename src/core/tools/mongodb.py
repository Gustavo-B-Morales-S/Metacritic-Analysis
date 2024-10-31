# Native Libraries
from contextlib import contextmanager
from functools import cached_property
from typing import Generator, Literal

# Third Party Libraries
from loguru import logger
from pymongo import MongoClient
from pymongo.client_session import ClientSession
from pymongo.cursor import Cursor
from pymongo.database import Database
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

# Local Modules
from src.core.contracts import HTTPResponse
from src.core.settings import mongodb_settings


class MongoDBClient:
    def __init__(
        self,
        host: str = mongodb_settings.host,
        port: int = mongodb_settings.port,
        database: str = mongodb_settings.database,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database

    @cached_property
    def _client(self) -> MongoClient:
        try:
            client: MongoClient = MongoClient(self.host, self.port, connect=True)
            logger.info(
                f'Connected to MongoDB at {self.host}:{self.port}/{self.database}'
            )
            return client

        except ServerSelectionTimeoutError as err:
            logger.error(f'Connection failed: {err}')
            raise
        except PyMongoError as err:
            logger.error(f'A MongoDB error occurred: {err}')
            raise
        except Exception as err:
            logger.error(f'An unexpected error occurred: {err}')
            raise

    @cached_property
    def _database(self) -> Database:
        return self._client[self.database]

    @contextmanager
    def get_session(self) -> Generator[ClientSession, None, None]:
        """Context manager for MongoDB session handling."""
        session: ClientSession = self._client.start_session(causal_consistency=True)

        try:
            yield session

        finally:
            session.end_session()

    def insert_document(
        self, document: HTTPResponse, collection: Literal['paths', 'contents']
    ) -> None:
        """Insert a document into a specific collection with session management."""
        try:
            with self.get_session() as session:
                self._database[collection].insert_one(
                    document.to_dict(), session=session
                )

        except PyMongoError as err:
            logger.error(f'Failed to insert document: {err}')
            raise

    def get_all_documents(
        self, collection: Literal['paths', 'contents']
    ) -> Generator[HTTPResponse, None, None]:
        """Retrieve all documents from a specific collection."""
        try:
            with self.get_session() as session:
                documents: Cursor = self._database[collection].find(
                    {}, {'_id': 0}, session=session
                )

                for document in documents:
                    yield HTTPResponse(**document)

        except PyMongoError as err:
            logger.error(f'Failed to retrieve documents: {err}')
            raise

    def drop_all_collections(self) -> None:
        """Drop all collections in the database"""
        try:
            with self.get_session() as session:
                for collection in self._database.list_collection_names(
                    session=session
                ):
                    self._database.drop_collection(collection, session=session)
                logger.info('All collections dropped.')

        except PyMongoError as err:
            logger.error(f'Failed to drop collections: {err}')
            raise

    def close_connection(self) -> None:
        """Close the MongoDB client connection."""
        try:
            self._client.close()
            logger.info('MongoDB connection closed.')

        except PyMongoError as err:
            logger.error(f'Failed to close connection: {err}')
            raise

mongo_client: MongoDBClient = MongoDBClient()
