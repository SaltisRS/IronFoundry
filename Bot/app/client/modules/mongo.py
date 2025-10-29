import os
from typing import Optional, List, Dict, Any
from pymongo import AsyncMongoClient
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult
from pymongo.collection import Collection
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


class MongoClient:
    """MongoDB client using PyMongo's async API (4.10.1)."""

    def __init__(self, db_name: str = os.getenv("DB_NAME")):
        self.uri: str = os.getenv("MONGO_URI", "")
        self.client: AsyncMongoClient = AsyncMongoClient(self.uri)
        self.db = self.client[db_name]
        logger.debug(f"MongoClient initialized with DB: {db_name}")

    async def close(self) -> None:
        """Close the MongoDB connection."""
        await self.client.close()
        logger.debug("MongoDB connection closed.")

    def get_collection(self, collection: str) -> Collection:
        """Retrieve a collection."""
        logger.debug(f"Accessing collection: {collection}")
        return self.db[collection]

    async def get_document(
        self, collection: str, query: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a single document."""
        logger.debug(f"Fetching one document from {collection} with query: {query}")
        document = await self.get_collection(collection).find_one(query)
        if document:
            logger.debug(f"Document found: {document}")
        else:
            logger.debug("No document found.")
        return document

    async def get_many(
        self, collection: str, query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve multiple documents."""
        logger.debug(
            f"Fetching multiple documents from {collection} with query: {query}"
        )
        cursor = self.get_collection(collection).find(query)
        documents = [doc async for doc in cursor]
        logger.debug(f"Retrieved {len(documents)} documents.")
        return documents

    async def get_count(self, collection: str, query: Dict[str, Any] = {}) -> int:
        """Count documents matching a query."""
        logger.debug(f"Counting documents in {collection} with query: {query}")
        count = await self.get_collection(collection).count_documents(query)
        logger.debug(f"Document count: {count}")
        return count

    async def insert_document(
        self, collection: str, document: Dict[str, Any]
    ) -> Optional[str]:
        """Insert a document and return its inserted ID."""
        logger.debug(f"Inserting document into {collection}: {document}")
        result: InsertOneResult = await self.get_collection(collection).insert_one(
            document
        )
        inserted_id = str(result.inserted_id) if result.inserted_id else None
        logger.debug(f"Document inserted with ID: {inserted_id}")
        return inserted_id

    async def update_document(
        self, collection: str, query: Dict[str, Any], update: Dict[str, Any]
    ) -> UpdateResult:
        """Update a document."""
        logger.debug(
            f"Updating document in {collection} with query: {query} and update: {update}"
        )

        # Check if update already has a `$` operator (like `$push`, `$inc`, etc.)
        if any(key.startswith("$") for key in update.keys()):
            update_query = update  # Use update as-is if it contains an operator
        else:
            update_query = {"$set": update}  # Otherwise, wrap in `$set`

        result: UpdateResult = await self.get_collection(collection).update_one(
            query, update_query
        )
        logger.debug(
            f"Matched {result.matched_count}, modified {result.modified_count} documents."
        )
        return result

    async def delete_document(
        self, collection: str, query: Dict[str, Any]
    ) -> DeleteResult:
        """Delete a document."""
        logger.debug(f"Deleting document from {collection} with query: {query}")
        result: DeleteResult = await self.get_collection(collection).delete_one(query)
        logger.debug(f"Deleted {result.deleted_count} document(s).")
        return result
