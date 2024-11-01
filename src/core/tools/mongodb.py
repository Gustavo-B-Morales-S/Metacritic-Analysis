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
    '''
    A client for connecting to a MongoDB instance and managing database operations.

    Args:
        host (str): The MongoDB server host.
        port (int): The MongoDB server port.
        database (str): The MongoDB database name.

    Attributes:
        host (str): The MongoDB server host.
        port (int): The MongoDB server port.
        database (str): The MongoDB database name.
    '''

    def __init__(
        self,
        host: str = mongodb_settings.host,
        port: int = mongodb_settings.port,
        database: str = mongodb_settings.database,
    ) -> None:
        '''
        Initializes the MongoDBClient instance with the given server host, port, and database name.

        Args:
            host (str): The MongoDB server host.
            port (int): The MongoDB server port.
            database (str): The MongoDB database name.
        '''
        self.host = host
        self.port = port
        self.database = database

    @cached_property
    def _client(self) -> MongoClient:
        '''
        Establishes a connection to the MongoDB server and returns the client.

        Returns:
            MongoClient: The MongoDB client.

        Raises:
            ServerSelectionTimeoutError: If the server could not be reached in time.
            PyMongoError: For general MongoDB-related errors.
            Exception: For any other unexpected errors.
        '''
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
        '''
        Provides access to the specified MongoDB database.

        Returns:
            Database: The MongoDB database instance.
        '''
        return self._client[self.database]

    @contextmanager
    def get_session(self) -> Generator[ClientSession, None, None]:
        '''
        Context manager for MongoDB session handling.

        Yields:
            ClientSession: The MongoDB client session.

        Usage:
            Use this method to ensure that operations within the context are
            performed within the same session for causal consistency.
        '''
        session: ClientSession = self._client.start_session(causal_consistency=True)

        try:
            yield session

        finally:
            session.end_session()

    def insert_document(
        self, document: HTTPResponse, collection: Literal['paths', 'contents']
    ) -> None:
        '''
        Inserts a document into a specified collection within a MongoDB session.

        Args:
            document (HTTPResponse): The document to insert, as an HTTPResponse object.
            collection (Literal['paths', 'contents']): The name of the collection to insert the document into.

        Raises:
            PyMongoError: If an error occurs during the document insertion.
        '''
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
        '''
        Retrieves all documents from a specified collection.

        Args:
            collection (Literal['paths', 'contents']): The name of the collection to retrieve documents from.

        Yields:
            HTTPResponse: Each document from the collection, converted into an HTTPResponse object.

        Raises:
            PyMongoError: If an error occurs during the document retrieval.
        '''
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
        '''
        Drops all collections in the current database.

        Raises:
            PyMongoError: If an error occurs during the collection drop process.
        '''
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
        '''
        Closes the MongoDB client connection.

        Raises:
            PyMongoError: If an error occurs while closing the connection.
        '''
        try:
            self._client.close()
            logger.info('MongoDB connection closed.')

        except PyMongoError as err:
            logger.error(f'Failed to close connection: {err}')
            raise

mongo_client: MongoDBClient = MongoDBClient()
