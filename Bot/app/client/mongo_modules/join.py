import discord
from loguru import logger
from ..modules.mongo import MongoClient


client = MongoClient()
connected = False

async def client_connect() -> None:
    global connected
    if not connected:
        try:
            await client.connect()
            await client.set_database("IronFoundry")
            connected = True
        except Exception as e:
            connected = False
            logger.error(f"Error connecting to MongoDB: {e}")

async def get_roles() -> None | list:
    await client_connect()
    try:
        roles = await client.get_collection("Join-roles")
        roles = await client.get_many(roles, {})
        join_roles: list[discord.Object] = []
        for doc in roles:
            join_roles.append(discord.Object(doc.get("_id")))
        return join_roles
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        return None
    finally:
        await client.close()
        global connected
        connected = False
        
async def add_role(role: discord.Role) -> None:
    await client_connect()
    new_role = {"_id": role.id, "name": role.name}
    try:
        roles = await client.get_collection("Join-roles")
        await client.insert_document(roles, new_role)
    except Exception as e:
        logger.error(f"Error adding role: {e}")
    finally:
        await client.close()
        global connected
        connected = False