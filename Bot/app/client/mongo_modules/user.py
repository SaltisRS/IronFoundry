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
            # update state
            connected = True
        except Exception as e:
            connected = False
            logger.error(f"Error connecting to MongoDB: {e}")


async def link_new(user_id: int, user_data: dict):
    await client_connect()
    # base format for a new user
    base_format: dict = {
        "_id": None,
        "rsn": None,
        "rank": None,
        "donations": 0,
        "event_winnings": 0,
        "loot_value": 0,
        "activity_flag": None,
        "alts": [],
        "pk_kills": 0,
        "pk_deaths": 0,
        "pk_kd": 0,
        "pk_gained": 0,
        "pk_lost": 0,
        "known_names": [],
        "hof_ref": None,
        "individual_permissions": None,
        "tags": [],
        "incidents": {},
    }

    new_user = base_format.copy()
    new_user.update(
        {"_id": user_id, "rsn": user_data.get("rsn"), "alts": user_data.get("alts")}
    )
    try:
        # check if user already exists
        users = await client.get_collection("Users")
        user = await client.get_document(users, {"_id": user_id})
        if user:
            await client.update_document(users, {"_id": user_id}, {"$set": new_user})
            return "User already exists, updated details"
        await client.insert_document(users, new_user)
        return "User linked"
    except Exception as e:
        # re-raise the exception, handle it in the calling function
        raise e
    finally:
        await client.close()
        global connected
        connected = False


async def update_rsn(user_id: int, rsn: str):
    await client_connect()
    try:
        users = await client.get_collection("Users")
        await client.update_document(users, {"_id": user_id}, {"$set": {"rsn": rsn}})
    except Exception as e:
        logger.error(f"Error updating RSN: {e}")
    finally:
        await client.close()
        global connected
        connected = False
