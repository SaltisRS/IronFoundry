import discord
from loguru import logger
from ..modules.mongo import MongoClient


client = MongoClient()

async def get_roles() -> None | list:
    try:
        roles = await client.get_many(collection="Join-roles", query={})
        join_roles: list[discord.Object] = []
        for doc in roles:
            join_roles.append({"id": doc["_id"], "name": doc["name"]})
        return join_roles
    except Exception as e:
        logger.error(f"Error getting roles: {e}")

        
async def add_role(role: discord.Role) -> None | bool:
    new_role = {"_id": role.id, "name": role.name}
    logger.info(role.name)
    try:
        await client.insert_document(collection="Join-roles", document=new_role)
        return True
    except Exception as e:
        logger.error(f"Error adding role: {e}")


async def delete_role(role: discord.Role) -> None | bool:
    try:
        await client.delete_document(collection="Join-roles", query={"_id": role.id})
        return True
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
