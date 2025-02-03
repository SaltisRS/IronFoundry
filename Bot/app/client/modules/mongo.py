import os

from loguru import logger
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.cursor import AsyncCursor
from dotenv import load_dotenv


load_dotenv()

class MongoClient:
    """
    Class to handle the connection to the MongoDB database
    
    Must call the connect method to establish a connection before using the client
    """
    def __init__(self):
        self.uri = os.getenv("MONGO_URI")
        self.client = None
        self.db = None
    
    async def connect(self) -> AsyncMongoClient:
        self.client = AsyncMongoClient(self.uri)
        return self.client
    
    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None
    
    async def set_database(self, database: str) -> str:
        if not self.client:
            raise Exception("Must connect to the client before setting the database")
        self.db = self.client[database]
        logger.debug(f"Database set to {database}")
        return True
    
    async def get_collection(self, collection: str) -> AsyncCollection | None:
        return self.db[collection]
    
    async def get_document(self, collection: str, query: dict) -> dict | None:
        doc = await self.client[self.db][collection].find_one(query)
        if not doc:
            raise Exception("Document not found")
        return doc
    
    async def get_many(self, collection: str, query: dict) -> AsyncCursor:
        docs = await self.client[self.db][collection].find(query)
        if not docs:
            raise Exception("No documents found")
        return docs
    
    async def get_count(self, collection: str, query: dict = {}) -> int:
        return await self.client[self.db][collection].count_documents(query)
    
    async def insert_document(self, collection: str, document: dict):
        return await self.client[self.db][collection].insert_one(document)
    
    async def update_document(self, collection: str, query: dict, update: dict):
        return await self.client[self.db][collection].update_one(query, update)
    
    async def delete_document(self, collection: str, query: dict):
        return await self.client[self.db][collection].delete_one(query)